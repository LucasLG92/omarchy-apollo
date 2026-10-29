#!/usr/bin/python3
"""Check Landlock with fresh synthetic files in a child process only."""
from pathlib import Path
import ctypes,errno,json,os,platform,re,tempfile

assert platform.machine()=='aarch64'
header=Path('/usr/include/asm-generic/unistd.h').read_text()
for name,number in (('landlock_create_ruleset',444),('landlock_add_rule',445),('landlock_restrict_self',446)):
 assert re.search(r'^#define\s+__NR_'+name+r'\s+'+str(number)+r'\b',header,re.M)
libc=ctypes.CDLL(None,use_errno=True); libc.syscall.restype=ctypes.c_long
abi=libc.syscall(444,ctypes.c_void_p(),ctypes.c_size_t(0),ctypes.c_uint(1))
assert abi>=1
class Ruleset(ctypes.Structure):
 _fields_=[('handled_access_fs',ctypes.c_uint64)]
class PathRule(ctypes.Structure):
 _pack_=1
 _fields_=[('allowed_access',ctypes.c_uint64),('parent_fd',ctypes.c_int32)]
with tempfile.TemporaryDirectory(prefix='apollo-landlock-') as temporary:
 root=Path(temporary); allowed=root/'allowed'; denied=root/'denied'
 allowed.mkdir(); denied.mkdir()
 (allowed/'sample').write_bytes(b'apollo synthetic allowed\n')
 (denied/'sample').write_bytes(b'apollo synthetic denied\n')
 readfd,writefd=os.pipe(); pid=os.fork()
 if pid==0:
  os.close(readfd)
  try:
   attribute=Ruleset(1<<2)
   ruleset=libc.syscall(444,ctypes.byref(attribute),ctypes.c_size_t(ctypes.sizeof(attribute)),ctypes.c_uint(0))
   assert ruleset>=0
   pathfd=os.open(allowed,os.O_PATH|os.O_DIRECTORY|os.O_CLOEXEC)
   rule=PathRule(1<<2,pathfd)
   assert libc.syscall(445,ctypes.c_int(ruleset),ctypes.c_uint(1),ctypes.byref(rule),ctypes.c_uint(0))==0
   assert libc.prctl(38,1,0,0,0)==0
   assert libc.syscall(446,ctypes.c_int(ruleset),ctypes.c_uint(0))==0
   descriptor=os.open(allowed/'sample',os.O_RDONLY)
   content=os.read(descriptor,128); os.close(descriptor)
   assert content==b'apollo synthetic allowed\n'
   blocked=False
   try:
    descriptor=os.open(denied/'sample',os.O_RDONLY); os.close(descriptor)
   except PermissionError as error: blocked=error.errno==errno.EACCES
   assert blocked
   result={'passed':True,'landlock_abi':abi,'allowed_read_passed':True,'disallowed_read_denied':True,
           'restriction_applied_to_child_only':True,'user_files_read':False,'global_policy_changed':False}
   os.write(writefd,json.dumps(result).encode()); os.close(writefd); os._exit(0)
  except BaseException:
   os.write(writefd,b'{"passed":false}'); os.close(writefd); os._exit(1)
 os.close(writefd); raw=os.read(readfd,4096); os.close(readfd)
 _,status=os.waitpid(pid,0)
 result=json.loads(raw)
 assert os.waitstatus_to_exitcode(status)==0 and result['passed']
print(json.dumps(result,indent=2))
