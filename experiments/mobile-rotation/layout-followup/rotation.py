#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Apollo SSC SensorProxy client for Hyprland 0.57; reviewed profile required."""
import argparse
import fcntl
import json
import math
import os
import re
import socket
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ORIENTATIONS={'normal':0,'left-up':1,'bottom-up':2,'right-up':3}
APP_OVERRIDES=Path('/etc/apollo/app-orientation.json')
APP_HINTS=Path('/run/omamobile/orientation-hints.json')
FOREGROUND_EVENTS={b'activewindowv2',b'workspacev2',b'closewindow',b'movewindowv2',b'focusedmonv2'}

# One named rule, two lifetime listeners and generation-bound five-second
# compositor timers. No daemon-lifetime dependency, idle poll, focus action or
# title access. Named rule replacement keeps the rule count bounded.
HOME_GUARD_LUA=r'''
local g = _apollo_rotation_android_hold
if not g then
  g = { version=1, active=false }
  _apollo_rotation_android_hold = g
end
-- Refresh functions on a package upgrade without replacing the state table
-- captured by the two lifetime listeners or old generation timers.
  function g.finish(generation)
    if g.generation ~= generation then return end
    if g.rule then g.rule:set_enabled(false) end
    g.active=false
    if not g.class or g.was_float then return end
    local targets={}
    for _,w in ipairs(hl.get_windows()) do
      if w.mapped and w.class == g.class then targets[#targets+1]=w end
    end
    -- A legitimate second task is never closed, merged or tiled with Android.
    if #targets == 1 and targets[1].floating and
       targets[1].fullscreen == 1 and targets[1].workspace and targets[1].workspace.id == g.workspace then
      hl.dispatch(hl.dsp.window.float({window='address:'..targets[1].address, action='off'}))
    end
    if #targets <= 1 then g.class=nil;g.old_address=nil end
  end
  function g.cancel()
    g.finish(g.generation)
  end
  function g.expire(generation)
    if not g.active then return end
    g.finish(generation)
  end
  function g.start(generation, class, workspace, home, address, was_float)
    local inherited_float=was_float
    if g.class == class and g.was_float == false then inherited_float=false end
    g.cancel()
    local current = hl.get_active_workspace()
    if not current or current.id ~= home or hl.get_active_window() then return end
    local found=false
    for _,w in ipairs(hl.get_windows()) do
      if w.mapped and w.address == address and w.class == class and w.workspace and w.workspace.id == workspace then found=true end
    end
    if not found then return end
    g.generation,g.class,g.workspace,g.home,g.old_address,g.was_float=generation,class,workspace,home,address,inherited_float
    g.rule=hl.window_rule({name='apollo-rotation-background-android', match={class='^'..class:gsub('%.','\\.')..'$'},
                           workspace=tostring(workspace)..' silent', float=true, maximize=true})
    g.active=true
    -- Old generation timers may finish naturally; they cannot disable a newer
    -- rule. The 450ms rotation dwell bounds simultaneous five-second timers.
    g.timer=hl.timer(function() g.expire(generation) end,{timeout=5000,type='oneshot'})
    assert(g.active == true and g.rule:is_enabled() == true)
    return true
  end
if not g.listeners then
  g.listeners={
    hl.on('workspace.active',function(w) if g.active and w and w.id ~= g.home then g.cancel() end end),
    hl.on('window.active',function(w) if g.active and w then g.cancel() end end)
  }
end
'''

class RotationError(RuntimeError): pass

def require(value):
    if not value: raise RotationError('rotation precondition failed')

def profile(data):
    require(isinstance(data,dict) and data.get('monitor_rule_verified') is True)
    for name in ('monitor','touch_device','baseline_touch_output'):
        require(isinstance(data.get(name),str) and data[name]!='UNSET' and re.fullmatch(r'[A-Za-z0-9_.:()+ -]{1,100}',data[name]))
    require(data['monitor'].startswith('DSI-') and type(data.get('baseline_touch_transform')) is int and data['baseline_touch_transform'] in range(4))
    require(type(data.get('baseline_monitor_transform')) is int and data['baseline_monitor_transform'] in range(4))
    mapping=data.get('orientation_map',[0,1,2,3])
    require(isinstance(mapping,list) and all(type(x) is int for x in mapping) and sorted(mapping)==[0,1,2,3])
    return dict(data,orientation_map=mapping)

