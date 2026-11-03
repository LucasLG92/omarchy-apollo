# SPDX-License-Identifier: MIT
from test_support import TEST_BASE, bootstrap_parent
from pathlib import Path
import importlib.util,importlib.machinery,json,subprocess,sys,tempfile,types,unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;BASE=TEST_BASE
WORK=Path(tempfile.mkdtemp(prefix='atomic-integration-tests-',dir=BASE))
def module(name,path):
 loader=importlib.machinery.SourceFileLoader(name,str(path));spec=importlib.util.spec_from_loader(name,loader)
 value=importlib.util.module_from_spec(spec);sys.modules[name]=value;loader.exec_module(value);return value
b=module('review_mobile_bridge',HERE/'runtime/mobile_bridge.py')
a=module('review_mobile_adapter',HERE/'integration/omamobile-update')
class BridgeTests(unittest.TestCase):
 def setUp(self):
  self.cap=WORK/'cap';self.registry=WORK/'registry';self.cap.unlink(missing_ok=True);self.registry.unlink(missing_ok=True)
  b.CAPABILITY=self.cap;b.REGISTRY=self.registry
 def test_inactive_until_boot_capability(self):
  self.assertFalse(b.active());self.cap.write_text('apollo-versioned-usr-1\n');self.assertTrue(b.active())
 def test_writable_boot_capability_rejected(self):
  self.cap.write_text('x');self.cap.chmod(0o666);self.assertFalse(b.active())
 def test_missing_release_yields_no_updates(self):self.assertEqual(b.available(),[])
 def test_unsigned_writable_registry_rejected(self):
  self.registry.write_text(json.dumps({'schema':1,'updates':['x']}));self.registry.chmod(0o666);self.assertEqual(b.available(),[])
 def test_public_registry_is_bounded(self):
  self.registry.write_text(json.dumps({'schema':1,'updates':['valid',1,'x'*600]}));self.assertEqual(b.available(),['valid'])
 def test_adapter_legacy_behavior_retained(self):
  with patch.object(a,'transactional_bridge',return_value=None),patch.object(a,'apollo_update_blocker',return_value='legacy-policy'),\
   patch.object(a,'battery',return_value={'present':False}),patch.object(a,'battery_blocker',return_value=''),\
   patch.object(a,'repository_order',return_value=''),patch.object(a,'installed_version',return_value='x'),\
   patch.object(a,'running',return_value=False),patch.object(a,'credential',return_value={}),patch.object(a,'patch_summary',return_value={}):
   self.assertEqual(a.check()['blockers'],['legacy-policy'])
 def test_adapter_routes_new_boot_to_new_backend(self):
  sentinel={'apollo_transactional':True};bridge=types.SimpleNamespace(check=lambda adapter,offline:sentinel)
  with patch.object(a,'transactional_bridge',return_value=bridge):self.assertIs(a.check(),sentinel)
 def test_authenticated_update_uses_generation_command(self):
  bridge=types.SimpleNamespace(check=lambda adapter:{'ok':True})
  with patch.object(a,'transactional_bridge',return_value=bridge),patch.object(a.threading,'Thread'),\
   patch.object(a,'RUNTIME',str(WORK/'mobile-runtime')),patch.object(a.subprocess,'run',return_value=types.SimpleNamespace(returncode=0)) as run:
   self.assertEqual(a.inner([]),0)
   self.assertIn([a.SUDO,'-n','/usr/bin/apollo-system-update','apply-registered'],[v.args[0] for v in run.call_args_list])
   self.assertTrue(json.loads((WORK/'mobile-runtime/restart.json').read_text())['needs_reboot'])
 def test_auth_failure_never_prepares_generation(self):
  with patch.object(a.subprocess,'run',return_value=types.SimpleNamespace(returncode=1)) as run:
   self.assertEqual(a.inner([]),3);self.assertEqual(len(run.call_args_list),1)


if __name__ == '__main__':
    unittest.main()
