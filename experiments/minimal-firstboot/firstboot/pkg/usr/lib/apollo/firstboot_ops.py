# SPDX-License-Identifier: MIT
"""Fixed production operations. Never used by the synthetic account tests."""
from pathlib import Path
from contextlib import contextmanager
import fcntl
import grp
import json
import os
import pwd
import stat
import subprocess
import tempfile

from firstboot_engine import FirstbootError
from owner_account import protected, read_record, validate_record

ENV = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8'}
STATE = Path('/var/lib/apollo')
JOURNAL = STATE / 'owner-provisioning.json'
READY = STATE / 'owner-ready'
MAPPING = Path('/etc/apollo/owner-account.json')
ROLE = Path('/run/apollo-owner/role.json')
SKEL = Path('/usr/share/apollo/owner-skel')


def atomic_json(path, record, mode=0o600):
    protected(path.parent, directory=True)
    if path.exists() or path.is_symlink():
        protected(path, private=(mode == 0o600))
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(record, stream, separators=(',', ':'))
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def private_directory(path):
    path.mkdir(mode=0o700, parents=False, exist_ok=True)
    protected(path, directory=True, private=True)


def account_record(account):
    return {'schema': 1, 'name': account.pw_name, 'uid': account.pw_uid,
            'gid': account.pw_gid, 'home': account.pw_dir}


