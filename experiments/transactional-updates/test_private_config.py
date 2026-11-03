# SPDX-License-Identifier: MIT
from test_support import TEST_BASE, bootstrap_parent
from pathlib import Path
import importlib.util,json,stat,tempfile,unittest
HERE=Path(__file__).resolve().parent;BASE=TEST_BASE
spec=importlib.util.spec_from_file_location('private_config_review',HERE/'runtime/apollo_updates.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
WORK=Path(tempfile.mkdtemp(prefix='private-config-tests-',dir=BASE))
class Tests(unittest.TestCase):
 def setUp(self):
  self.root=Path(tempfile.mkdtemp(dir=WORK));(self.root/'etc').mkdir()
  self.path=self.root/'etc/pacman.conf';self.original=b'[options]\nSigLevel = Required\nDownloadUser = alpm\n'
  self.path.write_bytes(self.original);self.path.chmod(0o640)
 def test_override_is_private_and_signature_policy_retained(self):
  with m.private_download_config(self.root):
   body=self.path.read_bytes();self.assertNotIn(b'DownloadUser = alpm',body);self.assertIn(b'SigLevel = Required',body)
  self.assertEqual(self.path.read_bytes(),self.original);self.assertEqual(stat.S_IMODE(self.path.stat().st_mode),0o640)
 def test_transaction_failure_restores_original(self):
  with self.assertRaisesRegex(RuntimeError,'fixture-failure'):
   with m.private_download_config(self.root):raise RuntimeError('fixture-failure')
  self.assertEqual(self.path.read_bytes(),self.original)
 def test_required_config_migration_is_rejected(self):
  with self.assertRaises(RuntimeError):
   with m.private_download_config(self.root):self.path.write_text('changed-by-package\n')
  self.assertEqual(self.path.read_bytes(),self.original)
 def test_symlink_cannot_redirect_restore_to_outside_file(self):
  outside=self.root/'outside-canary';outside.write_text('unchanged\n')
  with self.assertRaises((OSError,RuntimeError)):
   with m.private_download_config(self.root):self.path.unlink();self.path.symlink_to(outside)
  self.assertEqual(outside.read_text(),'unchanged\n');self.assertFalse(self.path.is_symlink());self.assertEqual(self.path.read_bytes(),self.original)
 def test_replaced_parent_cannot_redirect_restore(self):
  outside=self.root/'outside';outside.mkdir();(outside/'pacman.conf').write_text('unchanged\n')
  moved=self.root/'saved-private-etc'
  with self.assertRaises(RuntimeError):
   with m.private_download_config(self.root):(self.root/'etc').rename(moved);(self.root/'etc').symlink_to(outside)
  self.assertEqual((outside/'pacman.conf').read_text(),'unchanged\n');self.assertEqual((moved/'pacman.conf').read_bytes(),self.original)

if __name__ == '__main__':
    unittest.main()
