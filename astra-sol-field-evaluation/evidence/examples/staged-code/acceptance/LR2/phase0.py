import copy
from pathlib import Path
import tempfile
import unittest
from retrieval import DocumentIndex

def event(id='a', version=1, body='red fox', tags=None, deleted=False):
    return dict(id=id, version=version, body=body, tags=[] if tags is None else tags, deleted=deleted)

class Base:
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'index.json'; self.index = DocumentIndex(self.path)
    def apply(self, batch, events, tenant='t'): return self.index.apply_batch(tenant, batch, events)
    def ids(self, query='', **kw): return [x['id'] for x in self.index.search('t', query, **kw)]
    def reopen(self): self.index = DocumentIndex(self.path)

class Acceptance(Base, unittest.TestCase):
    def test_all_query_tokens_and_precise_tokenization(self):
        self.apply('b', [event('a', body='RED fox'), event('b', body='red dog'),
                         event('c', body='red fox,')])
        self.assertEqual(self.ids('red fox'), ['a'])
        self.assertEqual(self.ids('red fox fox'), ['a'])
        self.assertEqual(self.ids('red fox,'), ['c'])

    def test_filter_before_limit_and_stable_ties(self):
        self.apply('b', [event('a', body='red red red', tags=['private']),
                         event('c', body='red', tags=['public', 'live']),
                         event('b', body='red', tags=['public', 'live'])])
        self.assertEqual(self.ids('red', limit=1, required_tags=['public', 'live']), ['b'])
        self.assertEqual(self.ids('', required_tags=['public', 'live']), ['b', 'c'])
        self.assertEqual(self.ids('red', limit=0), [])

    def test_tenants_and_separator_keys(self):
        self.apply('b', [event('a', body='tenant one')], 't')
        self.apply('b', [event('a', body='tenant two')], 'u')
        self.apply('x:y', [event('z')], 'p')
        self.apply('y', [event('z', body='different')], 'p:x')
        self.assertEqual(self.ids('two'), [])
        self.assertEqual(self.index.search('u', 'one'), [])
        self.assertEqual(self.index.search('missing', ''), [])
        self.assertEqual(self.index.get('p', 'z')['body'], 'red fox')

    def test_tombstone_blocks_stale_restore(self):
        self.apply('b1', [event(version=5)])
        self.apply('b2', [event(version=7, deleted=True)])
        self.assertEqual(self.ids('red'), [])
        self.apply('b3', [event(version=6, body='restore')])
        self.reopen()
        self.assertTrue(self.index.get('t', 'a')['deleted'])
        self.assertEqual(self.index.get('t', 'a')['version'], 7)
        self.assertEqual(self.ids(), [])
        self.apply('b4', [event(version=8, body='restored')])
        self.assertEqual(self.ids('restored'), ['a'])

    def test_equal_version_replay_conflict_and_receipt(self):
        self.apply('b1', [event()])
        self.assertTrue(self.apply('b2', [event()]))
        self.assertFalse(self.apply('b2', [event()]))
        with self.assertRaises(ValueError): self.apply('b3', [event(body='different')])
        self.assertTrue(self.apply('b3', [event(version=2)]))

    def test_batch_late_conflict_rolls_back_memory_disk_receipt(self):
        self.apply('seed', [event('existing')])
        with self.assertRaises(ValueError):
            self.apply('bad', [event('new'), event('existing', body='conflict')])
        self.assertIsNone(self.index.get('t', 'new'))
        self.reopen(); self.assertIsNone(self.index.get('t', 'new'))
        self.assertTrue(self.apply('bad', [event('new')]))

    def test_late_invalid_input_and_duplicate_are_atomic(self):
        for values in [[event('a'), event('b', version=True)], [event('a'), event('a')],
                       [event('a'), event('b', tags=['x', 'x'])]]:
            with self.subTest(values=values), self.assertRaises(ValueError): self.apply('bad', values)
            self.assertEqual(self.ids(), [])
        self.assertTrue(self.apply('bad', [])); self.assertFalse(self.apply('bad', []))

    def test_order_sensitive_receipts_and_event_payload(self):
        values = [event('a'), event('b')]; self.apply('b1', values)
        with self.assertRaises(ValueError): self.apply('b1', list(reversed(values)))
        self.apply('b2', [event('c', tags=['x', 'y'])])
        with self.assertRaises(ValueError): self.apply('b3', [event('c', tags=['y', 'x'])])
        self.assertEqual(self.index.get('t', 'c')['tags'], ['x', 'y'])

    def test_cache_updates_filters_limits_and_deletes(self):
        self.apply('b1', [event('a', tags=['x']), event('b', tags=['y'])])
        self.assertEqual(self.ids('red', limit=1), ['a'])
        self.assertEqual(self.ids('red', required_tags=['y']), ['b'])
        self.apply('b2', [event('a', version=2, body='blue', tags=['x'])])
        self.assertEqual(self.ids('red', limit=1), ['b'])
        self.apply('b3', [event('b', version=2, deleted=True)])
        self.assertEqual(self.ids('red'), [])

    def test_validation_on_empty_or_missing_tenant(self):
        for args in [('', 10, None), ('red', True, None), ('red', -1, None),
                     ('red', 10, ['x', 'x']), (5, 10, None)]:
            query, limit, required = args
            if args[0] == '':
                with self.assertRaises(ValueError): self.index.search('', query, limit, required)
            else:
                with self.assertRaises(ValueError): self.index.search('missing', query, limit, required)

    def test_score_repeated_query_terms_once_and_restart_order(self):
        self.apply('b', [event('z', body='red red fox'), event('a', body='red fox fox fox'),
                         event('b', body='red red fox')])
        self.assertEqual(self.ids('red red fox'), ['a', 'b', 'z'])
        self.reopen(); self.assertEqual(self.ids('red red fox'), ['a', 'b', 'z'])
