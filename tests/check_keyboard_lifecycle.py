#!/usr/bin/python3
"""Exercise the real keyboard against a disposable nested compositor."""
from pathlib import Path
import argparse
import json
import os
import shutil
import signal
import stat
import subprocess
import tempfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--keyboard',type=Path,default=Path('/usr/bin/wvkbd-mobintl'))
    arguments=parser.parse_args()
    assert os.getuid()>=1000, 'Run as the desktop user without sudo'
    keyboard=arguments.keyboard.resolve(strict=True)
    assert keyboard.is_file() and os.access(keyboard,os.X_OK)
    for executable in ('kwin_wayland','Hyprland','hyprctl','cc','pkg-config','wayland-scanner','dbus-run-session'):
        assert shutil.which(executable), 'Missing optional test tool: '+executable
    runtime=Path(os.environ['XDG_RUNTIME_DIR'])
    assert runtime.is_dir() and runtime.stat().st_uid==os.getuid()
    owner=Path(__file__).resolve().parent/'support/keyboard-lifecycle-owner.py'
    os.umask(0o077)
    with tempfile.TemporaryDirectory(prefix='keyboard-check-',dir=runtime) as temporary:
        report=Path(temporary)/'result.json'
        process=subprocess.Popen(['dbus-run-session','--','python','-I',str(owner),str(report),str(keyboard)],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
        try:
            output,error=process.communicate(timeout=210)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGTERM)
            try:process.communicate(timeout=25)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.communicate()
            raise TimeoutError('Keyboard checks exceeded their deadline')
        assert process.returncode==0,error[:1000]+'\n...\n'+error[-16000:]
        assert report.is_file(),'Missing private result file: '+output[-1000:]
        descriptor=os.open(report,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
        try:
            info=os.fstat(descriptor)
            assert stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and info.st_size<65536
            record=json.loads(os.read(descriptor,65536))
        finally:os.close(descriptor)
    assert not record['physical_display_used'] and not record['owner_credentials_used']
    print(json.dumps(record,indent=2))


if __name__=='__main__': main()
