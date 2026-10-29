#!/usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-only
"""Runs ON the phone: checked boot-only update with local recovery and readback."""
from pathlib import Path
import fcntl,hashlib,json,os,stat,struct,subprocess,sys,time

assert __debug__ and os.geteuid()==0
root=Path('/run/apollo-storage'); directory=root/'maintenance/kernel22'
manifest=json.loads((directory/'upgrade-manifest.json').read_text())
old=manifest['known-good-kernel21-r3.img']; new=manifest['boot-persistent.img']
assert Path('/run/apollo-persistent').is_file()
assert (root/'.apollo-storage-v1').read_text()=='apollo-persistent-v1\n'
assert b'xiaomi,apollo' in Path('/proc/device-tree/compatible').read_bytes().split(b'\0')
assert subprocess.check_output(['findmnt','-n','-o','FSTYPE',str(root)],text=True).strip()=='ext4'
for name,item in manifest.items():
 p=directory/name
 assert p.stat().st_size==item['size']
 with p.open('rb') as stream: assert hashlib.file_digest(stream,'sha256').hexdigest()==item['sha256']
assert subprocess.check_output(['pacman','-Q','linux-apollo'],text=True).strip()=='linux-apollo 7.1.0-21'
nodes=[p.parent.name for p in Path('/sys/class/block').glob('*/uevent') if 'PARTNAME=boot' in p.read_text().splitlines()]
assert len(nodes)==1
name=nodes[0]; device=Path('/dev')/name; sysfs=Path('/sys/class/block')/name
assert stat.S_ISBLK(device.stat().st_mode)
assert int((sysfs/'size').read_text())*512==134217728
assert (sysfs/'ro').read_text().strip()=='0' and not list((sysfs/'holders').iterdir())
assert int(Path('/sys/class/power_supply/qcom-battery/capacity').read_text())>=30
assert new['size']<134217728
lock=Path('/run/apollo-kernel-upgrade.lock').open('w')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
fd=os.open(device,os.O_RDWR|os.O_EXCL)
try:
 assert os.fstat(fd).st_rdev==device.stat().st_rdev
 assert struct.unpack('Q',fcntl.ioctl(fd,0x80081272,b'\0'*8))[0]==134217728
 previous=os.pread(fd,old['size'],0)
 assert hashlib.sha256(previous).hexdigest()==old['sha256']
 time.sleep(0.2)
 assert hashlib.sha256(os.pread(fd,old['size'],0)).hexdigest()==old['sha256']
 if sys.argv[1]=='plan':
  print(json.dumps({'preflight_passed':True,'current_boot_verified':True,'target_boot_only':True,
                    'userdata_format_requested':False,'minimum_battery_satisfied':True}))
  raise SystemExit(0)
 assert sys.argv[1]=='apply'
 backup=directory/'kernel21-boot-readback.img'
 if backup.exists(): assert backup.read_bytes()==previous
 else:
  with backup.open('xb') as stream:
   os.chmod(backup,0o600); stream.write(previous); stream.flush(); os.fsync(stream.fileno())
 package=directory/'linux-apollo-7.1.0-22-aarch64.pkg.tar.xz'
 def write_all(data):
  offset=0
  while offset<len(data):
   amount=os.pwrite(fd,data[offset:offset+1024*1024],offset)
   assert amount>0
   offset+=amount
  os.fsync(fd)
 try:
  with (directory/'package-install.log').open('wb') as log:
   subprocess.run(['pacman','-U','--noconfirm',str(package)],stdout=log,stderr=subprocess.STDOUT,check=True)
   subprocess.run(['depmod','7.1.0'],stdout=log,stderr=subprocess.STDOUT,check=True)
   subprocess.run(['pacman','-Qkk','linux-apollo'],stdout=log,stderr=subprocess.STDOUT,check=True)
  payload=(directory/'boot-persistent.img').read_bytes()
  assert hashlib.sha256(payload).hexdigest()==new['sha256']
  write_all(payload)
  assert hashlib.sha256(os.pread(fd,new['size'],0)).hexdigest()==new['sha256']
 except Exception:
  if hashlib.sha256(os.pread(fd,old['size'],0)).hexdigest()!=old['sha256']:
   write_all(previous)
  assert hashlib.sha256(os.pread(fd,old['size'],0)).hexdigest()==old['sha256']
  with (directory/'rollback-package.log').open('wb') as log:
   subprocess.run(['pacman','-U','--noconfirm',str(directory/'linux-apollo-7.1.0-21-aarch64.pkg.tar.xz')],
                  stdout=log,stderr=subprocess.STDOUT,check=True)
  raise
 result={'package_installed':'linux-apollo 7.1.0-22','boot_sha256':new['sha256'],
         'boot_write_and_readback_verified':True,'original_boot_backup_verified':True,
         'userdata_formatted':False,'dtbo_modified':False,'reboot_not_yet_requested':True}
 (directory/'transaction-result.json').write_text(json.dumps(result,indent=2)+'\n')
 os.sync(); print(json.dumps(result))
finally:
 os.close(fd)
