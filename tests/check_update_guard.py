#!/usr/bin/python3
"""Exercise the real ALPM guard in disposable roots, without touching the live DB."""
from pathlib import Path
import io,json,os,re,shutil,subprocess,tarfile,tempfile

SOURCE=Path(__file__).resolve().parents[1]
assert os.geteuid()==0,'Run on the Apollo development device as root'
assert shutil.which('pacman') and shutil.which('ldd')
checks=[]

def check(name,condition):
    assert condition,name
    checks.append(name)

with tempfile.TemporaryDirectory(prefix='omarchy-apollo-alpm-test-',dir='/var/tmp') as temporary:
    base=Path(temporary)
    archive_dir=base/'archives';archive_dir.mkdir()
    def package(name,version,filename='usr/share/apollo-fixture/marker'):
        target=archive_dir/(name+'-'+version+'.pkg.tar')
        entries={'.PKGINFO':f'pkgname = {name}\npkgver = {version}\npkgdesc = Isolated Apollo guard fixture\nurl = https://example.invalid\nbuilddate = 1\npackager = Apollo test fixture\nsize = 32\narch = aarch64\n',filename:version+'\n'}
        with tarfile.open(target,'w') as archive:
            for path,contents in entries.items():
                data=contents.encode();info=tarfile.TarInfo(path)
                info.size=len(data);info.mode=0o644;info.mtime=1
                archive.addfile(info,io.BytesIO(data))
        return target

    config=base/'pacman.conf'
    config.write_text('[options]\nArchitecture = aarch64\nSigLevel = Never\nLocalFileSigLevel = Never\n')
    # Signature relaxation applies only to the generated test packages in this
    # isolated configuration. The live config and package database are untouched.
    def fixture(name):
        root=base/name;root.mkdir()
        for path in ('var/lib/pacman','var/cache/pacman/pkg','usr/share/libalpm/hooks','bin'):
            (root/path).mkdir(parents=True,exist_ok=True)
        libraries=subprocess.check_output(['ldd','/bin/bash'],text=True)
        for filename in {'/bin/bash',*re.findall(r'(/[A-Za-z0-9_./+-]+)',libraries)}:
            source=Path(filename)
            if source.is_file():
                destination=root/filename.lstrip('/')
                destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(source,destination)
        return root

    def protect(root):
        directory=root/'usr/lib/omarchy/apollo';directory.mkdir(parents=True,exist_ok=True)
        helper=directory/'guard-device-packages'
        shutil.copyfile(SOURCE/'platform/guard-device-packages',helper);helper.chmod(0o755)
        shutil.copyfile(SOURCE/'platform/00-omarchy-apollo-device-stack.hook',root/'usr/share/libalpm/hooks/00-omarchy-apollo-device-stack.hook')

    def pacman(root,*arguments):
        assert root.is_dir() and root.parent==base and root!=Path('/')
        command=['pacman','--root',str(root),'--config',str(config),'--dbpath',str(root/'var/lib/pacman'),'--cachedir',str(root/'var/cache/pacman/pkg'),'--logfile',str(root/'pacman.log'),'--noconfirm',*map(str,arguments)]
        env={'PATH':'/usr/bin','LANG':'C','OMARCHY_ALLOW_DIRECT_PACMAN':'1','OMARCHY_UPDATE_PACMAN':'1'}
        return subprocess.run(command,capture_output=True,text=True,env=env,timeout=25)

    safe=fixture('ordinary-app');protect(safe)
    first=package('apollo-app-fixture','1-1');second=package('apollo-app-fixture','2-1')
    check('ordinary application install succeeds',pacman(safe,'-U',first).returncode==0)
    check('ordinary application upgrade succeeds',pacman(safe,'-U',second).returncode==0 and (safe/'usr/share/apollo-fixture/marker').read_text()=='2-1\n')
    check('ordinary application removal succeeds',pacman(safe,'-R','apollo-app-fixture').returncode==0)

    for label,name,filename in (
        ('kernel package','linux-apollo-fixture','usr/share/apollo-fixture/marker'),
        ('camera package','libcamera-fixture','usr/share/apollo-fixture/marker'),
        ('PC settings package','omarchy-settings-fixture','usr/share/apollo-fixture/marker'),
        ('boot image path','apollo-boot-fixture','boot/Image'),
        ('firmware path','apollo-firmware-fixture','usr/lib/firmware/apollo-fixture/test.bin'),
        ('camera library path','apollo-camera-fixture','usr/lib/libcamera-fixture.so'),
    ):
        root=fixture(name);protect(root)
        result=pacman(root,'-U',package(name,'1-1',filename))
        rejected=result.returncode!=0 and 'tested boot, camera or firmware stack' in (result.stdout+result.stderr) and not (root/filename).exists()
        if not rejected:
            raise AssertionError(label+': '+result.stdout+'\n'+result.stderr)
        check(label+' is rejected before extraction',rejected)
        check(label+' never enters the installed database',pacman(root,'-Q',name).returncode!=0)

    root=fixture('existing-kernel')
    old=package('linux-apollo-fixture','1-1');new=package('linux-apollo-fixture','2-1')
    check('isolated existing-kernel fixture is seeded',pacman(root,'-U',old).returncode==0)
    protect(root)
    check('kernel upgrade preserves existing files and version',pacman(root,'-U',new).returncode!=0 and (root/'usr/share/apollo-fixture/marker').read_text()=='1-1\n' and '1-1' in pacman(root,'-Q','linux-apollo-fixture').stdout)
    check('kernel removal preserves existing files and version',pacman(root,'-R','linux-apollo-fixture').returncode!=0 and (root/'usr/share/apollo-fixture/marker').read_text()=='1-1\n' and '1-1' in pacman(root,'-Q','linux-apollo-fixture').stdout)

    injected=base/'startup-injection'
    startup=base/'bash-env';startup.write_text('printf injected > "'+str(injected)+'"\n')
    for name in ('guard-device-packages','guard-pc-updater'):
        helper=base/name;shutil.copyfile(SOURCE/'platform'/name,helper);helper.chmod(0o755)
        result=subprocess.run([str(helper)],env={'PATH':'/usr/bin','BASH_ENV':str(startup)},capture_output=True,text=True,timeout=10)
        check(name+' ignores Bash startup injection',result.returncode==1 and not injected.exists())
        result=subprocess.run(['/bin/bash',str(helper),'-p'],env={'PATH':'/usr/bin'},capture_output=True,text=True,timeout=10)
        check(name+' rejects an ordinary Bash launch with decoy -p',result.returncode==126)

    root=fixture('reload-boundary')
    helper=root/'reload-live-compositor'
    shutil.copyfile(SOURCE/'platform/reload-live-compositor',helper);helper.chmod(0o755)
    (root/'dev').mkdir();(root/'dev/null').touch()
    (root/'bash-env').write_text('printf injected > /unexpected-startup\n')
    result=subprocess.run(['chroot',str(root),'/reload-live-compositor'],env={'PATH':'/usr/bin','BASH_ENV':'/bash-env'},capture_output=True,text=True,timeout=10)
    check('reload boundary ignores Bash startup injection in an isolated root',result.returncode==0 and not (root/'unexpected-startup').exists())
    result=subprocess.run(['chroot',str(root),'/bin/bash','/reload-live-compositor','-p'],env={'PATH':'/usr/bin'},capture_output=True,text=True,timeout=10)
    check('reload boundary rejects an ordinary Bash launch with decoy -p',result.returncode==126)

print(json.dumps({'passed':len(checks),'checks':checks,'live_package_database_modified':False,'temporary_fixture_roots_removed':True},indent=2))
