from pathlib import Path
import copy,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pkg/usr/lib/apollo'))
from firstboot_profile import validate_profile
from firstboot_engine import Engine,FirstbootError
from test_backend import FakeOperations
P=dict(schema=1,display_name='Persona de prueba',hostname='apollo-test',locale='es_ES.UTF-8',timezone='Europe/Madrid',keyboard='es',apps=[])
class ProfileOps(FakeOperations):
 def verify_profile_supported(self,p):self.events.append('profile-supported')
 def apply_profile(self,account,p):
  self.events.append('apply-profile')
  if getattr(self,'fail_profile',False):raise FirstbootError('PROFILE_APPLY_FAILED')
  self.applied=copy.deepcopy(p)
class Tests(unittest.TestCase):
 def test_exact_profile(self):self.assertEqual(validate_profile(P),P)
 def test_reject_untrusted_input(self):
  for key,value in [('hostname','-bad'),('hostname','a;id'),('display_name','bad:name'),('display_name','bad\ud800'),('timezone','Europe/../../etc'),('locale',[]),('keyboard','$(id)'),('apps',['not.an.allowed.App']),('apps',['org.gnome.Maps']*2)]:
   candidate={**P,key:value}
   with self.subTest(key=key),self.assertRaises(ValueError):validate_profile(candidate)
 def test_profile_before_owner_commit(self):
  ops=ProfileOps();self.assertEqual(Engine(ops).configure('alice','Synthetic9!',lambda:None,P),'configured')
  self.assertEqual(ops.applied,P);self.assertEqual(ops.record['schema'],2)
  self.assertLess(ops.events.index('apply-profile'),ops.events.index('ready'))
 def test_profile_failure_resumes_without_password_reset(self):
  ops=ProfileOps();ops.fail_profile=True;engine=Engine(ops)
  with self.assertRaises(FirstbootError):engine.configure('alice','Synthetic9!',lambda:None,P)
  self.assertEqual(engine.state(),'finish-pending');self.assertFalse(ops.ready)
  ops.fail_profile=False;engine.configure('','',lambda:None)
  self.assertEqual(len(ops.password_calls),1);self.assertEqual(ops.applied,P)
 def test_invalid_profile_creates_no_account(self):
  ops=ProfileOps()
  with self.assertRaises(FirstbootError):Engine(ops).configure('alice','Synthetic9!',lambda:None,{**P,'hostname':'../bad'})
  self.assertIsNone(ops.account);self.assertEqual(ops.password_calls,[])
 def test_existing_owner_refused(self):
  ops=ProfileOps();ops.ready=True
  with self.assertRaises(FirstbootError):Engine(ops).configure('alice','Synthetic9!',lambda:None,P)
  self.assertFalse(hasattr(ops,'applied'))
