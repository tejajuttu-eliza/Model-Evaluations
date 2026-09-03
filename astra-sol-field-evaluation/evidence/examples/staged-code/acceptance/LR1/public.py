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

class Public(Base, unittest.TestCase):
    def test_basic_pin_and_replay(self):
        self.assertFalse(self.l.register_run('t', 'run', 'definition-v3', ['a', 'b', 'c'], 'human-v2'))
        with self.assertRaises(ValueError):
            self.l.register_run('t', 'run', 'changed', ['a', 'b', 'c'], 'human-v2')
        self.assertTrue(self.op(operation()))
        self.assertFalse(self.op(operation()))
        self.assertTrue(self.rev(review()))
        self.assertEqual(self.summary()['cost_per_accepted_usd'], '1.000000')

    def test_completion_and_quality_are_separate(self):
        self.l.complete_task('t', 'run', 'a')
        self.l.complete_task('t', 'run', 'b')
        self.rev(review(passed=False))
        s = self.summary()
        self.assertEqual((s['planned'], s['completed'], s['evaluated'], s['accepted']), (3, 2, 1, 0))
        self.assertIsNone(s['cost_per_accepted_usd'])

    def test_restart_and_detached_snapshot(self):
        self.op(operation())
        result = self.snapshot()
        result['operations'][0]['cost_microusd'] = 999
        self.reopen()
        self.assertEqual(self.snapshot()['operations'][0]['cost_microusd'], 1000000)
        self.assertEqual(self.summary()['total_cost_usd'], '1.000000')
