# SPDX-License-Identifier: MIT
from pathlib import Path
import importlib.machinery
import importlib.util
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'pkg/usr/lib/apollo'))
import firstboot_ops as ops
import firstboot_authorize as auth
import owner_account as owner


class Variant:
    def __init__(self, *args): self.value = args[-1]
    def unpack(self): return self.value


class FakeBus:
    def __init__(self, properties, credentials=None):
        self.properties = properties
        self.credentials = credentials or [(976, 42), (976, 42)]
        self.calls = []

    def call_sync(self, destination, path, interface, method, *_args):
        self.calls.append(method)
        if method == 'GetConnectionCredentials':
            uid, pid = self.credentials.pop(0)
            return Variant(({'UnixUserID': uid, 'ProcessID': pid},))
        if method == 'GetSessionByPID': return Variant(('/synthetic/greeter',))
        if method == 'GetAll': return Variant((self.properties,))
        raise AssertionError('Unexpected call')


def guard(bus):
    value = auth.SenderGuard.__new__(auth.SenderGuard)
    value.bus, value.sddm_uid = bus, 976
    value.Gio = types.SimpleNamespace(DBusCallFlags=types.SimpleNamespace(NONE=0))
    value.GLib = types.SimpleNamespace(Variant=Variant, VariantType=types.SimpleNamespace(new=lambda x: x))
    return value