class Operations:
    def __init__(self):
        if os.geteuid() != 0:
            raise FirstbootError('ROOT_REQUIRED')

    @contextmanager
    def transaction(self):
        runtime = Path('/run/apollo-firstboot')
        private_directory(runtime)
        fd = os.open(runtime / 'configure.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o077:
                raise FirstbootError('INVALID_LOCK')
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
        finally:
            os.close(fd)

    def native_ready(self):
        try:
            protected(Path('/etc/apollo/native-root-v1'))
            return True
        except FileNotFoundError:
            return False

    def owner_ready(self):
        if not READY.exists() and not READY.is_symlink():
            return False
        protected(READY, private=True)
        return True

    def journal(self):
        if not JOURNAL.exists() and not JOURNAL.is_symlink():
            return None
        return read_record(JOURNAL, private=True)

    def write_journal(self, record):
        private_directory(STATE)
        atomic_json(JOURNAL, record)

    def mapping_exists(self):
        return MAPPING.exists() or MAPPING.is_symlink()

    def account_by_uid(self, uid):
        try:
            return pwd.getpwuid(uid)
        except KeyError:
            return None

    def account_matches(self, account, name):
        return (account.pw_uid == 1000 and account.pw_name == name
                and account.pw_dir == '/home/' + name and account.pw_gid > 0)

    def name_or_group_exists(self, name):
        for lookup in (pwd.getpwnam, grp.getgrnam):
            try:
                lookup(name)
                return True
            except KeyError:
                pass
        home = Path('/home') / name
        return home.exists() or home.is_symlink()

    def owner_active(self):
        for process in Path('/proc').iterdir():
            if not process.name.isdecimal():
                continue
            try:
                for line in (process / 'status').read_text(encoding='ascii').splitlines():
                    if line.startswith('Uid:') and 1000 in [int(v) for v in line.split()[1:]]:
                        return True
            except (FileNotFoundError, ProcessLookupError):
                continue
            except PermissionError:
                # Unknown process identity is not permission to restart DM.
                return True
        return False

    def verify_admin_prerequisites(self):
        grp.getgrnam('wheel')
        path = Path('/etc/sudoers.d/20-apollo-owner')
        protected(path)
        lines = [' '.join(line.split('#', 1)[0].split()) for line in path.read_text(encoding='utf-8').splitlines()]
        if [line for line in lines if line] != ['%wheel ALL=(ALL:ALL) ALL']:
            raise FirstbootError('ADMIN_POLICY_NOT_READY')
        result = subprocess.run(['/usr/bin/pacman', '-Qqo', str(path)], env=ENV, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, timeout=5)
        if result.returncode or result.stdout.strip() != b'apollo-native-profile':
            raise FirstbootError('ADMIN_POLICY_NOT_PACKAGED')

    def verify_skeleton(self):
        groups = Path('/var/lib/omarchy/provisioning/groups')
        if groups.exists() or groups.is_symlink():
            protected(groups)
            if groups.stat().st_size > 4096:
                raise FirstbootError('GROUPS_NOT_TRUSTED')
        protected(SKEL, directory=True)
        version = SKEL / '.apollo-owner-skel-version'
        protected(version)
        if version.read_bytes() != b'1\n':
            raise FirstbootError('SKELETON_NOT_PREPARED')
        total = count = 0
        for path in SKEL.rglob('*'):
            info = path.lstat()
            count += 1
            if count > 4096 or info.st_uid != 0 or (not stat.S_ISLNK(info.st_mode) and info.st_mode & 0o022):
                raise FirstbootError('SKELETON_NOT_TRUSTED')
            if stat.S_ISREG(info.st_mode):
                total += info.st_size
            elif stat.S_ISLNK(info.st_mode):
                # Only links to the staged generic tree or fixed packaged
                # public mobile assets. Never a used home or arbitrary path.
                target = path.resolve(strict=True)
                allowed = (target.is_relative_to(SKEL) or
                           str(target).startswith('/usr/share/omamobile/shell/plugins/omamobile.') or
                           target == Path('/usr/share/omamobile/squeekboard/keyboards/terminal/us.yaml'))
                if not allowed:
                    raise FirstbootError('SKELETON_LINK_NOT_TRUSTED')
                protected(target, directory=target.is_dir())
            elif not stat.S_ISDIR(info.st_mode):
                raise FirstbootError('SKELETON_NOT_TRUSTED')
            if total > 16 * 1024 * 1024:
                raise FirstbootError('SKELETON_TOO_LARGE')

    def create_account(self, name):
        # This adapted helper reuses upstream's group/home creation code.
        # No password/config values in its arguments or environment.
        result = subprocess.run(['/usr/lib/omamobile-firstboot/owner-account.sh'], input=(name + '\n').encode('ascii'),
                                env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        if result.returncode:
            raise FirstbootError('ACCOUNT_CREATE_FAILED')

    def verify_home_and_groups(self, account):
        record = validate_record(account_record(account))
        info = Path(record['home']).lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != 1000 or info.st_gid != account.pw_gid:
            raise FirstbootError('HOME_NOT_READY')
        if grp.getgrnam('wheel').gr_gid not in os.getgrouplist(account.pw_name, account.pw_gid):
            raise FirstbootError('OWNER_ADMIN_NOT_READY')

    def password_status(self, name):
        result = subprocess.run(['/usr/bin/passwd', '-S', name], env=ENV, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, timeout=5)
        parts = result.stdout.decode('ascii', errors='strict').split()
        return parts[1] if not result.returncode and len(parts) >= 2 and parts[0] == name else 'unknown'

    def set_password(self, name, password):
        payload = (name + ':' + password + '\n').encode('utf-8', 'strict')
        try:
            result = subprocess.run(['/usr/bin/chpasswd'], input=payload, env=ENV,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=25)
            return result.returncode == 0
        finally:
            payload = None

    def write_mapping(self, account):
        record = validate_record(account_record(account))
        if self.mapping_exists() and read_record(MAPPING, private=True) != record:
            raise FirstbootError('OWNER_MAPPING_CONFLICT')
        atomic_json(MAPPING, record)

    def set_credential_mode(self, account, mode):
        from owner_mode import set_mode
        return set_mode(account_record(account), mode)

    def write_owner_ready(self):
        private_directory(STATE)
        fd = os.open(READY, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(b'Owner account configured through local firstboot.\n')
            stream.flush()
            os.fsync(stream.fileno())
        directory = os.open(STATE, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    def publish_role(self, account):
        directory = ROLE.parent
        directory.mkdir(mode=0o755, exist_ok=True)
        protected(directory, directory=True)
        atomic_json(ROLE, validate_record(account_record(account)), 0o644)

    def verify_profile_supported(self, preferences):
        from firstboot_profile import validate_profile
        preferences = validate_profile(preferences)
        zone = Path('/usr/share/zoneinfo') / preferences['timezone']
        if not zone.is_file() or not zone.resolve().is_relative_to(Path('/usr/share/zoneinfo')):
            raise FirstbootError('INVALID_PROFILE')
        result = subprocess.run(['/usr/bin/locale', '-a'], env=ENV, capture_output=True, timeout=5)
        available = {line.lower().replace('-', '') for line in result.stdout.decode().splitlines()}
        if result.returncode or preferences['locale'].lower().replace('-', '') not in available:
            raise FirstbootError('LOCALE_UNAVAILABLE')

    def apply_profile(self, account, preferences):
        from firstboot_profile import validate_profile, LOCALES
        preferences = validate_profile(preferences)
        self.verify_profile_supported(preferences)
        self.verify_home_and_groups(account)
        home = Path(account.pw_dir)
        def user_file(relative, body):
            path = home / relative
            cursor = home
            for part in path.parent.relative_to(home).parts:
                cursor = cursor / part
                if not cursor.exists():
                    cursor.mkdir(mode=0o700)
                    os.chown(cursor, account.pw_uid, account.pw_gid)
                info = cursor.lstat()
                if not stat.S_ISDIR(info.st_mode) or info.st_uid != account.pw_uid:
                    raise FirstbootError('PROFILE_APPLY_FAILED')
            if path.exists() or path.is_symlink():
                info = path.lstat()
                if not stat.S_ISREG(info.st_mode) or info.st_uid != account.pw_uid:
                    raise FirstbootError('PROFILE_APPLY_FAILED')
            fd, temp = tempfile.mkstemp(prefix='.'+path.name+'.', dir=path.parent)
            try:
                os.fchmod(fd, 0o600)
                os.fchown(fd, account.pw_uid, account.pw_gid)
                with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                    stream.write(body); stream.flush(); os.fsync(stream.fileno())
                os.replace(temp, path)
            finally:
                if os.path.exists(temp): os.unlink(temp)
        def root_text(path, body):
            protected(path.parent, directory=True)
            if path.exists() or path.is_symlink(): protected(path)
            fd, temp = tempfile.mkstemp(prefix='.'+path.name+'.', dir=path.parent)
            try:
                os.fchmod(fd, 0o644)
                with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                    stream.write(body); stream.flush(); os.fsync(stream.fileno())
                os.replace(temp, path)
            finally:
                if os.path.exists(temp): os.unlink(temp)
        # Account comment and preferences only; no credential is passed here.
        result = subprocess.run(['/usr/bin/usermod', '--comment='+preferences['display_name'], '--', account.pw_name],
                                env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        if result.returncode: raise FirstbootError('PROFILE_APPLY_FAILED')
        root_text(Path('/etc/hostname'), preferences['hostname']+'\n')
        root_text(Path('/etc/locale.conf'), 'LANG='+preferences['locale']+'\n')
        if Path('/run/systemd/system').is_dir():
            for command in (['hostnamectl', 'set-hostname', preferences['hostname']],
                            ['timedatectl', 'set-timezone', preferences['timezone']]):
                result = subprocess.run(['/usr/bin/'+command[0], *command[1:]], env=ENV,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
                if result.returncode: raise FirstbootError('PROFILE_APPLY_FAILED')
        else:
            localtime = Path('/etc/localtime'); temp = Path('/etc/.localtime.apollo-firstboot')
            if temp.exists() or temp.is_symlink(): raise FirstbootError('PROFILE_APPLY_FAILED')
            os.symlink('/usr/share/zoneinfo/'+preferences['timezone'], temp); os.replace(temp, localtime)
        user_file('.config/omarchy/language', LOCALES[preferences['locale']]+'\n')
        user_file('.config/uwsm/env.d/50-omarchy-language', 'export LANG='+preferences['locale']+'\n')
        inputs = home/'.config/hypr/input.lua'
        if inputs.is_file() and not inputs.is_symlink():
            import re
            source = inputs.read_text()
            source = re.sub(r'\n-- Apollo first-run keyboard\n.*?-- End Apollo first-run keyboard\n', '', source, flags=re.S)
            source += '\n-- Apollo first-run keyboard\nhl.config({ input = { kb_layout = "'+preferences['keyboard']+'" } })\n-- End Apollo first-run keyboard\n'
            user_file('.config/hypr/input.lua', source)
        user_file('.config/apollo/first-run.json', json.dumps(preferences, ensure_ascii=False, sort_keys=True)+'\n')

    def restart_greeter_if_no_owner(self):
        if self.owner_active():
            return False
        subprocess.run(['/usr/bin/systemctl', 'try-restart', 'display-manager.service'], env=ENV,
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
        return True
