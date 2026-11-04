#!/usr/bin/python3 -I
"""Root-only libfprint bridge. All decisions come from the native TEE backend.

Speaks the existing Omarchy line protocol; contains no Android HAL or container.
The socket and template store are root-only. fprintd applies the caller policy.
"""
from pathlib import Path
import json,os,selectors,signal,socket,stat,struct,subprocess,time
PREFIX=Path('/usr/lib/apollo/fingerprint')
def decision(status,result,cancelled,identity_matches,identity):
 if cancelled:return 'ERROR 5'
 if status!=0 or not isinstance(result,dict) or result.get('ok') is not True or result.get('hardware_cleanup_succeeded') is not True or result.get('biometric_bytes_exported') is not False:return 'ERROR 2'
 if not identity_matches:return 'ERROR 1'
 if result.get('matched') is True:return 'MATCH '+str(identity)
 if result.get('matched') is False:return 'NOMATCH'
 return 'ERROR 2'
def metadata():
 folder=Path('/var/lib/apollo/fingerprint-templates-v1/u1000')
 for p in (folder.parent,folder):
  s=p.lstat()
  if not stat.S_ISDIR(s.st_mode) or s.st_uid!=0 or stat.S_IMODE(s.st_mode)!=0o700:raise ValueError('untrusted_store')
 fd=os.open(folder/'enrolled-v1',os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  s=os.fstat(fd)
  if not stat.S_ISREG(s.st_mode) or s.st_uid!=0 or stat.S_IMODE(s.st_mode)!=0o600 or s.st_nlink!=1 or s.st_size<76 or s.st_size>4*1024*1024+24:raise ValueError('untrusted_record')
  header=os.read(fd,24)
  magic,uid,identity,finger,size=struct.unpack('<8sIIII',header)
  if magic!=b'APFPC001' or uid!=1000 or not identity or finger!=7 or size!=s.st_size-24:raise ValueError('invalid_record')
  return struct.unpack('<i',struct.pack('<I',identity))[0]
 finally:os.close(fd)
class Bridge:
 def __init__(self,listener):
  self.listener=listener;self.selector=selectors.DefaultSelector();self.selector.register(listener,selectors.EVENT_READ,'listen')
  self.client=None;self.input=b'';self.worker=None;self.final=None;self.cancelled=False;self.client_identity=None;self.idle_at=None;self.operation=None
 def send(self,line):
  if self.client is not None:
   try:self.client.sendall((line+'\n').encode())
   except OSError:self.disconnect()
 def cancel(self):
  self.cancelled=True
  if self.worker is not None and self.worker.poll() is None:
   try:os.kill(self.worker.pid,signal.SIGTERM)
   except ProcessLookupError:pass
 def disconnect(self):
  self.cancel()
  if self.client is not None:
   try:self.selector.unregister(self.client)
   except KeyError:pass
   self.client.close();self.client=None
  self.input=b'';self.idle_at=time.monotonic()
 def command(self,line):
  if line=='CANCEL':
   if self.worker is None:self.send('ERROR 5')
   else:self.cancel()
   return
  if self.worker is not None:self.send('ERROR 2');return
  if line=='LIST':
   try:self.send('LIST '+str(metadata()))
   except FileNotFoundError:self.send('LIST')
   except (ValueError,OSError):self.send('ERROR 1')
   return
  if line=='ENROLL':
   try:metadata()
   except FileNotFoundError:pass
   except (ValueError,OSError):self.send('ERROR 1');return
   else:self.send('ERROR 4');return
   self.operation='enroll';self.client_identity=None
  elif line=='AUTH':
   try:self.client_identity=metadata()
   except (ValueError,OSError):self.send('ERROR 1');return
   self.operation='verify'
  else:
   if line.startswith('DELETE '):self.send('ERROR 6')
   else:self.send('ERROR 2')
   return
  self.cancelled=False;self.final=None
  self.worker=subprocess.Popen([str(PREFIX/'native-session'),'--enroll-first' if self.operation=='enroll' else '--verify'],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,bufsize=0,env={'PATH':'/usr/bin:/bin','LC_ALL':'C'})
  self.selector.register(self.worker.stdout,selectors.EVENT_READ,'worker')
 def worker_event(self):
  line=self.worker.stdout.readline(2048)
  if not line:
   self.selector.unregister(self.worker.stdout);self.worker.stdout.close()
   status=self.worker.wait(timeout=5);result=self.final;self.worker=None
   if self.operation=='enroll':
    valid=status==0 and isinstance(result,dict) and result.get('ok') is True and result.get('finger_enrolled') is True and result.get('hardware_cleanup_succeeded') is True and result.get('biometric_bytes_exported') is False
    if self.cancelled:self.send('ERROR 5')
    elif valid:
     try:self.send('ENROLLED '+str(metadata()))
     except (ValueError,OSError):self.send('ERROR 1')
    else:self.send('ERROR 2')
   else:
    try:unchanged=metadata()==self.client_identity
    except (ValueError,OSError):unchanged=False
    self.send(decision(status,result,self.cancelled,unchanged,self.client_identity))
   return
  try:
   if len(line)>1024 or not line.endswith(b'\n'):raise ValueError('invalid_event')
   row=json.loads(line)
   if 'event' not in row:self.final=row;return
   if row['event']=='place-finger':self.send('FINGER NEEDED')
   elif row['event']=='remove-finger':self.send('FINGER UP')
   elif row['event']=='enrollment-progress':
    remaining=int(row['value'])
    if not 0<=remaining<=100:raise ValueError('invalid_remaining')
    self.send('PROGRESS 0 '+str(remaining))
   elif row['event'] in ('retry-sample','retry-capture'):self.send('ACQUIRED 2 0')
  except (ValueError,TypeError):self.cancel()
 def loop(self):
  while True:
   if self.client is None and self.worker is None and self.idle_at is not None and time.monotonic()-self.idle_at>20:return
   for key,_ in self.selector.select(1 if self.idle_at is not None else None):
    if key.data=='listen':
     client,_=self.listener.accept();pid,uid,gid=struct.unpack('3i',client.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))
     if uid!=0 or self.client is not None or self.worker is not None:client.close();continue
     client.settimeout(2);self.client=client;self.idle_at=None;self.input=b'';self.selector.register(client,selectors.EVENT_READ,'client');self.send('READY 0 0 0')
    elif key.data=='client':
     try:data=self.client.recv(128)
     except OSError:data=b''
     if not data:self.disconnect();continue
     self.input+=data
     if len(self.input)>256:self.disconnect();continue
     while b'\n' in self.input:
      line,self.input=self.input.split(b'\n',1)
      try:self.command(line.decode('ascii'))
      except (UnicodeError,ValueError,OSError):self.send('ERROR 2')
    elif key.data=='worker':self.worker_event()
 def close(self):
  self.disconnect()
  if self.worker is not None:
   try:self.worker.wait(timeout=12)
   except subprocess.TimeoutExpired:self.worker.kill();self.worker.wait(timeout=5)
def main():
 if os.geteuid()!=0 or os.environ.get('LISTEN_PID')!=str(os.getpid()) or os.environ.get('LISTEN_FDS')!='1':return 2
 listener=socket.socket(fileno=3)
 if listener.family!=socket.AF_UNIX or listener.getsockname()!='/run/apollo-fingerprint/bridge.sock':return 3
 bridge=Bridge(listener)
 def stop(*_):raise KeyboardInterrupt()
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 try:bridge.loop()
 except KeyboardInterrupt:pass
 finally:bridge.close();listener.close()
 return 0
if __name__=='__main__':raise SystemExit(main())
