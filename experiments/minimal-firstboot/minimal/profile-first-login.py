#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Apply only the chosen non-secret preferences, as the logged-in user."""
from pathlib import Path
import json,os,subprocess,sys
sys.path.insert(0,'/usr/lib/apollo')
from firstboot_profile import validate_profile
home=Path.home();source=home/'.config/apollo/first-run.json'
if not source.is_file():sys.exit(0)
profile=validate_profile(json.loads(source.read_text()))
state=home/'.local/state/apollo';state.mkdir(mode=0o700,parents=True,exist_ok=True)
marker=state/'first-run-apps.json'
def run(args,timeout=20):return subprocess.run(args,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=timeout).returncode
layout=profile['keyboard']
if run(['gsettings','set','org.gnome.desktop.input-sources','sources',"[('xkb', '"+layout+"')]"]):sys.exit(1)
chosen=profile['apps']
if marker.is_file() and json.loads(marker.read_text()).get('apps')==chosen:sys.exit(0)
# Flathub signature verification remains enabled; never execute catalog strings.
if chosen:
 if run(['flatpak','--user','remote-add','--if-not-exists','flathub','https://flathub.org/repo/flathub.flatpakrepo'],timeout=60):sys.exit(1)
 if run(['flatpak','--user','install','--noninteractive','-y','--arch=aarch64','flathub',*chosen],timeout=1800):sys.exit(1)
temp=marker.with_suffix('.new');temp.write_text(json.dumps({'schema':1,'apps':chosen})+'\n');temp.chmod(0o600);os.replace(temp,marker)
