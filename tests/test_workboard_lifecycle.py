"""Consumer-side reference tests: NOT tests of the installed ZipRunner application."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import workboard_lifecycle as l


def fixture():
    return {
        'schema': 'ziprunner.workboard-update.v1',
        'project': 'the-life-loop',
        'version': '0.5.41',
        'summary': 'Existing stable-ID lifecycle check',
        'implemented': [{
            'id': 'LL-246', 'title': 'Entrance support',
            'summary': 'Added verified entrance regression behavior',
            'operator_checks': ['Run entrance regression and confirm movement.'],
        }],
        'remaining': [{
            'id': 'LL-175', 'title': 'DOS timing',
            'summary': 'Timing traces unavailable', 'priority': 'medium',
        }],
    }


class WorkboardLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.update = fixture()
        self.existing = {
            'LL-246': {'id': 'LL-246', 'status': 'in_progress', 'title': 'Entrance support',
                       'acceptance_criteria': ['Entrances lead to correct buildings'],
                       'notes': []},
            'LL-175': {'id': 'LL-175', 'status': 'blocked', 'title': 'DOS timing',
                       'acceptance_criteria': ['Match original game travel timings'],
                       'notes': []},
        }
        self.sha = 'a' * 64
        self.review = {'qa_approved': True, 'operator_verified': True,
                       'acceptance_criteria_passed': True,
                       'evidence': ['Windows operator verified entrance test run 47'],
                       'actor': 'operator', 'timestamp': '2026-10-14T10:00:00+02:00'}

    def import_source(self, board=None, hashes=None, ok=True):
        return l.import_built_source(board if board is not None else self.existing,
                                     self.update, artifact_hash=self.sha,
                                     build_succeeded=ok, imported_hashes=hashes or set())

    def test_build_pass_does_not_mark_done(self):
        b, hashes, stats = self.import_source()
        self.assertEqual('awaiting_verification', b['LL-246']['status'])
        self.assertEqual('blocked', b['LL-175']['status'])
        self.assertEqual(['Entrances lead to correct buildings'], b['LL-246']['acceptance_criteria'])
        self.assertEqual(2, len(b))
        self.assertEqual(1, stats['awaiting_verification'])

    def test_review_closes_original_id(self):
        b, _, _ = self.import_source()
        completed = l.apply_trusted_review(b, 'LL-246', self.review, authorized=True)
        self.assertEqual('done', completed['LL-246']['status'])
        self.assertEqual(set(self.existing), set(completed))
        self.assertEqual([], l.release_readiness_errors(completed, {'LL-246'}))

    def test_release_blocks_open_delivered_work(self):
        b, _, _ = self.import_source()
        self.assertIn('LL-246', str(l.release_readiness_errors(b, {'LL-246'})))

    def test_release_excludes_unrelated_backlog(self):
        b, _, _ = self.import_source()
        b = l.apply_trusted_review(b, 'LL-246', self.review, authorized=True)
        self.assertEqual([], l.release_readiness_errors(b, {'LL-246'}))
        self.assertEqual('blocked', b['LL-175']['status'])

    def test_release_rejects_verified_but_open(self):
        b, _, _ = self.import_source()
        b = l.apply_trusted_review(b, 'LL-246', self.review, authorized=True)
        b['LL-246']['status'] = 'in_progress'
        self.assertIn('has not transitioned to Done', str(l.release_readiness_errors(b, {'LL-246'})))

    def test_no_done_on_unverified_review(self):
        b, _, _ = self.import_source()
        review = copy.deepcopy(self.review)
        review['operator_verified'] = False
        changed = l.apply_trusted_review(b, 'LL-246', review, authorized=True)
        self.assertEqual('in_progress', changed['LL-246']['status'])

    def test_no_done_on_unapproved_qa(self):
        b, _, _ = self.import_source()
        review = copy.deepcopy(self.review)
        review['qa_approved'] = False
        changed = l.apply_trusted_review(b, 'LL-246', review, authorized=True)
        self.assertNotEqual('done', changed['LL-246']['status'])

    def test_no_done_on_missing_evidence(self):
        b, _, _ = self.import_source()
        review = copy.deepcopy(self.review)
        review['evidence'] = []
        with self.assertRaises(l.WorkboardLifecycleError):
            l.apply_trusted_review(b, 'LL-246', review, authorized=True)

    def test_review_authorization_required(self):
        b, _, _ = self.import_source()
        with self.assertRaises(l.WorkboardLifecycleError):
            l.apply_trusted_review(b, 'LL-246', self.review, authorized=False)

    def test_build_failure_imports_no_delivered_work(self):
        b, hashes, stats = self.import_source(ok=False)
        self.assertEqual(self.existing, b)
        self.assertEqual(set(), hashes)
        self.assertEqual(0, stats['updated'])

    def test_hash_replay_is_idempotent(self):
        b, hashes, _ = self.import_source()
        again, hashes2, counts = self.import_source(b, hashes)
        self.assertEqual(b, again)
        self.assertEqual(hashes, hashes2)
        self.assertEqual(0, counts['updated'])

    def test_verified_done_is_not_reopened(self):
        b, hashes, _ = self.import_source()
        b = l.apply_trusted_review(b, 'LL-246', self.review, authorized=True)
        newer = 'b' * 64
        nxt, _, _ = l.import_built_source(b, self.update, artifact_hash=newer, build_succeeded=True, imported_hashes=hashes)
        self.assertEqual('done', nxt['LL-246']['status'])
        self.assertEqual(['Entrances lead to correct buildings'], nxt['LL-246']['acceptance_criteria'])

    def test_done_cannot_be_reopened_by_remaining(self):
        board = copy.deepcopy(self.existing)
        board['LL-175']['status'] = 'done'
        with self.assertRaisesRegex(l.WorkboardLifecycleError, 'cannot silently reopen'):
            self.import_source(board)

    def test_new_item_can_be_created(self):
        b, _, stats = self.import_source({})
        self.assertEqual(2, len(b))
        self.assertEqual(2, stats['created'])

    def test_blocked_requires_reason_and_unblock(self):
        b, _, _ = self.import_source()
        with self.assertRaises(l.WorkboardLifecycleError):
            l.apply_trusted_review(b, 'LL-246', {'blocked': True, 'reason': 'missing traces'}, authorized=True)
        reviewed = l.apply_trusted_review(b, 'LL-246', {'blocked': True, 'reason': 'missing traces', 'unblock_when': 'have traces'}, authorized=True)
        self.assertEqual('blocked', reviewed['LL-246']['status'])

    def test_missing_id_blocks_release(self):
        self.assertIn('missing task identity', str(l.release_readiness_errors(self.existing, {'LL-NONEXISTENT'})))

if __name__ == '__main__':
    unittest.main()
