#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Exercise update/rollback using owned regular files, never phone partitions."""
from pathlib import Path
import importlib.util
import os
import tempfile
import unittest
from unittest.mock import patch

source = Path(__file__).resolve().parents[1]/'system/update-kernel22-to23.py'
spec = importlib.util.spec_from_file_location('apollo_boot_update', source)
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)


class BootTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='apollo-boot-fixture-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.size = 3*1024*1024+127
        self.original = bytes(range(256))*(self.size//256)+bytes(range(self.size % 256))
        self.device = self.root/'synthetic-partition'
        self.device.write_bytes(self.original)
        self.fd = os.open(self.device, os.O_RDWR)
        self.addCleanup(os.close, self.fd)
        self.image = self.root/'candidate.img'
        self.image.write_bytes(b'new-image'*180000)
        self.backup = self.root/'private-backup.img'
        self.actions = []

    def install(self):
        self.actions.append('install-new')

    def restore(self):
        self.actions.append('restore-old')

    def transact(self, install=None):
        return update.update_with_rollback(self.fd, self.image, self.backup, self.size,
                                           install or self.install, self.restore)

    def test_success_preserves_original_tail(self):
        result = self.transact()
        self.assertTrue(result['boot_write_and_readback_verified'])
        data = self.device.read_bytes()
        payload = self.image.read_bytes()
        self.assertEqual(data[:len(payload)], payload)
        self.assertEqual(data[len(payload):], self.original[len(payload):])
        self.assertEqual(self.backup.read_bytes(), self.original)
        self.assertEqual(self.actions, ['install-new'])

    def test_install_failure_never_writes_partition(self):
        def fail():
            raise RuntimeError('Synthetic package failure')
        with patch.object(update.os, 'pwrite', wraps=os.pwrite) as write:
            with self.assertRaises(RuntimeError):
                self.transact(fail)
            write.assert_not_called()
        self.assertEqual(self.device.read_bytes(), self.original)
        self.assertEqual(self.actions, ['restore-old'])

    def test_partial_write_restores_entire_partition(self):
        real = os.pwrite
        calls = 0
        def interrupted(fd, data, offset):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('Synthetic interrupted write')
            return real(fd, data, offset)
        with patch.object(update.os, 'pwrite', side_effect=interrupted):
            with self.assertRaises(OSError):
                self.transact()
        self.assertEqual(self.device.read_bytes(), self.original)
        self.assertEqual(self.actions, ['install-new', 'restore-old'])

    def test_corrupt_readback_rolls_back_tail_and_package(self):
        real = update.write_image
        def corrupted(fd, path):
            real(fd, path)
            if path == self.image:
                os.pwrite(fd, b'!', 0)
                os.fsync(fd)
        with patch.object(update, 'write_image', side_effect=corrupted):
            with self.assertRaisesRegex(OSError, 'readback mismatch'):
                self.transact()
        self.assertEqual(self.device.read_bytes(), self.original)
        self.assertEqual(self.actions, ['install-new', 'restore-old'])

    def test_mismatched_backup_is_preserved_and_refused(self):
        self.backup.write_bytes(b'other backup')
        with self.assertRaises(ValueError):
            self.transact()
        self.assertEqual(self.backup.read_bytes(), b'other backup')
        self.assertEqual(self.device.read_bytes(), self.original)
        self.assertEqual(self.actions, [])

    def test_oversized_image_is_refused_before_install(self):
        with self.image.open('wb') as stream:
            stream.truncate(self.size)
        with self.assertRaises(ValueError):
            self.transact()
        self.assertFalse(self.backup.exists())
        self.assertEqual(self.device.read_bytes(), self.original)
        self.assertEqual(self.actions, [])

    def test_short_device_read_is_an_error(self):
        with self.assertRaisesRegex(OSError, 'Short read'):
            update.digest_fd(self.fd, self.size+1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
