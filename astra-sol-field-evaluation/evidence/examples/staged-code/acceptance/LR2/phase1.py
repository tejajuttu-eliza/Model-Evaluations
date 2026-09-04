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

class Policy(Base, unittest.TestCase):
    def set_policy(self, revision, tags, tenant='t'):
        return self.index.set_policy(tenant, revision, tags)

    def test_policy_filters_any_blocked_tag_before_limit(self):
        self.apply('b', [event('a', body='red red red', tags=['restricted']),
                         event('b', body='red red', tags=['pending', 'public']), event('c', tags=['public'])])
        self.set_policy(1, ['restricted', 'pending'])
        self.assertEqual(self.ids('red', limit=1), ['c'])
        self.assertEqual(self.ids('', required_tags=['public']), ['c'])
        self.assertEqual(self.index.get('t', 'a')['version'], 1)

    def test_policy_before_documents_and_tenant_isolation(self):
        self.assertTrue(self.set_policy(4, ['secret']))
        self.apply('b', [event(tags=['secret'])]); self.apply('b', [event(tags=['secret'])], 'u')
        self.assertEqual(self.ids(), [])
        self.assertEqual(len(self.index.search('u', '')), 1)
        self.assertEqual(self.index.get('t', 'a')['tags'], ['secret'])

    def test_stale_equal_and_normalized_order(self):
        self.assertTrue(self.set_policy(5, ['z', 'a']))
        self.assertFalse(self.set_policy(5, ['a', 'z']))
        self.assertFalse(self.set_policy(4, []))
        with self.assertRaises(ValueError): self.set_policy(5, ['a'])
        self.apply('b', [event(tags=['z'])]); self.assertEqual(self.ids(), [])

    def test_policy_clear_invalidates_cached_results(self):
        self.apply('b', [event(tags=['hold'])]); self.assertEqual(self.ids('red'), ['a'])
        self.set_policy(1, ['hold']); self.assertEqual(self.ids('red'), [])
        self.set_policy(2, []); self.assertEqual(self.ids('red'), ['a'])
        self.reopen(); self.assertEqual(self.ids('red'), ['a'])

    def test_policy_reopen_and_document_updates(self):
        self.apply('b', [event()]); self.set_policy(1, ['hold']); self.reopen()
        self.assertEqual(self.ids('red'), ['a'])
        self.apply('b2', [event(version=2, tags=['hold'])]); self.assertEqual(self.ids('red'), [])
        self.apply('b3', [event(version=3)]); self.assertEqual(self.ids('red'), ['a'])
        self.reopen(); self.assertEqual(self.ids('red'), ['a'])

    def test_validation_even_for_stale_policy_is_atomic(self):
        self.set_policy(5, ['hold']); self.apply('b', [event(tags=['hold'])])
        for revision, tags in [(True, []), (3, ['x', 'x']), (3, ['']), (-1, [])]:
            with self.subTest(revision=revision, tags=tags), self.assertRaises(ValueError):
                self.set_policy(revision, tags)
        self.reopen(); self.assertEqual(self.ids(), [])

    def test_input_detachment_and_policy_names_with_separators(self):
        tags = ['blocked']; self.set_policy(1, tags); tags.clear()
        self.apply('b', [event(tags=['blocked'])]); self.assertEqual(self.ids(), [])
        self.set_policy(1, ['a:b'], 't:x')
        self.apply('b', [event(tags=['a:b'])], 't:x')
        self.assertEqual(self.index.search('t:x', ''), [])
        self.assertEqual(self.index.get('t:x', 'a')['tags'], ['a:b'])
