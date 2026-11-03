# SPDX-License-Identifier: MIT
"""Read-only owner identity. No credential reads, account edits or activation."""
from pathlib import Path
import grp
import json
import os
import pwd
import re
import stat

OWNER_UID = 1000
MAPPING = Path('/etc/apollo/owner-account.json')
READY = Path('/var/lib/apollo/owner-ready')
ROLE = Path('/run/apollo-owner/role.json')
NAME_RE = re.compile(r'[a-z_][a-z0-9_-]{0,31}\Z', re.ASCII)


class OwnerError(Exception):
    pass


def protected(path, directory=False, private=False):
    info = path.lstat()
    kind = stat.S_ISDIR if directory else stat.S_ISREG
    if not kind(info.st_mode) or info.st_uid != 0 or info.st_mode & (0o077 if private else 0o022):
        raise OwnerError('INVALID_OWNER_METADATA')
    for parent in path.parents:
        item = parent.lstat()
        if not stat.S_ISDIR(item.st_mode) or item.st_uid != 0 or item.st_mode & 0o022:
            raise OwnerError('INVALID_OWNER_METADATA_PARENT')
    return info


def read_record(path, private=False):
    info = protected(path, private=private)
    if info.st_size > 4096:
        raise OwnerError('INVALID_OWNER_METADATA_SIZE')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        current = os.fstat(fd)
        if (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino):
            raise OwnerError('OWNER_METADATA_CHANGED')
        data = os.read(fd, 4097)
    finally:
        os.close(fd)
    if len(data) > 4096:
        raise OwnerError('INVALID_OWNER_METADATA_SIZE')
    return json.loads(data.decode('utf-8'))


def validate_record(record, lookup=pwd.getpwnam):
    if not isinstance(record, dict) or set(record) != {'schema', 'name', 'uid', 'gid', 'home'}:
        raise OwnerError('INVALID_OWNER_MAPPING')
    name = record['name']
    if type(record['schema']) is not int or record['schema'] != 1 or type(record['uid']) is not int or record['uid'] != OWNER_UID:
        raise OwnerError('INVALID_OWNER_UID')
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        raise OwnerError('INVALID_OWNER_NAME')
    if type(record['gid']) is not int or record['gid'] <= 0 or record['home'] != '/home/' + name:
        raise OwnerError('INVALID_OWNER_HOME')
    account = lookup(name)
    if (account.pw_uid, account.pw_gid, account.pw_dir) != (OWNER_UID, record['gid'], record['home']):
        raise OwnerError('OWNER_MAPPING_ACCOUNT_MISMATCH')
    return dict(record)


def wheel_member(record):
    wheel = grp.getgrnam('wheel').gr_gid
    return wheel in os.getgrouplist(record['name'], record['gid'])


def resolve_owner():
    protected(READY, private=True)
    if MAPPING.exists() or MAPPING.is_symlink():
        record = validate_record(read_record(MAPPING, private=True))
    else:
        # Compatibility is identity-only and only for an already-owned system.
        # Never creates/renames an account or changes a password/membership.
        account = pwd.getpwuid(OWNER_UID)
        record = validate_record({'schema': 1, 'name': account.pw_name, 'uid': OWNER_UID,
                                  'gid': account.pw_gid, 'home': account.pw_dir})
    if not wheel_member(record):
        raise OwnerError('OWNER_ADMIN_MEMBERSHIP_MISSING')
    return record


def role_matches(record, subject_name, lookup=pwd.getpwnam):
    try:
        if not isinstance(subject_name, str) or not NAME_RE.fullmatch(subject_name):
            return False
        return validate_record(record, lookup)['name'] == subject_name
    except (OwnerError, KeyError, TypeError, ValueError):
        return False
