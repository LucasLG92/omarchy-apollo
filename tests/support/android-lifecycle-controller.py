from pathlib import Path
import subprocess,os,json,time,pwd,signal,hashlib,stat
root=Path(os.environ['APOLLO_TEST_WORK'])
owner=pwd.getpwnam(os.environ['APOLLO_TEST_USER'])
assert owner.pw_uid>=1000
def read_owned(path,limit=65536):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
    try:
        info=os.fstat(fd)
        assert stat.S_ISREG(info.st_mode) and info.st_uid==owner.pw_uid and info.st_nlink==1 and not info.st_mode & 0o077 and info.st_size<=limit
        contents=bytearray()
        while len(contents)<=limit:
            part=os.read(fd,min(65536,limit+1-len(contents)))
            if not part:break
            contents.extend(part)
        assert len(contents)<=limit
        return bytes(contents)
    finally:os.close(fd)

def acknowledge(path):
    # The owner controls this fixture directory. Create a new inode exclusively
    # and change that descriptor's owner, never a path which could be a symlink.
    descriptor=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:
        os.fchmod(descriptor,0o600)
        os.fchown(descriptor,owner.pw_uid,owner.pw_gid)
    finally:os.close(descriptor)

pin_before=subprocess.check_output(['systemctl','show','omarchy-apollo-owner-pin-setup.service','-p','MainPID'],text=True)
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)
def android(*args):
    return subprocess.run(['/usr/bin/waydroid','shell',*args],capture_output=True,text=True,timeout=20)
def verify_android(label):
    p=android('getprop','sys.boot_completed');check(label+' Android boot completed',p.returncode==0 and p.stdout.strip()=='1')
    p=android('dumpsys','package','org.fdroid.fdroid')
    check(label+' F-Droid package and version exist','versionName=2.0.2' in p.stdout)
    p=android('dumpsys','SurfaceFlinger')
    check(label+' Android uses the FD650 GPU','GLES: freedreno, FD650' in p.stdout)
def foreign(uid):
    code="import os,dbus,json; f=os.memfd_create('apollo-apk-denied-test');os.write(f,b'not an APK');s=dbus.Interface(dbus.SystemBus().get_object('org.omarchy.Apollo.Android','/org/omarchy/Apollo/Android'),'org.omarchy.Apollo.Android1');ok,reason=s.InstallApk(dbus.types.UnixFd(f),timeout=15);released=s.Release(timeout=15);print(json.dumps({'ok':bool(ok),'code':str(reason),'released':bool(released)}))"
    args=['/usr/bin/python','-I','-c',code]
    if uid!=0:args=['/usr/bin/setpriv','--reuid='+str(uid),'--regid='+str(uid),'--clear-groups',*args]
    p=subprocess.run(args,capture_output=True,text=True,timeout=20)
    assert p.returncode==0,p.stderr
    result=json.loads(p.stdout)
    check(('root' if uid==0 else 'another desktop UID')+' cannot install in the owner session',not result['ok'] and result['code']=='APOLLO_ACCESS_DENIED')
    check(('root' if uid==0 else 'another desktop UID')+' cannot release the owner installer',not result['released'])

log_path=Path(os.environ['APOLLO_TEST_CONTROL'])/'owner.log'
log=log_path.open('w')
env={'PATH':'/usr/bin','LANG':'C.UTF-8','XDG_RUNTIME_DIR':'/run/user/'+str(owner.pw_uid),'WAYLAND_DISPLAY':os.environ['APOLLO_TEST_DISPLAY'],'APOLLO_TEST_UID':str(owner.pw_uid),'APOLLO_TEST_DISPLAY':os.environ['APOLLO_TEST_DISPLAY']}
process=subprocess.Popen(['runuser','-u',owner.pw_name,'--','dbus-run-session','--','/usr/bin/python','-I',str(root/'owner.py')],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
def terminate(signum,frame):
    raise KeyboardInterrupt
signal.signal(signal.SIGTERM,terminate)

handled=set();deadline=time.monotonic()+480
try:
    while time.monotonic()<deadline:
        if process.poll() is not None:
            if process.returncode:raise RuntimeError(log_path.read_text(encoding='utf-8')[-7000:])
            break
        phasefile=root/'phase.json'
        if phasefile.exists():
            try:
                state=json.loads(read_owned(phasefile));stage=state['phase']
            except json.JSONDecodeError:
                continue
            if stage not in handled:
                if stage=='ready':
                    check('Waydroid daemon activated from the stopped state',subprocess.check_output(['systemctl','is-active','waydroid-container.service'],text=True).strip()=='active')
                    foreign(0);foreign(1000 if owner.pw_uid!=1000 else 1001)
                elif stage in ('installed','restarted'):
                    verify_android(stage)
                    if stage=='installed':
                        check('APK helper has exited before Android is stopped',subprocess.check_output(['systemctl','show','omarchy-apollo-apk.service','-p','MainPID','--value'],text=True).strip()=='0')
                elif stage=='done':
                    check('container is stopped after testing',subprocess.check_output(['lxc-info','-P','/var/lib/waydroid/lxc','-n','waydroid','-sH'],text=True).strip()=='STOPPED')
                else:raise RuntimeError('Unexpected integration-test phase')
                acknowledge(root/('continue-'+stage))
                handled.add(stage)
        time.sleep(0.2)
    else:raise TimeoutError('Android lifecycle test exceeded its deadline')
    check('all lifecycle phases completed',handled=={'ready','installed','restarted','done'} and process.returncode==0)
    result=json.loads(read_owned(root/'result.json'));checks=result['checks']+checks
    check('local PIN-setup process was not interrupted',pin_before==subprocess.check_output(['systemctl','show','omarchy-apollo-owner-pin-setup.service','-p','MainPID'],text=True))
    cache=Path('/var/cache/omarchy-apollo-apks')
    check('no APK snapshot files remain in the root cache',cache.is_dir() and not any(cache.iterdir()))
    input_info=(root/'F-Droid.apk').stat()
    check('the user APK keeps its owner and file permissions',input_info.st_uid==owner.pw_uid and input_info.st_mode & 0o777==0o600)
    check('the user APK contents are unchanged',hashlib.sha256(read_owned(root/'F-Droid.apk',128*1024*1024)).hexdigest()==result['apk_sha256'])
    record={'passed':len(checks),'checks':checks,'apk_sha256':result['apk_sha256'],'physical_display_used':False,'owner_credentials_used':False,'android_stopped_after_test':True}
    # The caller captures only sanitized JSON; private logs stay in the fixture.
    print(json.dumps(record,indent=2),flush=True)
finally:
    if process.poll() is None:
        os.killpg(process.pid,signal.SIGTERM)
        try:process.wait(timeout=40)
        except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
    log.close()
