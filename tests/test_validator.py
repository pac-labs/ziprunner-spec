import copy
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import validate as zr

class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.manifest=json.loads((ROOT/'examples/ziprunner-manifest.json').read_text())
        self.available={'evidence/EX-100-static-check.txt'}

    def test_valid_example(self):
        self.assertEqual([],zr.validate_manifest(self.manifest,available=self.available,expected_project='example-project'))

    def test_unaccounted_work(self):
        self.manifest['todo_work']=[]
        self.assertIn('planned_work IDs must equal',str(zr.validate_manifest(self.manifest)))

    def test_fake_passed_without_evidence(self):
        self.manifest['validation']['checks'][0]['status']='passed'
        self.assertIn('requires evidence_ref',str(zr.validate_manifest(self.manifest)))

    def test_cannot_disable_approval(self):
        self.manifest['release']['requires_operator_approval']=False
        self.assertIn('requires_operator_approval=true',str(zr.validate_manifest(self.manifest)))

    def test_bad_reference(self):
        self.manifest['done_work'][0]['evidence'][0]['ref']='../bad.txt'
        self.assertIn('traversal',str(zr.validate_manifest(self.manifest)))

    def test_missing_actual_evidence(self):
        self.assertIn('not present',str(zr.validate_manifest(self.manifest,available=set())))

    def test_blocked_must_have_blocker(self):
        self.manifest['todo_work'][0]['blockers']=[]
        self.assertIn('blockers required',str(zr.validate_manifest(self.manifest)))

    def test_timezone_required(self):
        self.manifest['update']['created_at']='2026-10-10T10:00:00'
        self.assertIn('timezone',str(zr.validate_manifest(self.manifest)))

    def test_cross_project_rejected(self):
        self.assertIn('project.key mismatch',str(zr.validate_manifest(self.manifest,expected_project='another-project')))

    def test_path_safety(self):
        for path in ('../evil.py','C:/evil.py','/etc/passwd','sub/../evil','sub\\evil', 'CON.txt','a//b','a/b.','a:bad'):
            with self.subTest(path=path):self.assertIsNotNone(zr.archive_path_error(path))

    def test_legacy_state_example(self):
        obj=json.loads((ROOT/'examples/ziprunner.project-state.json').read_text())
        self.assertEqual('ziprunner.project-state.v1',obj['schema'])
        self.assertEqual(['EX-100','EX-110'],[x['id'] for x in obj['roadmap']])

    def test_json_schemas_parse(self):
        for file in (ROOT/'schemas').glob('*.json'):
            with self.subTest(file=file.name):
                obj=json.loads(file.read_text())
                self.assertEqual('https://json-schema.org/draft/2020-12/schema',obj['$schema'])

class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.manifest=json.loads((ROOT/'examples/ziprunner-manifest.json').read_text())
        self.recipe=(ROOT/'examples/project.zr').read_bytes()
        self.evidence=(ROOT/'examples/evidence/EX-100-static-check.txt').read_bytes()

    def pack(self,additional=None,manifest=None):
        tmp=tempfile.TemporaryDirectory()
        path=Path(tmp.name)/'test.zip'
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('ziprunner-manifest.json',json.dumps(self.manifest if manifest is None else manifest))
            z.writestr('project.zr',self.recipe)
            z.writestr('evidence/EX-100-static-check.txt',self.evidence)
            for name,content in (additional or []):z.writestr(name,content)
        return tmp,path

    def test_source_update_valid(self):
        t,path=self.pack()
        try:self.assertEqual([],zr.inspect_archive(path,'example-project'))
        finally:t.cleanup()

    def test_unsafe_zip_filename(self):
        t,path=self.pack([('../escape','x')])
        try:self.assertIn('unsafe ZIP path',str(zr.inspect_archive(path)))
        finally:t.cleanup()

    def test_config_forbidden(self):
        t,path=self.pack([('ziprunner.config.json','{}')])
        try:self.assertIn('config.json must not be shipped',str(zr.inspect_archive(path)))
        finally:t.cleanup()

    def test_mismatch(self):
        t,path=self.pack()
        try:self.assertIn('project.key mismatch',str(zr.inspect_archive(path,'not-my-project')))
        finally:t.cleanup()

    def test_progress_update_cannot_include_recipe(self):
        m=copy.deepcopy(self.manifest)
        m['update']['kind']='progress_update'
        t,path=self.pack(manifest=m)
        try:self.assertIn('progress_update cannot ship source',str(zr.inspect_archive(path)))
        finally:t.cleanup()

    def test_duplicate_casefold(self):
        t,path=self.pack([('Readme.md','ok'),('README.md','bad')])
        try:self.assertIn('case-insensitive duplicate',str(zr.inspect_archive(path)))
        finally:t.cleanup()

    def test_symlink_entry(self):
        tmp=tempfile.TemporaryDirectory();path=Path(tmp.name)/'symlink.zip'
        with zipfile.ZipFile(path,'w') as z:
            z.writestr('ziprunner-manifest.json',json.dumps(self.manifest))
            z.writestr('project.zr',self.recipe)
            z.writestr('evidence/EX-100-static-check.txt',self.evidence)
            item=zipfile.ZipInfo('link');item.create_system=3;item.external_attr=(0o120777<<16)
            z.writestr(item,'target')
        try:self.assertIn('nonregular archive entry',str(zr.inspect_archive(path)))
        finally:tmp.cleanup()

if __name__=='__main__':unittest.main()