def read_profile(path):
    fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid==0 and not info.st_mode&0o022 and 0<info.st_size<=8192)
        data=os.read(fd,8193);require(len(data)<=8192)
        return profile(json.loads(data))
    finally:os.close(fd)

def app_rules(data,source):
    require(isinstance(data,dict) and set(data)=={'version','rules'} and type(data.get('version')) is int and data['version']==1)
    require(isinstance(data['rules'],list) and len(data['rules'])<=64)
    rules={}
    for row in data['rules']:
        require(isinstance(row,dict) and set(row)=={'app_id','orientation','source'})
        name=row['app_id']
        require(isinstance(name,str) and 0<len(name)<=256 and name==name.strip() and name.isprintable() and name not in rules)
        require(row['orientation'] in ('auto','portrait','landscape') and row['source']==source)
        rules[name]=row['orientation']
    return rules

def read_app_rules(path,source):
    try:fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW)
    except FileNotFoundError:return {}
    try:
        info=os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid==0 and not info.st_mode&0o022 and 0<info.st_size<=65536)
        body=os.read(fd,65537);require(len(body)<=65536)
        return app_rules(json.loads(body),source)
    finally:os.close(fd)

class AppOrientation:
    """Exact foreground app identity; user compatibility overrides metadata."""
    def __init__(self):self.overrides={};self.hints={}
    def reload(self):
        overrides=read_app_rules(APP_OVERRIDES,'user-compatibility')
        hints=read_app_rules(APP_HINTS,'android-activity')
        self.overrides,self.hints=overrides,hints
    def resolve(self,app_id):
        if app_id in self.overrides:return self.overrides[app_id],'user-compatibility'
        if app_id in self.hints:return self.hints[app_id],'android-activity'
        return 'auto','sensor'
    def constraint(self,app_id):return self.resolve(app_id)[0]

def orientation_target(sensor_orientation,mapping,constraint):
    require(constraint in ('auto','portrait','landscape'))
    index=ORIENTATIONS.get(sensor_orientation)
    sensor=mapping[index] if index is not None else None
    if constraint=='portrait':return sensor if sensor in (0,2) else 0
    if constraint=='landscape':return sensor if sensor in (1,3) else 1
    return sensor

class Policy:
    """Stable orientation timer; freeze means retain current orientation."""
    def __init__(self,dwell=0.45):
        self.dwell=dwell;self.pending=None;self.since=None;self.current=None;self.allowed=False
    def gate(self,allowed):
        self.allowed=allowed
        if not allowed:self.pending=None;self.since=None
    def observe(self,orientation,now):
        self.observe_target(ORIENTATIONS.get(orientation),now)
    def observe_target(self,target,now):
        if not self.allowed or target is None:
            self.pending=None;self.since=None;return
        if target!=self.pending:self.pending=target;self.since=now
    def due(self,now):
        if self.allowed and self.pending is not None and now-self.since>=self.dwell and self.pending!=self.current:return self.pending
        return None
    def committed(self,target):self.current=target

def monitor_snapshot(rows,name):
    require(isinstance(rows,list))
    choices=[x for x in rows if isinstance(x,dict) and x.get('name')==name]
    require(len(choices)==1)
    m=choices[0]
    for key in ('id','width','height','x','y','transform'):require(type(m.get(key)) is int)
    for key in ('scale','refreshRate'):require(type(m.get(key)) in (int,float) and math.isfinite(m[key]) and m[key]>0)
    require(m['width']>0 and m['height']>0 and m['transform'] in range(4) and type(m.get('dpmsStatus')) is bool)
    return {k:m[k] for k in ('name','id','width','height','x','y','scale','refreshRate','transform','dpmsStatus')}

def invariant(m):return tuple(m[k] for k in ('name','id','width','height','x','y','scale','refreshRate'))

