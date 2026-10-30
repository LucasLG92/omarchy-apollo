"""Build input fixtures that refuse to operate on physical display outputs."""
from pathlib import Path
import hashlib
import json
import os
import shlex
import subprocess
import sys
import urllib.request

COMMIT='c11408942e2fb54d41dadb84cdf844331076ae11'
POINTER_SHA256='3ff6d540be0bc5228195bf072bde42117ea17945a5c2061add5d3cf97d6bb524'


def build(destination):
    assert os.getuid()>=1000, 'Build as the local desktop user'
    destination=Path(destination)
    destination.mkdir(mode=0o700)
    source=Path(__file__).resolve().parent/'support'
    url='https://raw.githubusercontent.com/swaywm/wlr-protocols/'+COMMIT+'/unstable/wlr-virtual-pointer-unstable-v1.xml'
    with urllib.request.urlopen(url,timeout=30) as response: xml=response.read(65536)
    assert hashlib.sha256(xml).hexdigest()==POINTER_SHA256
    pointer=destination/'wlr-virtual-pointer-unstable-v1.xml';pointer.write_bytes(xml)
    protocols=Path(subprocess.check_output(['pkg-config','--variable=pkgdatadir','wayland-protocols'],text=True).strip())
    lock=protocols/'staging/ext-session-lock/ext-session-lock-v1.xml'
    for name,protocol in (('wlr-virtual-pointer-unstable-v1',pointer),('ext-session-lock-v1',lock)):
        for mode,suffix in (('client-header','-client-protocol.h'),('private-code','-protocol.c')):
            subprocess.run(['wayland-scanner',mode,str(protocol),str(destination/(name+suffix))],check=True,capture_output=True)
    flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','wayland-client'],text=True))
    for name,protocol in (('nested-pointer-click','wlr-virtual-pointer-unstable-v1'),('nested-lock-fixture','ext-session-lock-v1')):
        subprocess.run(['cc','-O2','-Wall','-Wextra','-Wno-unused-parameter','-I'+str(destination),
            str(source/(name+'.c')),str(destination/(protocol+'-protocol.c')),'-o',str(destination/name),*flags],check=True,capture_output=True)
    return {'virtual_pointer_commit':COMMIT,'virtual_pointer_xml_sha256':POINTER_SHA256,
        'session_lock_xml_sha256':hashlib.sha256(lock.read_bytes()).hexdigest()}


if __name__=='__main__': print(json.dumps(build(sys.argv[1]),indent=2))
