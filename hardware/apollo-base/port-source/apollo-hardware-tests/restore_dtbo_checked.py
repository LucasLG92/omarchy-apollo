"""Restore only the verified original DTBO after a stable fastboot handshake."""
from pathlib import Path
import datetime,hashlib,json,re,subprocess,sys,time
base=Path(__file__).resolve().parents[2]; out=base/'outputs/arch-apollo'
tool=base/'work/downloads/android-tools-current/platform-tools/fastboot.exe'
file=out/'recovery-backup/dtbo.img'
manifest=json.loads((file.parent/'manifest.json').read_text())
expected=manifest['partitions']['dtbo']
assert file.stat().st_size==expected['size']
assert hashlib.sha256(file.read_bytes()).hexdigest()==expected['sha256']
tag=sys.argv[1]; assert re.fullmatch(r'hardware-\d{8}T\d{6}Z',tag)
assert sys.argv[2:] in ([],['--preflight'])
preflight=sys.argv[2:]==['--preflight']
report=out/'experimental'/tag; report.mkdir(exist_ok=True)
proof_file=report/('checked-live-preflight.json' if preflight else 'checked-dtbo-restoration.json')
def command(*args,timeout=8):
    p=subprocess.run([str(tool),'-s',__import__('os').environ['APOLLO_SERIAL'],*args],capture_output=True,text=True,timeout=timeout)
    return p.returncode,p.stdout+p.stderr
def value(name):
    try: code,text=command('getvar',name)
    except subprocess.TimeoutExpired: return None
    match=re.search(re.escape(name)+r':\s*(\S+)',text)
    return match[1] if code==0 and match else None
proof={'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'target':__import__('os').environ['APOLLO_SERIAL'],'dtbo_sha256':expected['sha256'],'observations':[],
    'bootloader_restart_attempts':[],
    'operation':'live_boot_preflight' if preflight else 'restore_original_dtbo'}
stable=0; previous=None
deadline=time.monotonic()+80
for attempt in range(30):
    if time.monotonic()>deadline: break
    item={'product':value('product'),'partition_size':value('partition-size:dtbo'),
          'maximum_download_size':value('max-download-size')}
    proof['observations'].append(item)
    try:
        good=item['product']=='apollo' and int(item['partition_size'],0)==expected['size'] and int(item['maximum_download_size'],0)>=file.stat().st_size
    except (ValueError,TypeError): good=False
    stable=stable+1 if good and item==previous else (1 if good else 0)
    previous=item
    if stable>=2: break
    if attempt in (3,10) and not good:
        # Product can be exposed while UFS/download variables are still invalid.
        # Do not use a product-only guard before restoring a real partition.
        try:
            code,text=command('reboot','bootloader')
            proof['bootloader_restart_attempts'].append({'exit':code,'output':text})
        except subprocess.TimeoutExpired:
            proof['bootloader_restart_attempts'].append({'timeout':True})
        stable=0; previous=None
    time.sleep(1)
if stable<2:
    proof_file.write_text(json.dumps(proof,indent=2)+'\n')
    raise SystemExit('No stable product, partition size and download limit; no flash attempted')
if preflight:
    proof['passed']=True
    proof['partition_write_attempted']=False
    proof_file.write_text(json.dumps(proof,indent=2)+'\n')
    print('Live preflight passed two matching product/size/download-limit checks; no partition written')
    raise SystemExit(0)
code,text=command('flash','dtbo',str(file),timeout=60)
proof['flash_exit']=code; proof['flash_output']=text
proof_file.write_text(json.dumps(proof,indent=2)+'\n')
assert code==0,text
code,text=command('reboot')
assert code==0,text
print('Original DTBO restored after two matching product/size/download-limit checks; Android reboot requested')
