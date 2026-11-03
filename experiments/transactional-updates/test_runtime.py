# SPDX-License-Identifier: MIT
from test_support import TEST_BASE, bootstrap_parent
#!/usr/bin/env python3
"""Selector and signed-cohort edge cases using private synthetic data only."""
from pathlib import Path
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
BASE=TEST_BASE
spec=importlib.util.spec_from_file_location('apollo_updates',HERE/'runtime/apollo_updates.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
WORK=Path(tempfile.mkdtemp(prefix='update-runtime-review-',dir=BASE))
SELECTOR=WORK/'selector'
subprocess.run(['gcc','-static','-O2','-Wall','-Wextra','-Werror',str(HERE/'runtime/selector.c'),'-o',str(SELECTOR)],check=True)

def command(*args,ok=True):
    r=subprocess.run([str(SELECTOR),*map(str,args)],capture_output=True,text=True)
    if ok and r.returncode:raise AssertionError(r.stderr)
    if not ok and not r.returncode:raise AssertionError('unexpected success')
    return r.stdout.strip().splitlines()

def ready(store,name,kernel=None):
    p=store/'deployments'/name;p.mkdir(parents=True,mode=0o700)
    for d in ('usr','opt','pacman-local'):(p/d).mkdir()
    (p/'ready-v1').write_text(f'APOLLO_DEPLOYMENT_1\n{name}\n{kernel or os.uname().release}\n'+64*'a'+'\n')
    return p

class SelectorTests(unittest.TestCase):
    def setUp(self):
        self.store=Path(tempfile.mkdtemp(dir=WORK));ready(self.store,'a');ready(self.store,'b')
        command(self.store,'init');command(self.store,'seed','a')
    def state(self):return dict(zip(('good','previous','trial','tries','launched','token','failures','sequence'),command(self.store,'status')))
    def select(self):return command(self.store,'select')
    def test_trials_fall_back_after_two_boots(self):
        command(self.store,'queue','b',1)
        self.assertEqual([self.select()[0] for _ in range(3)],['b','b','a'])
    def test_bless_promotes_and_remembers_previous(self):
        command(self.store,'queue','b',1);i,t=self.select();command(self.store,'bless',i,t)
        self.assertEqual((self.state()['good'],self.state()['previous']),('b','a'))
    def test_stale_proof_rejected(self):
        command(self.store,'queue','b',1);i,t=self.select();self.select()
        command(self.store,'bless',i,t,ok=False)
    def test_wrong_token_rejected(self):
        i,t=self.select();command(self.store,'bless',i,'a'*64,ok=False)
    def test_successful_bless_cannot_be_replayed(self):
        i,t=self.select();command(self.store,'bless',i,t);command(self.store,'bless',i,t,ok=False)
    def test_repeated_failure_of_good_escapes_to_legacy(self):
        self.assertEqual([self.select()[0] for _ in range(3)],['a','a','-'])
    def test_bless_resets_failure_count(self):
        self.select();i,t=self.select();command(self.store,'bless',i,t)
        self.assertEqual(self.state()['failures'],'0')
    def test_missing_candidate_never_launched(self):
        command(self.store,'queue','b',1);(self.store/'deployments/b/ready-v1').unlink()
        self.assertEqual(self.select()[0],'a')
    def test_foreign_kernel_never_queued(self):
        ready(self.store,'foreign','different-kernel');command(self.store,'queue','foreign',1,ok=False)
    def test_incomplete_generation_never_queued(self):
        (self.store/'deployments/b/pacman-local').rmdir();command(self.store,'queue','b',1,ok=False)
    def test_nonmonotonic_sequence_rejected(self):
        command(self.store,'queue','b',3);i,t=self.select();command(self.store,'bless',i,t)
        command(self.store,'queue','a',3,ok=False)
    def test_rollback_requires_previous_healthy_generation(self):
        command(self.store,'rollback',ok=False)
        command(self.store,'queue','b',1);i,t=self.select();command(self.store,'bless',i,t)
        command(self.store,'rollback');self.assertEqual(self.select()[0],'a')
    def test_rollback_is_pending_until_health_accepts_it(self):
        command(self.store,'queue','b',1);i,t=self.select();command(self.store,'bless',i,t)
        command(self.store,'rollback');self.assertEqual((self.state()['good'],self.state()['trial']),('b','a'))
        i,t=self.select();command(self.store,'bless',i,t);self.assertEqual(self.state()['good'],'a')
    def test_failed_rollback_returns_to_current_good(self):
        command(self.store,'queue','b',1);i,t=self.select();command(self.store,'bless',i,t)
        command(self.store,'rollback');self.assertEqual([self.select()[0] for _ in range(3)],['a','a','b'])
    def test_symlinked_state_rejected(self):
        p=self.store/'state-v1';p.rename(self.store/'other');p.symlink_to('other');command(self.store,'select',ok=False)
    def test_group_writable_state_rejected(self):
        (self.store/'state-v1').chmod(0o620);command(self.store,'select',ok=False)
    def test_symlinked_deployment_rejected(self):
        d=self.store/'deployments';(d/'b').rename(d/'other');(d/'b').symlink_to('other');command(self.store,'queue','b',1,ok=False)
    def test_trailing_state_data_rejected(self):
        with (self.store/'state-v1').open('a') as f:f.write('extra\n')
        command(self.store,'select',ok=False)
    def test_state_is_never_executed(self):
        marker=self.store/'EXECUTED';(self.store/'state-v1').write_text('$(touch '+str(marker)+')\n')
        command(self.store,'select',ok=False);self.assertFalse(marker.exists())
    def test_double_initialization_rejected(self):command(self.store,'init',ok=False)
    def test_pending_boot_cannot_be_overwritten(self):
        self.select();command(self.store,'queue','b',1,ok=False)
    def test_64_character_identifier_roundtrip(self):
        name='x'*64;ready(self.store,name);command(self.store,'queue',name,1)
        i,t=self.select();self.assertEqual(i,name);command(self.store,'bless',i,t)
    def test_v2_requires_adapter_metadata(self):
        path=self.store/'deployments/b/ready-v1';path.write_text(path.read_text().replace('APOLLO_DEPLOYMENT_1','APOLLO_DEPLOYMENT_2'))
        command(self.store,'queue','b',1,ok=False)
    def test_v2_with_adapter_metadata_can_boot(self):
        path=self.store/'deployments/b/ready-v1';path.write_text(path.read_text().replace('APOLLO_DEPLOYMENT_1','APOLLO_DEPLOYMENT_2'))
        (self.store/'deployments/b/adapter-state').mkdir();command(self.store,'queue','b',1)
        self.assertEqual(self.select()[0],'b')
    def test_initial_baseline_refresh_is_atomic_state_change(self):
        command(self.store,'reseed','b');self.assertEqual((self.state()['good'],self.state()['previous']),('b','a'))
    def test_baseline_refresh_forbidden_after_updates(self):
        command(self.store,'queue','b',1);i,t=self.select();command(self.store,'bless',i,t)
        command(self.store,'reseed','a',ok=False)

class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.work=Path(tempfile.mkdtemp(dir=WORK));self.manifest=self.work/'release.json';self.keyring=self.work/'public.gpg'
        self.keyring.write_bytes(b'synthetic-public-key')
        package=self.work/'fixture-2-1-any.pkg.tar.zst';package.write_bytes(b'synthetic-package-not-executable')
        Path(str(package)+'.sig').write_bytes(b'synthetic-signature')
        Path(str(self.manifest)+'.sig').write_bytes(b'synthetic-signature')
        self.data={'schema':'apollo-system-release-1','id':'test-2','sequence':1,'device':'xiaomi,apollo',
            'kernel':os.uname().release,'config_abi':'apollo-shared-etc-1','packages':[{'name':'fixture','from_version':'1-1',
            'version':'2-1','file':package.name,'bytes':package.stat().st_size,'sha256':m.digest(package)}]}
        self.verifier=lambda args:'[GNUPG:] VALIDSIG '+m.KEY+' test\n'
    def load(self):
        self.manifest.write_text(json.dumps(self.data));return m.read_manifest(self.manifest,self.verifier,self.keyring)
    def test_valid_schema_and_artifact(self):self.assertEqual(self.load()['id'],'test-2')
    def test_wrong_signer_rejected(self):
        self.verifier=lambda args:'[GNUPG:] VALIDSIG '+64*'a'+' test\n'
        with self.assertRaises(RuntimeError):self.load()
    def test_path_traversal_rejected(self):
        self.data['packages'][0]['file']='../escape.pkg.tar.zst'
        with self.assertRaises(RuntimeError):self.load()
    def test_duplicate_package_rejected(self):
        self.data['packages']*=2
        with self.assertRaises(RuntimeError):self.load()
    def test_tampered_package_rejected(self):
        (self.work/self.data['packages'][0]['file']).write_bytes(b'modified')
        with self.assertRaises(RuntimeError):self.load()
    def test_unknown_config_migration_rejected(self):
        self.data['config_abi']='unknown'
        with self.assertRaises(RuntimeError):self.load()
    def test_foreign_device_rejected(self):
        self.data['device']='other'
        with self.assertRaises(RuntimeError):self.load()
    def test_boolean_sequence_rejected(self):
        self.data['sequence']=True
        with self.assertRaises(RuntimeError):self.load()
    def test_symlink_artifact_rejected(self):
        path=self.work/self.data['packages'][0]['file'];path.rename(self.work/'real');path.symlink_to('real')
        with self.assertRaises(RuntimeError):self.load()
    def test_conflicting_json_keys_rejected(self):
        self.manifest.write_text('{"schema":1,"schema":2}')
        with self.assertRaises(RuntimeError):m.read_manifest(self.manifest,self.verifier,self.keyring)
    def test_oversized_manifest_rejected(self):
        self.manifest.write_bytes(b'x'*(1024**2+1))
        with self.assertRaises(RuntimeError):m.read_manifest(self.manifest,self.verifier,self.keyring)
    def test_null_from_version_supports_new_packages(self):
        self.data['packages'][0]['from_version']=None;self.assertIsNone(self.load()['packages'][0]['from_version'])


if __name__ == '__main__':
    unittest.main()