class Transaction:
    def __init__(self,backend,config):
        self.backend=backend;self.config=profile(config);self.busy=False
        self.touch=(config['baseline_touch_transform'],config['baseline_touch_output'])
        self.monitor_transform=config['baseline_monitor_transform']
    def adopt_live_pair(self,status_path):
        current=self.backend.snapshot()
        if current['transform']==self.monitor_transform:return
        # Read before Client.refresh/write_status can replace the last daemon's
        # acknowledged request. This is not a libinput matrix readback.
        fd=os.open(status_path,os.O_RDONLY|os.O_CLOEXEC|os.O_NOFOLLOW)
        try:
            info=os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and info.st_nlink==1 and
                    not info.st_mode&0o077 and 0<info.st_size<=4096)
            previous=json.loads(os.read(fd,4097))
        finally:os.close(fd)
        require(previous.get('version')==1 and type(previous.get('last_output_transform')) is int and
                type(previous.get('touch_transform_requested')) is int and
                previous['last_output_transform']==previous['touch_transform_requested']==current['transform'])
        self.monitor_transform=current['transform'];self.touch=(current['transform'],self.config['monitor'])
    def wait_transform(self,before,target):
        # The property flush updates libinput now, but MonitorRuleManager only
        # applies the output on render.preChecks. Do not treat one old frame as
        # failure. Stop on a foreign layout/transform instead of overwriting it.
        deadline=time.monotonic()+1.0
        while True:
            current=self.backend.snapshot()
            require(invariant(current)==invariant(before) and current['transform'] in (before['transform'],target))
            if current['transform']==target:return current
            require(time.monotonic()<deadline)
            time.sleep(.025)
    def apply(self,target):
        require(type(target) is int and target in range(4) and not self.busy)
        self.busy=True;before=None;old_touch=self.touch;attempted=False
        try:
            before=self.backend.snapshot();require(before['dpmsStatus'])
            require(before['transform']==self.monitor_transform)
            require(self.backend.touch_present(self.config['touch_device']))
            if target!=before['transform'] and hasattr(self.backend,'hold_background_android'):
                self.backend.hold_background_android()
            attempted=True
            # Touch.cpp consumes the already calibrated normalized e.pos
            # directly. No monitor transform is applied in that input path:
            # libinput and output must both receive the same quarter-turn.
            self.backend.set_pair(target,target,self.config['monitor'])
            self.wait_transform(before,target)
            if target!=before['transform']:
                # Hyprland 0.57's soft monitor-rule path updates xdg-output and
                # layer sizes but omits wl_output's modeChanged notification.
                # Publish the CURRENT rule once through the official dispatcher;
                # no mode, refresh, scale or reserved-area value is written.
                self.backend.publish_layout()
                self.wait_transform(before,target)
            self.touch=(target,self.config['monitor'])
            self.monitor_transform=target
            return True
        except Exception:
            if hasattr(self.backend,'cancel_home_hold'):
                try:self.backend.cancel_home_hold()
                except Exception:pass
            if before is not None and attempted:
                try:
                    current=self.backend.snapshot()
                    # Never overwrite a foreign transform/monitor/layout change.
                    if invariant(current)==invariant(before) and current['transform'] in (before['transform'],target):
                        self.backend.set_pair(before['transform'],*old_touch)
                        self.wait_transform(current,before['transform'])
                        if current['transform']!=before['transform']:
                            self.backend.publish_layout()
                            self.wait_transform(current,before['transform'])
                except Exception:pass
            raise RotationError('rotation transaction failed; paused for review') from None
        finally:self.busy=False

