#!/usr/bin/python3
"""Reproduce the on-device APK/lifecycle checks on a separate headless display."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pwd
import shutil
import signal
import stat
import subprocess
import tempfile
import time

APK_SHA256='19d51fad482239f6df6a99120e34513667e9a86d136dafdc4a211a68c3327b52'
SOURCE=Path(__file__).resolve().parent/'support'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk',required=True,help='Previously signature-verified F-Droid 2.0.2 APK')
    parser.add_argument('--user',default='apollo',help='Local desktop account, default: apollo')
    args=parser.parse_args()
    assert os.getuid()==0 and os.geteuid()==0,'Run as root on the Apollo test device'
    assert subprocess.check_output(['/usr/bin/omarchy-hw-platform'],text=True).strip()=='aarch64-apollo'
    assert shutil.which('weston'),'The optional Weston test tool is required'
    owner=pwd.getpwnam(args.user);assert 1000<=owner.pw_uid<65534
    assert subprocess.check_output(['lxc-info','-P','/var/lib/waydroid/lxc','-n','waydroid','-sH'],text=True).strip()=='STOPPED','Stop Android before testing'
    os.umask(0o077)
    runtime=Path('/run/user')/str(owner.pw_uid)
    assert runtime.is_dir() and runtime.stat().st_uid==owner.pw_uid
    display='wayland-apollo-test-'+str(os.getpid())
    unit='omarchy-apollo-test-display-'+str(os.getpid())+'.service'
    user_command=['runuser','-u',owner.pw_name,'--','env','XDG_RUNTIME_DIR='+str(runtime),'DBUS_SESSION_BUS_ADDRESS=unix:path='+str(runtime/'bus')]
    subprocess.run(['systemctl','stop','omarchy-apollo-apk.service'],check=True,timeout=20)
    subprocess.run(['systemctl','stop','waydroid-container.service'],check=True,timeout=30)
    with tempfile.TemporaryDirectory(prefix='omarchy-apollo-android-test-',dir='/var/tmp') as temporary:
        base=Path(temporary);base.chmod(0o711)
        control=base/'control';control.mkdir(mode=0o700)
        snapshot=control/'fixture.apk'
        descriptor=os.open(args.apk,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
        try:
            info=os.fstat(descriptor)
            assert stat.S_ISREG(info.st_mode) and 0<info.st_size<=128*1024*1024,'Use the documented F-Droid fixture'
            with snapshot.open('wb') as output:
                remaining=info.st_size
                while remaining:
                    data=os.read(descriptor,min(1024*1024,remaining))
                    assert data,'APK changed during reading'
                    output.write(data);remaining-=len(data)
            assert hashlib.sha256(snapshot.read_bytes()).hexdigest()==APK_SHA256,'Use the documented F-Droid fixture'
        finally:os.close(descriptor)
        work=base/'owner';work.mkdir(mode=0o700);os.chown(work,owner.pw_uid,owner.pw_gid)
        shutil.copyfile(snapshot,work/'F-Droid.apk');os.chown(work/'F-Droid.apk',owner.pw_uid,owner.pw_gid)
        shutil.copyfile(SOURCE/'android-lifecycle-owner.py',work/'owner.py');os.chown(work/'owner.py',owner.pw_uid,owner.pw_gid)
        controller=base/'controller.py';shutil.copyfile(SOURCE/'android-lifecycle-controller.py',controller);controller.chmod(0o600)
        process=None
        try:
            subprocess.run([*user_command,'systemd-run','--user','--collect','--unit='+unit,
                '--property=RuntimeMaxSec=600','--property=UMask=0077','/usr/bin/weston',
                '--backend=headless','--renderer=gl','--shell=kiosk','--socket='+display,
                '--width=1080','--height=2400','--refresh-rate=30000','--fake-seat',
                '--idle-time=0','--no-config','--log='+str(runtime/(unit+'.log'))],
                check=True,capture_output=True,text=True,timeout=15)
            deadline=time.monotonic()+15
            while not (runtime/display).is_socket():
                if time.monotonic()>deadline:raise TimeoutError('Headless display did not become ready')
                time.sleep(0.1)
            env={'PATH':'/usr/bin','LANG':'C.UTF-8','APOLLO_TEST_WORK':str(work),
                 'APOLLO_TEST_CONTROL':str(control),'APOLLO_TEST_USER':owner.pw_name,'APOLLO_TEST_DISPLAY':display}
            process=subprocess.Popen(['/usr/bin/python','-I',str(controller)],
                                     env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                output,error=process.communicate(timeout=540)
            except subprocess.TimeoutExpired:
                process.terminate();output,error=process.communicate(timeout=45)
                raise TimeoutError('Android integration checks exceeded their deadline')
            assert process.returncode==0,error[-5000:]
            result=json.loads(output)
            assert result['passed']==31 and result['android_stopped_after_test']
            print(json.dumps(result,indent=2))
        finally:
            if process is not None and process.poll() is None:
                process.terminate()
                try:process.wait(timeout=45)
                except subprocess.TimeoutExpired:process.kill();process.wait()
            subprocess.run([*user_command,'systemctl','--user','stop',unit],capture_output=True,timeout=25)
            (runtime/(unit+'.log')).unlink(missing_ok=True)


if __name__=='__main__':
    main()
