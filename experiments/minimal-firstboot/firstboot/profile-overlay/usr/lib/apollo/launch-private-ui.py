#!/usr/bin/python3
# SPDX-License-Identifier: MIT
"""Start one fixed trusted local GUI after the owner Wayland session exists."""
from pathlib import Path
import os,re,resource,stat,subprocess,sys,time,xml.etree.ElementTree as ET

def wait_for_owner_display(kind):
    """A SIM form may wait at the greeter until its owner actually signs in."""
    attempts=0
    while True:
        sockets=[p for p in Path('/run/user/1000').glob('wayland-*') if p.is_socket() and p.stat().st_uid==1000]
        if len(sockets)==1:return sockets[0]
        attempts+=1
        if kind=='owner' and attempts>=180:
            raise RuntimeError('The local owner display is not available')
        time.sleep(1)

kind=sys.argv[1] if len(sys.argv)==2 else ''
assert kind == 'sim' and os.geteuid()==0
assert Path('/etc/apollo/native-root-v1').is_file()
resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.umask(0o077)
if kind=='sim':
    while not Path('/var/lib/apollo/owner-ready').exists():time.sleep(1)
    while subprocess.run(['systemctl','is-active','--quiet','apollo-owner-setup.service']).returncode==0:time.sleep(1)
sys.path.insert(0, '/usr/lib/apollo')
from owner_account import resolve_owner
owner=resolve_owner()
assert owner['uid']==1000
display=wait_for_owner_display(kind)
if kind=='sim':
    # Check the current SIM only after login, not a stale lock from the greeter.
    from gi.repository import Gio,GLib
    name='org.freedesktop.ModemManager1'
    for _ in range(90):
        try:
            bus=Gio.bus_get_sync(Gio.BusType.SYSTEM,None)
            tree=bus.call_sync(name,'/org/freedesktop/ModemManager1/Modem','org.freedesktop.DBus.Introspectable',
                'Introspect',None,GLib.VariantType.new('(s)'),Gio.DBusCallFlags.NONE,1500,None).unpack()[0]
            nodes=[n.get('name','') for n in ET.fromstring(tree).findall('node')]
            nodes=[n for n in nodes if re.fullmatch('[0-9]+',n)]
            if nodes:
                path='/org/freedesktop/ModemManager1/Modem/'+nodes[0]
                value=bus.call_sync(name,path,'org.freedesktop.DBus.Properties','Get',
                    GLib.Variant('(ss)',(name+'.Modem','UnlockRequired')),GLib.VariantType.new('(v)'),
                    Gio.DBusCallFlags.NONE,1500,None).unpack()[0]
                if isinstance(value,GLib.Variant):value=value.unpack()
                if value in (1,3,5):sys.exit(0)
                if value in (2,4):break
        except GLib.Error:pass
        time.sleep(1)
    else:sys.exit(0)
runtime=Path('/run/apollo-'+kind+'-ui');runtime.mkdir(mode=0o700,exist_ok=True)
info=runtime.lstat();assert stat.S_ISDIR(info.st_mode) and info.st_uid==0 and not info.st_mode&0o077
environment={'PATH':'/usr/bin:/bin','HOME':str(runtime),'LANG':'es_ES.UTF-8',
 'XDG_RUNTIME_DIR':str(runtime),'WAYLAND_DISPLAY':str(display),'GDK_BACKEND':'wayland',
 'DBUS_SESSION_BUS_ADDRESS':'unix:path='+str(runtime/'no-session-bus'),'GTK_USE_PORTAL':'0'}
os.execve('/usr/bin/apollo-sim-unlock',['apollo-sim-unlock'],environment)
