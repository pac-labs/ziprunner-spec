"""Reference contract regression tests; no application commands or browser sends."""
import copy
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import validate
import verification_contract as vc


class TestFunctionalPlan(unittest.TestCase):
    def setUp(self):
        self.plan=json.loads((ROOT/'examples/verification-plan.json').read_text())
        self.wb=json.loads((ROOT/'examples/ziprunner-workboard-update.example.json').read_text())

    def errs(self):
        return vc.validate_plan(self.plan, self.wb, project='example-project', version='1.2.3')

    def test_reference_valid(self):
        self.assertEqual([],self.errs())

    def test_wrong_project(self):
        self.plan['project']='other'
        self.assertIn('project does not match',str(self.errs()))

    def test_wrong_version(self):
        self.plan['version']='999'
        self.assertIn('version does not match',str(self.errs()))

    def test_missing_implemented_item(self):
        self.plan['tasks'][0]['id']='FAKE-100'
        self.assertIn('must equal delivered implemented IDs',str(self.errs()))

    def test_duplicate_task(self):
        self.plan['tasks'].append(copy.deepcopy(self.plan['tasks'][0]))
        self.assertIn('duplicate task IDs',str(self.errs()))

    def test_duplicate_check(self):
        self.plan['checks'].append(copy.deepcopy(self.plan['checks'][0]))
        self.assertIn('duplicate check IDs',str(self.errs()))

    def test_missing_check_reference(self):
        self.plan['tasks'][0]['criteria'][0]['checks']=['NOT-FOUND']
        self.assertIn('missing declared check',str(self.errs()))

    def test_wrong_kind_for_automated(self):
        self.plan['tasks'][0]['criteria'][0]['checks']=['EX-100-M1']
        self.assertIn('missing',str(self.errs()))

    def test_duplicate_criterion(self):
        self.plan['tasks'][0]['criteria'].append(copy.deepcopy(self.plan['tasks'][0]['criteria'][0]))
        self.assertIn('duplicate criterion IDs',str(self.errs()))

    def test_unlinked_check(self):
        self.plan['checks'].append({'id':'ZZZ','kind':'manual','stage':'acceptance','description':'third party','instructions':'Inspect screen'})
        self.assertIn('unlinked verification check',str(self.errs()))

    def test_no_automated_runner(self):
        del self.plan['checks'][0]['runner_ref']
        self.assertIn('trusted runner_ref',str(self.errs()))

    def test_no_assertions(self):
        self.plan['checks'][0]['assertions']=[]
        self.assertIn('feature assertions',str(self.errs()))

    def test_missing_test_implementation_ref(self):
        del self.plan['checks'][0]['test_ref']
        self.assertIn('test_ref',str(self.errs()))

    def test_unsafe_test_ref(self):
        self.plan['checks'][0]['test_ref']='../escape.py'
        self.assertIn('safe relative test_ref',str(self.errs()))

    def test_manual_instruction_required(self):
        del self.plan['checks'][1]['instructions']
        self.assertIn('manual check missing instructions',str(self.errs()))

    def test_no_shell_command_schema_field(self):
        self.plan['checks'][0]['command']='rm -rf /'
        self.assertIn('unsupported field command',str(self.errs()))

    def test_non_utf8_rejected(self):
        with self.assertRaises(ValueError):vc.parse_plan_bytes(b'\xff')

    def test_duplicate_json_key_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):
            vc.parse_plan_bytes(b'{"project":"one","project":"two"}')

    def test_oversized_plan_rejected(self):
        with self.assertRaisesRegex(ValueError,'256 KiB'):
            vc.parse_plan_bytes(b'a'*(262145))

    def test_plan_package_gate_opt_in(self):
        manifest=(ROOT/'examples/ziprunner-manifest.json').read_bytes()
        recipe=(ROOT/'examples/project.zr').read_bytes()
        wb=(ROOT/'examples/ziprunner-workboard-update.example.json').read_bytes()
        evidence=(ROOT/'examples/evidence/EX-100-static-check.txt').read_bytes()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'project.zip'
            def build(keep_plan):
                with zipfile.ZipFile(path,'w') as z:
                    for name,data in [('ziprunner-manifest.json',manifest),('project.zr',recipe),('.ziprunner-workboard-update.json',wb),('evidence/EX-100-static-check.txt',evidence)]:
                        z.writestr(name,data)
                    if keep_plan:
                        z.writestr('ziprunner-verification-plan.json',json.dumps(self.plan))
            build(False)
            self.assertEqual([],validate.inspect_archive(path,'example-project'))
            self.assertIn('missing ziprunner-verification-plan',str(validate.inspect_archive(path,'example-project',True)))
            # The referenced test must exist in the source package.
            with zipfile.ZipFile(path,'a') as z:
                z.writestr('tests/identity_guard_test.py',(ROOT/'examples/tests/identity_guard_test.py').read_bytes())
            build(True)
            self.assertIn('test implementation missing',str(validate.inspect_archive(path,'example-project',True)))
            with zipfile.ZipFile(path,'a') as z:
                z.writestr('tests/identity_guard_test.py',(ROOT/'examples/tests/identity_guard_test.py').read_bytes())
            self.assertEqual([],validate.inspect_archive(path,'example-project',True))
            self.plan['project']='another-project'
            build(True)
            self.assertIn('plan project does not match',str(validate.inspect_archive(path,'example-project',True)))


