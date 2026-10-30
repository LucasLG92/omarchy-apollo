#!/usr/bin/python3
"""Exercise the real privileged initializer in a private mount namespace.

Run through systemd-run with PrivateMounts=yes, PrivateDevices=yes and
ProtectKernelTunables=yes. The fixture replaces only Waydroid's download/init
command; it never initializes Android, accesses Google, or touches existing data.
The supplied workspace must be an empty root-owned directory on ext4.
"""
from pathlib import Path
import argparse
import json
import os
import shutil
import stat
import subprocess

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--workspace',type=Path,required=True)
parser.add_argument('--initializer',type=Path,required=True)
args=parser.parse_args()
assert os.getuid()==0 and os.geteuid()==0
assert os.readlink('/proc/self/ns/mnt')!=os.readlink('/proc/1/ns/mnt'), 'A private mount namespace is required.'
workspace=args.workspace.resolve()
assert workspace.is_dir() and not any(workspace.iterdir())
assert workspace.stat().st_uid==0 and not workspace.stat().st_mode&0o077
assert subprocess.check_output(['findmnt','-n','-o','FSTYPE','-T',str(workspace)],text=True).strip()=='ext4'
root=workspace/'fixture';root.mkdir(mode=0o700)
mounted=[];checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)
def command(*items):
    subprocess.run(items,check=True,capture_output=True,text=True,timeout=20)
def run(*options):
    return subprocess.run(['chroot',str(root),'/usr/bin/python','-I','/opt/initializer',*options],capture_output=True,text=True,timeout=20)
def reset():
    for relative in ('var/lib/waydroid','var/lib/omarchy-apollo'):
        path=root/relative
        if path.is_symlink():path.unlink()
        elif path.exists():shutil.rmtree(path)
        path.mkdir(parents=True,mode=0o700)
try:
    for name in ('usr','proc','dev','etc','opt','var/lib/waydroid','var/lib/omarchy-apollo'):
        (root/name).mkdir(parents=True,exist_ok=True)
    for name,destination in (('bin','usr/bin'),('sbin','usr/bin'),('lib','usr/lib')):
        (root/name).symlink_to(destination)
    shutil.copyfile(args.initializer,root/'opt/initializer')
    stub=workspace/'waydroid-fixture';stub.write_text('''#!/usr/bin/python3
from pathlib import Path
import sys,json
storage=Path('/var/lib/waydroid')
with (storage/'calls').open('a') as output:output.write(json.dumps(sys.argv[1:])+'\\n')
if (storage/'fail-next').exists():raise SystemExit(1)
(storage/'waydroid.cfg').write_text('fixture-only\\n')
print('Fixture initialization completed')
''');stub.chmod(0o755)
    command('mount','--bind',str(root),str(root));mounted.append(root)
    for name in ('usr','proc','dev'):
        path=root/name
        command('mount','--rbind','/'+name,str(path));mounted.append(path)
        command('mount','--make-rslave',str(path))
        if name=='usr':command('mount','-o','remount,bind,ro',str(path))
    target=root/'usr/bin/waydroid'
    command('mount','--bind',str(stub),str(target));mounted.append(target)
    command('mount','-o','remount,bind,ro',str(target))
    for selected,expected in ((None,'VANILLA'),('vanilla','VANILLA'),('gapps','GAPPS')):
        reset();process=run(*([] if selected is None else ['--flavor',selected]))
        label=selected or 'default'
        check(label+': initialization succeeds',process.returncode==0)
        record=json.loads((root/'var/lib/omarchy-apollo/android-installation.json').read_text())
        check(label+': selected image type reaches Waydroid',json.loads((root/'var/lib/waydroid/calls').read_text())==['init','-s',expected])
        check(label+': public result describes selection without a Google account',record['waydroid_system_type']==expected and record['google_account_configured_by_installer'] is False)
        check(label+': diagnostic log stays private',stat.S_IMODE((root/'var/lib/omarchy-apollo/preflight/android-first-initialization-private.log').stat().st_mode)==0o600)
        check(label+': ordinary session can traverse Android configuration storage',stat.S_IMODE((root/'var/lib/waydroid').stat().st_mode)==0o755)
        check(label+': shared Android configuration is readable',stat.S_IMODE((root/'var/lib/waydroid/waydroid.cfg').stat().st_mode)==0o644)
        before=(root/'var/lib/waydroid/calls').read_bytes()
        again=run('--flavor','gapps' if expected=='VANILLA' else 'vanilla')
        check(label+': a later choice preserves the existing installation',again.returncode!=0 and (root/'var/lib/waydroid/calls').read_bytes()==before)
    reset();invalid=run('--flavor','other')
    check('invalid flavor never starts initialization',invalid.returncode!=0 and not (root/'var/lib/waydroid/calls').exists())
    reset();(root/'var/lib/waydroid/waydroid.cfg').symlink_to('/missing')
    check('even a dangling existing configuration is preserved',run().returncode!=0 and not (root/'var/lib/waydroid/calls').exists())
    reset();(root/'var/lib/waydroid').chmod(0o777)
    check('writable Android storage is rejected',run().returncode!=0 and not (root/'var/lib/waydroid/calls').exists())
    reset();private=root/'var/lib/omarchy-apollo/preflight';private.mkdir(mode=0o755)
    check('public diagnostic directory is rejected',run().returncode!=0 and not (root/'var/lib/waydroid/calls').exists())
    reset();private=root/'var/lib/omarchy-apollo/preflight';private.mkdir(mode=0o700)
    sentinel=root/'opt/sentinel';sentinel.write_text('preserve this fixture file')
    (private/'android-first-initialization-private.log').symlink_to('/opt/sentinel')
    check('diagnostic symlinks cannot overwrite files or start initialization',run().returncode!=0 and sentinel.read_text()=='preserve this fixture file' and not (root/'var/lib/waydroid/calls').exists())
    reset();(root/'var/lib/waydroid/fail-next').touch()
    check('failed initialization is reported without a success record',run().returncode!=0 and not (root/'var/lib/omarchy-apollo/android-installation.json').exists())
    result={'checks_passed':len(checks),'checks':checks,'waydroid_command_replaced_by_fixture':True,'real_google_installation_tested':False,'existing_android_data_accessed':False}
    (workspace/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
finally:
    for path in reversed(mounted):subprocess.run(['umount','-R',str(path)],capture_output=True)
