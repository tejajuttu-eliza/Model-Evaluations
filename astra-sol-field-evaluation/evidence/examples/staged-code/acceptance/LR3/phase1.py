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

class Cancellation(Base, unittest.TestCase):
    def cancel(self, request='r', job='j', tenant='t'): return self.q.cancel(tenant, job, request)

    def test_queued_cancellation_is_durable_and_not_claimable(self):
        self.submit(); self.assertTrue(self.cancel()); self.reopen()
        self.assertFalse(self.cancel()); self.assertIsNone(self.claim())
        self.assertEqual(self.state(), dict(state='cancelled', cursor=0, total=3,
                         artifact_sha256=None, lease_expires=None))

    def test_late_cancellation_retains_cursor_but_blocks_all_writes(self):
        self.submit(); token = self.claim()['token']; self.append(token, ROWS[:1])
        self.cancel(); self.reopen()
        self.assertEqual(self.state()['cursor'], 1)
        self.assertEqual(self.state()['state'], 'cancelled')
        self.assertIsNone(self.state()['lease_expires'])
        with self.assertRaises(ValueError): self.append(token, ROWS[:1])
        with self.assertRaises(ValueError): self.append(token, ROWS[1:], 'rest')
        with self.assertRaises(ValueError): self.commit(token)
        self.assertIsNone(self.claim(now=100))

    def test_cancel_after_all_chunks_before_commit(self):
        self.submit(); token = self.claim()['token']; self.append(token, ROWS)
        self.cancel()
        self.assertEqual(self.state()['cursor'], 3)
        self.assertIsNone(self.state()['artifact_sha256'])
        with self.assertRaises(ValueError): self.commit(token)

    def test_completed_cancellation_rejected_without_consuming_request(self):
        self.submit(); token = self.claim()['token']; self.append(token, ROWS); self.commit(token)
        self.submit(job='other')
        with self.assertRaises(ValueError): self.cancel('shared')
        self.assertTrue(self.cancel('shared', 'other'))
        self.assertEqual(self.commit(token, now=100), digest(ROWS))
        self.assertEqual(self.state()['state'], 'completed')

    def test_request_scope_conflict_is_atomic_and_tenant_safe(self):
        self.submit(); self.submit(job='other'); self.submit(tenant='u')
        self.cancel('same')
        with self.assertRaises(ValueError): self.cancel('same', 'other')
        self.assertEqual(self.state('other')['state'], 'queued')
        self.assertTrue(self.cancel('same', tenant='u'))
        self.reopen(); self.assertEqual(self.state('other')['state'], 'queued')

    def test_new_receipt_for_cancelled_and_submit_identity_preserved(self):
        self.submit(); self.cancel('first'); self.assertFalse(self.cancel('second'))
        self.reopen(); self.assertFalse(self.cancel('second')); self.assertFalse(self.submit())
        with self.assertRaises(ValueError): self.submit(list(reversed(ROWS)))
        self.submit(job='other')
        with self.assertRaises(ValueError): self.cancel('second', 'other')

    def test_invalid_cancel_does_not_mutate_or_reserve(self):
        self.submit()
        with self.assertRaises(ValueError): self.cancel('')
        with self.assertRaises(ValueError): self.cancel('unused', 'missing')
        self.assertEqual(self.state()['state'], 'queued')
        self.assertTrue(self.cancel('unused'))