class Hyprland:
    def __init__(self,config):self.config=config;self.last_home_hold_armed=False
    def call(self,*args):
        r=subprocess.run(['/usr/bin/hyprctl',*args],capture_output=True,timeout=2)
        require(r.returncode==0 and len(r.stdout)<=262144)
        return r.stdout
    def snapshot(self):return monitor_snapshot(json.loads(self.call('-j','monitors')),self.config['monitor'])
    def foreground_app(self):
        data=json.loads(self.call('-j','activewindow'));require(isinstance(data,dict))
        name=data.get('class')
        if name is None or name=='':return None
        require(isinstance(name,str) and len(name)<=256 and name.isprintable())
        return name
    def cancel_home_hold(self):
        reply=self.call('eval',HOME_GUARD_LUA+"\nif _apollo_rotation_android_hold and _apollo_rotation_android_hold.version==1 then _apollo_rotation_android_hold.cancel() end")
        require(reply.strip()==b'ok')
    def hold_background_android(self):
        self.last_home_hold_armed=False
        active=json.loads(self.call('-j','activewindow'))
        home=json.loads(self.call('-j','activeworkspace'))
        if active.get('class') or home.get('windows')!=0 or type(home.get('id')) is not int:return
        rows=json.loads(self.call('-j','clients'));require(isinstance(rows,list))
        candidates=[w for w in rows if isinstance(w,dict) and w.get('mapped',True) and not w.get('hidden',False)
          and isinstance(w.get('class'),str) and re.fullmatch(r'waydroid\.[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+',w['class'])
          and type((w.get('workspace') or {}).get('id')) is int and w['workspace']['id']>0 and w['workspace']['id']!=home['id']]
        if not candidates:return
        candidates.sort(key=lambda w:w.get('focusHistoryID') if type(w.get('focusHistoryID')) is int and w['focusHistoryID']>=0 else 2147483647)
        w=candidates[0];address=w.get('address')
        if not isinstance(address,str) or not re.fullmatch(r'0x[0-9a-fA-F]+',address):return
        generation=str(time.monotonic_ns())
        args=(generation,w['class'],w['workspace']['id'],home['id'],address,bool(w.get('floating',False)))
        literal=lambda x:('true' if x else 'false') if type(x) is bool else json.dumps(x)
        reply=self.call('eval',HOME_GUARD_LUA+'\nassert(_apollo_rotation_android_hold.start('+','.join(literal(x) for x in args)+'),"background rotation context changed")')
        require(reply.strip()==b'ok')
        # start() checks the live Lua Window.address (0x-prefixed in0.57)
        # and asserts both active and rule:is_enabled before this IPC returns.
        self.last_home_hold_armed=True
    def touch_present(self,name):
        data=json.loads(self.call('-j','devices'))
        rows=data.get('touch') if isinstance(data,dict) else None
        return isinstance(rows,list) and sum(isinstance(x,dict) and x.get('name')==name for x in rows)==1
    def publish_layout(self):
        reply=self.call('eval','hl.dispatch(hl.dsp.force_renderer_reload())').decode(errors='replace')
        require(reply.strip()=='ok')
    def set_pair(self,monitor_transform,touch_transform,touch_output):
        # hl.monitor 0.57 copies an existing exact-output rule before applying
        # provided fields. A reviewed explicit-output rule is mandatory here.
        lua=('hl.device({name='+json.dumps(self.config['touch_device'])+',transform='+str(touch_transform)+
             ',output='+json.dumps(touch_output)+'});hl.monitor({output='+json.dumps(self.config['monitor'])+
             ',transform='+str(monitor_transform)+'});hl.exec_scheduled_prop_refresh_immediately()')
        reply=self.call('eval',lua).decode(errors='replace')
        # Commands.cpp's evalRequest returns exactly "ok" for accepted code.
        require(reply.strip()=='ok')

