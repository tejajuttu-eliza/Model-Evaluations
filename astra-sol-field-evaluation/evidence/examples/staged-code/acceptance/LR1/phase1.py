import copy
import json
from pathlib import Path
import tempfile
import unittest
from evalledger import Ledger

def operation(id='op', task='a', **kw):
    out = dict(id=id, task_id=task, kind='workflow', invoked=True, replay=False,
               status='succeeded', cost_microusd=1000000)
    out.update(kw)
    return out

def review(id='r', task='a', **kw):
    out = dict(id=id, task_id=task, metric_revision='human-v2', status='completed',
               sequence=1, passed=True)
    out.update(kw)
    return out

class Base:
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'ledger.json'
        self.l = Ledger(self.path)
        self.l.register_run('t', 'run', 'definition-v3', ['a', 'b', 'c'], 'human-v2')

    def op(self, value): return self.l.record_operation('t', 'run', value)
    def rev(self, value): return self.l.record_review('t', 'run', value)
    def summary(self): return self.l.summary('t', 'run')
    def snapshot(self): return self.l.snapshot('t', 'run')
    def reopen(self): self.l = Ledger(self.path)

class Correction(Base, unittest.TestCase):
    def retract(self, review_id, rid='x', reason='wrong judgment'):
        return self.l.retract_review('t', 'run', review_id, rid, reason)

    def test_retraction_falls_back_to_older_primary(self):
        self.rev(review('old', sequence=1, passed=False))
        self.rev(review('new', sequence=2, passed=True))
        self.assertEqual(self.summary()['accepted'], 1)
        self.assertTrue(self.retract('new'))
        self.assertEqual((self.summary()['evaluated'], self.summary()['accepted']), (1, 0))
        self.assertEqual(len(self.snapshot()['reviews']), 2)

    def test_all_retracted_becomes_unevaluated_and_preserves_cost(self):
        self.op(operation(cost_microusd=3))
        self.l.complete_task('t', 'run', 'a')
        self.rev(review())
        self.retract('r')
        s = self.summary()
        self.assertEqual((s['completed'], s['evaluated'], s['accepted']), (1, 0, 0))
        self.assertEqual(s['total_cost_usd'], '0.000003')
        self.assertIsNone(s['pass_rate'])
        self.assertIsNone(s['cost_per_accepted_usd'])

    def test_durable_exact_replay_and_multiple_receipts(self):
        self.rev(review())
        self.assertTrue(self.retract('r'))
        self.reopen()
        self.assertFalse(self.retract('r'))
        self.assertTrue(self.retract('r', 'y', 'confirmed correction'))
        self.assertEqual(self.summary()['evaluated'], 0)
        self.assertEqual(self.snapshot()['retractions'], [
            dict(id='x', review_id='r', reason='wrong judgment'),
            dict(id='y', review_id='r', reason='confirmed correction')])

    def test_conflict_and_missing_target_are_atomic(self):
        self.rev(review('a')); self.rev(review('b', task='b'))
        self.retract('a'); before = self.snapshot()
        with self.assertRaises(ValueError): self.retract('b')
        with self.assertRaises(ValueError): self.retract('a', reason='changed')
        with self.assertRaises(ValueError): self.retract('missing', 'new')
        self.assertEqual(self.snapshot(), before)
        self.reopen(); self.assertEqual(self.snapshot(), before)

    def test_retracted_review_identity_is_still_immutable(self):
        self.rev(review()); self.retract('r')
        self.assertFalse(self.rev(review()))
        with self.assertRaises(ValueError): self.rev(review(passed=False))
        self.rev(review('later', sequence=2))
        self.assertEqual(self.summary()['accepted'], 1)

    def test_pending_and_nonprimary_retraction_has_no_quality_effect(self):
        self.rev(review())
        self.rev(review('pending', status='pending', passed=None))
        self.rev(review('other', metric_revision='format'))
        self.retract('pending', 'p'); self.retract('other', 'o')
        self.assertEqual(self.summary()['accepted'], 1)
        for reason in ['', 3, 'x' * 501]:
            with self.subTest(reason=reason), self.assertRaises(ValueError): self.retract('r', 'bad', reason)

    def test_tenant_retraction_isolation_and_detachment(self):
        self.rev(review()); self.retract('r')
        self.l.register_run('u', 'run', 'v', ['a'], 'human-v2')
        self.l.record_review('u', 'run', review())
        self.assertEqual(self.l.summary('u', 'run')['accepted'], 1)
        snap = self.snapshot(); snap['retractions'].clear()
        self.assertEqual(self.summary()['evaluated'], 0)
        self.assertTrue(self.l.retract_review('u', 'run', 'r', 'x', 'different tenant'))
