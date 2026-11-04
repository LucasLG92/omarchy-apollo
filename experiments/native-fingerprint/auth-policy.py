#!/usr/bin/python3 -I
"""Reversible service-scoped PAM configuration; no credentials or biometrics.

Only root can enable. Requires an on-device root attestation produced after the
real standard fprintd test. Installation alone never changes authentication.
"""
from pathlib import Path
import hashlib,json,os,re,stat,sys

SERVICES=('sddm','sudo','polkit-1')
PREFIX='apollo-password-'
FINGERPRINT='''#%PAM-1.0
# Apollo fingerprint branch. No password or authorization rules are replaced.
auth required pam_shells.so
auth requisite pam_nologin.so
auth requisite pam_faillock.so preauth
auth [success=1 default=bad] pam_fprintd.so max-tries=3 timeout=20
auth [default=die] pam_faillock.so authfail
auth required pam_faillock.so authsucc
auth required pam_env.so
'''.encode()
LOCK=b'''#%PAM-1.0
auth substack apollo-fingerprint-auth
account include system-local-login
'''
EXTRAS={
 'usr/share/sddm/themes/omarchy-apollo-firstboot/theme.conf.user':b'[General]\nApolloFingerprintEnabled=true\n',
 'etc/apollo/fingerprint-authentication.json':b'{"schema":1,"initial_login":true,"lock":true,"admin":true}\n',
}

def sha(body):return hashlib.sha256(body).hexdigest()
def require(ok,message):
 if not ok:raise RuntimeError(message)
def trusted(path,regular=True):
 s=path.lstat()
 kind=stat.S_ISREG(s.st_mode) if regular else stat.S_ISDIR(s.st_mode)
 require(kind and s.st_uid==0 and not s.st_mode&0o022 and (not regular or s.st_nlink==1),'untrusted authentication path')
 return s
def file_sha(path):
 trusted(path)
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def read(path):
 trusted(path);body=path.read_bytes();require(len(body)<65536,'oversized PAM configuration');return body

def split_auth(body):
 text=body.decode('utf-8');require('\\\n' not in text and '\x00' not in text,'continued or binary PAM requires review')
 auth=[];other=[]
 for line in text.splitlines(keepends=True):
  clean=line.strip()
  if not clean or clean.startswith('#'):other.append(line);continue
  require(re.match(r'^-?(?:auth|account|password|session)\s+',clean) is not None,'unreviewed PAM syntax')
  if re.match(r'^-?auth\s+',clean):auth.append(line)
  else:other.append(line)
 require(auth and all('pam_apollo_method' not in x and 'apollo-password-' not in x for x in auth),'already customized authentication stack')
 return ''.join(auth).encode(),''.join(other).encode()

def wrap(service,body):
 require(service in SERVICES,'unsupported PAM service')
 auth,other=split_auth(body)
 rules=f'''# Apollo: typed password uses the original stack immediately.
# An empty response explicitly selects the fingerprint branch (UID1000 only).
# Jumps do not grant authentication. A missing selector uses the password stack.
auth [success=2 default=ignore] pam_apollo_method.so select-fingerprint
auth substack {PREFIX}{service}
auth [default=1] pam_succeed_if.so quiet uid >= 0
auth substack apollo-fingerprint-auth
'''.encode()
 return b'#%PAM-1.0\n'+rules+other,auth

def plan(root=Path('/')):
 etc=root/'etc/pam.d';trusted(etc,False);files={};before={}
 for service in SERVICES:
  local=etc/service;vendor=root/'usr/lib/pam.d'/service
  source=local if local.exists() or local.is_symlink() else vendor
  original=read(source);wrapped,password=wrap(service,original)
  before[service]={'local':source==local,'body':original.decode(),'sha256':sha(original),'mode':stat.S_IMODE(source.lstat().st_mode)}
  files[service]=wrapped;files[PREFIX+service]=password
 files['apollo-fingerprint-auth']=FINGERPRINT
 lock=etc/'omarchy-lock-fingerprint'
 before['omarchy-lock-fingerprint']={'local':lock.exists(),'body':read(lock).decode() if lock.exists() else None,'mode':stat.S_IMODE(lock.lstat().st_mode) if lock.exists() else 0o644}
 files['omarchy-lock-fingerprint']=LOCK
 for name in files:
  if name.startswith('apollo-'):require(not (etc/name).exists() and not (etc/name).is_symlink(),'managed PAM name already exists')
 for name in EXTRAS:
  path=root/name;trusted(path.parent,False);require(not path.exists() and not path.is_symlink(),'authentication UI override already exists; review required')
 return {'schema':1,'original':before,'managed':{name:body.decode() for name,body in files.items()},'managed_sha256':{name:sha(body) for name,body in files.items()},'extras':{name:body.decode() for name,body in EXTRAS.items()}}

