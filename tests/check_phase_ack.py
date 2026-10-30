#!/usr/bin/python3
"""Exercise the root test controller's acknowledgement against fixture symlinks."""
import argparse
import ast
import errno
import hashlib
import json
import os
from pathlib import Path
import pwd
import stat
import subprocess
import tempfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--user',default='apollo')
    args=parser.parse_args()
    assert os.getuid()==0 and os.geteuid()==0,'Run on the development device as root'
    owner=pwd.getpwnam(args.user);assert 1000<=owner.pw_uid<65534
    source=Path(__file__).resolve().parent/'support/android-lifecycle-controller.py'
    tree=ast.parse(source.read_text())
    functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='acknowledge']
    assert len(functions)==1
    namespace={'os':os,'owner':owner}
    # Load only the actual helper; the controller's Android/session body is not run.
    exec(compile(ast.Module(body=functions,type_ignores=[]),str(source),'exec'),namespace)
    acknowledge=namespace['acknowledge']
    checks=[]
    def check(name,condition):
        assert condition,name
        checks.append(name)
    os.umask(0o077)
    with tempfile.TemporaryDirectory(prefix='apollo-phase-ack-',dir='/var/tmp') as temporary:
        # Keep the legacy reproduction unreachable to real desktop processes.
        # Root preplaces the attack entry inside this root-only fixture.
        base=Path(temporary);base.chmod(0o700)
        work=base/'owner';work.mkdir(mode=0o700)
        canary=base/'root-canary';canary.write_bytes(b'Synthetic root-only acknowledgement fixture.\n');canary.chmod(0o600)
        digest=hashlib.sha256(canary.read_bytes()).digest()
        marker=work/'continue-ready';marker.symlink_to(canary);os.lchown(marker,owner.pw_uid,owner.pw_gid)
        # Reproduce the previous two-operation boundary on this synthetic file.
        marker.touch();os.chown(marker,owner.pw_uid,owner.pw_gid)
        check('old path-based acknowledgement demonstrates symlink ownership change',canary.stat().st_uid==owner.pw_uid)
        os.chown(canary,0,0)
        rejected=False
        try:acknowledge(marker)
        except OSError as error:rejected=error.errno in (errno.EEXIST,errno.ELOOP)
        check('actual controller helper rejects a preplaced symlink',rejected and marker.is_symlink())
        check('root-only canary ownership and contents are preserved',canary.stat().st_uid==0 and hashlib.sha256(canary.read_bytes()).digest()==digest)
        marker.unlink()
        acknowledge(marker)
        info=marker.stat()
        check('normal acknowledgement belongs to the intended user with mode 0600',stat.S_ISREG(info.st_mode) and info.st_uid==owner.pw_uid and info.st_gid==owner.pw_gid and stat.S_IMODE(info.st_mode)==0o600)
        marker.write_bytes(b'existing fixture marker\n')
        rejected=False
        try:acknowledge(marker)
        except FileExistsError:rejected=True
        check('an existing acknowledgement is refused without overwriting it',rejected and marker.read_bytes()==b'existing fixture marker\n')
        # All path-following legacy operations are over. Allow traversal to the
        # root-owned canary for a real unprivileged permission check; the marker
        # directory remains root-only throughout the test.
        base.chmod(0o711)
        probe="import os,sys\ntry:os.open(sys.argv[1],os.O_RDONLY)\nexcept PermissionError:raise SystemExit(0)\nraise SystemExit(1)\n"
        result=subprocess.run(['setpriv','--reuid='+str(owner.pw_uid),'--regid='+str(owner.pw_gid),'--clear-groups','/usr/bin/python','-I','-c',probe,str(canary)],capture_output=True,timeout=10)
        check('desktop user cannot read the protected synthetic canary',result.returncode==0)
    assert not base.exists()
    print(json.dumps({'passed':len(checks),'checks':checks,'temporary_files_removed':True,'owner_credentials_used':False,'android_or_desktop_services_modified':False},indent=2))


if __name__=='__main__':
    main()
