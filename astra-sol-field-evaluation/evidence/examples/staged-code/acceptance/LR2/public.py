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

class Public(Base, unittest.TestCase):
    def test_insert_search_and_replay(self):
        values = [event('a'), event('b', body='red red fox')]
        self.assertTrue(self.apply('batch', values)); self.assertFalse(self.apply('batch', values))
        self.assertEqual(self.ids('RED fox'), ['b', 'a'])

    def test_latest_version_and_restart(self):
        self.apply('b1', [event(body='old')]); self.apply('b2', [event(version=2, body='new')])
        self.reopen()
        self.assertEqual(self.ids('new'), ['a']); self.assertEqual(self.ids('old'), [])
        self.assertEqual(self.index.get('t', 'a')['version'], 2)

    def test_detached_input_and_result(self):
        values = [event(tags=['x'])]; self.apply('b', values); values[0]['tags'].append('leak')
        result = self.index.search('t', 'red'); result[0]['body'] = 'changed'
        self.assertEqual(self.index.get('t', 'a'), event(tags=['x']))
