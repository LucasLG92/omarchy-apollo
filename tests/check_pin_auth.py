#!/usr/bin/env python3
"""Device-local authentication checks using an isolated, disposable account.

Requires root, gcc, libxcrypt and PAM development headers. Does not enroll an
owner PIN or modify the owner's PAM service. Test secrets are generated in
memory, passed on stdin and never printed.
"""
from pathlib import Path
import json
import os
import pwd
import secrets
import subprocess
import tempfile
import time

REPO = Path(__file__).resolve().parents[1]
NAME = 'apollo-pin-test'
SERVICE = Path('/etc/pam.d/omarchy-apollo-pin-test')
PARENT = Path('/var/lib/omarchy-apollo')


def run(args, **kwargs):
    return subprocess.run(args, capture_output=True, text=True, timeout=15, **kwargs)


def main():
    if os.geteuid() != 0:
        raise SystemExit('Run this device-local test as root.')
    assert run(['getent', 'passwd', NAME]).returncode != 0, 'Test account already exists; refusing to reuse it.'
    assert not SERVICE.exists(), 'Test PAM service already exists; refusing to replace it.'
    PARENT.mkdir(mode=0o755, exist_ok=True)
    checks = []
    account_created = False
    owner = None
    with tempfile.TemporaryDirectory(prefix='pin-auth-test-', dir=PARENT) as folder:
        folder = Path(folder)
        folder.chmod(0o755)
        source = (REPO/'lock/verify-pin.c').read_text(encoding='utf-8')
        original = '#define PIN_ROOT "/var/lib/omarchy-apollo/pins"'
        assert source.count(original) == 1
        # Change only the fixed data directory in the test build. Production
        # code has no environment or command-line switch for this directory.
        (folder/'verify-pin.c').write_text(source.replace(original, '#define PIN_ROOT "'+str(folder/'pins')+'"'), encoding='utf-8')
        helper = folder/'verify-pin'
        probe = folder/'pam-probe'
        for source, output, library in [(folder/'verify-pin.c', helper, 'crypt'), (REPO/'tests/support/pam-probe.c', probe, 'pam')]:
            result = run(['gcc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', '-fstack-protector-strong', '-D_FORTIFY_SOURCE=3', str(source), '-o', str(output), '-l'+library])
            assert result.returncode == 0, result.stderr
        try:
            result = run(['useradd', '--no-create-home', '--shell', '/usr/bin/nologin', NAME])
            assert result.returncode == 0, result.stderr
            account_created = True
            owner = pwd.getpwnam(NAME)
            os.chown(helper, 0, owner.pw_gid)
            helper.chmod(0o4750)
            pin = ''.join(secrets.choice('0123456789') for _ in range(8))
            wrong = str((int(pin)+1) % 100000000).zfill(8)
            password = secrets.token_urlsafe(24)

            def direct(value, args=(), pam_user=NAME):
                return run(['runuser', '-u', NAME, '--', 'env', 'PAM_USER='+pam_user, 'PAM_TYPE=auth', str(helper), *args], input=value)

            def enroll():
                result = run([str(helper), '--enroll', str(owner.pw_uid)], input=pin+'\n'+pin+'\n')
                assert result.returncode == 0

            enroll()
            checks.append('root enrollment')
            assert direct(pin+'\n').returncode == 0
            checks.append('correct PIN')
            assert direct(pin+'\n', pam_user='root').returncode != 0
            checks.append('PAM user mismatch rejected')
            assert direct(pin+'\n'+pin+'\n', ['--enroll', str(owner.pw_uid)]).returncode != 0
            checks.append('unprivileged enrollment rejected')
            assert run(['runuser', '-u', NAME, '--', 'cat', str(folder/'pins'/str(owner.pw_uid)/'hash')]).returncode != 0
            checks.append('verifier unreadable to user')
            assert direct(password+'\n').returncode != 0 and direct(pin+'\n').returncode == 0
            checks.append('Unix-password input does not lock the PIN')
            assert direct(wrong+'\n').returncode != 0 and direct(pin+'\n').returncode == 2
            checks.append('direct helper retry limit')
            time.sleep(2.2)
            assert direct(pin+'\n').returncode == 0
            checks.append('correct PIN after retry delay')
            for attempt in range(5):
                assert direct(wrong+'\n').returncode != 0
                if attempt < 4:
                    time.sleep(2.2)
            assert direct(pin+'\n').returncode == 2
            checks.append('five-failure lockout')
            result = direct('', ['--status'])
            assert result.returncode == 0 and result.stdout.strip() == 'configured'
            checks.append('status contains no verifier')

            # Exercise the real Linux PAM conversation and Unix fallback.
            enroll()
            assert run(['chpasswd'], input=NAME+':'+password+'\n').returncode == 0
            pam = (REPO/'lock/omarchy-lock-password').read_text(encoding='utf-8')
            SERVICE.write_text(pam.replace('/usr/lib/omarchy/apollo/verify-pin', str(helper)), encoding='utf-8')
            SERVICE.chmod(0o644)

            def authenticate(value):
                return run(['runuser', '-u', NAME, '--', str(probe), SERVICE.name], input=value+'\n').returncode

            assert authenticate(pin) == 0
            checks.append('PIN through real PAM conversation')
            assert authenticate(password) == 0
            checks.append('independent Unix password fallback')
            assert authenticate(password+'x') != 0
            checks.append('wrong password rejected')
            assert authenticate(wrong) != 0
            checks.append('wrong numeric PIN rejected')
            time.sleep(2.2)
            assert authenticate(pin) == 0
            checks.append('PIN usable after failed attempts')
        finally:
            if helper.exists():
                helper.chmod(0o750)
            SERVICE.unlink(missing_ok=True)
            if account_created:
                assert pwd.getpwnam(NAME).pw_uid == owner.pw_uid
                run(['loginctl', 'terminate-user', NAME])
                for attempt in range(20):
                    result = run(['userdel', NAME])
                    if result.returncode == 0:
                        break
                    assert 'currently used by process' in result.stderr, result.stderr
                    time.sleep(0.2)
                else:
                    raise RuntimeError('The temporary account manager did not stop.')
            (Path('/run/faillock')/NAME).unlink(missing_ok=True)
    print(json.dumps({'passed': checks, 'owner_credentials_used': False, 'temporary_account_removed': True}, indent=2))


if __name__ == '__main__':
    main()
