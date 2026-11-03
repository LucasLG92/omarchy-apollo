#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Keep the existing mobile update sheet's auth, layout and progress protocol."""
from pathlib import Path
import json
import os
import stat

CAPABILITY=Path('/run/apollo-versioned-usr-v1')
REGISTRY=Path('/var/lib/apollo-updates/release.json')

def active():
    try:
        s=CAPABILITY.lstat()
        return stat.S_ISREG(s.st_mode) and s.st_uid==0 and not s.st_mode&0o022
    except OSError:return False

def available():
    try:
        s=REGISTRY.lstat()
        if not stat.S_ISREG(s.st_mode) or s.st_uid!=0 or s.st_mode&0o022 or s.st_size>1024**2:return []
        data=json.loads(REGISTRY.read_text())
        if data.get('schema')!=1 or not isinstance(data.get('updates'),list):return []
        return [s for s in data['updates'] if isinstance(s,str) and len(s)<512]
    except (OSError,ValueError):return []

def check(adapter,offline=False):
    bat=adapter.battery();blockers=[]
    b=adapter.battery_blocker(bat)
    if b:blockers.append(b)
    free=adapter.free_bytes()
    if 0<=free<adapter.MIN_FREE:blockers.append('Se necesitan al menos 10 GiB libres para preparar una versión.')
    updates=available()
    if not updates:blockers.append('No hay una publicación Apollo firmada registrada para este dispositivo.')
    running=adapter.running()
    if running:blockers.append('Ya hay una actualización en marcha.')
    return {'battery':bat,'min_battery':adapter.MIN_BATTERY,'battery_ok':not adapter.battery_blocker(bat),
        'repositories_ok':True,'repositories':'','free_gib':round(free/1024**3,1) if free>=0 else None,
        'omarchy':adapter.installed_version('omarchy'),'omarchy_update':'','updates':updates,
        'update_count':len(updates),'boot_packages':[],'running':running,'credential':adapter.credential(),
        'patches':adapter.patch_summary(),'release_notes':adapter.RELEASE_NOTES,'checked_offline':offline,
        'blockers':blockers,'ok':not blockers,'apollo_transactional':True}
