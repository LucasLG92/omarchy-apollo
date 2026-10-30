#!/usr/bin/python3
"""Check PIN admin policies with real PAM and a disposable locked account.

Does not change the live sudo/polkit policies or use an owner's PIN. The test
copies the actual installed account/session policies into isolated PAM services.
"""
from pathlib import Path
import argparse
import json
import os
import pwd
import runpy
import secrets
import subprocess
import tempfile
import time

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[1])
args=parser.parse_args();assert os.getuid()==0 and os.geteuid()==0
source=args.source;name='apollo-admin-pin-test'
def run(items,**options):return subprocess.run(items,capture_output=True,text=True,timeout=15,**options)
assert run(['getent','passwd',name]).returncode!=0
core=Path('/etc/pam.d/omarchy-apollo-admin-fixture')
services={item:Path('/etc/pam.d/omarchy-apollo-admin-fixture-'+item) for item in ('sudo','polkit-1')}
assert not core.exists() and not any(path.exists() for path in services.values())
module=runpy.run_path(str(source/'platform/omarchy-apollo-enable-pin-administration'),run_name='apollo_admin_policy_test')
created=False;checks=[]
def check(label,condition):assert condition,label;checks.append(label)
try:
    with tempfile.TemporaryDirectory(prefix='admin-pin-check-',dir='/var/lib/omarchy-apollo') as folder:
        folder=Path(folder);folder.chmod(0o755)
        text=(source/'lock/verify-pin.c').read_text();marker='#define PIN_ROOT "/var/lib/omarchy-apollo/pins"'
        assert text.count(marker)==1
        helper_source=folder/'verify-pin.c';helper_source.write_text(text.replace(marker,'#define PIN_ROOT "'+str(folder/'pins')+'"'))
        probe_code=(source/'tests/support/pam-probe.c').read_text();target='  if (handle) pam_end(handle, status);'
        assert probe_code.count(target)==1
        probe_source=folder/'pam-probe.c';probe_source.write_text(probe_code.replace(target,'  if (status == PAM_SUCCESS) status = pam_acct_mgmt(handle, 0);\n'+target))
        helper=folder/'verify-pin';probe=folder/'pam-probe'
        for src,out,library in ((helper_source,helper,'crypt'),(probe_source,probe,'pam')):
            result=run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-fstack-protector-strong','-D_FORTIFY_SOURCE=3',str(src),'-o',str(out),'-l'+library]);assert result.returncode==0,result.stderr
        result=run(['useradd','--no-create-home','--shell','/bin/bash',name]);assert result.returncode==0;created=True
        owner=pwd.getpwnam(name);os.chown(helper,0,owner.pw_gid);helper.chmod(0o4750)
        check('synthetic account has no Unix password',run(['passwd','-S',name]).stdout.split()[1]=='L')
        pin=''.join(secrets.choice('0123456789') for _ in range(8));wrong=str((int(pin)+1)%100000000).zfill(8)
        assert run([str(helper),'--enroll',str(owner.pw_uid)],input=pin+'\n'+pin+'\n').returncode==0
        core.write_text((source/'lock/omarchy-lock-password').read_text().replace('/usr/lib/omarchy/apollo/verify-pin',str(helper)));core.chmod(0o644)
        for service,target_file in services.items():
            original=Path('/etc/pam.d')/service
            if not original.exists():original=Path('/usr/lib/pam.d')/service
            before=original.read_text();after=module['transform'](service,before)
            check(service+': account and session policies unchanged',[row for row in before.splitlines() if not row.startswith('auth')]==[row for row in after.splitlines() if not row.startswith('auth')])
            check(service+': transform is idempotent',module['transform'](service,after)==after)
            target_file.write_text(after.replace('omarchy-apollo-admin',core.name));target_file.chmod(0o644)
            def authenticate(value):return run(['runuser','-u',name,'--',str(probe),target_file.name],input=value+'\n').returncode
            check(service+': PIN passes real PAM authentication and account checks',authenticate(pin)==0)
            if service=='sudo':
                check('wrong numeric admin PIN rejected',authenticate(wrong)!=0)
                time.sleep(2.2)
                check('correct admin PIN works after retry delay',authenticate(pin)==0)
        for text in ('auth sufficient pam_permit.so\n'+before,before+'auth include system-auth\n'):
            try:module['transform']('polkit-1',text)
            except RuntimeError:rejected=True
            else:rejected=False
            check('unexpected authentication policy rejected',rejected)
        result={'checks_passed':len(checks),'checks':checks,'pam_authentication_and_account_management_checked':True,'actual_sudo_or_polkit_process_tested':False,'owner_credentials_used':False,'live_sudo_and_polkit_policies_changed':False,'unix_password_created_for_fixture':False}
finally:
    core.unlink(missing_ok=True)
    for path in services.values():path.unlink(missing_ok=True)
    if created:
        run(['faillock','--user',name,'--reset'])
        run(['loginctl','terminate-user',name])
        for attempt in range(20):
            removal=run(['userdel',name])
            if removal.returncode==0:break
            assert 'currently used by process' in removal.stderr,removal.stderr
            time.sleep(0.2)
        else:raise RuntimeError('The temporary account manager did not stop for cleanup.')
result['temporary_account_removed']=run(['getent','passwd',name]).returncode!=0
assert result['temporary_account_removed']
print(json.dumps(result,indent=2))
