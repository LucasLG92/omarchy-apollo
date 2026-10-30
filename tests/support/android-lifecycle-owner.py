from pathlib import Path
import subprocess,os,json,time,hashlib
import dbus

root=Path(__file__).resolve().parent
os.umask(0o077)
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)
def command(*args,timeout=140):
    return subprocess.run(['/usr/bin/omarchy-apollo-android',*args],capture_output=True,text=True,timeout=timeout)
def phase(name):
    (root/'phase.json').write_text(json.dumps({'phase':name,'checks':checks})+'\n')
    deadline=time.monotonic()+90
    while not (root/('continue-'+name)).exists():
        if time.monotonic()>deadline:raise TimeoutError('Controller did not acknowledge '+name)
        time.sleep(0.2)
def call(fd):
    service=dbus.Interface(dbus.SystemBus().get_object('org.omarchy.Apollo.Android','/org/omarchy/Apollo/Android'),'org.omarchy.Apollo.Android1')
    ok,code=service.InstallApk(dbus.types.UnixFd(fd),timeout=240)
    return bool(ok),str(code)

assert os.getuid()==int(os.environ['APOLLO_TEST_UID']) and os.environ['WAYLAND_DISPLAY']==os.environ['APOLLO_TEST_DISPLAY']
try:
    p=command('prepare')
    check('Android prepares on demand on the separate headless display',p.returncode==0)
    phase('ready')
    wrong=root/'invalid.apk';wrong.write_bytes(b'This is not an APK.\n')
    descriptor=os.open(wrong,os.O_WRONLY)
    try:check('write-only descriptors are rejected',call(descriptor)==(False,'APOLLO_INVALID_APK_INPUT'))
    finally:os.close(descriptor)
    descriptor,writer=os.pipe()
    try:check('pipe descriptors are rejected without waiting for data',call(descriptor)==(False,'APOLLO_INVALID_APK_INPUT'))
    finally:os.close(descriptor);os.close(writer)
    descriptor=os.open(wrong,os.O_PATH)
    try:check('path-only descriptors are rejected',call(descriptor)==(False,'APOLLO_INVALID_APK_INPUT'))
    finally:os.close(descriptor)
    empty=root/'empty.apk';empty.touch()
    descriptor=os.open(empty,os.O_RDONLY)
    try:check('empty APK input is rejected',call(descriptor)==(False,'APOLLO_INVALID_APK_SIZE'))
    finally:os.close(descriptor)
    large=root/'oversize.apk'
    with large.open('wb') as stream:stream.truncate(1024*1024*1024+1)
    descriptor=os.open(large,os.O_RDONLY)
    try:check('oversized APK input is rejected before copying',call(descriptor)==(False,'APOLLO_INVALID_APK_SIZE'))
    finally:os.close(descriptor);large.unlink()
    descriptor=os.open(wrong,os.O_RDONLY)
    try:
        ok,code=call(descriptor)
        check('Android itself rejects the malformed APK',not ok and code.startswith('INSTALL_'))
    finally:os.close(descriptor)
    p=command('install',str(wrong),timeout=250)
    check('an invalid APK returns failure rather than installed',p.returncode!=0 and 'Aplicación instalada' not in p.stdout)
    (root/'invalid-apk-result.json').write_text(json.dumps({'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})+'\n')
    apk=root/'F-Droid.apk'
    digest=hashlib.sha256(apk.read_bytes()).hexdigest()
    (root/'input-apk.json').write_text(json.dumps({'apk_sha256':digest})+'\n')
    p=command('install',str(apk),timeout=250)
    (root/'valid-apk-result.json').write_text(json.dumps({'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})+'\n')
    check('signed F-Droid APK installation returns confirmed success',p.returncode==0 and 'Aplicación instalada en Android.' in p.stdout)
    phase('installed')
    p=command('stop');check('Android stops cleanly',p.returncode==0)
    p=command('prepare');check('Android starts again on demand',p.returncode==0)
    phase('restarted')
    p=command('stop');check('Android stops after the repeat cycle',p.returncode==0)
    p=command('stop');check('stopping Android twice is harmless',p.returncode==0)
    (root/'result.json').write_text(json.dumps({'passed':len(checks),'checks':checks,'apk_sha256':digest})+'\n')
    phase('done')
finally:
    command('stop',timeout=45)
