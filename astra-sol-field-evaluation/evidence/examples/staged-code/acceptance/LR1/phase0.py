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

class Acceptance(Base, unittest.TestCase):
    def test_failed_attempts_judges_and_replays(self):
        self.op(operation('first', status='failed', cost_microusd=2000000))
        self.op(operation('retry', cost_microusd=3000000))
        self.op(operation('judge', kind='judge', status='failed', cost_microusd=500000))
        self.op(operation('replay', replay=True, cost_microusd=None))
        self.op(operation('preflight', invoked=False, cost_microusd=9000000))
        s = self.summary()
        self.assertEqual((s['billable_operations'], s['priced_operations']), (3, 3))
        self.assertEqual(s['total_cost_usd'], '5.500000')
        self.assertEqual(s['cost_coverage'], 1.0)

    def test_unknown_cost_preserves_known_subtotal(self):
        self.op(operation('known', cost_microusd=1234567))
        self.op(operation('unknown', cost_microusd=None))
        self.rev(review())
        s = self.summary()
        self.assertEqual(s['known_cost_usd'], '1.234567')
        self.assertIsNone(s['total_cost_usd'])
        self.assertIsNone(s['cost_per_accepted_usd'])
        self.assertEqual(s['cost_coverage'], 0.5)

    def test_pinned_primary_pending_and_tie_order(self):
        self.rev(review('z', sequence=4, passed=False))
        self.rev(review('a', sequence=4, passed=True))
        self.rev(review('later-pending', sequence=100, status='pending', passed=None))
        self.rev(review('format', sequence=500, metric_revision='format-v1', passed=True))
        self.assertEqual(self.summary()['accepted'], 0)
        self.rev(review('accepted', sequence=5, passed=True))
        self.assertEqual(self.summary()['accepted'], 1)

    def test_quality_denominators_and_exact_rounding(self):
        self.op(operation(cost_microusd=1))
        self.rev(review('a'))
        self.rev(review('b', task='b'))
        s = self.summary()
        self.assertEqual((s['completed'], s['evaluated'], s['accepted']), (0, 2, 2))
        self.assertEqual(s['review_coverage'], 2 / 3)
        self.assertEqual(s['planned_success'], 2 / 3)
        self.assertEqual(s['pass_rate'], 1.0)
        self.assertEqual(s['cost_per_accepted_usd'], '0.000001')
        self.assertEqual(s['total_cost_usd'], '0.000001')

    def test_empty_cost_and_review_denominators(self):
        s = self.summary()
        self.assertEqual(s['total_cost_usd'], '0.000000')
        self.assertEqual(s['known_cost_usd'], '0.000000')
        self.assertEqual(s['cost_coverage'], 1.0)
        self.assertIsNone(s['pass_rate'])
        self.assertIsNone(s['cost_per_accepted_usd'])
        self.assertEqual(s['planned_success'], 0.0)

    def test_tenant_run_identity_and_separator_collisions(self):
        for tenant, run in [('t', 'other'), ('t:run', 'other'), ('t', 'run:other')]:
            self.l.register_run(tenant, run, 'v1', ['a'], 'human-v2')
            self.l.record_operation(tenant, run, operation(cost_microusd=7))
            self.l.record_review(tenant, run, review())
            self.assertEqual(self.l.summary(tenant, run)['total_cost_usd'], '0.000007')
        self.assertEqual(self.summary()['billable_operations'], 0)
        self.reopen()
        self.assertEqual(self.l.summary('t:run', 'other')['accepted'], 1)

    def test_record_conflicts_are_atomic_and_do_not_replace(self):
        self.op(operation())
        self.rev(review())
        before = self.snapshot()
        with self.assertRaises(ValueError): self.op(operation(cost_microusd=2))
        with self.assertRaises(ValueError): self.rev(review(passed=False))
        with self.assertRaises(ValueError): self.op(operation('bad', task='unknown'))
        with self.assertRaises(ValueError): self.l.complete_task('t', 'run', 'unknown')
        self.assertEqual(self.snapshot(), before)
        self.reopen()
        self.assertEqual(self.snapshot(), before)

    def test_boolean_numeric_and_status_validation(self):
        invalid = [operation(cost_microusd=True), operation(cost_microusd=-1),
                   operation(invoked=1), operation(status='pending'), operation(kind='tool')]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError): self.op(value)
        for value in [review(sequence=True), review(passed=1), review(status='pending', passed=False)]:
            with self.subTest(value=value), self.assertRaises(ValueError): self.rev(value)
        self.assertEqual(self.snapshot()['operations'], [])
        self.assertEqual(self.snapshot()['reviews'], [])

    def test_mutable_inputs_and_insert_order(self):
        value = operation('z'); self.op(value); value['cost_microusd'] = 100
        self.op(operation('a', cost_microusd=3))
        r = review('z'); self.rev(r); r['passed'] = False
        self.rev(review('a', task='b'))
        self.l.complete_task('t', 'run', 'c'); self.l.complete_task('t', 'run', 'a')
        self.assertFalse(self.l.complete_task('t', 'run', 'c'))
        s = self.snapshot()
        self.assertEqual([o['id'] for o in s['operations']], ['z', 'a'])
        self.assertEqual([r['id'] for r in s['reviews']], ['z', 'a'])
        self.assertEqual(s['completed'], ['a', 'c'])
        self.assertEqual(self.summary()['accepted'], 2)
        self.reopen()
        self.assertEqual([o['id'] for o in self.snapshot()['operations']], ['z', 'a'])
        self.assertEqual([r['id'] for r in self.snapshot()['reviews']], ['z', 'a'])

    def test_definition_validation_is_atomic(self):
        for tasks in [[], ['a', 'a'], [''], 'abc']:
            with self.subTest(tasks=tasks), self.assertRaises(ValueError):
                self.l.register_run('new', 'run', 'v', tasks, 'm')
        with self.assertRaises(ValueError): self.l.snapshot('new', 'run')
        with self.assertRaises(ValueError):
            self.l.register_run('t', 'run', 'definition-v3', ['b', 'a', 'c'], 'human-v2')
        self.assertEqual(self.snapshot()['task_ids'], ['a', 'b', 'c'])

    def test_practical_maximum_and_single_final_round(self):
        for i in range(25): self.op(operation(str(i), cost_microusd=1_000_000_000))
        for task in ['a', 'b', 'c']: self.rev(review(task, task=task))
        s = self.summary()
        self.assertEqual(s['total_cost_usd'], '25000.000000')
        self.assertEqual(s['cost_per_accepted_usd'], '8333.333333')
