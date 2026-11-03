#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Prevent native app changes being lost after a generation is queued."""
from pathlib import Path
import os,stat,subprocess,sys
STORE=Path('/var/lib/apollo/system-versions')
SELECTOR='/usr/lib/apollo/apollo-boot-selector'

def pending(lines):
    if len(lines)!=8:raise RuntimeError('Invalid selector state')
    return lines[2]!='-' or lines[4]!='-'

def main():
    state=STORE/'state-v1'
    if not state.exists():return 0
    s=state.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_uid!=0 or s.st_mode&0o022:return 1
    result=subprocess.run([SELECTOR,str(STORE),'status'],capture_output=True,text=True,timeout=10)
    if result.returncode or pending(result.stdout.strip().splitlines()):
        print('Apollo: reinicia para terminar la actualización preparada antes de cambiar paquetes nativos. Las aplicaciones Flatpak se gestionan por separado.',file=sys.stderr)
        return 1
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired):
        print('Apollo: no se pudo verificar la actualización pendiente.',file=sys.stderr);sys.exit(1)
