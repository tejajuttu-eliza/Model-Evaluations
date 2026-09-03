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

class Acceptance(Base, unittest.TestCase):
    def test_exact_expiry_reclaim_unique_tokens_and_cursor(self):
        self.submit(); first = self.claim(); self.append(first['token'], ROWS[:1])
        self.reopen(); second = self.claim(now=10)
        self.assertIsNotNone(second); self.assertNotEqual(second['token'], first['token'])
        self.assertEqual(second['cursor'], 1)
        with self.assertRaises(ValueError): self.append(first['token'], ROWS[1:], now=11)
        self.append(second['token'], ROWS[1:], chunk='rest', now=11)
        self.assertEqual(self.commit(second['token'], now=12), digest(ROWS))

    def test_stale_lease_cannot_acknowledge_chunk_replay(self):
        self.submit(); token = self.claim()['token']; self.append(token, ROWS[:1])
        with self.assertRaises(ValueError): self.append(token, ROWS[:1], now=10)
        second = self.claim(now=10)
        self.assertFalse(self.append(second['token'], ROWS[:1], now=11))
        self.assertEqual(self.state()['cursor'], 1)

    def test_lost_response_restart_replay_once(self):
        self.submit(); token = self.claim()['token']; self.append(token, ROWS[:2], 'c1')
        self.reopen(); self.assertFalse(self.append(token, ROWS[:2], 'c1', now=2))
        self.append(token, ROWS[2:], 'c2', now=3)
        receipt = self.commit(token, now=4); self.reopen()
        self.assertEqual(self.commit(token, now=1000), receipt)
        self.assertEqual(self.state()['cursor'], 3)
        self.assertIsNone(self.claim(now=1000))

    def test_partial_commit_and_rejected_chunk_do_not_reserve_ids(self):
        self.submit(); token = self.claim()['token']
        with self.assertRaises(ValueError): self.commit(token)
        with self.assertRaises(ValueError): self.append(token, ROWS[1:], 'x')
        self.assertEqual(self.state()['cursor'], 0)
        self.assertTrue(self.append(token, ROWS, 'x'))
        self.assertEqual(self.commit(token), digest(ROWS))

    def test_changed_chunk_and_commit_identity_rejected(self):
        self.submit(); token = self.claim()['token']; self.append(token, ROWS[:1])
        with self.assertRaises(ValueError): self.append(token, ROWS[1:2])
        self.assertEqual(self.state()['cursor'], 1)
        self.append(token, ROWS[1:], 'rest'); self.commit(token)
        for badtoken, badid in [(token, 'other'), ('wrong', 'commit')]:
            with self.assertRaises(ValueError): self.commit(badtoken, badid)
        self.assertEqual(self.state()['artifact_sha256'], digest(ROWS))

    def test_ordered_claims_and_tenant_job_identity(self):
        self.submit(job='z'); self.submit(job='a'); self.submit(job='a', tenant='u')
        first = self.claim(); self.assertEqual(first['job_id'], 'a')
        second = self.claim(); self.assertEqual(second['job_id'], 'z')
        other = self.claim(tenant='u'); self.assertEqual(other['job_id'], 'a')
        self.assertEqual(len({first['token'], second['token'], other['token']}), 3)
        with self.assertRaises(ValueError): self.append(other['token'], ROWS, job='a')

    def test_submission_order_conflict_and_validation(self):
        self.submit()
        with self.assertRaises(ValueError): self.submit(list(reversed(ROWS)))
        with self.assertRaises(ValueError): self.submit([ROWS[0], ROWS[0]], 'bad')
        with self.assertRaises(ValueError): self.submit([dict(id='x', value=3)], 'bad')
        with self.assertRaises(ValueError): self.q.inspect('t', 'bad')
        self.assertEqual(self.state()['state'], 'queued')

    def test_invalid_time_lease_and_replay_parameters(self):
        self.submit()
        for now, ttl in [(True, 5), (0, 0), (-1, 4), (0, True)]:
            with self.subTest(now=now, ttl=ttl), self.assertRaises(ValueError): self.claim(now, ttl)
        token = self.claim()['token']; self.append(token, ROWS); self.commit(token)
        with self.assertRaises(ValueError): self.commit(token, now=True)
        with self.assertRaises(ValueError): self.commit(token, cid='')

    def test_inspection_is_precise_and_non_mutating(self):
        self.submit()
        self.assertEqual(self.state(), dict(state='queued', cursor=0, total=3,
                         artifact_sha256=None, lease_expires=None))
        token = self.claim(now=4, ttl=6)['token']; snapshot = self.state(); snapshot['cursor'] = 999
        self.assertEqual(self.state(), dict(state='running', cursor=0, total=3,
                         artifact_sha256=None, lease_expires=10))
        self.reopen(); self.assertEqual(self.state()['cursor'], 0)
        self.assertEqual(self.state()['lease_expires'], 10)

    def test_duplicate_rows_and_noncontiguous_chunks_leave_disk_unchanged(self):
        self.submit(); token = self.claim()['token']
        for rows in [[], [ROWS[0], ROWS[0]], [ROWS[1]], list(reversed(ROWS))]:
            with self.subTest(rows=rows), self.assertRaises(ValueError): self.append(token, rows)
        self.reopen(); self.assertEqual(self.state()['cursor'], 0)
        self.assertTrue(self.append(token, ROWS))

    def test_unicode_digest_chunk_replay_after_new_claim(self):
        self.submit(); token = self.claim()['token']; self.append(token, ROWS[:2], 'p')
        self.reopen(); token2 = self.claim(now=11)['token']
        self.assertFalse(self.append(token2, ROWS[:2], 'p', now=12))
        self.append(token2, ROWS[2:], 'q', now=13)
        self.assertEqual(self.commit(token2, now=14), digest(ROWS))
