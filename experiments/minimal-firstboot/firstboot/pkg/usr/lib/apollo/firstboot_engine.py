# SPDX-License-Identifier: MIT
"""One-owner state machine; operations injected for deterministic no-PAM tests."""
import re
from firstboot_profile import validate_profile

OWNER_UID = 1000
NAME = re.compile(r'[a-z_][a-z0-9_-]{0,31}\Z', re.ASCII)
# From omamobile-firstboot 0.1.2, retaining its namespace reservations.
RESERVED = re.compile(r'(root|alarm|omamobile|omandroid|omarchy|bin|daemon|mail|ftp|http|nobody|dbus|systemd-.*|tss|uuidd|alpm|git|avahi|cups|cups-browsed|lp|_talkd|polkitd|rtkit|qemu|brltty|gluster|rpc|libvirt-qemu|pcscd|nvidia-persistenced|sddm|builder|admin)\Z')
PHASES = {'reserved', 'account-created', 'password-pending', 'credential-set', 'ready'}


class FirstbootError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def valid_name(value):
    return isinstance(value, str) and NAME.fullmatch(value) is not None and RESERVED.fullmatch(value) is None


def valid_password(value):
    if not isinstance(value, str) or not 8 <= len(value) <= 128 or any(c in value for c in '\0\r\n'):
        return False
    try:
        value.encode('utf-8', 'strict')
    except UnicodeError:
        return False
    return True


def validate_journal(record):
    if not isinstance(record, dict) or set(record) != ({'schema', 'uid', 'name', 'phase', 'editor', 'profile'} if record.get('schema') == 2 else {'schema', 'uid', 'name', 'phase', 'editor'}):
        raise FirstbootError('NEEDS_ADMIN')
    if type(record['schema']) is not int or record['schema'] not in (1, 2) or type(record['uid']) is not int or record['uid'] != OWNER_UID:
        raise FirstbootError('NEEDS_ADMIN')
    if (not valid_name(record['name']) or not isinstance(record['phase'], str) or record['phase'] not in PHASES
            or record['editor'] not in ('pin', 'password')):
        raise FirstbootError('NEEDS_ADMIN')
    if record['schema'] == 2:
        try: validate_profile(record['profile'])
        except (ValueError, TypeError, KeyError): raise FirstbootError('NEEDS_ADMIN') from None
    return dict(record)


