from pathlib import Path
import subprocess,os,json,time,signal
import shutil
import gi,array,math
gi.require_version("Gst","1.0")
from gi.repository import Gst
Gst.init(None)

root=Path(os.environ['APOLLO_AUDIO_TEST_WORK'])
os.umask(0o077)
runtime=Path('/run/user')/str(os.getuid())
private=runtime/('apollo-audio-test-'+str(os.getpid()));private.mkdir(mode=0o700)
for name in ('pwconf','wpconf','pulse','state','config','cache','data'):(private/name).mkdir(mode=0o700)
for source in Path('/usr/share/pipewire').glob('*.conf'):
 (private/'pwconf'/source.name).write_bytes(source.read_bytes())
(private/'wpconf/wireplumber.conf').write_bytes(Path('/usr/share/wireplumber/wireplumber.conf').read_bytes())
env=dict(os.environ)
env.update({'PIPEWIRE_RUNTIME_DIR':str(private),'PIPEWIRE_CONFIG_DIR':str(private/'pwconf'),
 'WIREPLUMBER_CONFIG_DIR':str(private/'wpconf'),'PULSE_RUNTIME_PATH':str(private/'pulse'),
 'PULSE_SERVER':'unix:'+str(private/'pulse/native'),'XDG_STATE_HOME':str(private/'state'),
 'XDG_CONFIG_HOME':str(private/'config'),'XDG_CACHE_HOME':str(private/'cache'),'XDG_DATA_HOME':str(private/'data')})
processes=[];logs=[];session=None;pipeline=None;captured=bytearray()
def start(name,args,extra=None):
 log=(private/(name+'.log')).open('w');logs.append(log)
 child=subprocess.Popen(args,env=env if extra is None else extra,stdout=log,stderr=subprocess.STDOUT)
 processes.append(child);return child
def wait_socket(path,child):
 deadline=time.monotonic()+15
 while not path.is_socket():
  assert child.poll() is None,'Private server stopped: '+path.name
  assert time.monotonic()<deadline,'Private socket did not appear'
  time.sleep(0.1)
def command(*args):return subprocess.run(args,env=env,capture_output=True,text=True,timeout=12)
def phase(name,data):
 pending=root/'phase-next.json'
 pending.write_text(json.dumps({'phase':name,**data})+'\n')
 pending.replace(root/'phase.json')
 deadline=time.monotonic()+150
 while not (root/('continue-'+name)).is_file():
  if time.monotonic()>deadline:raise TimeoutError('Root test controller did not acknowledge '+name)
  time.sleep(0.2)
