#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Axis hints from APK launcher ActivityInfo; no UI/Intent/account/log access.

Listen to compositor focus events. Only a verified Waydroid client can trigger
the metadata query. Runtime app_id stays in its root-owned local hints file;
no app names, PID, command output or other values are logged.
"""
from pathlib import Path
import json,os,pwd,re,signal,socket,stat,subprocess,time

DIR=Path('/run/omamobile');DEST=DIR/'orientation-hints.json'
ROOTFS=Path('/var/lib/waydroid/rootfs')
ENV={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C'}
PKG=re.compile(r'[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+')
STOP=False

def orientation(value):
    if value in (1,7,9,12):return 'portrait'
    if value in (0,6,8,11):return 'landscape'
    return 'auto'  # Unspecified/user/sensor; behind/nosensor/locked have no inferred axis.

def parse_metadata(body):
    match=re.search(rb'\bscreenOrientation=(-?[0-9]{1,2})\b',body)
    if not match:return 'auto'
    return orientation(int(match.group(1)))

def run(argv,timeout=5):
    try:return subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=timeout,env=ENV)
    except (OSError,subprocess.TimeoutExpired):return None

def user_command(sig,args):
    owner=pwd.getpwuid(1000)
    return ['runuser','-u',owner.pw_name,'--','env','-i','PATH=/usr/bin:/bin','HOME='+owner.pw_dir,
        'XDG_RUNTIME_DIR=/run/user/1000','HYPRLAND_INSTANCE_SIGNATURE='+sig,*args]

def verify_destination():
    if not DIR.exists():DIR.mkdir(mode=0o755)
    info=DIR.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or info.st_gid!=0 or info.st_mode&0o022:raise ValueError('untrusted-runtime-directory')
    os.chmod(DIR,0o755)  # Explicit traversal/watch access despite the unit's private umask.
    if DEST.exists() or DEST.is_symlink():
        info=DEST.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_gid!=0 or stat.S_IMODE(info.st_mode)!=0o644:raise ValueError('untrusted-runtime-hints')

def write_rules(rules):
    verify_destination();body=(json.dumps({'version':1,'rules':rules},separators=(',',':'))+'\n').encode()
    if DEST.exists() and DEST.read_bytes()==body:return
    tmp=DIR/('orientation-hints.tmp-'+str(os.getpid()))
    fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
    try:
        with os.fdopen(fd,'wb') as stream:
            os.fchmod(stream.fileno(),0o644);stream.write(body);stream.flush();os.fsync(stream.fileno())
        os.replace(tmp,DEST)
    finally:
        if tmp.exists():tmp.unlink()

def package_for_client(client):
    app=client.get('class','');pid=client.get('pid')
    if not isinstance(app,str) or not isinstance(pid,int) or pid<=1:return None
    package=app.removeprefix('waydroid.')
    if not PKG.fullmatch(package):return None
    # Android client identity is verified using inode metadata, no device/files opened.
    try:
        if not os.path.samefile(Path('/proc')/str(pid)/'root/system/build.prop',ROOTFS/'system/build.prop'):return None
    except OSError:return None
    return app,package

def update(sig,cache):
    r=run(user_command(sig,['hyprctl','-j','activewindow']))
    if r is None or r.returncode:write_rules([]);return
    try:client=json.loads(r.stdout)
    except (ValueError,TypeError):write_rules([]);return
    pair=package_for_client(client)
    if pair is None:write_rules([]);return
    app,package=pair
    # A single active package suffices; never persist an inventory of installed APKs.
    if package not in cache:
        r=run(['waydroid','shell','--','/system/bin/cmd','package','resolve-activity','-a','android.intent.action.MAIN',
            '-c','android.intent.category.LAUNCHER','-p',package],8)
        value=parse_metadata(r.stdout) if r is not None and r.returncode==0 and len(r.stdout)<=65536 else 'auto'
        cache.clear();cache[package]=value
    write_rules([{'app_id':app,'orientation':cache[package],'source':'android-activity'}])

def stop(_sig,_frame):
    global STOP
    STOP=True

def main():
    if os.geteuid()!=0:raise SystemExit(1)
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    cache={}
    try:
        write_rules([])
        while not STOP:
            paths=[p for p in Path('/run/user/1000/hypr').glob('*/.socket2.sock') if p.is_socket()]
            if len(paths)!=1:time.sleep(2);continue
            path=paths[0];sig=path.parent.name
            try:
                with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as stream:
                    stream.settimeout(2);stream.connect(str(path));update(sig,cache);pending=b''
                    while not STOP:
                        try:block=stream.recv(16384)
                        except socket.timeout:continue
                        if not block:break
                        pending+=block
                        if len(pending)>65536:pending=b'';continue
                        lines=pending.split(b'\n');pending=lines.pop()
                        if any(line.split(b'>>',1)[0] in (b'closewindow',b'openwindow') for line in lines):cache.clear()
                        if any(line.split(b'>>',1)[0] in (b'activewindowv2',b'workspacev2',b'windowtitlev2',b'closewindow',b'openwindow') for line in lines):
                            update(sig,cache)
            except (OSError,ValueError,TypeError):
                write_rules([]);cache.clear();time.sleep(2)
    finally:write_rules([])

if __name__=='__main__':
    try:main()
    except Exception:raise SystemExit(1)  # Never put runtime identifiers in journal/tracebacks.