class Engine:
    def __init__(self, operations):
        self.ops = operations

    def state(self):
        if not self.ops.native_ready():
            return 'unavailable'
        if self.ops.owner_ready():
            return 'ready'
        record = self.ops.journal()
        account = self.ops.account_by_uid(OWNER_UID)
        if record is None:
            return 'unowned' if account is None and not self.ops.mapping_exists() else 'needs-admin'
        try:
            record = validate_journal(record)
        except FirstbootError:
            return 'needs-admin'
        if account is None:
            return 'unowned-reserved' if record['phase'] == 'reserved' else 'needs-admin'
        if not self.ops.account_matches(account, record['name']):
            return 'needs-admin'
        status = self.ops.password_status(record['name'])
        if status == 'L' and record['phase'] in {'reserved', 'account-created', 'password-pending'}:
            return 'needs-password'
        if status == 'P' and record['phase'] in {'password-pending', 'credential-set', 'ready'}:
            return 'finish-pending'
        return 'needs-admin'

    def _record(self, name, phase, editor, preferences=None):
        record = {'schema': 1, 'uid': OWNER_UID, 'name': name, 'phase': phase, 'editor': editor}
        if preferences is not None: record.update(schema=2, profile=validate_profile(preferences))
        self.ops.write_journal(record)
        return record

    def _finish(self, record, account, authorize):
        authorize()
        if self.ops.owner_ready():
            raise FirstbootError('ALREADY_OWNED')
        if self.ops.owner_active():
            raise FirstbootError('OWNER_ALREADY_ACTIVE')
        if not self.ops.account_matches(account, record['name']) or self.ops.password_status(record['name']) != 'P':
            raise FirstbootError('NEEDS_ADMIN')
        self.ops.verify_home_and_groups(account)
        self._record(record['name'], 'credential-set', record['editor'], record.get('profile'))
        if record.get('profile') is not None:
            authorize()
            self.ops.apply_profile(account, record['profile'])
        if not self.ops.set_credential_mode(account, record['editor']):
            raise FirstbootError('MODE_SYNC_PENDING')
        self.ops.write_mapping(account)
        self.ops.publish_role(account)
        self.ops.write_owner_ready()
        # owner-ready is the commit point. A final journal annotation must
        # not turn an already committed account into a password retry.
        try:
            self._record(record['name'], 'ready', record['editor'], record.get('profile'))
        except Exception:
            pass
        return 'configured'

    def configure(self, username, password, authorize, preferences=None):
        # The broker supplies a real sender/session recheck, never request data.
        with self.ops.transaction():
            authorize()
            if not self.ops.native_ready():
                raise FirstbootError('UNAVAILABLE')
            if self.ops.owner_ready():
                raise FirstbootError('ALREADY_OWNED')
            current = self.state()
            if current == 'finish-pending':
                if username != '' or password != '':
                    raise FirstbootError('FINISH_WITHOUT_NEW_CREDENTIAL')
                record = validate_journal(self.ops.journal())
                return self._finish(record, self.ops.account_by_uid(OWNER_UID), authorize)
            if current not in {'unowned', 'unowned-reserved', 'needs-password'}:
                raise FirstbootError('NEEDS_ADMIN')
            if not valid_name(username):
                raise FirstbootError('INVALID_NAME')
            if not valid_password(password):
                raise FirstbootError('INVALID_PASSWORD')
            editor = 'pin' if re.fullmatch('[0-9]+', password, re.ASCII) else 'password'
            if self.ops.owner_active():
                raise FirstbootError('OWNER_ALREADY_ACTIVE')
            self.ops.verify_admin_prerequisites()
            if preferences is not None:
                try: preferences = validate_profile(preferences)
                except (ValueError, TypeError, KeyError): raise FirstbootError('INVALID_PROFILE') from None
                self.ops.verify_profile_supported(preferences)
            record = self.ops.journal()
            if record is not None:
                record = validate_journal(record)
                if record['name'] != username:
                    raise FirstbootError('IDENTITY_ALREADY_RESERVED')
            account = self.ops.account_by_uid(OWNER_UID)
            if account is None:
                if self.ops.name_or_group_exists(username):
                    raise FirstbootError('NAME_UNAVAILABLE')
                self.ops.verify_skeleton()
                record = self._record(username, 'reserved', editor, preferences)
                authorize()
                if self.ops.owner_ready() or self.ops.owner_active() or self.ops.account_by_uid(OWNER_UID) is not None:
                    raise FirstbootError('OWNER_STATE_CHANGED')
                self.ops.create_account(username)
                account = self.ops.account_by_uid(OWNER_UID)
            if account is None or record is None or not self.ops.account_matches(account, username):
                raise FirstbootError('NEEDS_ADMIN')
            self.ops.verify_home_and_groups(account)
            if self.ops.password_status(username) != 'L':
                # Never reset an existing credential, including a crash replay.
                raise FirstbootError('NEEDS_ADMIN')
            preferences = preferences if preferences is not None else record.get('profile')
            self._record(username, 'account-created', editor, preferences)
            authorize()
            if self.ops.owner_ready() or self.ops.owner_active():
                raise FirstbootError('OWNER_STATE_CHANGED')
            record = self._record(username, 'password-pending', editor, preferences)
            if not self.ops.set_password(username, password):
                raise FirstbootError('PASSWORD_REJECTED')
            password = None
            return self._finish(record, account, authorize)
