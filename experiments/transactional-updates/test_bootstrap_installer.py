# SPDX-License-Identifier: MIT
from test_support import TEST_BASE, bootstrap_parent
"""Check additive absent-package support in the signed bootstrap installer."""
from pathlib import Path
import hashlib,importlib.util,importlib.machinery,json,subprocess,tempfile,types,unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
loader=importlib.machinery.SourceFileLoader('bootstrap_review',str(HERE/'integration/apollo-install-release'))
spec=importlib.util.spec_from_loader(loader.name,loader);m=importlib.util.module_from_spec(spec);loader.exec_module(m)
PARENT=bootstrap_parent()
class Tests(unittest.TestCase):
 def setUp(self):
  self.work=Path(tempfile.mkdtemp(prefix='apollo-bootstrap-fixture-',dir=PARENT))
  self.pub=self.work/'pub.gpg';self.pub.write_bytes(b'synthetic-public-key');m.PUB=self.pub
  self.manifest=self.work/'release.json';self.package=self.work/'apollo-fixture-1-1-any.pkg.tar.zst'
  self.package.write_bytes(b'synthetic-package');Path(str(self.package)+'.sig').write_bytes(b'signature')
  Path(str(self.manifest)+'.sig').write_bytes(b'signature')
  self.data={'schema':1,'kernel':__import__('os').uname().release,'expected_current':{'apollo-fixture':None},
   'packages':[{'name':'apollo-fixture','version':'1-1','file':self.package.name,'sha256':hashlib.sha256(self.package.read_bytes()).hexdigest()}]}
 def validate(self,code=1,output=''):
  self.manifest.write_text(json.dumps(self.data))
  def run(args,timeout=30):
   if args[0]=='gpgv':return '[GNUPG:] VALIDSIG '+m.KEY+' test\n'
   if args[:2]==['pacman','-Qp']:return 'apollo-fixture 1-1\n'
   if args[0]=='pacman-key':return ''
   if '--print' in args:return 'apollo-fixture 1-1\n'
   raise AssertionError(args)
  original=m.Path.is_file
  def is_file(path):
   if str(path)=='/etc/apollo/native-root-v1':return True
   return original(path)
  with patch.object(m,'run',run),patch.object(m.subprocess,'run',return_value=types.SimpleNamespace(returncode=code,stdout=output)),\
   patch.object(m.Path,'is_file',is_file):return m.validate(self.manifest)
 def test_new_package_absent_allowed(self):self.assertEqual(len(self.validate()[1]),1)
 def test_query_error_is_not_absent(self):
  with self.assertRaises(RuntimeError):self.validate(2)
 def test_existing_package_cannot_claim_absent(self):
  with self.assertRaises(RuntimeError):self.validate(0,'apollo-fixture 1-1\n')
 def test_exact_old_version_still_required(self):
  self.data['expected_current']['apollo-fixture']='0-1';self.assertEqual(len(self.validate(0,'apollo-fixture 0-1\n')[1]),1)
 def test_wrong_old_version_rejected(self):
  self.data['expected_current']['apollo-fixture']='0-1'
  with self.assertRaises(RuntimeError):self.validate(0,'apollo-fixture 9-1\n')
 def test_untyped_old_version_rejected(self):
  self.data['expected_current']['apollo-fixture']=4
  with self.assertRaises(RuntimeError):self.validate()

if __name__ == '__main__':
    unittest.main()
