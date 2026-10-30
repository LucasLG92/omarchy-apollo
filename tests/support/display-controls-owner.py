"""Real device sensor and compositor checks on a private virtual display."""
from pathlib import Path
import os,subprocess,tempfile,time,json,signal,socket,sys
import dbus
source=Path(__file__).resolve().parents[2]/'platform/omarchy-apollo-display'
def interrupted(number,frame):raise InterruptedError('Display controls test interrupted')
signal.signal(signal.SIGTERM,interrupted)
os.umask(0o077)
with tempfile.TemporaryDirectory(prefix='h',dir=os.environ['XDG_RUNTIME_DIR']) as temporary:
 root=Path(temporary)
 for name in ('state','cache','config','data'):(root/name).mkdir(mode=0o700)
 env=dict(os.environ);env.update({'XDG_RUNTIME_DIR':str(root),'XDG_STATE_HOME':str(root/'state'),'XDG_CACHE_HOME':str(root/'cache'),'XDG_CONFIG_HOME':str(root/'config'),'XDG_DATA_HOME':str(root/'data'),'AQ_DRM_DEVICES':'/dev/null','HYPRLAND_NO_SD_VARS':'1','HYPRLAND_NO_SD_TARGET':'1','HYPRLAND_NO_RT':'1'})
 for key in ('HYPRLAND_INSTANCE_SIGNATURE','DISPLAY','WAYLAND_DISPLAY','QT_QPA_PLATFORM','QT_QPA_PLATFORMTHEME','QT_PLUGIN_PATH'):
  env.pop(key,None)
 processes=[];logs=[]
 try:
  log=(root/'parent.log').open('w');logs.append(log)
  parent=subprocess.Popen(['kwin_wayland','--virtual','--socket','wayland-parent','--width','1080','--height','2400','--no-lockscreen','--no-global-shortcuts','--no-kactivities'],env=env,stdout=log,stderr=subprocess.STDOUT);processes.append(parent)
  deadline=time.monotonic()+15
  while not (root/'wayland-parent').is_socket():
   assert parent.poll() is None,(root/'parent.log').read_text()[-2500:]
   assert time.monotonic()<deadline;time.sleep(0.1)
  parent_bus=dbus.SessionBus()
  while not parent_bus.name_has_owner('org.kde.KWin'):
   assert parent.poll() is None,(root/'parent.log').read_text()[-3000:]
   assert time.monotonic()<deadline,(root/'parent.log').read_text()[-3000:]
   time.sleep(0.1)
  config=root/'hyprland.lua';config.write_text('hl.monitor({ output = "", mode = "1080x2400@60", scale = 2.5 })\nhl.config({ misc = { disable_hyprland_logo = true, disable_splash_rendering = true }, debug = { disable_logs = false } })\n')
  env['WAYLAND_DISPLAY']='wayland-parent'
  log=(root/'hyprland.log').open('w');logs.append(log)
  child=subprocess.Popen(['Hyprland','--config',str(config)],env=env,stdout=log,stderr=subprocess.STDOUT);processes.append(child)
  deadline=time.monotonic()+20
  while True:
   assert child.poll() is None,(root/'hyprland.log').read_text()[-4500:]
   p=subprocess.run(['hyprctl','instances','-j'],env=env,capture_output=True,text=True,timeout=3)
   instances=json.loads(p.stdout) if p.returncode==0 and p.stdout.strip().startswith('[') else []
   ours=[value for value in instances if value['pid']==child.pid]
   if ours:break
   assert time.monotonic()<deadline;time.sleep(0.2)
  env['HYPRLAND_INSTANCE_SIGNATURE']=ours[0]['instance'];env['WAYLAND_DISPLAY']=ours[0]['wl_socket']
  def query(*args):
   p=subprocess.run(['hyprctl',*args],env=env,capture_output=True,text=True,timeout=5)
   assert p.returncode==0,p.stderr+p.stdout
   return p.stdout.strip()
  deadline=time.monotonic()+30
  while not json.loads(query('monitors','-j')):
   assert child.poll() is None,(root/'hyprland.log').read_text()[-3000:]
   if time.monotonic()>=deadline:
    log=root/'hypr'/env['HYPRLAND_INSTANCE_SIGNATURE']/'hyprland.log'
    raise TimeoutError('Nested output not ready: '+(log.read_text()[-10000:] if log.is_file() else (root/'hyprland.log').read_text()[-4000:])+'\nParent: '+(root/'parent.log').read_text()[-4000:])
   time.sleep(0.2)
  monitors=json.loads(query('monitors','-j'))
  assert len(monitors)==1 and monitors[0]['name']!='DSI-1',[row['name'] for row in monitors]
  before={key:monitors[0].get(key) for key in ('name','width','height','scale','transform')}
  output=monitors[0]['name']
  query('eval','hl.monitor({ output = '+json.dumps(output)+', mode = "1080x2400@60", scale = 2.5, transform = 0 })')
  deadline=time.monotonic()+4
  while (json.loads(query('monitors','-j'))[0]['width'],json.loads(query('monitors','-j'))[0]['height'])!=(1080,2400):
   assert time.monotonic()<deadline;time.sleep(0.1)
  checks=[]
  def check(name,condition):
   assert condition,name
   checks.append(name)
  bootstrap="import runpy,sys,signal;from pathlib import Path;m=runpy.run_path(sys.argv[1],run_name='apollo_display_test_module');m['DBusGMainLoop'](set_as_default=True);loop=m['GLib'].MainLoop();c=m['Controller'](m['dbus'].SessionBus(),m['Backend'](sys.argv[2]),Path(sys.argv[3]),loop.quit);m['GLib'].unix_signal_add(m['GLib'].PRIORITY_DEFAULT,signal.SIGTERM,lambda:(loop.quit(),False)[1]);\ntry:loop.run()\nfinally:c.release_sensor();c.events.close()"
  preferences=root/'state/omarchy-apollo/display.json'
  def start_control():
   log=(root/'controller.log').open('a');logs.append(log)
   process=subprocess.Popen(['python','-I','-c',bootstrap,str(source),output,str(preferences)],env=env,stdout=log,stderr=subprocess.STDOUT);processes.append(process)
   deadline=time.monotonic()+6
   while True:
    assert process.poll() is None,(root/'controller.log').read_text()[-4000:]
    if not parent_bus.name_has_owner('org.omarchy.Apollo.Display'):
     assert time.monotonic()<deadline;time.sleep(0.05);continue
    daemon=dbus.Interface(parent_bus.get_object('org.freedesktop.DBus','/org/freedesktop/DBus'),'org.freedesktop.DBus')
    assert int(daemon.GetConnectionUnixProcessID('org.omarchy.Apollo.Display'))==process.pid
    p=subprocess.run(['python','-I',str(source),'status'],env=env,capture_output=True,text=True,timeout=5)
    if p.returncode==0:return process
    assert time.monotonic()<deadline;time.sleep(0.1)
  def state():
   p=subprocess.run(['python','-I',str(source),'status'],env=env,capture_output=True,text=True,timeout=6)
   assert p.returncode==0,p.stderr
   return json.loads(p.stdout)
  def change(category,value,okay=True):
   p=subprocess.run(['python','-I',str(source),category,value],env=env,capture_output=True,text=True,timeout=15)
   assert (p.returncode==0)==okay,p.stderr+p.stdout
   return p.stdout.strip()
  controller=start_control()
  initial=state()
  check('default service does not claim the accelerometer or create preferences',not initial['auto'] and not initial['sensor_claimed'] and not preferences.exists())
  for name,transform in [('portrait',0),('landscape-left',1),('portrait-inverted',2),('landscape-right',3)]:
   change('orientation',name)
   value=state();touch=json.loads(query('getoption','input.touchdevice.transform','-j'))['int']
   check(name+' matches compositor and touch transforms',value['applied_transform']==transform and touch==transform)
  change('orientation','lock')
  check('lock preserves the current landscape orientation',state()['applied_transform']==3 and not state()['auto'])
  old=preferences.read_bytes();old_transform=state()['applied_transform']
  rejected=change('orientation','invalid;touch /tmp/apollo-display-should-not-exist',False)
  check('invalid orientation is rejected without changing preferences or monitor',rejected=='APOLLO_INVALID_ORIENTATION' and preferences.read_bytes()==old and state()['applied_transform']==old_transform)
  rejected=change('refresh','999',False)
  check('invalid refresh selection is rejected without changing preferences',rejected=='APOLLO_INVALID_DISPLAY_SETTING' and preferences.read_bytes()==old)
  # The virtual output has no 144 Hz mode; the phone's real panel does.
  rejected=change('refresh','144',False)
  check('an unadvertised refresh mode is rejected with the display unchanged',rejected=='APOLLO_REFRESH_UNAVAILABLE' and state()['applied_transform']==old_transform and preferences.read_bytes()==old)
  preferences.parent.chmod(0o500)
  try:
   rejected=change('orientation','portrait',False)
  finally:preferences.parent.chmod(0o700)
  value=state();touch=json.loads(query('getoption','input.touchdevice.transform','-j'))['int']
  check('a real preference-write failure restores the previous monitor and touch state',rejected=='APOLLO_DISPLAY_CHANGE_FAILED' and value['applied_transform']==old_transform and touch==old_transform and preferences.read_bytes()==old)
  change('orientation','auto')
  value=state()
  check('automatic rotation claims the actual device accelerometer',value['auto'] and value['sensor_claimed'])
  check('actual sensor orientation is represented by a matching transform',value['orientation'] in ('normal','left-up','bottom-up','right-up') and value['applied_transform']=={'normal':0,'left-up':1,'bottom-up':2,'right-up':3}[value['orientation']])
  change('orientation','landscape-left')
  check('manual orientation releases the actual accelerometer claim',not state()['auto'] and not state()['sensor_claimed'])
  def reload_and_wait():
   with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as events:
    events.connect(str(root/'hypr'/env['HYPRLAND_INSTANCE_SIGNATURE']/'.socket2.sock'))
    events.settimeout(5);query('reload');buffer=bytearray()
    while b'configreloaded>>' not in buffer:
     part=events.recv(65536);assert part;buffer.extend(part);assert len(buffer)<262144
  reload_and_wait()
  deadline=time.monotonic()+6
  while state()['applied_transform']!=1:
   assert time.monotonic()<deadline;time.sleep(0.1)
  check('saved orientation is restored after a real compositor configuration reload',json.loads(query('getoption','input.touchdevice.transform','-j'))['int']==1)
  controller.terminate();controller.wait(timeout=8)
  reload_and_wait();time.sleep(0.2)
  check('the test compositor returns to its base transform while the service is stopped',json.loads(query('monitors','-j'))[0]['transform']==0)
  controller=start_control()
  deadline=time.monotonic()+6
  while state()['applied_transform']!=1:
   assert time.monotonic()<deadline;time.sleep(0.1)
  check('service restart restores the persisted orientation',state()['transform']==1 and json.loads(query('getoption','input.touchdevice.transform','-j'))['int']==1)
  # Exercise the real keyboard layer without sending any key to the phone.
  log=(root/'keyboard.log').open('w');logs.append(log)
  keyboard=subprocess.Popen(['wvkbd-mobintl','--hidden','-H','300','-L','180','--fn','JetBrainsMono Nerd Font 18','-l','simple,special,emoji'],env=env,stdout=log,stderr=subprocess.STDOUT);processes.append(keyboard)
  time.sleep(0.3);assert keyboard.poll() is None,(root/'keyboard.log').read_text()
  keyboard.send_signal(signal.SIGUSR2)
  def keyboard_height():
   layers=json.loads(query('layers','-j'))
   values=[layer for monitor in layers.values() for group in monitor.get('levels',{}).values() for layer in group if 'wvkbd' in layer.get('namespace','').lower()]
   return values[0].get('h') if len(values)==1 else None
  deadline=time.monotonic()+5
  while keyboard_height()!=180:
   assert time.monotonic()<deadline,query('layers','-j');time.sleep(0.1)
  check('the real keyboard reserves 180 logical pixels in landscape',keyboard_height()==180)
  change('orientation','portrait')
  deadline=time.monotonic()+5
  while keyboard_height()!=300:
   assert time.monotonic()<deadline,query('layers','-j');time.sleep(0.1)
  check('the real keyboard reserves 300 logical pixels in portrait',keyboard_height()==300)
  keyboard.terminate();keyboard.wait(timeout=8)
  log=(root/'settings.log').open('w');logs.append(log)
  settings=subprocess.Popen(['python','-I',str(source),'settings'],env=env,stdout=log,stderr=subprocess.STDOUT);processes.append(settings)
  deadline=time.monotonic()+8
  while True:
   assert settings.poll() is None,(root/'settings.log').read_text()[-3000:]
   clients=json.loads(query('clients','-j'))
   ours=[client for client in clients if client.get('class')=='org.omarchy.Apollo.DisplaySettings']
   if ours:break
   assert time.monotonic()<deadline;time.sleep(0.1)
  check('the actual GTK settings window renders inside the private compositor',len(ours)==1 and all(number>0 for number in ours[0]['size']))
  query('eval','hl.dispatch(hl.dsp.window.close())');settings.wait(timeout=8)
  check('the settings window closes normally through a window-manager request',settings.returncode==0)
  check('the tested compositor has no configuration errors',not query('configerrors'))
  value=json.loads(preferences.read_text())
  check('preferences are private and contain only display settings',set(value)=={'auto','transform','refresh'} and preferences.stat().st_mode & 0o777==0o600)
  controller.terminate();controller.wait(timeout=8)
  check('the display controller exits normally and releases its sensor connection',controller.returncode==0)
  record={'passed':len(checks),'checks':checks,'backend':'Hyprland Wayland on virtual KWin','source_sha256':__import__('hashlib').sha256(source.read_bytes()).hexdigest(),'physical_display_used':False,'physical_touch_or_refresh_acceptance':False,'owner_credentials_used':False,'sensor_used':True,'physical_orientation_changes_tested':False}
  Path(sys.argv[1]).write_text(json.dumps(record))
 finally:
  for child in reversed(processes):
   if child.poll() is None:
    child.terminate()
    try:child.wait(timeout=8)
    except subprocess.TimeoutExpired:child.kill();child.wait()
  for log in logs:log.close()
