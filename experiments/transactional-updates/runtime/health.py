#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Confirm a generation only after stable storage and a live mobile desktop.

Lock state, passwords, SIM presence and Internet connectivity are irrelevant.
A login screen can wait for the user without causing a reboot loop.
"""
from pathlib import Path
import json
import os
import pwd
import re
import stat
import subprocess
import sys
import time

sys.path.insert(0,'/usr/lib/apollo/transactional')
from apollo_updates import STORE, SELECTOR, ID, trusted, require, run

def same_directory(left,right):
    a,b=left.stat(),right.stat()
    return (a.st_dev,a.st_ino)==(b.st_dev,b.st_ino)

def desktop_state():
    candidates=[]
    for runtime in Path('/run/user').glob('[0-9]*'):
        if not runtime.name.isdigit() or int(runtime.name)<1000:continue
        for socket in (runtime/'hypr').glob('*/.socket.sock'):
            if socket.is_socket():candidates.append((int(runtime.name),socket.parent.name))
    for uid,instance in candidates:
        account=pwd.getpwuid(uid)
        env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','XDG_RUNTIME_DIR':f'/run/user/{uid}',
            'DBUS_SESSION_BUS_ADDRESS':f'unix:path=/run/user/{uid}/bus'}
        prefix=['/usr/bin/runuser','-u',account.pw_name,'--','/usr/bin/env',
            *[k+'='+v for k,v in env.items()],'/usr/bin/systemd-run','--user',
            '--quiet','--wait','--pipe','--collect']
        try:
            monitors=json.loads(run(prefix+['/usr/bin/hyprctl','-j','-i',instance,'monitors'],timeout=15))
            if not any(m.get('width',0)>0 and m.get('height',0)>0 and not m.get('disabled',False) for m in monitors):continue
            home=json.loads(run(prefix+['/usr/bin/omarchy-shell','shell','call','omamobile.home','renderState',''],timeout=15))
            if home.get('sceneErrors')==0 and isinstance(home.get('window'),dict):return 'desktop'
        except (OSError,RuntimeError,ValueError,subprocess.TimeoutExpired):continue
    if subprocess.run(['/usr/bin/systemctl','is-active','--quiet','display-manager.service'],capture_output=True).returncode==0:
        return 'waiting-for-desktop'
    return 'unhealthy'

def main():
    marker=Path('/run/apollo-deployment-v1');trusted(marker)
    lines=marker.read_text().splitlines()
    require(len(lines)==2 and ID.fullmatch(lines[0]) and re.fullmatch('[0-9a-f]{64}',lines[1]),'Prueba de arranque no válida.')
    release,token=lines
    generation=STORE/'deployments'/release;trusted(generation,True)
    require(all(same_directory(Path(live),generation/saved) for live,saved in
        (('/usr','usr'),('/opt','opt'),('/var/lib/pacman/local','pacman-local'))),'Montajes de versión incompletos.')
    if (generation/'adapter-state').exists():
        require(same_directory(Path('/var/lib/omamobile/omarchy-patches'),generation/'adapter-state'),'Metadatos del adaptador no coincidentes.')
    require(os.access('/etc',os.W_OK) and os.access('/var',os.W_OK),'Estado persistente no disponible.')
    passes=0;bad=0
    for attempt in range(100):
        state=desktop_state()
        if state=='desktop':passes+=1;bad=0
        elif state=='waiting-for-desktop':passes=0;bad=0
        else:passes=0;bad+=1
        if passes>=3:
            run([SELECTOR,STORE,'bless',release,token]);marker.unlink()
            print('Apollo: versión confirmada tras comprobar el escritorio y sus montajes.')
            return 0
        if bad>=10:
            print('Apollo: el escritorio no arranca; se solicitará volver por el cargador.',file=sys.stderr)
            return 1
        time.sleep(3)
    # Do not count a still-open login screen as a failed device.
    print('Apollo: confirmación pendiente; el siguiente arranque conservará el límite de intentos.')
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired):
        print('Apollo: no se pudo confirmar esta versión.',file=sys.stderr);sys.exit(1)