def interrupted(signum,frame):raise InterruptedError('Audio transport test interrupted')
signal.signal(signal.SIGTERM,interrupted)
try:
 core=start('pipewire',['/usr/bin/pipewire'])
 wait_socket(private/'pipewire-0',core)
 policy=start('policy',['/usr/bin/wireplumber','--profile','policy'])
 pulse=start('pulse',['/usr/bin/pipewire-pulse'])
 wait_socket(private/'pulse/native',pulse)
 # The private parent restricts host access; the owned Android session receives
 # only this synthetic server's socket, with no real audio devices behind it.
 (private/'pulse/native').chmod(0o666)
 result=command('pactl','load-module','module-null-sink','sink_name=apollo_android_audio_test','channels=2','rate=48000','sink_properties=device.description=ApolloAndroidAudioTest')
 assert result.returncode==0,result.stderr
 deadline=time.monotonic()+10
 while True:
  result=command('pactl','--format=json','list','sinks');assert result.returncode==0,result.stderr
  sinks=json.loads(result.stdout)
  if any(sink['name']=='apollo_android_audio_test' for sink in sinks):break
  assert time.monotonic()<deadline
  time.sleep(0.1)
 assert len(sinks)==1 and sinks[0].get('properties',{}).get('device.api')!='alsa'
 result=command('pw-dump');assert result.returncode==0,result.stderr
 objects=json.loads(result.stdout)
 assert not any(n.get('info',{}).get('props',{}).get('device.api') in ('alsa','bluez5','libcamera','v4l2') for n in objects)
 result=command('pactl','set-default-sink','apollo_android_audio_test');assert result.returncode==0,result.stderr
 # Keep the installed desktop's data paths: only audio transport is private.
 wayenv=dict(os.environ);wayenv['PULSE_RUNTIME_PATH']=str(private/'pulse')
 session=start('waydroid',['/usr/bin/waydroid','session','start'],extra=wayenv)
 deadline=time.monotonic()+100
 while True:
  assert session.poll() is None,'Waydroid session stopped while starting'
  try:
   result=subprocess.run(['/usr/bin/waydroid','prop','get','sys.boot_completed'],env=wayenv,capture_output=True,text=True,timeout=min(5,max(0.1,deadline-time.monotonic())))
   if result.returncode==0 and result.stdout.strip()=='1':break
  except subprocess.TimeoutExpired:
   pass
  assert time.monotonic()<deadline,'Android did not finish booting'
  time.sleep(0.4)
 pipeline=Gst.parse_launch('pulsesrc server="'+env['PULSE_SERVER']+'" device=apollo_android_audio_test.monitor ! audio/x-raw,format=S16LE,channels=2,rate=48000 ! appsink name=capture emit-signals=true sync=false max-buffers=10 drop=false enable-last-sample=false')
 def receive(sink):
  sample=sink.emit('pull-sample');buffer=sample.get_buffer()
  if len(captured)+buffer.get_size()>16*1024*1024:return Gst.FlowReturn.ERROR
  captured.extend(buffer.extract_dup(0,buffer.get_size()))
  return Gst.FlowReturn.OK
 pipeline.get_by_name('capture').connect('new-sample',receive)
 assert pipeline.set_state(Gst.State.PLAYING)!=Gst.StateChangeReturn.FAILURE
 state=pipeline.get_state(8*Gst.SECOND)
 assert state[0]!=Gst.StateChangeReturn.FAILURE
 phase('ready',{'private_audio_directory':str(private),'private_pulse_runtime':str(private/'pulse'),'physical_audio_devices_exposed':False})
 time.sleep(0.3)
 pipeline.set_state(Gst.State.NULL);pipeline.get_state(5*Gst.SECOND)
 message=pipeline.get_bus().pop_filtered(Gst.MessageType.ERROR)
 assert message is None,str(message.parse_error()) if message else ''
 pcm=array.array('h');pcm.frombytes(captured)
 assert len(pcm)>48000*2,'No synthetic monitor samples'
 def amplitude(values,frequency):
  cosine=2*math.cos(2*math.pi*frequency/48000);first=second=0.0
  for value in values:
   current=value+cosine*first-second;second=first;first=current
  power=first*first+second*second-cosine*first*second
  return 2*math.sqrt(max(0,power))/len(values)
 channels=[]
 for channel,target,other in ((0,997,1499),(1,1499,997)):
  values=pcm[channel::2];best=None
  for offset in range(0,len(values)-48000+1,12000):
   segment=values[offset:offset+48000]
   strength=amplitude(segment,target)
   if best is None or strength>best['target_amplitude']:
    wrong=amplitude(segment,other)
    best={'channel':channel,'target_hz':target,'target_amplitude':round(strength,3),'opposite_tone_amplitude':round(wrong,3),'separation_db':round(20*math.log10(max(strength,0.000001)/max(wrong,0.000001)),2)}
  channels.append(best)
 assert all(item['target_amplitude']>20 and item['separation_db']>20 for item in channels),json.dumps(channels)
 result=command('pw-dump');assert result.returncode==0
 objects=json.loads(result.stdout)
 assert not any(n.get('info',{}).get('props',{}).get('device.api') in ('alsa','bluez5','libcamera','v4l2') for n in objects)
 print(json.dumps({'android_booted_with_private_audio':True,'physical_audio_devices_exposed':False,'physical_sound_played':False,'microphone_recorded':False,'synthetic_frames_captured':len(pcm)//2,'channels':channels}),flush=True)
finally:
 if pipeline is not None:pipeline.set_state(Gst.State.NULL)
 if session is not None:
  subprocess.run(['/usr/bin/omarchy-apollo-android','stop'],env=os.environ,capture_output=True,timeout=50)
  try:session.wait(timeout=10)
  except subprocess.TimeoutExpired:session.terminate();session.wait(timeout=10)
 for process in reversed(processes):
  if process.poll() is None:
   process.terminate()
   try:process.wait(timeout=10)
   except subprocess.TimeoutExpired:process.kill();process.wait()
 for log in logs:log.close()
 shutil.rmtree(private)