class OperationTests(unittest.TestCase):
    def test_plain_password_uses_only_normal_pam_stdin(self):
        sink = ops.Operations.__new__(ops.Operations)
        with patch.object(ops.subprocess, 'run', return_value=types.SimpleNamespace(returncode=0)) as run:
            self.assertTrue(sink.set_password('alice', ' á:Demo9!'))
        args, kwargs = run.call_args
        self.assertEqual(args[0], ['/usr/bin/chpasswd'])
        self.assertEqual(kwargs['input'], 'alice: á:Demo9!\n'.encode())
        self.assertEqual(kwargs['env'], ops.ENV)
        self.assertIs(kwargs['stdout'], subprocess.DEVNULL)
        self.assertIs(kwargs['stderr'], subprocess.DEVNULL)
        self.assertNotIn('Demo', repr(args))

    def test_account_adapter_stdin_only_and_no_user_manager(self):
        sink = ops.Operations.__new__(ops.Operations)
        with patch.object(ops.subprocess, 'run', return_value=types.SimpleNamespace(returncode=0)) as run:
            sink.create_account('alice')
        args, kwargs = run.call_args
        self.assertEqual(args[0], ['/usr/lib/omamobile-firstboot/owner-account.sh'])
        self.assertEqual(kwargs['input'], b'alice\n')
        self.assertEqual(kwargs['env'], ops.ENV)

    def test_password_status_has_no_hash_query(self):
        sink = ops.Operations.__new__(ops.Operations)
        with patch.object(ops.subprocess, 'run', return_value=types.SimpleNamespace(returncode=0, stdout=b'alice P synthetic\n')) as run:
            self.assertEqual(sink.password_status('alice'), 'P')
        self.assertEqual(run.call_args.args[0], ['/usr/bin/passwd', '-S', 'alice'])

    def test_guard_checks_bus_uid_pid_executable_and_logind_twice(self):
        props = {'User': (976, '/user'), 'Active': True, 'Remote': False,
                 'Class': 'greeter', 'Type': 'wayland', 'Seat': ('seat0', '/seat')}
        bus = FakeBus(props)
        with patch.object(auth.os, 'readlink', return_value='/usr/bin/sddm-greeter-qt6'), patch.object(auth, 'protected'):
            guard(bus).check(':1.9', write=True)
        self.assertEqual(bus.calls, ['GetConnectionCredentials', 'GetSessionByPID', 'GetAll', 'GetConnectionCredentials'])

    def test_guard_denies_other_uid_name_pid_reuse_and_untrusted_executable(self):
        for credentials in [[(1000, 42)], [(0, 42)], [(976, 0)], [(976, 42), (976, 43)]]:
            bus = FakeBus({}, credentials)
            with patch.object(auth.os, 'readlink', return_value='/usr/bin/sddm-greeter-qt6'), patch.object(auth, 'protected'):
                with self.assertRaises(auth.Denied): guard(bus).check(':1.9')
        with self.assertRaises(auth.Denied): guard(FakeBus({})).check('org.spoof.Greeter')
        with patch.object(auth.os, 'readlink', return_value='/tmp/sddm-greeter-qt6'):
            with self.assertRaises(auth.Denied): guard(FakeBus({})).check(':1.9')

    def test_guard_readonly_does_not_require_or_mutate_session(self):
        bus = FakeBus({})
        with patch.object(auth.os, 'readlink', return_value='/usr/bin/sddm-greeter-qt6'), patch.object(auth, 'protected'):
            guard(bus).check(':1.9', write=False)
        self.assertEqual(bus.calls, ['GetConnectionCredentials', 'GetConnectionCredentials'])

    def test_mapping_requires_exact_identity_and_does_not_rename(self):
        account = types.SimpleNamespace(pw_uid=1000, pw_gid=1000, pw_dir='/home/alice')
        record = dict(schema=1, name='alice', uid=1000, gid=1000, home='/home/alice')
        self.assertEqual(owner.validate_record(record, lambda _: account), record)
        for field, bad in [('uid', 1001), ('gid', 0), ('home', '/root'), ('name', '../root')]:
            with self.assertRaises(owner.OwnerError): owner.validate_record(dict(record, **{field: bad}), lambda _: account)

    def test_legacy_owner_resolution_is_ready_guarded_and_read_only(self):
        account = types.SimpleNamespace(pw_name='legacy', pw_uid=1000, pw_gid=1000, pw_dir='/home/legacy')
        # Patch the mapping constant to a nonexistent fixture path only. No
        # actual /etc mapping, readiness or password files are accessed.
        with patch.object(owner, 'MAPPING', HERE/'tests/nonexistent-mapping'), patch.object(owner, 'protected') as prot, \
             patch.object(owner.pwd, 'getpwuid', return_value=account), patch.object(owner, 'validate_record', side_effect=lambda r:r), \
             patch.object(owner, 'wheel_member', return_value=True):
            self.assertEqual(owner.resolve_owner()['name'], 'legacy')
            prot.assert_called_once_with(owner.READY, private=True)

    def test_profile_overlay_preserves_fixed_action_and_removes_initial_reset(self):
        ui = (HERE/'profile-overlay/usr/lib/apollo/owner-ui/owner-setup.py').read_text()
        helper = (HERE/'profile-overlay/usr/lib/apollo/owner-password-change').read_text()
        rule = (HERE/'profile-overlay/usr/share/polkit-1/rules.d/49-apollo-sim-ui.rules').read_text()
        self.assertNotIn("ACCOUNT = 'omarchy'", ui + helper)
        self.assertNotIn('def finish_initial_setup', ui)
        self.assertIn("if mode != 'change'", ui)
        self.assertIn("if sys.argv[1:] != ['--change']", ui)
        self.assertIn('resolve_owner()', helper)
        self.assertNotIn('subject.uid', rule.split('polkit.addRule', 1)[1])
        self.assertIn('subject.local && subject.active', rule)
        self.assertIn('"apollo-sim-pin.service"', rule)
        self.assertIn('owner-role-check', rule)

    def test_packaged_policy_is_narrow_and_owner_ready_unit_remains_available(self):
        config = (HERE/'pkg/usr/share/dbus-1/system.d/org.apollo.OwnerProvisioning1.conf').read_text()
        unit = (HERE/'pkg/usr/lib/systemd/system/apollo-owner-provisioner.service').read_text()
        self.assertIn('<deny send_destination=', config)
        self.assertIn('<policy user="sddm">', config)
        self.assertNotIn('allow send_destination="*"', config)
        self.assertNotIn('ConditionPathExists=!', unit)
        self.assertNotIn('Before=display-manager', unit)
        self.assertNotIn('After=display-manager', unit)


if __name__ == '__main__': unittest.main()
