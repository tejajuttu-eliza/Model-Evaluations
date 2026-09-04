import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from exports import ExportQueue

ROWS = [dict(id='a', value='first'), dict(id='b', value='second'), dict(id='c', value='café')]
def digest(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':'),
                                   ensure_ascii=False).encode('utf-8')).hexdigest()

class Base:
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'queue.json'; self.q = ExportQueue(self.path)
    def submit(self, rows=ROWS, job='j', tenant='t'): return self.q.submit(tenant, job, copy.deepcopy(rows))
    def claim(self, now=0, ttl=10, tenant='t'): return self.q.claim(tenant, 'worker', now, ttl)
    def append(self, token, rows, chunk='chunk', now=1, job='j', tenant='t'):
        return self.q.append(tenant, job, token, chunk, copy.deepcopy(rows), now)
    def commit(self, token, cid='commit', now=2, job='j', tenant='t'):
        return self.q.commit(tenant, job, token, cid, now)
    def state(self, job='j', tenant='t'): return self.q.inspect(tenant, job)
    def reopen(self): self.q = ExportQueue(self.path)

class Public(Base, unittest.TestCase):
    def test_complete_export_digest_and_replay(self):
        self.assertTrue(self.submit()); self.assertFalse(self.submit())
        claim = self.claim(); self.assertEqual(claim['cursor'], 0)
        self.assertTrue(self.append(claim['token'], ROWS))
        self.assertEqual(self.commit(claim['token']), digest(ROWS))
        self.assertEqual(self.commit(claim['token'], now=100), digest(ROWS))
        self.assertEqual(self.state()['state'], 'completed')

    def test_partial_restart_keeps_cursor(self):
        self.submit(); token = self.claim()['token']; self.append(token, ROWS[:1])
        self.reopen(); self.assertEqual(self.state()['cursor'], 1)
        self.assertIsNone(self.claim(now=5))

    def test_empty_export_and_detached_submission(self):
        rows = [dict(id='a', value='original')]; self.q.submit('t', 'j', rows); rows[0]['value'] = 'mutated'
        token = self.claim()['token']; self.append(token, [dict(id='a', value='original')])
        self.assertEqual(self.commit(token), digest([dict(id='a', value='original')]))
        self.submit([], 'empty'); empty = self.claim(now=3)
        self.assertEqual(self.commit(empty['token'], job='empty', now=4), digest([]))
