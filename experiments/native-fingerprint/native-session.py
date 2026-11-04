#!/usr/bin/python3 -I
"""Root-only, bounded native Apollo fingerprint operation and cleanup."""
from pathlib import Path
import fcntl,hashlib,json,os,selectors,signal,stat,subprocess,sys,time
PREFIX=Path('/usr/lib/apollo/fingerprint');stop=False
UNITS=('apollo-fpc-ta.service','apollo-qsee-supplicant.service','apollo-fpc-native-check.service')
def interrupted(*_):
 global stop
 stop=True
def run(args,timeout=15):return subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=timeout,env={'PATH':'/usr/bin:/bin','LC_ALL':'C'})
def checked(args,timeout=15):
 p=run(args,timeout)
 if p.returncode:raise RuntimeError('native_command_failed')
 return p.stdout
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def trusted(path,mode=None):
 s=Path(path).lstat()
 if s.st_uid!=0 or s.st_mode&0o022 or (mode is not None and stat.S_IMODE(s.st_mode)!=mode):raise RuntimeError('untrusted_runtime')
 return s
def guard(cleanup_only=False):
 if os.geteuid()!=0 or os.uname().release!='7.3.1-apollo-native-r15':raise RuntimeError('wrong_runtime')
 if b'xiaomi,apollo' not in Path('/proc/device-tree/compatible').read_bytes().split(b'\0'):raise RuntimeError('wrong_board')
 if Path('/etc/apollo/ram-trial').exists() or (not cleanup_only and Path('/var/lib/pacman/db.lck').exists()):raise RuntimeError('busy_or_trial')
 checked(['/usr/lib/apollo/native-storage-guard.py'],15)
 if cleanup_only:return {}
 cfgpath=Path('/usr/share/apollo/fingerprint/native-backend-v1.json');s=trusted(cfgpath)
 if not stat.S_ISREG(s.st_mode):raise RuntimeError('invalid_config')
 cfg=json.loads(cfgpath.read_text())
 for name,key in (('qsee-supplicant','listener_sha256'),('apollo-enrollment-authority','authority_sha256'),('apollo-biometric','backend_sha256')):
  path=PREFIX/name;s=trusted(path)
  if not stat.S_ISREG(s.st_mode) or digest(path)!=cfg[key]:raise RuntimeError('binary_changed')
 return cfg
def cleanup():
 stopped=run(['systemctl','stop',*UNITS],30).returncode==0
 removed=not Path('/sys/module/fpc_apollo').exists() or run(['modprobe','-r','fpc_apollo'],10).returncode==0
 return stopped and removed and not Path('/sys/module/fpc_apollo').exists()
def main():
 if sys.argv[1:] not in (['--verify'],['--enroll-first'],['--cleanup']):return 2
 signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
 signal.signal(signal.SIGHUP,interrupted)
 worker=None;lock=None;report={'ok':False,'matched':False,'finger_enrolled':False};phase='guard';started=False
 try:
  cfg=guard(cleanup_only=sys.argv[1:] == ['--cleanup']);runtime=Path('/run/apollo-fingerprint');s=trusted(runtime,0o700)
  if not stat.S_ISDIR(s.st_mode):raise RuntimeError('invalid_runtime_dir')
  lock=os.open(runtime/'operation.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
  s=os.fstat(lock)
  if s.st_uid!=0 or not stat.S_ISREG(s.st_mode) or stat.S_IMODE(s.st_mode)!=0o600 or s.st_nlink!=1:raise RuntimeError('invalid_operation_lock')
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if sys.argv[1:] == ['--cleanup']:
   report={'ok':cleanup(),'matched':False,'finger_enrolled':False,'cleanup_only':True};return 0 if report['ok'] else 1
  if stop:raise RuntimeError('cancelled')
  phase='secure_services';started=True;checked(['systemctl','start','apollo-fpc-ta.service'],40)
  for unit in UNITS:
   if checked(['systemctl','is-active',unit]).strip()!=b'active':raise RuntimeError('not_ready')
  pid=int(checked(['systemctl','show','apollo-qsee-supplicant.service','-p','MainPID','--value']))
  if pid<=0 or digest(Path('/proc')/str(pid)/'exe')!=cfg['listener_sha256']:raise RuntimeError('listener_not_ready')
  if Path('/sys/module/fpc_apollo').exists():checked(['modprobe','-r','fpc_apollo'],10)
  checked(['modprobe','fpc_apollo','allow_hw=1'],12);s=trusted('/dev/fpc1020',0o600)
  if not stat.S_ISCHR(s.st_mode):raise RuntimeError('wrong_sensor_node')
  if stop:raise RuntimeError('cancelled')
  phase='biometric_operation';mode='--verify-uid1000' if sys.argv[1]=='--verify' else '--enroll-first-right-index'
  worker=subprocess.Popen(['timeout','--kill-after=3','180',str(PREFIX/'apollo-biometric'),mode],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True,bufsize=0,env={'PATH':'/usr/bin:/bin','LC_ALL':'C'})
  sel=selectors.DefaultSelector();sel.register(worker.stdout,selectors.EVENT_READ);deadline=time.monotonic()+190;cancel_at=None;final=None
  while time.monotonic()<deadline:
   if stop and cancel_at is None:
    os.killpg(worker.pid,signal.SIGTERM);cancel_at=time.monotonic()
   if cancel_at is not None and worker.poll() is None and time.monotonic()-cancel_at>3:os.killpg(worker.pid,signal.SIGKILL)
   for key,_ in sel.select(.1):
    line=key.fileobj.readline(2048)
    if not line:sel.unregister(key.fileobj);continue
    if len(line)>1024 or not line.endswith(b'\n'):raise RuntimeError('invalid_backend_event')
    row=json.loads(line)
    if 'event' in row:
     if row['event'] not in ('place-finger','remove-finger','enrollment-progress','retry-sample','retry-capture','enrollment-completed','verify-match','verify-no-match'):raise RuntimeError('invalid_event')
     # Verification success is emitted only after cleanup, never at this point.
     if row['event'] not in ('verify-match','verify-no-match','enrollment-completed'):print(json.dumps(row),flush=True)
    else:final=row
   if worker.poll() is not None and not sel.get_map():break
  if stop:raise RuntimeError('cancelled')
  if worker.poll() not in (0,1) or final is None or final.get('biometric_bytes_exported') or final.get('lock_or_PAM_changed'):raise RuntimeError('backend_failed')
  report=final
 except Exception:
  report={'ok':False,'matched':False,'finger_enrolled':False,'phase':phase,'cancelled':bool(stop)}
 finally:
  if worker is not None and worker.poll() is None:
   os.killpg(worker.pid,signal.SIGKILL);worker.wait(timeout=5)
  if started:
   try:clean=cleanup()
   except Exception:clean=False
   report['hardware_cleanup_succeeded']=clean
   if not clean:report.update(ok=False,matched=False)
  if lock is not None:os.close(lock)
  report['biometric_bytes_exported']=False
  print(json.dumps(report),flush=True)
 return 0 if report['ok'] else 1
if __name__=='__main__':raise SystemExit(main())
