#!/usr/bin/python3
"""Check Android AudioTrack to Linux stereo transport without physical audio."""
import argparse
import hashlib
import io
import zipfile


def run(args,control_directory):
    from pathlib import Path
    import subprocess,os,json,time,tempfile,pwd,signal,stat
    import dbus
    owner=pwd.getpwnam(args.user);assert 1000<=owner.pw_uid<65534
    root=Path(control_directory)
    runtime=Path('/run/user')/str(owner.pw_uid)
    assert runtime.is_dir() and runtime.stat().st_uid==owner.pw_uid
    assert subprocess.check_output(['/usr/bin/omarchy-hw-platform'],text=True).strip()=='aarch64-apollo'
    OWNER_SOURCE=(Path(__file__).resolve().parent/'support/android-audio-owner.py').read_text()
    descriptor=os.open(args.probe_jar,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
     info=os.fstat(descriptor);assert stat.S_ISREG(info.st_mode) and 0<info.st_size<=1024*1024
     probe=os.read(descriptor,1024*1024+1);assert len(probe)==info.st_size
    finally:os.close(descriptor)
    with zipfile.ZipFile(io.BytesIO(probe)) as fixture:assert fixture.namelist()==['classes.dex']
    probe_sha256=hashlib.sha256(probe).hexdigest()
    assert subprocess.check_output(['lxc-info','-P','/var/lib/waydroid/lxc','-n','waydroid','-sH'],text=True).strip()=='STOPPED'
    prefix=['runuser','-u',owner.pw_name,'--','env','XDG_RUNTIME_DIR='+str(runtime),'DBUS_SESSION_BUS_ADDRESS=unix:path='+str(runtime/'bus'),'LANG=C.UTF-8']
    pin_before=subprocess.check_output(['systemctl','show','omarchy-apollo-owner-pin-setup.service','-p','MainPID'],text=True)
    desktop_before={name:subprocess.check_output([*prefix,'systemctl','--user','show',name,'-p','MainPID'],text=True) for name in ('pipewire.service','pipewire-pulse.service','wireplumber.service')}
    default_before=subprocess.check_output([*prefix,'pactl','get-default-sink'],text=True).strip()
    socket='wayland-apollo-audio-'+str(os.getpid());unit='omarchy-apollo-audio-display-'+str(os.getpid())+'.service'
    assert not (runtime/socket).exists()
    subprocess.run([*prefix,'systemd-run','--user','--collect','--unit='+unit,'--property=RuntimeMaxSec=300','--property=UMask=0077','/usr/bin/weston','--backend=headless','--renderer=gl','--shell=kiosk','--socket='+socket,'--width=432','--height=960','--refresh-rate=30000','--fake-seat','--idle-time=0','--no-config','--log='+str(runtime/(unit+'.log'))],check=True,capture_output=True,timeout=15)
    process=None
    try:
     deadline=time.monotonic()+15
     while not (runtime/socket).is_socket():
      assert time.monotonic()<deadline
      time.sleep(0.1)
     with tempfile.TemporaryDirectory(prefix='apollo-audio-discovery-',dir='/var/tmp') as temporary:
      base=Path(temporary);base.chmod(0o711);work=base/'owner';work.mkdir(mode=0o700);os.chown(work,owner.pw_uid,owner.pw_gid)
      process=subprocess.Popen([*prefix,'WAYLAND_DISPLAY='+socket,'APOLLO_AUDIO_TEST_WORK='+str(work),'dbus-run-session','--','python','-I','-'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
      process.stdin.write(OWNER_SOURCE);process.stdin.close();process.stdin=None
      deadline=time.monotonic()+140
      while not (work/'phase.json').exists():
       if process.poll() is not None:
        output,error=process.communicate()
        (root/'android-audio-transport-failure-private.log').write_text(output+error)
        raise RuntimeError(error[-3500:])
       assert time.monotonic()<deadline
       time.sleep(0.2)
      fd=os.open(work/'phase.json',os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
      try:
       info=os.fstat(fd);assert stat.S_ISREG(info.st_mode) and info.st_uid==owner.pw_uid and info.st_size<65536
       phase=json.loads(os.read(fd,65536))
      finally:os.close(fd)
      assert phase['phase']=='ready'
      session=dict(dbus.Interface(dbus.SystemBus().get_object('id.waydro.Container','/ContainerManager'),'id.waydro.ContainerManager').GetSession(timeout=10))
      assert str(session.get('user_id'))==str(owner.pw_uid) and session.get('wayland_display')==socket
      assert session.get('pulse_runtime_path')==phase['private_pulse_runtime']
      record={'private_pulse_socket_mounted':True,'physical_audio_devices_exposed':False,'probe_sha256':probe_sha256}
      lxc=['/usr/bin/lxc-attach','-P','/var/lib/waydroid/lxc','-n','waydroid','--clear-env','--uid','2000','--gid','2000','--set-var','PATH=/system/bin:/system/xbin:/vendor/bin']
      def android(args,**kwargs):
       return subprocess.run([*lxc,'--',*args],capture_output=True,timeout=30,**kwargs)
      assert android(['/system/bin/test','-e','/dev/snd']).returncode==1,'Android has physical sound devices'
      result=android(['/system/bin/sh','-c','umask 077; rm -f /data/local/tmp/omarchy-apollo-audio-result.json; cat > /data/local/tmp/omarchy-apollo-audio-probe.jar; chmod 0444 /data/local/tmp/omarchy-apollo-audio-probe.jar'],input=probe)
      assert result.returncode==0,result.stderr
      try:
       # Match Waydroid's framework environment; app_process requires ART roots
       # and the classpath generated by this Android image, unlike native pm/cmd.
       import ast
       tree=ast.parse(Path('/usr/lib/waydroid/tools/helpers/lxc.py').read_text())
       environment=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ANDROID_ENV' for t in node.targets))
       generated=subprocess.run(['/usr/bin/lxc-attach','-P','/var/lib/waydroid/lxc','-n','waydroid','--clear-env','--','/system/bin/cat','/data/system/environ/classpath'],capture_output=True,text=True,timeout=10)
       assert generated.returncode==0 and len(generated.stdout)<65536
       for line in generated.stdout.splitlines():
        parts=line.split(' ',2)
        if len(parts)==3 and parts[1]=='BOOTCLASSPATH':environment['BOOTCLASSPATH']=parts[2]
       environment['CLASSPATH']='/data/local/tmp/omarchy-apollo-audio-probe.jar'
       options=[part for key,value in environment.items() for part in ('--set-var',key+'='+value)]
       try:
        result=subprocess.run([*lxc,*options,'--','/system/bin/app_process','/system/bin','org.omarchy.apollo.AndroidAudioProbe'],capture_output=True,text=True,timeout=45)
       except subprocess.TimeoutExpired as failure:
        status=android(['/system/bin/cat','/data/local/tmp/omarchy-apollo-audio-result.json'])
        (root/'android-audio-transport-progress-private.json').write_bytes(status.stdout or b'{}')
        (root/'android-audio-transport-framework-private.log').write_bytes((failure.stdout or b'')+(failure.stderr or b''))
        raise
       (root/'android-audio-transport-framework-private.log').write_text(result.stdout+result.stderr)
       assert result.returncode==0,result.stderr[-3500:]
       status=android(['/system/bin/cat','/data/local/tmp/omarchy-apollo-audio-result.json'])
       assert status.returncode==0,status.stderr
       record['framework_probe']=json.loads(status.stdout)
       assert record['framework_probe'].get('framework_audio_track') is True
       assert record['framework_probe']['sample_rate']==48000 and record['framework_probe']['channels']==2
       assert record['framework_probe']['frames_played']>=record['framework_probe']['frames_written']==144000
      finally:
       android(['/system/bin/rm','-f','/data/local/tmp/omarchy-apollo-audio-probe.jar','/data/local/tmp/omarchy-apollo-audio-result.json'])
      (root/'android-audio-transport-private.json').write_text(json.dumps(record,indent=2)+'\n')
      marker=os.open(work/'continue-ready',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
      try:os.fchown(marker,owner.pw_uid,owner.pw_gid)
      finally:os.close(marker)
      output,error=process.communicate(timeout=75)
      (root/'android-audio-transport-private.log').write_text(output+error)
      assert process.returncode==0,error[-3500:]
      record['owner_result']=json.loads(output)
      record['android_stopped_after_test']=subprocess.check_output(['lxc-info','-P','/var/lib/waydroid/lxc','-n','waydroid','-sH'],text=True).strip()=='STOPPED'
      record['desktop_audio_processes_unchanged']=all(value==subprocess.check_output([*prefix,'systemctl','--user','show',name,'-p','MainPID'],text=True) for name,value in desktop_before.items())
      record['desktop_default_sink_unchanged']=default_before==subprocess.check_output([*prefix,'pactl','get-default-sink'],text=True).strip()
      record['pin_setup_process_unchanged']=pin_before==subprocess.check_output(['systemctl','show','omarchy-apollo-owner-pin-setup.service','-p','MainPID'],text=True)
      (root/'android-audio-transport-private.json').write_text(json.dumps(record,indent=2)+'\n')
      assert all(record[key] for key in ('android_stopped_after_test','desktop_audio_processes_unchanged','desktop_default_sink_unchanged','pin_setup_process_unchanged'))
      print(json.dumps(record,indent=2),flush=True)
    finally:
     if process is not None and process.poll() is None:
      os.killpg(process.pid,signal.SIGTERM)
      try:process.wait(timeout=30)
      except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
     subprocess.run([*prefix,'systemctl','--user','stop',unit],capture_output=True,timeout=20)
     (runtime/(unit+'.log')).unlink(missing_ok=True)


def main():
    import os,tempfile
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe-jar',required=True,help='Fixture built from support/AndroidAudioProbe.java')
    parser.add_argument('--user',default='apollo',help='Active local desktop account')
    args=parser.parse_args()
    assert os.getuid()==0 and os.geteuid()==0,'Run as root on the development phone'
    os.umask(0o077)
    with tempfile.TemporaryDirectory(prefix='apollo-audio-control-',dir='/var/tmp') as control:
        run(args,control)


if __name__=='__main__':
    main()