def atomic(path,body,replace=False,mode=0o644):
 temp=path.parent/('.'+path.name+'.apollo-new')
 fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
 try:
  with os.fdopen(fd,'wb') as out:out.write(body);out.flush();os.fchmod(out.fileno(),mode);os.fsync(out.fileno())
  if replace:os.replace(temp,path)
  else:os.link(temp,path,follow_symlinks=False);temp.unlink()
  directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);os.fsync(directory);os.close(directory)
 finally:
  if temp.exists():temp.unlink()

def enable(root=Path('/')):
 require(os.geteuid()==0,'root required');state=root/'var/lib/apollo/fingerprint-auth-v1';trusted(state,False)
 marker=state/'provider-verified.json';s=trusted(marker);require(stat.S_IMODE(s.st_mode)==0o600,'provider attestation must be private')
 approved=json.loads(read(marker));require(approved.get('schema')==1 and approved.get('real_standard_fprintd_match_observed') is True and approved.get('wrong_finger_rejected') is True,'real provider acceptance missing')
 require(file_sha(root/'usr/lib/libfprint-2.so.2.0.0')==approved.get('library_sha256'),'verified provider changed')
 require(file_sha(root/'usr/lib/security/pam_apollo_method.so')==approved.get('selector_sha256'),'verified selector changed')
 template=root/'var/lib/apollo/fingerprint-templates-v1/u1000/enrolled-v1';ts=trusted(template)
 require(ts.st_ino==approved.get('template_inode') and ts.st_size==approved.get('template_bytes') and stat.S_IMODE(ts.st_mode)==0o600,'enrolled record changed')
 backup=state/'before.json';require(not backup.exists(),'already activated or interrupted; inspect saved state')
 selected=plan(root)
 atomic(backup,(json.dumps(selected,sort_keys=True)+'\n').encode());backup.chmod(0o600)
 etc=root/'etc/pam.d';done=[]
 try:
  # Password branches and fingerprint stack must exist before service wrappers.
  order=[PREFIX+s for s in SERVICES]+['apollo-fingerprint-auth','omarchy-lock-fingerprint']+list(SERVICES)
  for name in order:
   path=etc/name;previous=selected['original'].get(name)
   if previous and previous['local']:
    expected=previous.get('sha256') or sha(previous['body'].encode());require(sha(read(path))==expected,'PAM changed during activation')
   else:require(not path.exists() and not path.is_symlink(),'PAM override appeared during activation')
   atomic(path,selected['managed'][name].encode(),replace=bool(previous and previous['local']),mode=previous['mode'] if previous and previous['local'] else 0o644);done.append(name)
  for name,body in selected['extras'].items():atomic(root/name,body.encode())
 except Exception:
  restore(root,allow_partial=True);raise
 return {'ok':True,'configured_services':list(SERVICES)+['omarchy-lock-fingerprint'],'password_route_preserved':True,'global_PAM_unchanged':True,'physical_unlock_still_requires_test':True}

def restore(root=Path('/'),allow_partial=False):
 require(os.geteuid()==0,'root required');state=root/'var/lib/apollo/fingerprint-auth-v1';trusted(state,False)
 backup=state/'before.json';selected=json.loads(read(backup));etc=root/'etc/pam.d'
 # Check ALL paths before writing any. Never overwrite a later administrator edit.
 for name,expected in selected['managed_sha256'].items():
  path=etc/name;original=selected['original'].get(name)
  if not path.exists():require(allow_partial,'managed PAM file removed externally');continue
  actual=sha(read(path));require(actual==expected or (allow_partial and original and original['local'] and actual==sha(original['body'].encode())),'PAM edited after activation; manual review required')
 for name,body in selected['extras'].items():
  path=root/name
  if not path.exists():require(allow_partial,'authentication UI override removed externally');continue
  require(sha(read(path))==sha(body.encode()),'authentication UI override changed; manual review required')
 for name in selected['extras']:
  path=root/name
  if path.exists():path.unlink()
 for name in list(SERVICES)+['omarchy-lock-fingerprint']+[PREFIX+s for s in SERVICES]+['apollo-fingerprint-auth']:
  path=etc/name;original=selected['original'].get(name)
  if original and original['local']:atomic(path,original['body'].encode(),replace=path.exists(),mode=original['mode'])
  elif path.exists():path.unlink()
 backup.rename(state/'restored-before.json')
 return {'ok':True,'original_service_configuration_restored':True,'fingerprint_records_changed':False}

def main():
 require(os.geteuid()==0,'root required')
 require(sys.argv[1:] in (['--plan'],['--enable'],['--restore']),'unsupported operation')
 if sys.argv[1]=='--plan':
  selected=plan();print(json.dumps({'ok':True,'services':list(SERVICES),'configuration_sha256':sha(json.dumps(selected,sort_keys=True).encode()),'changes_applied':False}));return
 print(json.dumps(enable() if sys.argv[1]=='--enable' else restore()))
if __name__=='__main__':main()
