#!/usr/bin/python3
"""Real PAM and sudo regression for a real-root PAM helper caller.

Run as root in a systemd PrivateMounts namespace. Uses a disposable account,
synthetic PIN and isolated verifier store. Never reads the owner PIN or hash.
"""
from pathlib import Path
import argparse,json,os,pwd,runpy,secrets,shutil,subprocess,tempfile,time

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--baseline-source',type=Path,required=True)
args=parser.parse_args()
assert os.getuid()==0 and os.geteuid()==0
assert os.readlink('/proc/self/ns/mnt')!=os.readlink('/proc/1/ns/mnt')
name='apollo-pin-context-test';checks=[];created=False;mounts=[];services=[]
def run(command,**kw):return subprocess.run(command,capture_output=True,text=True,timeout=20,**kw)
def check(label,condition):assert condition,label;checks.append(label)
assert run(['getent','passwd',name]).returncode!=0
try:
    with tempfile.TemporaryDirectory(prefix='pin-context-',dir='/var/lib/omarchy-apollo') as temporary:
        root=Path(temporary);root.chmod(0o755)
        policy=runpy.run_path(str(args.source/'platform/omarchy-apollo-enable-pin-administration'),run_name='pin_context_policy')
        assert run(['useradd','--no-create-home','--shell','/bin/bash',name]).returncode==0;created=True
        user=pwd.getpwnam(name)
        check('temporary account has no Unix password',run(['passwd','-S',name]).stdout.split()[1]=='L')
        pin=''.join(secrets.choice('0123456789') for _ in range(8))
        wrong=str((int(pin)+1)%100000000).zfill(8)
        marker='#define PIN_ROOT "/var/lib/omarchy-apollo/pins"'
        helpers={}
        for label,path in [('baseline',args.baseline_source),('fixed',args.source/'lock/verify-pin.c')]:
            text=path.read_text();assert text.count(marker)==1
            src=root/(label+'.c');src.write_text(text.replace(marker,'#define PIN_ROOT "'+str(root/'pins')+'"'))
            binary=root/label
            p=run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-fstack-protector-strong','-D_FORTIFY_SOURCE=3',str(src),'-o',str(binary),'-lcrypt']);assert p.returncode==0,p.stderr
            os.chown(binary,0,user.pw_gid);binary.chmod(0o4750);helpers[label]=binary
        assert run([str(helpers['fixed']),'--enroll',str(user.pw_uid)],input=pin+'\n'+pin+'\n').returncode==0
        text=(args.source/'tests/support/pam-probe.c').read_text()
        text=text.replace('if (argc != 2 || !fgets', 'if ((argc != 2 && argc != 3) || (argc == 3 && getuid() != 0) || !fgets')
        text=text.replace('struct passwd *owner = getpwuid(getuid());','struct passwd *owner = argc == 3 ? getpwnam(argv[2]) : getpwuid(getuid());')
        text=text.replace('  if (handle) pam_end(handle, status);','  if (status == PAM_SUCCESS) status = pam_acct_mgmt(handle, 0);\n  if (handle) pam_end(handle, status);')
        src=root/'probe.c';src.write_text(text);probe=root/'probe'
        p=run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(src),'-o',str(probe),'-lpam']);assert p.returncode==0,p.stderr
        for label,helper in helpers.items():
            service=Path('/etc/pam.d')/('apollo-pin-context-'+label);assert not service.exists();services.append(service)
            service.write_text((args.source/'lock/omarchy-lock-password').read_text().replace('/usr/lib/omarchy/apollo/verify-pin',str(helper)));service.chmod(0o644)
            ordinary=run(['runuser','-u',name,'--',str(probe),service.name],input=pin+'\n')
            check(label+': ordinary-user PAM context accepts the synthetic PIN',ordinary.returncode==0)
            privileged=run([str(probe),service.name,name],input=pin+'\n')
            check(label+': root PAM context '+('reproduces the rejection' if label=='baseline' else 'accepts the same synthetic PIN'),privileged.returncode!=(0) if label=='baseline' else privileged.returncode==0)
        for service_name in ['sudo','polkit-1']:
            original=Path('/etc/pam.d')/service_name
            if not original.exists():original=Path('/usr/lib/pam.d')/service_name
            service=Path('/etc/pam.d')/('apollo-pin-context-'+service_name);assert not service.exists();services.append(service)
            transformed=policy['transform'](service_name,original.read_text())
            service.write_text(transformed.replace('auth include omarchy-apollo-admin','auth include apollo-pin-context-fixed'));service.chmod(0o644)
            check(service_name+': real-root PAM authentication and account checks pass',run([str(probe),service.name,name],input=pin+'\n').returncode==0)
        # Root may use PAM_USER; an ordinary setuid caller cannot select another UID.
        for label,uid,identity,pam_type in [('root user disallowed',0,'root','auth'),('wrong PAM type disallowed',0,name,'account'),('ordinary user cannot impersonate another account',user.pw_uid,'nobody','auth')]:
            command=['env','PAM_USER='+identity,'PAM_TYPE='+pam_type,str(helpers['fixed'])]
            if uid:command=['runuser','-u',name,'--',*command]
            check(label,run(command,input=pin+'\n').returncode!=0)
        # Bind the candidate into this namespace only. The real sudo program and
        # real installed PAM stack now exercise the production invocation path.
        target=Path('/usr/lib/omarchy/apollo/verify-pin')
        assert run(['mount','--bind',str(helpers['fixed']),str(target)]).returncode==0;mounts.append(target)
        rules=root/'sudoers.d';shutil.copytree('/etc/sudoers.d',rules)
        rule=rules/'90-apollo-pin-context-test';rule.write_text(name+' ALL=(root) /usr/bin/true\n');rule.chmod(0o440)
        assert run(['mount','--bind',str(rules),'/etc/sudoers.d']).returncode==0;mounts.append(Path('/etc/sudoers.d'))
        assert run(['visudo','--check']).returncode==0
        command=['runuser','-u',name,'--','sudo','-k','-S','-p','','--','/usr/bin/true']
        check('actual sudo authorizes the harmless root command with the PIN',run(command,input=pin+'\n').returncode==0)
        check('actual sudo rejects an incorrect PIN',run(command,input=wrong+'\n').returncode!=0)
        time.sleep(2.2)
        check('actual sudo accepts the correct PIN after retry delay',run(command,input=pin+'\n').returncode==0)
        result={'checks_passed':len(checks),'checks':checks,'actual_sudo_process_tested':True,'root_pam_context_tested':True,'owner_credentials_used':False,'owner_verifier_store_accessed':False,'physical_polkit_popup_accepted':False,'existing_live_authentication_policies_modified':False}
finally:
    for target in reversed(mounts):assert run(['umount',str(target)]).returncode==0
    for service in services:service.unlink(missing_ok=True)
    if created:
        run(['faillock','--user',name,'--reset']);run(['loginctl','terminate-user',name])
        for attempt in range(20):
            p=run(['userdel',name])
            if p.returncode==0:break
            assert 'currently used by process' in p.stderr,p.stderr
            time.sleep(0.2)
        else:raise RuntimeError('Temporary account did not stop')
assert run(['getent','passwd',name]).returncode!=0
result['temporary_account_removed']=True
print(json.dumps(result,indent=2))
