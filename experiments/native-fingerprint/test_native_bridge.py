"""Authentication gate regression tests; no TEE/device/mock match activation."""
from pathlib import Path
import importlib.util,itertools,json
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('bridge',HERE/'native-bridge.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
count=0
for status,cancel,identity,ok,clean,exported,matched in itertools.product((0,1,-1),(False,True),(False,True),(None,False,True,'yes'),(None,False,True),(None,False,True),(None,False,True,'yes')):
 row={'ok':ok,'hardware_cleanup_succeeded':clean,'biometric_bytes_exported':exported,'matched':matched}
 result=b.decision(status,row,cancel,identity,123)
 should_match=status==0 and not cancel and identity and ok is True and clean is True and exported is False and matched is True
 assert (result=='MATCH 123')==should_match
 if cancel:assert result=='ERROR 5'
 count+=1
for value in (None,[],True,'MATCH 123'):
 assert b.decision(0,value,False,True,123)=='ERROR 2';count+=1
result={'ok':True,'authentication_decision_cases':count,'success_requires_exact_native_result_cleanup_and_same_record':True,'cancellation_wins_over_late_match':True,'real_hardware_or_credentials_used':False}
(HERE/'native-bridge-test-proof.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
