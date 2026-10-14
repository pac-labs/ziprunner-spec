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

class WorkboardTests(unittest.TestCase):
    def setUp(self):
        self.board=json.loads((ROOT/'examples/ziprunner-workboard-update.example.json').read_text())

    def test_valid_reference(self):
        self.assertEqual([],zr.validate_workboard(self.board,expected_project='example-project',expected_version='1.2.3'))

    def test_empty_implemented(self):
        self.board['implemented']=[]
        self.assertIn('too few items',str(zr.validate_workboard(self.board)))

    def test_remaining_must_be_explicit(self):
        del self.board['remaining']
        self.assertIn('missing remaining',str(zr.validate_workboard(self.board)))

    def test_wrong_schema_spelling(self):
        self.board['schema']='ziprunner.workboard-update/v1'
        self.assertIn('schema must be exactly',str(zr.validate_workboard(self.board)))

    def test_wrong_target(self):
        self.assertIn('workboard project mismatch',str(zr.validate_workboard(self.board,expected_project='other')))

    def test_wrong_version(self):
        self.assertIn('workboard version mismatch',str(zr.validate_workboard(self.board,expected_version='9.9.9')))

    def test_duplicate_task_id_cross_array(self):
        self.board['remaining'][0]['id']=self.board['implemented'][0]['id']
        self.assertIn('duplicate task id',str(zr.validate_workboard(self.board)))

    def test_invalid_task_id(self):
        for ident in ('-bad','x/y','x y','x\\y',':bad'):
            with self.subTest(ident=ident):
                self.board['implemented'][0]['id']=ident
                self.assertIn('invalid task id',str(zr.validate_workboard(self.board)))

    def test_blank_operator_checks(self):
        self.board['implemented'][0]['operator_checks']=['  ']
        self.assertIn('invalid operator_checks text',str(zr.validate_workboard(self.board)))

    def test_invalid_priority(self):
        self.board['remaining'][0]['priority']='urgent'
        self.assertIn('invalid priority',str(zr.validate_workboard(self.board)))

    def test_official_v1_reference_example(self):
        reference=json.loads((ROOT/'examples/ziprunner-workboard-update.reference.json').read_text())
        self.assertEqual([],zr.validate_workboard(reference,expected_project='YOUR-PROJECT-KEY'))

    def test_official_field_limit(self):
        self.board['implemented'][0]['title']='X'*241
        self.assertIn('max 240',str(zr.validate_workboard(self.board)))

    def test_official_check_limit(self):
        self.board['implemented'][0]['operator_checks']=['ok']*21
        self.assertIn('1-20 operator_checks',str(zr.validate_workboard(self.board)))

    def test_official_max_items(self):
        base=self.board['implemented'][0]
        self.board['implemented']=[dict(base, id='ID-'+str(i)) for i in range(151)]
        self.assertIn('too many items',str(zr.validate_workboard(self.board)))

    def test_official_task_id_length(self):
        self.board['implemented'][0]['id']='A'*121
        self.assertIn('invalid task id',str(zr.validate_workboard(self.board)))

    def test_invalid_utf8(self):
        with self.assertRaisesRegex(ValueError,'UTF-8'):
            zr.read_workboard_bytes(b'\xff')

    def test_oversize(self):
        with self.assertRaisesRegex(ValueError,'256 KiB'):
            zr.read_workboard_bytes(b'x'*(256*1024+1))

    def test_duplicate_json_key(self):
        with self.assertRaisesRegex(ValueError,'duplicate JSON key'):
            zr.read_workboard_bytes(b'{"project":"one","project":"two"}')


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.manifest=json.loads((ROOT/'examples/ziprunner-manifest.json').read_text())
        self.recipe=(ROOT/'examples/project.zr').read_bytes()
        self.workboard=json.loads((ROOT/'examples/ziprunner-workboard-update.example.json').read_text())
        self.evidence=(ROOT/'examples/evidence/EX-100-static-check.txt').read_bytes()

    def pack(self,additional=None,manifest=None,workboard=True):
        tmp=tempfile.TemporaryDirectory()
        path=Path(tmp.name)/'test.zip'
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('ziprunner-manifest.json',json.dumps(self.manifest if manifest is None else manifest))
            z.writestr('project.zr',self.recipe)
            if workboard: z.writestr('.ziprunner-workboard-update.json',json.dumps(self.workboard))
            z.writestr('evidence/EX-100-static-check.txt',self.evidence)
            for name,content in (additional or []):z.writestr(name,content)
        return tmp,path

    def test_source_update_valid(self):
        t,path=self.pack()
        try:self.assertEqual([],zr.inspect_archive(path,'example-project'))
        finally:t.cleanup()

    def test_source_update_missing_workboard(self):
        t,path=self.pack(workboard=False)
        try:self.assertIn('missing required root-level .ziprunner-workboard-update.json',str(zr.inspect_archive(path)))
        finally:t.cleanup()

    def test_source_update_wrong_schema(self):
        self.workboard['schema']='ziprunner.workboard-update/v1'
        t,path=self.pack()
        try:self.assertIn('workboard schema must be exactly',str(zr.inspect_archive(path)))
        finally:t.cleanup()

    def test_source_update_wrong_workboard_project(self):
        self.workboard['project']='other'
        t,path=self.pack()
        try:self.assertIn('workboard project mismatch',str(zr.inspect_archive(path)))
        finally:t.cleanup()

    def test_source_update_wrong_workboard_version(self):
        self.workboard['version']='0.0.1'
        t,path=self.pack()
        try:self.assertIn('workboard version mismatch',str(zr.inspect_archive(path)))
        finally:t.cleanup()

    def test_source_update_root_only(self):
        t,path=self.pack(workboard=False,additional=[('nested/.ziprunner-workboard-update.json',json.dumps(self.workboard))])
        try:self.assertIn('missing required root-level',str(zr.inspect_archive(path)))
        finally:t.cleanup()

    def test_source_update_workboard_exceeds_limit(self):
        t,path=self.pack(workboard=False,additional=[('.ziprunner-workboard-update.json',' '* (256*1024+1))])
        try:self.assertIn('size exceeds 256 KiB',str(zr.inspect_archive(path)))
        finally:t.cleanup()

    def test_source_update_missing_supplemental_manifest_still_reports_missing_workboard(self):
        tmp=tempfile.TemporaryDirectory();path=Path(tmp.name)/'test.zip'
        with zipfile.ZipFile(path,'w') as z:z.writestr('project.zr',self.recipe)
        try:
            errs=zr.inspect_archive(path)
            self.assertIn('missing supplemental ziprunner-manifest.json',str(errs))
            self.assertIn('missing required root-level',str(errs))
        finally:tmp.cleanup()

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
            z.writestr('.ziprunner-workboard-update.json',json.dumps(self.workboard))
            z.writestr('evidence/EX-100-static-check.txt',self.evidence)
            item=zipfile.ZipInfo('link');item.create_system=3;item.external_attr=(0o120777<<16)
            z.writestr(item,'target')
        try:self.assertIn('nonregular archive entry',str(zr.inspect_archive(path)))
        finally:tmp.cleanup()

if __name__=='__main__':unittest.main()
