"""Replay recovery invariants with a fake fastboot; never contacts the phone."""
from pathlib import Path
import contextlib,hashlib,io,json,runpy,shutil,subprocess,sys,tempfile
from unittest.mock import patch
base=Path(__file__).resolve().parents[2]
source=base/'work/restore_dtbo_checked.py'
payload=b'dummy-original-dtbo-for-offline-replay'
size=len(payload)
good={'product':'apollo','partition-size:dtbo':hex(size),'max-download-size':'0x10000000'}
cases=[
    ('ufs_not_ready_then_recovers',[{'product':'apollo','partition-size:dtbo':'0x0','max-download-size':'0x0'}]*4+[good,good],True),
    ('wrong_partition_size',[{**good,'partition-size:dtbo':'0x0'}],False),
    ('wrong_device',[{**good,'product':'different-device'}],False),
    ('download_limit_too_small',[{**good,'max-download-size':'0x1'}],False),
    ('one_good_snapshot_is_insufficient',[good,{**good,'partition-size:dtbo':'0x0'},good,good],True),
]
results=[]
for label,snapshots,should_pass,preflight in [
    (*case,False) for case in cases
]+[
    ('preflight_valid',[good,good],True,True),
    ('preflight_recovers_ufs',[{'product':'apollo','partition-size:dtbo':'0x0','max-download-size':'0x0'}]*4+[good,good],True,True),
    ('preflight_rejects_wrong_size',[{**good,'partition-size:dtbo':'0x0'}],False,True),
    ('preflight_rejects_wrong_device',[{**good,'product':'different-device'}],False,True),
    ('preflight_rejects_download_limit',[{**good,'max-download-size':'0x1'}],False,True),
]:
    with tempfile.TemporaryDirectory(prefix='restore-guard-test-',dir=base/'work') as directory:
        root=Path(directory).resolve()
        assert root.parent==(base/'work').resolve() and root.name.startswith('restore-guard-test-')
        (root/'work').mkdir()
        (root/'outputs/arch-apollo/recovery-backup').mkdir(parents=True)
        (root/'outputs/arch-apollo/experimental').mkdir()
        script=root/'work/restore_dtbo_checked.py'; shutil.copyfile(source,script)
        backup=root/'outputs/arch-apollo/recovery-backup'
        (backup/'dtbo.img').write_bytes(payload)
        (backup/'manifest.json').write_text(json.dumps({'partitions':{'dtbo':{
            'size':size,'sha256':hashlib.sha256(payload).hexdigest()}}}))
        seen=[]; index=0; consecutive=0; flashes=0; invalid_flash=False
        def fake_run(argv,**kwargs):
            global index,consecutive,flashes,invalid_flash
            assert argv[1:3]==['-s',__import__('os').environ['APOLLO_SERIAL']]
            args=argv[3:]; seen.append(args)
            if args[0]=='getvar':
                state=snapshots[min(index,len(snapshots)-1)]
                name=args[1]; value=state[name]
                if name=='max-download-size':
                    valid=state==good
                    consecutive=consecutive+1 if valid else 0
                    index+=1
                return subprocess.CompletedProcess(argv,0,'',name+': '+value+'\n')
            if args==['reboot','bootloader']:
                consecutive=0
            elif args[0]=='flash':
                assert args[1]=='dtbo' and Path(args[2]).read_bytes()==payload
                flashes+=1
                invalid_flash=consecutive<2
            elif args!=['reboot']:
                raise AssertionError('Unexpected action '+str(args))
            return subprocess.CompletedProcess(argv,0,'OKAY\n','')
        output=io.StringIO(); exit_message=None
        with patch.object(sys,'argv',[str(script),'hardware-20000101T000000Z']+(['--preflight'] if preflight else [])),patch('subprocess.run',side_effect=fake_run),patch('time.sleep',return_value=None),contextlib.redirect_stdout(output):
            try: runpy.run_path(str(script),run_name='__main__')
            except SystemExit as error: exit_message=str(error)
        assert flashes==int(should_pass and not preflight) and not invalid_flash,(label,seen)
        assert should_pass==(exit_message in (None,'0')),(label,exit_message)
        if preflight:
            assert ['reboot'] not in seen and not any(x[0] in ('flash','erase') for x in seen)
            proof_file=root/'outputs/arch-apollo/experimental/hardware-20000101T000000Z/checked-live-preflight.json'
            observed=json.loads(proof_file.read_text())
            assert observed.get('passed',False)==should_pass
            if should_pass: assert observed['partition_write_attempted'] is False
        if label=='ufs_not_ready_then_recovers': assert ['reboot','bootloader'] in seen
        results.append({'case':label,'passed':True,'preflight':preflight,'flash_attempts':flashes,
            'simulated_snapshots':index,'real_device_contacted':False})
proof={'scope':'Offline protocol replay with fake subprocess and dummy backup, not a new physical UFS recovery test',
       'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'cases':results,'passed':True}
(base/'work/restore-guard-offline-validation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print('Preflight and recovery invariants passed ten offline replays; no phone commands executed')
