import hashlib
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.util.spec_from_file_location('zr_validator_looprd', ROOT / 'tools' / 'validate.py')
validate = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(validate)


class LooprdLinkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copy2(ROOT / 'examples' / 'looprd.yaml', self.root / 'looprd.yaml')
        self.link = json.loads((ROOT / 'examples' / 'ziprunner.looprd.json').read_text())

    def tearDown(self):
        self.temp.cleanup()

    def check(self, link=None):
        return validate.validate_looprd_link(link or self.link, root=self.root, expected_project='example-project')

    def test_valid_link(self):
        self.assertEqual([],self.check())

    def test_wrong_project(self):
        self.link['project']='wrong'
        self.assertTrue(any('project mismatch' in x for x in self.check()))

    def test_wrong_component_id(self):
        self.link['component']='UPPER'
        self.assertTrue(self.check())

    def test_bad_yaml_hash(self):
        self.link['specification_sha256']='0'*64
        self.assertTrue(any('SHA-256 mismatch' in x for x in self.check()))

    def test_missing_yaml(self):
        (self.root/'looprd.yaml').unlink()
        self.assertTrue(any('cannot read' in x for x in self.check()))

    def test_traversal(self):
        self.link['specification']='../other.yaml'
        self.assertTrue(any('unsafe path' in x for x in self.check()))

    def test_absolute_path(self):
        self.link['specification']='/etc/passwd'
        self.assertTrue(any('unsafe path' in x for x in self.check()))

    def test_extra_fields_cannot_be_secrets(self):
        self.link['token']='secret'
        self.assertTrue(any('unsupported field' in x for x in self.check()))

    def test_oversized_yaml(self):
        (self.root/'looprd.yaml').write_bytes(b'x'*(1024*1024+1))
        self.assertTrue(any('exceeds upstream' in x for x in self.check()))

    def test_linked_yaml_symlink_is_rejected(self):
        (self.root/'looprd.yaml').unlink()
        (self.root/'target.yaml').write_text('apiVersion: looprd/v1')
        try:
            (self.root/'looprd.yaml').symlink_to(self.root/'target.yaml')
        except OSError:
            self.skipTest('symlinks unavailable')
        self.assertTrue(any('symlink' in x for x in self.check()))

    def test_archive_package_with_optional_link(self):
        import zipfile
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'fixture.zip'
            with zipfile.ZipFile(path,'w') as z:
                for name in ('ziprunner-manifest.json','project.zr','ziprunner-workboard-update.example.json'):
                    src=ROOT/'examples'/name
                    dest='.ziprunner-workboard-update.json' if name.startswith('ziprunner-workboard') else name
                    z.write(src,dest)
                z.write(ROOT/'examples'/'evidence/EX-100-static-check.txt','evidence/EX-100-static-check.txt')
                z.write(ROOT/'examples'/'looprd.yaml','looprd.yaml')
                z.write(ROOT/'examples'/'ziprunner.looprd.json','ziprunner.looprd.json')
            self.assertEqual([],validate.inspect_archive(path,'example-project'))
            self.link['specification_sha256']='0'*64
            with zipfile.ZipFile(path,'a') as z:
                z.writestr('unrelated.txt','hi')
                # replace link with new archive below to avoid duplicate ZIP entries
            path2=Path(temp)/'modified.zip'
            with zipfile.ZipFile(path) as input_z, zipfile.ZipFile(path2,'w') as output_z:
                for info in input_z.infolist():
                    content=json.dumps(self.link).encode() if info.filename=='ziprunner.looprd.json' else input_z.read(info.filename)
                    output_z.writestr(info.filename,content)
            self.assertTrue(any('Looprd specification SHA-256 mismatch' in x for x in validate.inspect_archive(path2,'example-project')))

    def test_no_looprd_required_on_normal_package(self):
        self.assertNotIn('ziprunner.looprd.json', ['.ziprunner-workboard-update.json','ziprunner-manifest.json'])


if __name__ == '__main__':
    unittest.main()
