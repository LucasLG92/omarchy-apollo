#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Public source checks with synthetic data, no phone, TEE or PAM changes."""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,shutil,subprocess,tempfile
HERE=Path(__file__).resolve().parent
def main():
 pins=json.loads((HERE/'SOURCEPINS.json').read_text())
 for name,digest in pins['exact_development_source_files'].items():
  path=HERE/name;assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,name
  if path.suffix=='.py':ast.parse(path.read_text())
 spec=importlib.util.spec_from_file_location('apollo_public_bridge',HERE/'native-bridge.py');bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
 assert bridge.decision(0,{'ok':True,'hardware_cleanup_succeeded':True,'biometric_bytes_exported':False,'matched':True},False,True,123)=='MATCH 123'
 assert bridge.decision(0,{'ok':True,'hardware_cleanup_succeeded':True,'biometric_bytes_exported':False,'matched':True},True,True,123)=='ERROR 5'
 assert bridge.decision(0,{'ok':True,'hardware_cleanup_succeeded':False,'biometric_bytes_exported':False,'matched':True},False,True,123)=='ERROR 2'
 compiler=shutil.which('clang') or shutil.which('cc');assert compiler,'A Linux C compiler and libc/Linux headers are needed for the synthetic C checks'
 common=['bio-wire/apollo-bio.c','qsee-transport.c','apollo-auth-check.c']
 cases=[('bio-wire/test-apollo-bio.c',common),('bio-wire/test-apollo-database.c',common),('auth-wire/test-gatekeeper-wire.c',['auth-wire/gatekeeper-wire.c']),('auth-wire/test-gatekeeper-legacy.c',['auth-wire/gatekeeper-wire.c']),('auth-wire/test-rpmb-observer.c',['auth-wire/rpmb-observer.c']),('auth-wire/test-rpmb-readonly.c',['auth-wire/rpmb-observer.c','auth-wire/rpmb-readonly.c']),('auth-wire/test-rpmb-authenticated.c',['auth-wire/rpmb-observer.c','auth-wire/rpmb-readonly.c','auth-wire/rpmb-authenticated.c']),('auth-wire/test-time-listener.c',['auth-wire/time-listener.c'])]
 root_only=[('bio-wire/test-template-store.c',common),('auth-wire/test-credential-store.c',['auth-wire/credential-store.c'])]
 if os.geteuid()==0:cases+=root_only
 results=[]
 with tempfile.TemporaryDirectory(prefix='apollo-public-codec-') as directory:
  for index,(test,sources) in enumerate(cases):
   binary=Path(directory)/str(index)
   compiled=subprocess.run([compiler,'-std=gnu11','-O2','-Wall','-Wextra','-Werror',str(HERE/test),*(str(HERE/name) for name in sources),'-o',str(binary)],capture_output=True,text=True)
   if compiled.returncode:raise SystemExit(test+'\n'+compiled.stderr.replace(str(HERE),'<source>'))
   r=subprocess.run([str(binary)],capture_output=True,check=True,text=True);results.append({'test':test,'result':r.stdout.strip()})
 print(json.dumps({'ok':True,'exact_source_hashes_verified':len(pins['exact_development_source_files']),'synthetic_C_suites_passed':len(results),'root_only_suites_skipped':0 if os.geteuid()==0 else len(root_only),'results':results,'physical_device_or_PAM_operations':0},indent=2))
if __name__=='__main__':main()