class TestObservedVerification(unittest.TestCase):
    def setUp(self):
        self.plan=json.loads((ROOT/'examples/verification-plan.json').read_text())
        self.report=json.loads((ROOT/'examples/verification-report.example.json').read_text())

    def errs(self):
        return vc.validate_report(self.report,self.plan,artifact_sha256='a'*64,plan_sha256='b'*64)

    def test_reference_valid_and_manual_unverified(self):
        self.assertEqual([],self.errs())
        self.assertEqual(set(),vc.covered_task_ids(self.plan,self.report))

    def test_failed_build_cannot_yield_pass(self):
        self.report['build']['status']='failed'
        self.assertIn('cannot pass',str(self.errs()))
        self.assertEqual(set(),vc.covered_task_ids(self.plan,self.report))

    def test_stale_artifact(self):
        self.report['artifact_sha256']='0'*64
        self.assertIn('stale',str(self.errs()))

    def test_stale_plan(self):
        self.report['plan_sha256']='0'*64
        self.assertIn('plan digest',str(self.errs()))

    def test_missing_check_result(self):
        self.report['checks'].pop()
        self.assertIn('exactly one outcome',str(self.errs()))

    def test_unobserved_producer_pass(self):
        self.report['checks'][0]['provenance']='producer_reported'
        self.assertIn('producer report cannot prove',str(self.errs()))

    def test_no_evidence_for_pass(self):
        self.report['checks'][0]['evidence']=[]
        self.assertIn('requires observed evidence',str(self.errs()))

    def test_wrong_runner(self):
        self.report['checks'][0]['runner_ref']='untrusted-runner'
        self.assertIn('trusted runner reference',str(self.errs()))

    def test_manual_pass_requires_operator(self):
        self.report['checks'][1]['status']='passed'
        self.report['checks'][1]['evidence']=[{'reference':'sample-log','sha256':'c'*64}]
        self.assertIn('operator-observed',str(self.errs()))

    def test_both_checks_pass_without_granting_done(self):
        self.report['checks'][1]['status']='passed'
        self.report['checks'][1]['provenance']='operator_observed'
        self.report['checks'][1]['evidence']=[{'reference':'sample-operator-log','sha256':'c'*64}]
        del self.report['checks'][1]['reason']
        self.assertEqual([],self.errs())
        self.assertEqual({'EX-100'},vc.covered_task_ids(self.plan,self.report))
        # This only produces a candidate; operator/QA state is outside the report.


class TestOriginFeedback(unittest.TestCase):
    def setUp(self):
        self.envelope=json.loads((ROOT/'examples/origin-feedback.example.json').read_text())
        self.report=json.loads((ROOT/'examples/verification-report.example.json').read_text())

    def errs(self):
        return vc.validate_feedback(self.envelope,self.report,trusted_request_id='EXREQ-20261015-01')

    def test_reference_valid(self):
        self.assertEqual([],self.errs())

    def test_wrong_request_prevents_reply(self):
        self.envelope['origin_request_id']='WRONG'
        self.assertIn('trusted intake',str(self.errs()))

    def test_wrong_artifact_prevents_reply(self):
        self.envelope['artifact_sha256']='0'*64
        self.assertIn('mismatches observed report',str(self.errs()))

    def test_unverified_destination_cannot_send(self):
        self.envelope['destination_binding']='unresolved'
        self.assertIn('unverified origin',str(self.errs()))

    def test_submitted_does_not_equal_acknowledged(self):
        s=vc.delivery_transition('queued','submit',origin_verified=True)
        self.assertEqual('submitted',s)
        self.assertEqual('submitted',vc.delivery_transition(s,'ack',origin_verified=True,acknowledged=False))
        self.assertEqual('acknowledged',vc.delivery_transition(s,'ack',origin_verified=True,acknowledged=True))

    def test_ack_requires_timestamp(self):
        self.envelope['delivery']['state']='acknowledged'
        self.assertIn('acknowledgement timestamp',str(self.errs()))

    def test_retry_does_not_redirect_unknown_origin(self):
        self.assertEqual('waiting_for_origin',vc.delivery_transition('retryable_failure','retry',origin_verified=False))

    def test_deterministic_message_identity(self):
        one=vc.feedback_id('R1','REQ1','c'*64)
        self.assertEqual(one,vc.feedback_id('R1','REQ1','c'*64))
        self.assertNotEqual(one,vc.feedback_id('R1','REQ2','c'*64))


class TestSchemas(unittest.TestCase):
    def test_examples_valid_against_draft_202012(self):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            self.skipTest('third-party JSON Schema engine not installed; default validator tests still apply')
        for schema_file,example_file in [('verification-plan.schema.json','verification-plan.json'),('verification-report.schema.json','verification-report.example.json'),('origin-feedback.schema.json','origin-feedback.example.json')]:
            with self.subTest(schema=schema_file):
                schema=json.loads((ROOT/'schemas'/schema_file).read_text())
                Draft202012Validator.check_schema(schema)
                Draft202012Validator(schema).validate(json.loads((ROOT/'examples'/example_file).read_text()))

if __name__=='__main__':unittest.main()
