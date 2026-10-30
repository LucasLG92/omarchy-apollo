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
  config=root/'hyprland.lua';config.write_text('hl.monitor({ output = "", mode = "1080x2400@60", scale = 2.5 })\nhl.config({ input = { follow_mouse = 0 }, misc = { disable_hyprland_logo = true, disable_splash_rendering = true }, debug = { disable_logs = false } })\n')
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
  import runpy,hashlib
  candidate=Path(sys.argv[2]);assert candidate.is_file()
  tools=root/'helpers'
  provenance=runpy.run_path(str(Path(__file__).resolve().parents[1]/'build_keyboard_helpers.py'))['build'](tools)
  fixture=Path(__file__).with_name('keyboard-text-fixture.py')
  log=(root/'fixture.log').open('w');logs.append(log)
  app=subprocess.Popen(['python','-I',str(fixture)],env=env,stdout=log,stderr=subprocess.STDOUT);processes.append(app)
  deadline=time.monotonic()+10
  while not parent_bus.name_has_owner('org.omarchy.Apollo.KeyboardFixture'):
   assert app.poll() is None,(root/'fixture.log').read_text()[-4000:]
   assert time.monotonic()<deadline;time.sleep(0.1)
  bus_api=dbus.Interface(parent_bus.get_object('org.freedesktop.DBus','/org/freedesktop/DBus'),'org.freedesktop.DBus')
  check('fixture_bus_owned_by_test_process',int(bus_api.GetConnectionUnixProcessID('org.omarchy.Apollo.KeyboardFixture'))==app.pid)
  fixture_api=dbus.Interface(parent_bus.get_object('org.omarchy.Apollo.KeyboardFixture','/org/omarchy/Apollo/KeyboardFixture'),'org.omarchy.Apollo.KeyboardFixture1')
  assert fixture_api.Focus('button',timeout=3)
  keyboard=None
  def layers():
   values=json.loads(query('layers','-j'))
   return [layer for monitor in values.values() for group in monitor.get('levels',{}).values() for layer in group if 'wvkbd' in layer.get('namespace','').lower()]
  def wait_count(count):
   deadline=time.monotonic()+5
   stable=None
   while True:
    if keyboard is not None:assert keyboard.poll() is None,(root/'keyboard.log').read_text()[-3000:]
    now=time.monotonic()
    if len(layers())==count:
     if stable is None:stable=now
     # A layer entry precedes its first rendered buffer and popup configure.
     if now-stable>=(0.35 if count else 0.1):return
    else:stable=None
    assert time.monotonic()<deadline,('Layer count',count,layers(),(root/'keyboard.log').read_text()[-3000:] if (root/'keyboard.log').exists() else '')
    time.sleep(0.05)
  def start_keyboard(hidden=True,auto=True):
   log=(root/'keyboard.log').open('a');logs.append(log)
   command=[str(candidate),'-H','300','-L','180','--fn','JetBrainsMono Nerd Font 18','-l','simple,special,emoji']
   if hidden:command.append('--hidden')
   if auto:command.append('--auto')
   keyboard_env=dict(env);keyboard_env['WAYLAND_DEBUG']='1'
   child=subprocess.Popen(command,env=keyboard_env,stdout=log,stderr=subprocess.STDOUT);processes.append(child)
   return child
  keyboard=start_keyboard()
  # Actual focus changes, not simulated input-method callbacks.
  measured=[]
  for index in range(3):
   assert fixture_api.Focus('text',timeout=3)
   wait_count(1);measured.append(layers()[0]['h'])
   assert fixture_api.Focus('button',timeout=3)
   wait_count(0)
  check('three_real_gtk_focus_show_hide_cycles',measured==[300,300,300])
  assert fixture_api.Focus('text',timeout=3);wait_count(1)
  layer=layers()[0]
  # First key in the first of four rows of the upstream simple layout is q.
  x=int(layer['x']+layer['w']/20);y=int(layer['y']+layer['h']/8)
  subprocess.run([str(tools/'nested-pointer-click'),str(x),str(y),'432','960'],env=env,check=True,capture_output=True,timeout=5)
  deadline=time.monotonic()+5
  while fixture_api.Text(timeout=3)!='q':
   assert time.monotonic()<deadline,('Actual virtual-keyboard entry',str(fixture_api.Text(timeout=3)),layer,query('cursorpos'),query('activewindow','-j'),(root/'keyboard.log').read_text()[-12000:])
   time.sleep(0.05)
  check('actual_pointer_click_enters_q_through_wvkbd',True)
  for index in range(12):
   keyboard.send_signal(signal.SIGUSR1);wait_count(0)
   assert fixture_api.Focus('button',timeout=3);wait_count(0)
   assert fixture_api.Focus('text',timeout=3);wait_count(1)
   layer=layers()[0]
   subprocess.run([str(tools/'nested-pointer-click'),str(int(layer['x']+layer['w']/20)),str(int(layer['y']+layer['h']/8)),'432','960'],env=env,check=True,capture_output=True,timeout=5)
   deadline=time.monotonic()+4
   while fixture_api.Text(timeout=3)!='q'*(index+2):
    assert keyboard.poll() is None,(root/'keyboard.log').read_text()[-6000:]
    assert time.monotonic()<deadline,('Write/hide cycle',index,str(fixture_api.Text(timeout=3)),query('activewindow','-j'),(root/'keyboard.log').read_text()[-7000:])
    time.sleep(0.03)
  check('twelve_write_hide_show_cycles_without_process_exit',True)
  keyboard.send_signal(signal.SIGUSR1);wait_count(0)
  fixture_api.SetText('qq',timeout=3);time.sleep(0.3)
  check('surrounding_text_update_does_not_cancel_manual_hide',len(layers())==0)
  assert fixture_api.Focus('button',timeout=3)
  assert fixture_api.Focus('text',timeout=3);wait_count(1)
  check('new_activation_restores_automatic_keyboard',True)
  lock_report=root/'lock-state'
  log=(root/'lock.log').open('w');logs.append(log)
  lock=subprocess.Popen([str(tools/'nested-lock-fixture'),str(lock_report)],env=env,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,text=True);processes.append(lock)
  deadline=time.monotonic()+8
  while not lock_report.exists() or lock_report.read_text().strip()!='locked':
   assert lock.poll() is None,(root/'lock.log').read_text()[-4000:]
   assert time.monotonic()<deadline;time.sleep(0.05)
  check('real_nested_session_lock_acquired',query('locked')=='true')
  wait_count(0);check('keyboard_layer_removed_when_session_locks',True)
  for requested in (signal.SIGUSR2,signal.SIGRTMIN):
   keyboard.send_signal(requested);time.sleep(0.15)
   check('visibility_signal_'+str(int(requested))+'_cannot_remap_locked_keyboard',not layers())
  keyboard.terminate();keyboard.wait(timeout=5);keyboard=None
  keyboard=start_keyboard(hidden=False)
  # Let the new client drain its initial lock notification and reach its event loop.
  time.sleep(0.5)
  check('keyboard_started_visible_while_locked_stays_unmapped',keyboard.poll() is None and not layers())
  lock.stdin.write('unlock\n');lock.stdin.flush();lock.wait(timeout=5)
  check('nested_fixture_unlocks_explicitly',lock.returncode==0 and lock_report.read_text().strip()=='unlocked' and query('locked')=='false')
  assert fixture_api.Focus('button',timeout=3);wait_count(0);assert fixture_api.Focus('text',timeout=3);wait_count(1)
  check('automatic_keyboard_recovers_after_unlock',True)
  layer=layers()[0]
  # Latch Ctrl, hide the keyboard, then lock: unlocking must not retain Ctrl.
  subprocess.run([str(tools/'nested-pointer-click'),str(int(layer['x']+layer['w']*.25)),str(int(layer['y']+layer['h']*.875)),'432','960'],env=env,check=True,capture_output=True,timeout=5)
  deadline=time.monotonic()+4
  while not int(fixture_api.CurrentModifiers(timeout=3))&4:
   assert time.monotonic()<deadline,('Ctrl latch not observed',int(fixture_api.CurrentModifiers(timeout=3)))
   time.sleep(0.05)
  check('real_ctrl_modifier_observed_before_hidden_lock',str(fixture_api.Text(timeout=3))=='qq')
  keyboard.send_signal(signal.SIGUSR1);wait_count(0)
  lock_report=root/'hidden-modifier-lock-state'
  log=(root/'hidden-modifier-lock.log').open('w');logs.append(log)
  lock=subprocess.Popen([str(tools/'nested-lock-fixture'),str(lock_report)],env=env,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,text=True);processes.append(lock)
  deadline=time.monotonic()+8
  while not lock_report.exists() or lock_report.read_text().strip()!='locked':
   assert lock.poll() is None,(root/'hidden-modifier-lock.log').read_text()[-4000:]
   assert time.monotonic()<deadline;time.sleep(0.05)
  assert query('locked')=='true' and not layers()
  lock.stdin.write('unlock\n');lock.stdin.flush();lock.wait(timeout=5)
  assert lock.returncode==0 and query('locked')=='false'
  assert fixture_api.Focus('button',timeout=3);wait_count(0);assert fixture_api.Focus('text',timeout=3);wait_count(1)
  layer=layers()[0]
  subprocess.run([str(tools/'nested-pointer-click'),str(int(layer['x']+layer['w']/20)),str(int(layer['y']+layer['h']/8)),'432','960'],env=env,check=True,capture_output=True,timeout=5)
  deadline=time.monotonic()+4
  while fixture_api.Text(timeout=3)!='qqq':
   assert time.monotonic()<deadline,('Hidden modifier retained',str(fixture_api.Text(timeout=3)),int(fixture_api.LastModifiers(timeout=3)),query('activewindow','-j'),query('cursorpos'),(root/'keyboard.log').read_text()[-20000:])
   time.sleep(0.05)
  check('hidden_keyboard_ctrl_latch_cleared_on_session_lock',True)
  keyboard.terminate();keyboard.wait(timeout=5);keyboard=None
  assert fixture_api.Focus('button',timeout=3);wait_count(0)
  manager_env=dict(os.environ)
  manager_env['XDG_RUNTIME_DIR']='/run/user/'+str(os.getuid())
  manager_env['DBUS_SESSION_BUS_ADDRESS']='unix:path='+manager_env['XDG_RUNTIME_DIR']+'/bus'
  for index in range(3):
   unit='omarchy-apollo-keyboard-notify-'+str(os.getpid())+'-'+str(index)
   try:
    command=['systemd-run','--user','--quiet','--collect','--unit='+unit,'--property=Type=notify','--property=NotifyAccess=main','--property=TimeoutStartSec=10']
    for key in ('XDG_RUNTIME_DIR','WAYLAND_DISPLAY','HYPRLAND_INSTANCE_SIGNATURE','DBUS_SESSION_BUS_ADDRESS'):
     command.append('--setenv='+key+'='+env[key])
    command.extend([str(candidate),'--hidden','-H','300','-L','180','-l','simple,special,emoji'])
    result=subprocess.run(command,env=manager_env,capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stderr
    subprocess.run(['systemctl','--user','kill','--signal=USR2',unit],env=manager_env,check=True,capture_output=True,timeout=5)
    wait_count(1)
    active=subprocess.check_output(['systemctl','--user','is-active',unit],env=manager_env,text=True).strip()
    check('notify_start_then_immediate_show_cycle_'+str(index+1),active=='active')
   finally:
    subprocess.run(['systemctl','--user','stop',unit],env=manager_env,capture_output=True,timeout=10)
   wait_count(0)
  check('fixture_contains_only_disposable_test_text',str(fixture_api.Text(timeout=3))=='qqq')
  record={'passed':len(checks),'checks':checks,'keyboard_version':'0.20-2','keyboard_binary_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'gtk_focus_cycles':3,'actual_key_hide_cycles':12,'keyboard_heights':measured,'native_notify_start_cycles':3,'physical_display_used':False,'owner_credentials_used':False,'protocol_sources':provenance}
  Path(sys.argv[1]).write_text(json.dumps(record,indent=2)+'\n')
 finally:
  for child in reversed(processes):
   if child.poll() is None:
    child.terminate()
    try:child.wait(timeout=8)
    except subprocess.TimeoutExpired:child.kill();child.wait()
  for log in logs:log.close()
