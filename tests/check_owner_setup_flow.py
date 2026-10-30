#!/usr/bin/python3
"""Check the real first-password shell helper in a disposable chroot.

The dialog, account updater and service manager are fixtures. No owner secret,
live password database, desktop window or PIN enrollment is used.
Run in a private mount namespace with an empty root-owned workspace.
"""
from pathlib import Path
import argparse
import json
import os
import shutil
import socket
import stat
import subprocess

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--workspace',type=Path,required=True)
parser.add_argument('--helper',type=Path,required=True)
args=parser.parse_args()
assert os.getuid()==0 and os.geteuid()==0
assert os.readlink('/proc/self/ns/mnt')!=os.readlink('/proc/1/ns/mnt')
workspace=args.workspace.resolve();info=workspace.stat()
assert workspace.is_dir() and not any(workspace.iterdir()) and info.st_uid==0 and not info.st_mode&0o077
root=workspace/'fixture';root.mkdir(mode=0o700);mounted=[];checks=[]
def command(*items):subprocess.run(items,check=True,capture_output=True,text=True,timeout=15)
def check(name,condition):assert condition,name;checks.append(name)
def create(relative,data,mode=0o644):
    target=root/relative;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(data);target.chmod(mode);return target
def make_socket(name):
    directory=root/'run/user/1001';directory.mkdir(parents=True,exist_ok=True)
    before=Path.cwd()
    try:
        os.chdir(directory);instance=socket.socket(socket.AF_UNIX);instance.bind(name);instance.close()
    finally:os.chdir(before)
    os.chown(directory/name,1001,1001)
def reset():
    for relative in ('etc/omarchy-apollo','etc/sudoers.d','run/user','var/lib/fixture'):
        target=root/relative;assert target.resolve().is_relative_to(root.resolve())
        if target.exists():shutil.rmtree(target)
    create('etc/omarchy-apollo/firstboot-needed','fixture-only\n',0o600)
    create('etc/sudoers.d/omarchy-apollo-firstboot','fixture-only\n',0o440)
    (root/'var/lib/fixture').mkdir(parents=True)
    make_socket('wayland-1')
def run(mode='success',caller='apollo'):
    process=subprocess.run(['chroot',str(root),'/usr/bin/env','-i','PATH=/usr/bin',
        'SUDO_USER='+caller,'APOLLO_FIXTURE_MODE='+mode,'/bin/bash','/opt/helper'],capture_output=True,text=True,timeout=15)
    events=root/'var/lib/fixture/events.jsonl'
    values=[json.loads(line) for line in events.read_text().splitlines()] if events.exists() else []
    # The synthetic input must not escape through helper diagnostics or logs.
    sample='fixture-'+'passphrase-123'
    assert sample not in process.stdout+process.stderr+(events.read_text() if events.exists() else '')
    return process,values
