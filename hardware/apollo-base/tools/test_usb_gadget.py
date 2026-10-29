#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Configfs lifecycle fixtures only: no USB controller or phone is accessed."""
from pathlib import Path
import errno
import importlib.util
import tempfile
import unittest

source = Path(__file__).resolve().parents[1]/'system/apollo-usb-gadget.py'
spec = importlib.util.spec_from_file_location('apollo_usb', source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ConfigfsFixture(module.Gadget):
    def __init__(self, directory):
        root = directory/'gadgets'
        controllers = directory/'controllers'
        root.mkdir()
        controllers.mkdir()
        super().__init__(root, controllers)
        self.writes = []
        self.busy = False

    def mkdir(self, path):
        new = not path.exists()
        super().mkdir(path)
        if not new:
            return
        if path == self.path:
            for name in self.NUMBERS:
                (path/name).write_text('0x0000\n')
            (path/'UDC').write_text('\n')
            for name in ('strings', 'configs', 'functions'):
                (path/name).mkdir()
        elif path == self.path/'strings/0x409':
            for name in self.STRINGS:
                (path/name).write_text('\n')
        elif path == self.path/'configs/c.1':
            (path/'strings').mkdir()
            (path/'MaxPower').write_text('2\n')
        elif path == self.path/'configs/c.1/strings/0x409':
            (path/'configuration').write_text('\n')
        elif path == self.path/'functions/ncm.usb0':
            for name in ('dev_addr', 'host_addr'):
                (path/name).write_text('02:11:22:33:44:55\n')

    def write(self, path, value):
        if self.busy and path.name == 'UDC':
            raise OSError(errno.EBUSY, 'Synthetic controller busy')
        self.writes.append((str(path.relative_to(self.root)), str(value)))
        super().write(path, value)


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='apollo-usb-fixture-')
        self.addCleanup(self.temp.cleanup)
        self.gadget = ConfigfsFixture(Path(self.temp.name))

    def add_controller(self):
        (self.gadget.controllers/'synthetic-udc').mkdir()

    def test_controller_late_registration(self):
        self.assertEqual(self.gadget.ensure(), 'waiting-controller')
        self.assertFalse(self.gadget.read(self.gadget.path/'UDC'))
        self.add_controller()
        self.assertEqual(self.gadget.ensure(), 'bound')

    def test_restart_does_not_touch_bound_connection(self):
        self.add_controller()
        self.gadget.ensure()
        self.gadget.writes.clear()
        self.assertEqual(self.gadget.ensure(), 'already-bound')
        self.assertEqual(self.gadget.writes, [])

    def test_lpm_descriptor_selected_by_kernel_is_preserved(self):
        self.add_controller()
        self.gadget.ensure()
        (self.gadget.path/'bcdUSB').write_text('0x0201\n')
        self.gadget.writes.clear()
        self.assertEqual(self.gadget.ensure(), 'already-bound')
        self.assertEqual(self.gadget.writes, [])

    def test_unknown_usb_revision_is_refused(self):
        self.add_controller()
        self.gadget.ensure()
        (self.gadget.path/'bcdUSB').write_text('0x0300\n')
        self.gadget.writes.clear()
        with self.assertRaises(module.Refused):
            self.gadget.ensure()
        self.assertEqual(self.gadget.writes, [])

    def test_ncm_address_nul_terminator_preserves_bound_link(self):
        self.add_controller()
        self.gadget.ensure()
        for name in ('dev_addr', 'host_addr'):
            path = self.gadget.path/'functions/ncm.usb0'/name
            path.write_text(path.read_text().strip()+'\0\n')
        self.gadget.writes.clear()
        self.assertEqual(self.gadget.ensure(), 'already-bound')
        self.assertEqual(self.gadget.writes, [])

    def test_retry_after_temporary_bind_failure(self):
        self.add_controller()
        self.gadget.busy = True
        with self.assertRaises(OSError) as caught:
            self.gadget.ensure()
        self.assertEqual(caught.exception.errno, errno.EBUSY)
        self.gadget.busy = False
        self.gadget.writes.clear()
        self.assertEqual(self.gadget.ensure(), 'bound')
        self.assertEqual(self.gadget.writes, [('apollo/UDC', 'synthetic-udc')])

    def test_foreign_controller_owner_preserved(self):
        self.add_controller()
        foreign = self.gadget.root/'foreign'
        foreign.mkdir()
        (foreign/'UDC').write_text('synthetic-udc\n')
        with self.assertRaises(module.Refused):
            self.gadget.ensure()
        self.assertFalse(self.gadget.path.exists())
        self.assertEqual(self.gadget.writes, [])

    def test_foreign_descriptor_preserved(self):
        self.gadget.ensure()
        (self.gadget.path/'idVendor').write_text('0x1234\n')
        self.gadget.writes.clear()
        with self.assertRaises(module.Refused):
            self.gadget.ensure()
        self.assertEqual(self.gadget.writes, [])

    def test_unknown_function_preserved(self):
        self.gadget.ensure()
        (self.gadget.path/'functions/mass_storage.foreign').mkdir()
        self.gadget.writes.clear()
        with self.assertRaises(module.Refused):
            self.gadget.ensure()
        self.assertEqual(self.gadget.writes, [])

    def test_wrong_function_link_preserved(self):
        self.gadget.ensure()
        link = self.gadget.path/'configs/c.1/ncm.usb0'
        link.unlink()
        link.symlink_to(self.gadget.path/'functions/missing')
        self.gadget.writes.clear()
        with self.assertRaises(module.Refused):
            self.gadget.ensure()
        self.assertEqual(self.gadget.writes, [])

    def test_multiple_controllers_require_board_choice(self):
        self.add_controller()
        (self.gadget.controllers/'another-synthetic-udc').mkdir()
        with self.assertRaises(module.Refused):
            self.gadget.ensure()
        self.assertEqual(self.gadget.writes, [])

    def test_bound_mac_mismatch_preserved(self):
        self.add_controller()
        self.gadget.ensure()
        (self.gadget.path/'functions/ncm.usb0/dev_addr').write_text('02:99:99:99:99:99\n')
        self.gadget.writes.clear()
        with self.assertRaises(module.Refused):
            self.gadget.ensure()
        self.assertEqual(self.gadget.writes, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
