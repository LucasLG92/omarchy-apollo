# SPDX-License-Identifier: MIT
from test_support import TEST_BASE, bootstrap_parent
from pathlib import Path
import importlib.util,json,os,tempfile,unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;BASE=TEST_BASE
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=load('updates_pending_test',HERE/'runtime/apollo_updates.py')
g=load('pending_guard_test',HERE/'runtime/pending_guard.py')
WORK=Path(tempfile.mkdtemp(prefix='pending-guard-tests-',dir=BASE))
class Tests(unittest.TestCase):
 def setUp(self):
  self.root=Path(tempfile.mkdtemp(dir=WORK));self.db=self.root/'var/lib/pacman/local'
  self.db.mkdir(parents=True);(self.db/'metadata').write_text('installed-package-1\n')
  (self.root/'var/lib/apollo').mkdir()
  self.store=self.root/'var/lib/apollo/system-versions';self.engine=m.Engine(self.root,self.store,Path('/unused'))
  self.engine.setup();self.dep=self.store/'deployments/test';self.dep.mkdir()
  (self.dep/'base-database.sha256').write_text(m.database_digest(self.root)+'\n')
  self.cap=self.root/'cap';self.cap.write_text('apollo-versioned-usr-1\n')
 def queue(self):
  def selector(*args):
   self.assertTrue((self.root/'var/lib/pacman/db.lck').exists());return []
  with patch.object(m,'BOOT_CONTRACT',self.cap),patch.object(m,'REGISTRY',self.root/'registry'),\
   patch.object(m,'read_manifest',return_value={'id':'test','sequence':1}),patch.object(self.engine,'call_selector',selector):
   return self.engine.queue('test')
 def test_unchanged_database_allows_queue_under_ALPM_lock(self):
  self.assertEqual(self.queue()['pending'],'test');self.assertFalse((self.root/'var/lib/pacman/db.lck').exists())
 def test_installed_app_after_preparation_invalidates_candidate(self):
  (self.db/'another-package').write_text('new-app\n')
  with self.assertRaisesRegex(RuntimeError,'paquetes instalados cambiaron'):self.queue()
  self.assertFalse((self.root/'var/lib/pacman/db.lck').exists())
 def test_reinstall_metadata_change_invalidates_candidate(self):
  (self.db/'metadata').write_text('installed-package-2\n')
  with self.assertRaises(RuntimeError):self.queue()
 def test_reading_metadata_does_not_invalidate(self):
  (self.db/'metadata').read_text();self.assertEqual(self.queue()['pending'],'test')
 def test_steady_state_allows_native_package_operations(self):
  self.assertFalse(g.pending(['a','b','-','0','-','-','0','3']))
 def test_queued_generation_blocks_changes(self):
  self.assertTrue(g.pending(['a','b','trial','2','-','-','0','3']))
 def test_unconfirmed_boot_blocks_changes(self):
  self.assertTrue(g.pending(['a','b','-','0','a','f'*64,'0','3']))
 def test_corrupt_selector_output_is_not_silently_accepted(self):
  with self.assertRaises(RuntimeError):g.pending(['invalid'])

if __name__ == '__main__':
    unittest.main()