def markers_exist():return (root/'etc/omarchy-apollo/firstboot-needed').exists() and (root/'etc/sudoers.d/omarchy-apollo-firstboot').exists()
try:
    for name in ('usr','dev','proc','etc','opt','run','var/lib/fixture'):(root/name).mkdir(parents=True,exist_ok=True)
    for name,target in (('bin','usr/bin'),('sbin','usr/bin'),('lib','usr/lib')):(root/name).symlink_to(target)
    create('etc/passwd','root:x:0:0:root:/root:/bin/bash\napollo:x:1001:1001::/home/apollo:/bin/bash\n')
    create('etc/group','root:x:0:\napollo:x:1001:\n')
    create('etc/nsswitch.conf','passwd: files\ngroup: files\nshadow: files\n')
    create('run/apollo-persistent','')
    shutil.copyfile(args.helper,root/'opt/helper')
    wrapper=workspace/'runuser';wrapper.write_text('''#!/usr/bin/python3
import os,sys
assert sys.argv[1:4]==['-u','apollo','--']
os.execv('/usr/bin/'+sys.argv[4],sys.argv[4:])
''');wrapper.chmod(0o755)
    fixture=workspace/'fixture-command';fixture.write_text(r'''#!/usr/bin/python3
from pathlib import Path
import os,sys,json
kind=Path(sys.argv[0]).name;folder=Path('/var/lib/fixture')
mode=os.environ['APOLLO_FIXTURE_MODE'];sample='fixture-'+'passphrase-123'
def record(value):
 with (folder/'events.jsonl').open('a') as output:output.write(json.dumps(value)+'\n')
events=[json.loads(line) for line in (folder/'events.jsonl').read_text().splitlines()] if (folder/'events.jsonl').exists() else []
if kind=='password-dialog':
 count=sum(event['operation']=='dialog' for event in events);record({'operation':'dialog'})
 if mode=='cancel':raise SystemExit(2)
 print('short' if mode=='invalid-first' and count==0 else sample)
elif kind=='chpasswd':
 value=sys.stdin.read();correct=value=='apollo:'+sample+'\n'
 record({'operation':'password-update','stdin_matches_fixture':correct,'no_extra_arguments':len(sys.argv)==1})
 assert correct and len(sys.argv)==1
 if mode=='backend-retry' and not any(event['operation']=='password-update' for event in events):raise SystemExit(1)
elif kind=='zenity':record({'operation':'error-dialog'})
elif kind=='systemctl':record({'operation':'service-request','arguments':sys.argv[1:]})
else:raise SystemExit(1)
''');fixture.chmod(0o755)
    for name in ('usr','dev','proc'):
        path=root/name;command('mount','--rbind','/'+name,str(path));mounted.append(path)
        command('mount','--make-rslave',str(path))
        if name=='usr':command('mount','-o','remount,bind,ro',str(path))
    for target,source in (('usr/bin/runuser',wrapper),('usr/bin/chpasswd',fixture),('usr/bin/systemctl',fixture),('usr/bin/zenity',fixture),('usr/lib/omarchy/apollo/password-dialog',fixture)):
        path=root/target;assert path.is_file();command('mount','--bind',str(source),str(path));mounted.append(path)
    for mode in ('success','cancel','backend-retry','invalid-first'):
        reset();process,events=run(mode)
        updates=[event for event in events if event['operation']=='password-update']
        pins=[event for event in events if event.get('arguments')==['start','--no-block','omarchy-apollo-owner-pin-setup.service']]
        if mode=='cancel':check('cancellation preserves setup and never changes a password or starts PIN enrollment',process.returncode==0 and markers_exist() and not updates and not pins)
        else:
            check(mode+': password uses stdin and success advances to PIN setup',process.returncode==0 and not markers_exist() and len(pins)==1 and all(item['stdin_matches_fixture'] and item['no_extra_arguments'] for item in updates))
            if mode=='backend-retry':check('account-update failure is shown and retry succeeds',len(updates)==2 and sum(event['operation']=='error-dialog' for event in events)==1)
            if mode=='invalid-first':check('invalid dialog output is rejected before the account updater',len(updates)==1 and sum(event['operation']=='error-dialog' for event in events)==1)
    reset();process,events=run(caller='another-user')
    check('another caller cannot use the one-time helper',process.returncode!=0 and markers_exist() and not events)
    reset();(root/'etc/omarchy-apollo/firstboot-needed').chmod(0o644);process,events=run()
    check('incorrect marker permissions reject setup',process.returncode!=0 and markers_exist() and not events)
    reset();marker=root/'etc/omarchy-apollo/firstboot-needed';marker.unlink();marker.symlink_to('/etc/passwd');process,events=run()
    check('a setup-marker symlink is rejected',process.returncode!=0 and marker.is_symlink() and not events)
    reset();make_socket('wayland-2');process,events=run()
    check('ambiguous local displays are rejected',process.returncode!=0 and markers_exist() and not events)
    result={'checks_passed':len(checks),'checks':checks,'real_owner_credentials_used':False,'actual_password_database_changed':False,'dialog_account_updater_and_service_manager_replaced_by_fixtures':True,'real_pin_unlock_tested':False}
    (workspace/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
finally:
    for path in reversed(mounted):subprocess.run(['umount','-R',str(path)],capture_output=True)