class Client:
    def __init__(self,config):
        import gi
        gi.require_version('Gio','2.0')
        from gi.repository import Gio,GLib
        self.Gio,self.GLib=Gio,GLib
        self.config=config;self.backend=Hyprland(config);self.transaction=Transaction(self.backend,config)
        self.policy=Policy();self.claimed=False;self.sleeping=False;self.timer=0;self.failed=False;self.loop=None
        self.apps=AppOrientation();self.foreground_app=None;self.app_constraint='auto';self.app_source='sensor';self.sensor_orientation=None
        self.status_path=Path(os.environ['XDG_RUNTIME_DIR'])/'omamobile-rotation-state.json';self.status_last=None
        self.transaction.adopt_live_pair(self.status_path)
        self.policy.current=self.transaction.monitor_transform
        self.focus_dirty=False;self.event_buffer=b''
        self.bus=Gio.bus_get_sync(Gio.BusType.SYSTEM,None)
        self.sensor='net.hadess.SensorProxy';self.sensorpath='/net/hadess/SensorProxy'
        self.bus.signal_subscribe(self.sensor,'org.freedesktop.DBus.Properties','PropertiesChanged',self.sensorpath,None,Gio.DBusSignalFlags.NONE,self.changed)
        self.bus.signal_subscribe('org.freedesktop.login1','org.freedesktop.login1.Manager','PrepareForSleep',None,None,Gio.DBusSignalFlags.NONE,self.sleep)
        self.bus.signal_subscribe('org.freedesktop.login1','org.freedesktop.DBus.Properties','PropertiesChanged',None,None,Gio.DBusSignalFlags.NONE,lambda *a:self.refresh())
        # Match the existing native QuickSettings tile exactly. Its lockfile
        # currently uses HOME/.local/state, including when XDG_STATE_HOME differs.
        self.lockfile=Path.home()/'.local/state/omamobile/rotation-lock'
        self.watch=Gio.File.new_for_path(str(self.lockfile)).monitor_file(Gio.FileMonitorFlags.NONE,None)
        self.watch.connect('changed',lambda *a:self.refresh())
        self.rule_watches=[]
        for path in (APP_OVERRIDES,APP_HINTS):
            try:
                watch=Gio.File.new_for_path(str(path)).monitor_file(Gio.FileMonitorFlags.NONE,None)
                watch.connect('changed',lambda *a:self.queue_focus_refresh());self.rule_watches.append(watch)
            except Exception:pass # The existing health check also reloads rules.
        signature=os.environ.get('HYPRLAND_INSTANCE_SIGNATURE','')
        require(re.fullmatch(r'[A-Za-z0-9_.-]{1,200}',signature))
        event_path=Path(os.environ['XDG_RUNTIME_DIR'])/'hypr'/signature/'.socket2.sock'
        event_info=event_path.lstat();require(stat.S_ISSOCK(event_info.st_mode) and event_info.st_uid==os.getuid())
        self.event_socket=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.event_socket.settimeout(2);self.event_socket.connect(str(event_path));self.event_socket.setblocking(False)
        GLib.io_add_watch(self.event_socket.fileno(),GLib.IO_IN|GLib.IO_HUP|GLib.IO_ERR,self.foreground_event)
        # Hyprland0.57 exposes no DPMS-specific Lua event. Coarse watchdog only;
        # orientations are D-Bus events. No sensor-rate/fps/power-policy writes.
        GLib.timeout_add_seconds(5,self.refresh)
        self.refresh()
    def prop(self,name,path,iface,prop):
        value=self.bus.call_sync(name,path,'org.freedesktop.DBus.Properties','Get',
            self.GLib.Variant('(ss)',(iface,prop)),self.GLib.VariantType.new('(v)'),self.Gio.DBusCallFlags.NONE,1000,None)
        return value.unpack()[0]
    def method(self,method):
        self.bus.call_sync(self.sensor,self.sensorpath,self.sensor,method,None,None,self.Gio.DBusCallFlags.NONE,1000,None)
    def active(self):
        manager='org.freedesktop.login1';base='/org/freedesktop/login1'
        user=self.bus.call_sync(manager,base,manager+'.Manager','GetUser',self.GLib.Variant('(u)',(os.getuid(),)),
             self.GLib.VariantType.new('(o)'),self.Gio.DBusCallFlags.NONE,1000,None).unpack()[0]
        display=self.prop(manager,user,manager+'.User','Display')
        require(isinstance(display,tuple) and len(display)==2 and display[1]!='/')
        return self.prop(manager,display[1],manager+'.Session','Active') is True and self.prop(manager,display[1],manager+'.Session','LockedHint') is False
    def refresh(self):
        app_changed=False
        try:
            m=self.backend.snapshot()
            r=subprocess.run(['/usr/bin/omarchy-shell','lock','status'],capture_output=True,timeout=2)
            lock=json.loads(r.stdout)
            require(r.returncode==0 and isinstance(lock,dict))
            fields=('locked','requested','pending','sessionLocked','secure','authenticating')
            require(all(type(lock.get(x)) is bool for x in fields))
            allowed=(not self.failed and m['dpmsStatus'] and not self.lockfile.exists() and not any(lock[x] for x in fields)
                     and not self.sleeping and self.active() and self.prop(self.sensor,self.sensorpath,self.sensor,'HasAccelerometer') is True)
            if allowed:
                self.apps.reload();name=self.backend.foreground_app();constraint,source=self.apps.resolve(name)
                app_changed=name!=self.foreground_app or constraint!=self.app_constraint
                self.foreground_app,self.app_constraint,self.app_source=name,constraint,source
        except Exception:allowed=False
        self.policy.gate(allowed)
        try:
            if not allowed and self.claimed:
                self.method('ReleaseAccelerometer');self.claimed=False;self.sensor_orientation=None
            elif allowed and not self.claimed:
                self.method('ClaimAccelerometer');self.claimed=True
                self.observe(self.prop(self.sensor,self.sensorpath,self.sensor,'AccelerometerOrientation'))
            elif allowed and self.claimed and app_changed:self.queue_orientation()
        except Exception:self.policy.gate(False)
        self.write_status()
        return True
    def write_status(self):
        # One current numeric/enum snapshot, never an orientation history or
        # application identity. Touch is an acknowledged request, not readback.
        body=json.dumps({'version':1,'constraint':self.app_constraint,'constraint_source':self.app_source,
             'allowed':self.policy.allowed,'last_output_transform':self.transaction.monitor_transform,
             'touch_transform_requested':self.transaction.touch[0],
             'last_background_hold_armed':self.backend.last_home_hold_armed},sort_keys=True).encode()+b'\n'
        if body==self.status_last:return
        temporary=None
        try:
            with tempfile.NamedTemporaryFile(dir=self.status_path.parent,prefix='.omamobile-axis-',delete=False) as stream:
                temporary=stream.name;stream.write(body)
            os.replace(temporary,self.status_path);temporary=None;self.status_last=body
        except Exception:pass
        finally:
            if temporary is not None:
                try:os.unlink(temporary)
                except OSError:pass
    def observe(self,orientation):
        self.sensor_orientation=orientation
        self.queue_orientation()
    def queue_orientation(self):
        target=orientation_target(self.sensor_orientation,self.config['orientation_map'],self.app_constraint)
        self.policy.observe_target(target,time.monotonic())
        if self.timer:self.GLib.source_remove(self.timer)
        self.timer=self.GLib.timeout_add(450,self.commit)
    def queue_focus_refresh(self):
        if not self.focus_dirty:
            self.focus_dirty=True;self.GLib.idle_add(self.focus_refresh)
    def focus_refresh(self):
        self.focus_dirty=False;self.refresh();return False
    def foreground_event(self,fd,condition):
        try:
            require(not condition&(self.GLib.IO_HUP|self.GLib.IO_ERR))
            try:body=self.event_socket.recv(65536)
            except BlockingIOError:return True
            require(body);self.event_buffer+=body;require(len(self.event_buffer)<=262144)
            lines=self.event_buffer.split(b'\n');self.event_buffer=lines.pop()
            # Only event names are consumed; addresses, titles and app names
            # in the socket2 payload are discarded without logging them.
            if any(line.partition(b'>>')[0] in FOREGROUND_EVENTS for line in lines):self.queue_focus_refresh()
            return True
        except Exception:
            self.failed=True;self.refresh()
            if self.loop is not None:self.loop.quit()
            return False
    def changed(self,*args):
        try:
            iface,values,invalid=args[-1].unpack()
            if iface==self.sensor and 'AccelerometerOrientation' in values and self.claimed:self.observe(values['AccelerometerOrientation'])
        except Exception:self.policy.gate(False)
    def sleep(self,*args):
        self.sleeping=args[-1].unpack()[0] is True;self.refresh()
    def commit(self):
        self.timer=0;self.refresh()
        target=self.policy.due(time.monotonic())
        if target is not None:
            try:
                self.transaction.apply(target);self.policy.committed(target);self.write_status()
            except RotationError:
                # GLib catches exceptions raised by callbacks. Latch failure so
                # a later health check cannot silently retry a partial change.
                self.failed=True
                self.policy.gate(False)
                if self.claimed:
                    try:self.method('ReleaseAccelerometer')
                    except Exception:pass
                    self.claimed=False
                print('Auto-rotation paused; monitor/input transaction requires review',file=sys.stderr)
                if self.loop is not None:self.loop.quit()
        return False

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--profile',required=True)
    args=parser.parse_args();config=read_profile(args.profile)
    require(os.getuid()!=0 and os.environ.get('WAYLAND_DISPLAY'))
    runtime=Path(os.environ['XDG_RUNTIME_DIR']);require(runtime.is_dir() and runtime.stat().st_uid==os.getuid())
    fd=os.open(runtime/'omamobile-autorotate.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:
        info=os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and info.st_nlink==1 and not info.st_mode&0o077)
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        # A previous process may have stopped during an output transaction.
        Hyprland(config).cancel_home_hold()
        client=Client(config);loop=client.GLib.MainLoop();client.loop=loop
        try:
            loop.run();require(not client.failed)
        finally:
            try:client.backend.cancel_home_hold()
            except Exception:pass
            if client.claimed:
                try:client.method('ReleaseAccelerometer')
                except Exception:pass
            client.event_socket.close()
    finally:os.close(fd)

if __name__=='__main__':
    try:main()
    except Exception:raise SystemExit('Auto-rotation stopped; profile/backend requires review') from None
