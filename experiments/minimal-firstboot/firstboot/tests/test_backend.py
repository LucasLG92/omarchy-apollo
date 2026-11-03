# SPDX-License-Identifier: MIT
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import copy
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'pkg/usr/lib/apollo'))
from firstboot_engine import Engine, FirstbootError, valid_name, valid_password
from firstboot_authorize import Denied, greeter_properties_match
from firstboot_broker import Broker
from owner_account import role_matches, validate_record


def account(name='alice', uid=1000):
    return SimpleNamespace(pw_name=name, pw_uid=uid, pw_gid=1000, pw_dir='/home/' + name)


class FakeOperations:
    def __init__(self):
        self.ready = False
        self.native = True
        self.record = None
        self.mapping = None
        self.account = None
        self.status = 'L'
        self.active = False
        self.collision = False
        self.events = []
        self.password_calls = []
        self.fail_after_password = False
        self.fail_mapping = False
        self.fail_final_journal = False
        self.fail_mode = False
        self.restart = 0
    @contextmanager
    def transaction(self): yield
    def native_ready(self): return self.native
    def owner_ready(self): return self.ready
    def journal(self): return copy.deepcopy(self.record)
    def account_by_uid(self, uid): return self.account
    def account_matches(self, value, name):
        return value.pw_uid == 1000 and value.pw_name == name and value.pw_dir == '/home/' + name
    def password_status(self, name): return self.status
    def mapping_exists(self): return self.mapping is not None
    def owner_active(self): return self.active
    def name_or_group_exists(self, name): return self.collision
    def verify_admin_prerequisites(self): pass
    def verify_skeleton(self): pass
    def verify_home_and_groups(self, value):
        assert value.pw_uid == 1000
    def write_journal(self, record):
        if self.fail_final_journal and record['phase'] == 'ready':
            raise OSError('synthetic final annotation failure')
        self.record = copy.deepcopy(record)
        self.events.append('journal:' + record['phase'])
    def create_account(self, name):
        self.events.append('create')
        self.account = account(name)
    def set_password(self, name, password):
        self.password_calls.append((name, password))
        self.status = 'P'
        if self.fail_after_password:
            raise OSError('synthetic crash after PAM result')
        return True
    def write_mapping(self, value):
        if self.fail_mapping:
            raise OSError('synthetic mapping failure')
        self.mapping = {'schema': 1, 'name': value.pw_name, 'uid': 1000, 'gid': value.pw_gid, 'home': value.pw_dir}
        self.events.append('mapping')
    def publish_role(self, value): self.events.append('role')
    def set_credential_mode(self, value, editor):
        self.events.append('mode:' + editor)
        return not self.fail_mode
    def write_owner_ready(self):
        self.ready = True
        self.events.append('ready')
    def restart_greeter_if_no_owner(self):
        if not self.active:
            self.restart += 1
        return not self.active


