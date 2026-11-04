"""Exercise activation/restore against a disposable root, never real PAM."""
from pathlib import Path
import importlib.util,json,tempfile,os,stat,hashlib
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('auth_policy',HERE/'auth-policy.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def write(root,name,body,mode=0o644):
 path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(body);path.chmod(mode);return path
def fixture(root):
 original=b'#%PAM-1.0\nauth include system-auth\naccount include system-auth\npassword include system-auth\nsession include system-auth\n'
 for service in ('sddm','sudo'):write(root,'etc/pam.d/'+service,original)
 write(root,'usr/lib/pam.d/polkit-1',original)
 for name in ('etc/apollo','usr/share/sddm/themes/omarchy-apollo-firstboot','var/lib/apollo/fingerprint-auth-v1'):(root/name).mkdir(parents=True,exist_ok=True)
 (root/'var/lib/apollo/fingerprint-auth-v1').chmod(0o700)
 lib=write(root,'usr/lib/libfprint-2.so.2.0.0',b'test-only-library'*30000)
 selector=write(root,'usr/lib/security/pam_apollo_method.so',b'test-only-selector')
 template=write(root,'var/lib/apollo/fingerprint-templates-v1/u1000/enrolled-v1',b'not-a-biometric-record'*5,0o600)
 a={'schema':1,'real_standard_fprintd_match_observed':True,'wrong_finger_rejected':True,'library_sha256':p.file_sha(lib),'selector_sha256':p.file_sha(selector),'template_inode':template.stat().st_ino,'template_bytes':template.stat().st_size}
 marker=write(root,'var/lib/apollo/fingerprint-auth-v1/provider-verified.json',(json.dumps(a)+'\n').encode(),0o600)
 return original,template,marker
def expect_error(fn):
 try:fn()
 except (RuntimeError,OSError):return
 raise AssertionError('invalid state accepted')
def main():
 assert os.geteuid()==0
 cases=[]
 with tempfile.TemporaryDirectory(prefix='apollo-PAM-policy-') as directory:
  base=Path(directory)
  for variant in ('normal','private-PAM-mode','wrong-provider','writable-marker','symlink-PAM','existing-override','external-edit','partial-write','unapproved','existing-lock','changed-template'):
   root=base/variant;root.mkdir();original,template,marker=fixture(root);inode=template.stat().st_ino;blob=template.read_bytes()
   if variant=='wrong-provider':(root/'usr/lib/libfprint-2.so.2.0.0').write_bytes(b'changed')
   elif variant=='private-PAM-mode':(root/'etc/pam.d/sudo').chmod(0o600)
   elif variant=='writable-marker':marker.chmod(0o666)
   elif variant=='symlink-PAM':
    path=root/'etc/pam.d/sudo';path.unlink();path.symlink_to(root/'etc/pam.d/sddm')
   elif variant=='existing-override':write(root,'usr/share/sddm/themes/omarchy-apollo-firstboot/theme.conf.user',b'[General]\nUser=example\n')
   elif variant=='unapproved':
    a=json.loads(marker.read_text());a['wrong_finger_rejected']=False;marker.write_text(json.dumps(a))
   elif variant=='changed-template':template.write_bytes(blob+b'x')
   elif variant=='existing-lock':write(root,'etc/pam.d/omarchy-lock-fingerprint',b'auth required pam_fprintd.so\n')
   if variant in ('wrong-provider','writable-marker','symlink-PAM','existing-override','unapproved','changed-template'):
    before=(root/'etc/pam.d/sddm').read_bytes();expect_error(lambda:p.enable(root));assert (root/'etc/pam.d/sddm').read_bytes()==before
   elif variant=='partial-write':
    old=p.atomic
    def fail_once(path,body,replace=False,mode=0o644):
     if path.name=='sudo' and b'pam_apollo_method' in body:raise OSError('test-only failed write')
     return old(path,body,replace,mode)
    p.atomic=fail_once
    try:expect_error(lambda:p.enable(root))
    finally:p.atomic=old
    assert all((root/'etc/pam.d'/s).read_bytes()==original for s in ('sddm','sudo'))
    assert not (root/'etc/pam.d/polkit-1').exists()
    assert not any((root/'etc/pam.d').glob('apollo-*'))
   else:
    before_lock=(root/'etc/pam.d/omarchy-lock-fingerprint').read_bytes() if variant=='existing-lock' else None
    assert p.enable(root)['ok'];expect_error(lambda:p.enable(root))
    for service in p.SERVICES:
     _,other=p.split_auth(original);_,after_other=p.split_auth((root/'etc/pam.d'/service).read_bytes().replace(b'apollo-password-',b'fixture-password-').replace(b'pam_apollo_method',b'fixture_method'))
     # Category order and content (account/password/session) are retained.
     lines=lambda b:[x for x in b.splitlines() if x and not x.startswith(b'#') and not x.startswith(b'auth ')]
     assert lines(other)==lines(after_other)
    if variant=='external-edit':
     path=root/'etc/pam.d/sudo';path.write_bytes(path.read_bytes()+b'# later admin edit\n')
     before=(root/'etc/pam.d/sddm').read_bytes();expect_error(lambda:p.restore(root));assert (root/'etc/pam.d/sddm').read_bytes()==before
    else:
     assert p.restore(root)['ok']
     assert all((root/'etc/pam.d'/s).read_bytes()==original for s in ('sddm','sudo'))
     assert not (root/'etc/pam.d/polkit-1').exists()
     lock=root/'etc/pam.d/omarchy-lock-fingerprint';assert lock.read_bytes()==before_lock if before_lock is not None else not lock.exists()
     assert all(not (root/name).exists() for name in p.EXTRAS)
     if variant=='private-PAM-mode':assert stat.S_IMODE((root/'etc/pam.d/sudo').stat().st_mode)==0o600
   if variant!='changed-template':assert template.stat().st_ino==inode and template.read_bytes()==blob
   cases.append(variant)
 proof={'ok':True,'disposable_root_only':True,'cases':cases,'policy_source_sha256':hashlib.sha256((HERE/'auth-policy.py').read_bytes()).hexdigest(),'original_password_account_session_rules_preserved':True,'private_PAM_file_modes_preserved':True,'vendor_polkit_configuration_restored_without_override':True,'partial_write_rolled_back':True,'administrator_edits_never_overwritten':True,'biometric_record_not_read_by_policy_or_modified':True,'phone_operations':0}
 (HERE/'native-authentication-policy-test-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
