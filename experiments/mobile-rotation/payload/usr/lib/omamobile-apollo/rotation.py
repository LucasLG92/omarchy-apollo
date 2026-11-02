#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Apollo SSC SensorProxy client for Hyprland 0.57; reviewed profile required."""
import argparse
import fcntl
import json
import math
import os
import re
import stat
import subprocess
import sys
import time
from pathlib import Path

ORIENTATIONS={'normal':0,'left-up':1,'bottom-up':2,'right-up':3}

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

class Policy:
    """Stable orientation timer; freeze means retain current orientation."""
    def __init__(self,dwell=0.45):
        self.dwell=dwell;self.pending=None;self.since=None;self.current=None;self.allowed=False
    def gate(self,allowed):
        self.allowed=allowed
        if not allowed:self.pending=None;self.since=None
    def observe(self,orientation,now):
        target=ORIENTATIONS.get(orientation)
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
            attempted=True
            # Touch.cpp consumes the already calibrated normalized e.pos
            # directly. No monitor transform is applied in that input path:
            # libinput and output must both receive the same quarter-turn.
            self.backend.set_pair(target,target,self.config['monitor'])
            self.wait_transform(before,target)
            self.touch=(target,self.config['monitor'])
            self.monitor_transform=target
            return True
        except Exception:
            if before is not None and attempted:
                try:
                    current=self.backend.snapshot()
                    # Never overwrite a foreign transform/monitor/layout change.
                    if invariant(current)==invariant(before) and current['transform'] in (before['transform'],target):
                        self.backend.set_pair(before['transform'],*old_touch)
                        self.wait_transform(current,before['transform'])
                except Exception:pass
            raise RotationError('rotation transaction failed; paused for review') from None
        finally:self.busy=False

class Hyprland:
    def __init__(self,config):self.config=config
    def call(self,*args):
        r=subprocess.run(['/usr/bin/hyprctl',*args],capture_output=True,timeout=2)
        require(r.returncode==0 and len(r.stdout)<=262144)
        return r.stdout
    def snapshot(self):return monitor_snapshot(json.loads(self.call('-j','monitors')),self.config['monitor'])
    def touch_present(self,name):
        data=json.loads(self.call('-j','devices'))
        rows=data.get('touch') if isinstance(data,dict) else None
        return isinstance(rows,list) and sum(isinstance(x,dict) and x.get('name')==name for x in rows)==1
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
        try:
            m=self.backend.snapshot()
            r=subprocess.run(['/usr/bin/omarchy-shell','lock','status'],capture_output=True,timeout=2)
            lock=json.loads(r.stdout)
            require(r.returncode==0 and isinstance(lock,dict))
            fields=('locked','requested','pending','sessionLocked','secure','authenticating')
            require(all(type(lock.get(x)) is bool for x in fields))
            allowed=(not self.failed and m['dpmsStatus'] and not self.lockfile.exists() and not any(lock[x] for x in fields)
                     and not self.sleeping and self.active() and self.prop(self.sensor,self.sensorpath,self.sensor,'HasAccelerometer') is True)
        except Exception:allowed=False
        self.policy.gate(allowed)
        try:
            if not allowed and self.claimed:self.method('ReleaseAccelerometer');self.claimed=False
            elif allowed and not self.claimed:
                self.method('ClaimAccelerometer');self.claimed=True
                self.observe(self.prop(self.sensor,self.sensorpath,self.sensor,'AccelerometerOrientation'))
        except Exception:self.policy.gate(False)
        return True
    def observe(self,orientation):
        self.policy.observe(orientation,time.monotonic())
        if self.timer:self.GLib.source_remove(self.timer)
        self.timer=self.GLib.timeout_add(450,self.commit)
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
                self.transaction.apply(self.config['orientation_map'][target]);self.policy.committed(target)
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
        client=Client(config);loop=client.GLib.MainLoop();client.loop=loop
        try:
            loop.run();require(not client.failed)
        finally:
            if client.claimed:
                try:client.method('ReleaseAccelerometer')
                except Exception:pass
    finally:os.close(fd)

if __name__=='__main__':
    try:main()
    except Exception:raise SystemExit('Auto-rotation stopped; profile/backend requires review') from None