class BackendTests(unittest.TestCase):
    def rejected(self, engine, name, password, code):
        with self.assertRaises(FirstbootError) as caught:
            engine.configure(name, password, lambda: None)
        self.assertEqual(caught.exception.code, code)

    def test_validated_name_and_password_domain(self):
        for name in ['alice', 'a_9-', '_user']:
            self.assertTrue(valid_name(name))
        for name in ['root', 'sddm', 'omarchy', 'systemd-foo', '../alice', '--help', 'Alice', '1alice', 'a:b', 'álice', 'a' * 33]:
            self.assertFalse(valid_name(name), name)
        for value in ['  Letters:ñ !  ', '🔑' * 8, '0' * 128, ' ' * 8]:
            self.assertTrue(valid_password(value))
        for value in ['a' * 7, 'a' * 129, 'abcd\nxyz0', 'abcd\rxyz0', 'abcd\0xyz0', 'abcd\ud800xyz0']:
            self.assertFalse(valid_password(value))

    def test_numeric_mode_and_post_pam_mode_retry_never_reset_password(self):
        ops = FakeOperations()
        ops.fail_mode = True
        engine = Engine(ops)
        self.rejected(engine, 'alice', '12345678', 'MODE_SYNC_PENDING')
        self.assertEqual(engine.state(), 'finish-pending')
        self.assertEqual(ops.record['editor'], 'pin')
        self.assertFalse(ops.ready)
        ops.fail_mode = False
        self.assertEqual(engine.configure('', '', lambda: None), 'configured')
        self.assertEqual(len(ops.password_calls), 1)
        self.assertIn('mode:pin', ops.events)

    def test_finish_pending_refuses_active_owner_session(self):
        ops = FakeOperations()
        ops.fail_after_password = True
        with self.assertRaises(OSError): Engine(ops).configure('alice', 'Synthetic 7!', lambda: None)
        ops.active = True
        self.rejected(Engine(ops), '', '', 'OWNER_ALREADY_ACTIVE')
        self.assertFalse(ops.mapping or ops.ready)

    def test_existing_owner_never_reprovisioned_or_reset(self):
        ops = FakeOperations()
        ops.ready, ops.account, ops.status = True, account('omarchy'), 'P'
        engine = Engine(ops)
        self.assertEqual(engine.state(), 'ready')
        self.rejected(engine, 'alice', 'Synthetic 7!', 'ALREADY_OWNED')
        self.assertEqual(ops.events, [])
        self.assertEqual(ops.password_calls, [])

    def test_existing_uid_without_our_journal_is_not_a_template_to_rename(self):
        ops = FakeOperations()
        ops.account = account('omarchy')
        self.assertEqual(Engine(ops).state(), 'needs-admin')
        self.rejected(Engine(ops), 'alice', 'Synthetic 7!', 'NEEDS_ADMIN')
        self.assertFalse(ops.events or ops.password_calls)

    def test_success_has_fixed_uid_no_user_activation_no_secret_journal(self):
        ops = FakeOperations()
        secret = '  Synthetic:ñ 7!  '
        self.assertEqual(Engine(ops).configure('alice', secret, lambda: None), 'configured')
        self.assertTrue(ops.ready)
        self.assertEqual(ops.password_calls, [('alice', secret)])
        self.assertEqual(ops.mapping['uid'], 1000)
        self.assertEqual(ops.record['phase'], 'ready')
        self.assertNotIn(secret, json.dumps(ops.record))
        self.assertLess(ops.events.index('mapping'), ops.events.index('ready'))
        self.assertLess(ops.events.index('role'), ops.events.index('ready'))
        self.assertNotIn('user@', ' '.join(ops.events))

    def test_reserved_names_and_oversize_fail_without_any_write(self):
        for name, password, code in [('root', 'Synthetic 7!', 'INVALID_NAME'), ('alice', 'a' * 129, 'INVALID_PASSWORD')]:
            ops = FakeOperations()
            self.rejected(Engine(ops), name, password, code)
            self.assertFalse(ops.events or ops.password_calls)

    def test_active_uid_and_name_collisions_fail_closed(self):
        for field, code in [('active', 'OWNER_ALREADY_ACTIVE'), ('collision', 'NAME_UNAVAILABLE')]:
            ops = FakeOperations()
            setattr(ops, field, True)
            self.rejected(Engine(ops), 'alice', 'Synthetic 7!', code)
            self.assertFalse(ops.events or ops.password_calls)

    def test_sender_revoked_before_creation(self):
        ops = FakeOperations()
        calls = []
        def guard():
            calls.append(True)
            if len(calls) == 2:
                raise Denied()
        with self.assertRaises(Denied):
            Engine(ops).configure('alice', 'Synthetic 7!', guard)
        self.assertNotIn('create', ops.events)
        self.assertFalse(ops.password_calls)

    def test_crash_after_password_does_not_replay_or_reset_it(self):
        ops = FakeOperations()
        ops.fail_after_password = True
        with self.assertRaises(OSError):
            Engine(ops).configure('alice', 'Old synthetic 7!', lambda: None)
        self.assertEqual(Engine(ops).state(), 'finish-pending')
        self.rejected(Engine(ops), 'alice', 'Different synthetic 8!', 'FINISH_WITHOUT_NEW_CREDENTIAL')
        self.assertEqual(Engine(ops).configure('', '', lambda: None), 'configured')
        self.assertEqual(ops.password_calls, [('alice', 'Old synthetic 7!')])

    def test_retry_mapping_only_after_backend_success(self):
        ops = FakeOperations()
        ops.fail_mapping = True
        with self.assertRaises(OSError):
            Engine(ops).configure('alice', 'Synthetic 7!', lambda: None)
        self.assertFalse(ops.ready)
        ops.fail_mapping = False
        self.assertEqual(Engine(ops).configure('', '', lambda: None), 'configured')
        self.assertEqual(len(ops.password_calls), 1)

    def test_foreign_or_malformed_journal_never_enables_a_reset(self):
        for record in [{'schema': 1, 'uid': 0, 'name': 'root', 'phase': 'reserved'},
                       {'schema': 1, 'uid': 1000, 'name': 'alice', 'phase': 'reserved', 'password': 'test-only'}]:
            ops = FakeOperations()
            ops.record = record
            self.rejected(Engine(ops), 'alice', 'Synthetic 7!', 'NEEDS_ADMIN')
            self.assertFalse(ops.password_calls)

    def test_reserved_identity_cannot_change_on_retry(self):
        ops = FakeOperations()
        ops.record = {'schema': 1, 'uid': 1000, 'name': 'alice', 'phase': 'reserved', 'editor': 'password'}
        self.rejected(Engine(ops), 'bob', 'Synthetic 7!', 'IDENTITY_ALREADY_RESERVED')
        self.assertFalse(ops.password_calls)

    def test_unexpected_existing_password_before_attempt_requires_admin(self):
        ops = FakeOperations()
        ops.record = {'schema': 1, 'uid': 1000, 'name': 'alice', 'phase': 'reserved', 'editor': 'password'}
        ops.account, ops.status = account(), 'P'
        self.rejected(Engine(ops), 'alice', 'Synthetic 7!', 'NEEDS_ADMIN')
        self.assertFalse(ops.password_calls)

    def test_final_journal_failure_cannot_request_a_new_password(self):
        ops = FakeOperations()
        ops.fail_final_journal = True
        self.assertEqual(Engine(ops).configure('alice', 'Synthetic 7!', lambda: None), 'configured')
        self.rejected(Engine(ops), '', '', 'ALREADY_OWNED')
        self.assertEqual(len(ops.password_calls), 1)

    def test_sender_properties_require_real_local_active_greeter(self):
        good = {'User': (964, '/synthetic'), 'Active': True, 'Remote': False, 'Class': 'greeter', 'Type': 'wayland', 'Seat': ('seat0', '/synthetic')}
        self.assertTrue(greeter_properties_match(good, 964))
        for key, value in [('User', (1000, '/synthetic')), ('Active', False), ('Remote', True), ('Class', 'user'), ('Type', 'tty'), ('Seat', ('', '/'))]:
            self.assertFalse(greeter_properties_match({**good, key: value}, 964))

    def test_role_name_and_uid_are_bound_to_mapping(self):
        record = {'schema': 1, 'name': 'alice', 'uid': 1000, 'gid': 1000, 'home': '/home/alice'}
        lookup = lambda name: account(name)
        self.assertTrue(role_matches(record, 'alice', lookup))
        self.assertFalse(role_matches(record, 'bob', lookup))
        self.assertFalse(role_matches({**record, 'uid': 0}, 'alice', lookup))

    def test_reply_precedes_refresh_and_active_owner_blocks_restart(self):
        ops = FakeOperations()
        events = []
        class Guard:
            def check(self, sender, write=False):
                self_outer.assertEqual(sender, ':synthetic')
        self_outer = self
        timers = []
        broker = Broker(Engine(ops), Guard(), lambda inv, code: events.append(('reply', code)),
                        lambda fn, *args: fn(*args), lambda delay, fn: timers.append((delay, fn)), lambda fn: fn())
        broker.configure(':synthetic', 'alice', 'Synthetic 7!', object())
        self.assertEqual(events, [('reply', 'configured')])
        self.assertEqual(timers[0][0], 700)
        self.assertEqual(ops.restart, 0)
        ops.active = True
        timers[0][1]()
        self.assertEqual(ops.restart, 0)

    def test_get_state_is_read_only_and_denied_sender_gets_no_write(self):
        ops = FakeOperations()
        replies = []
        class Guard:
            def check(self, sender, write=False):
                raise Denied()
        broker = Broker(Engine(ops), Guard(), lambda inv, code: replies.append(code), lambda *_: None, lambda *_: None)
        broker.get_state(':synthetic', object())
        broker.configure(':synthetic', 'alice', 'Synthetic 7!', object())
        self.assertEqual(replies, ['denied', 'DENIED'])
        self.assertFalse(ops.events or ops.password_calls)


if __name__ == '__main__':
    unittest.main()
