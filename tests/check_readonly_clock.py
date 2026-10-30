#!/usr/bin/python3
"""Counter calibration tests. Never change the host clock or write RTC hardware."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

source = Path(__file__).resolve().parents[1]/'platform/omarchy-apollo-clock'
loader = importlib.machinery.SourceFileLoader('apollo_clock', str(source))
spec = importlib.util.spec_from_loader(loader.name, loader)
clock = importlib.util.module_from_spec(spec); loader.exec_module(clock)
NAME = 'rtc-pm8xxx fixture'
UTC = 1793360000


class ClockTests(unittest.TestCase):
    def test_shutdown_time_advances_without_network(self):
        self.assertEqual(clock.predict(clock.calibration(100, UTC, NAME), 3700, NAME), UTC+3600)

    def test_counter_reset_refused(self):
        with self.assertRaises(ValueError): clock.predict(clock.calibration(100, UTC, NAME), 99, NAME)

    def test_counter_wrap_refused(self):
        with self.assertRaises(ValueError): clock.predict(clock.calibration(0xffffffff, UTC, NAME), 1, NAME)

    def test_stale_calibration_refused(self):
        with self.assertRaises(ValueError): clock.predict(clock.calibration(1, UTC, NAME), clock.MAX_AGE+2, NAME)

    def test_changed_device_refused(self):
        with self.assertRaises(ValueError): clock.predict(clock.calibration(100, UTC, NAME), 101, NAME+'2')

    def test_unknown_format_refused(self):
        with self.assertRaises(ValueError): clock.predict({'version': 2}, 1, NAME)

    def test_invalid_types_and_ranges_refused(self):
        for raw, epoch in [(True, UTC), (1.1, UTC), (-1, UTC), (2**32, UTC), (1, 0), (1, clock.MAX_EPOCH), (1, '2026')]:
            with self.subTest(raw=raw, epoch=epoch), self.assertRaises(ValueError): clock.calibration(raw, epoch, NAME)

    def test_wrong_driver_refused(self):
        with self.assertRaises(ValueError): clock.calibration(1, UTC, 'different-rtc')

    def test_epoch_overflow_refused(self):
        with self.assertRaises(ValueError): clock.predict(clock.calibration(1, clock.MAX_EPOCH-1, NAME), 2, NAME)

    def test_private_atomic_state_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(clock, 'STATE', Path(directory)/'clock'):
            clock.trusted_directory()
            record=clock.calibration(10, UTC, NAME); clock.save_record(record)
            self.assertEqual(clock.read_record(), record)
            self.assertEqual((clock.STATE/'calibration.json').stat().st_mode & 0o777, 0o600)

    def test_symlink_state_refused(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(clock, 'STATE', Path(directory)/'clock'):
            clock.trusted_directory(); target=Path(directory)/'other'; target.write_text('{}')
            (clock.STATE/'calibration.json').symlink_to(target)
            with self.assertRaises(OSError): clock.read_record()

    def test_world_readable_state_refused(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(clock, 'STATE', Path(directory)/'clock'):
            clock.trusted_directory(); file=clock.STATE/'calibration.json'; file.write_text('{}'); file.chmod(0o644)
            with self.assertRaises(ValueError): clock.read_record()


if __name__ == '__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ClockTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'checks_passed': result.testsRun-len(result.failures)-len(result.errors), 'clock_changed': False, 'hardware_written': False}))
    raise SystemExit(not result.wasSuccessful())
