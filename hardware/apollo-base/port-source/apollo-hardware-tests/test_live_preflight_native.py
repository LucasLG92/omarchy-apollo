"""Exercise the host preflight on original Android; never erase or flash."""
from pathlib import Path
import datetime,json,subprocess,sys,time
base=Path(__file__).resolve().parents[2]
sdk=base/'work/downloads/android-tools-current/platform-tools'
tag='hardware-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
report=base/'outputs/arch-apollo/experimental'/tag; report.mkdir()

def cmd(name,*args):
    return subprocess.run([str(sdk/(name+'.exe')),'-s',__import__('os').environ['APOLLO_SERIAL'],*args],
        capture_output=True,text=True,timeout=20,check=True).stdout.strip()

assert cmd('adb','shell','getprop','sys.boot_completed')=='1'
cmd('adb','reboot','bootloader')
try:
    subprocess.run([sys.executable,str(base/'work/restore_dtbo_checked.py'),tag,'--preflight'],timeout=300,check=True)
finally:
    # DTBO was never touched; boot the existing original Android directly.
    cmd('fastboot','reboot')
subprocess.run([sys.executable,str(base/'work/verify_android_restore.py'),tag],timeout=180,check=True)
subprocess.run([sys.executable,str(base/'work/set_android_quiet.py')],timeout=45,check=True)
proof=json.loads((report/'checked-live-preflight.json').read_text())
assert proof['passed'] and proof['partition_write_attempted'] is False
proof['android_return_and_original_partition_hashes_verified']=True
proof['scope']='Real bootloader preflight on original Android; no Linux boot, erase or flash, no UFS fault injection'
(base/'outputs/arch-apollo/host-preflight-validation.json').write_text(json.dumps({
    'report':'experimental/'+tag,'results':proof},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Native preflight passed without partition writes; original Android verified and silent:',tag)
