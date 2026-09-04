#!/usr/bin/env python3
"""Replay final acceptance tests on six exported code snapshots in temporary directories.

This executes the supplied candidate Python code. It does not replay model calls,
the incremental edits, interrupted attempts, or persistence across model stages.
"""
import json
import sys
import tempfile
from pathlib import Path
import sandbox

ROOT=Path(__file__).resolve().parent
LOADER=r'''
import importlib.util,json,sys,unittest
workspace,*tests=sys.argv[1:]
sys.path.insert(0,workspace)
suite=unittest.TestSuite()
for i,path in enumerate(tests):
    spec=importlib.util.spec_from_file_location('acceptance_'+str(i),path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
result=unittest.TextTestRunner(verbosity=0).run(suite)
print(json.dumps({'passed':result.wasSuccessful() and not result.skipped,
                  'tests_run':result.testsRun,'failures':len(result.failures),
                  'errors':len(result.errors),'skipped':len(result.skipped)}))
'''


def main():
    assert Path('/usr/bin/sandbox-exec').is_file(), 'Optional replay requires the supplied macOS sandbox; no unsandboxed fallback.'
    isolation=sandbox.preflight()
    results=[]
    examples=ROOT/'examples/staged-code'
    for record in sorted(examples.glob('staged-repo-*.json')):
        d=json.loads(record.read_text());cid=d['run_id'].split('-')[2]
        with tempfile.TemporaryDirectory(prefix='model-evidence-') as tmp:
            workspace=Path(tmp)
            for name,content in d['files'].items():
                p=workspace/name
                assert p.resolve().is_relative_to(workspace.resolve())
                p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
            tests=[examples/'acceptance'/cid/name for name in ['public.py','phase0.py','phase1.py']]
            command=[sys.executable,'-I','-c',LOADER,str(workspace),*map(str,tests)]
            done=sandbox.run(command,workspace=workspace,read_paths=tests,timeout=30)
            assert done.returncode==0,(d['run_id'],done.stderr[-1000:])
            result=json.loads(done.stdout.splitlines()[-1]);result['run_id']=d['run_id']
            assert result['passed'] is True,(d['run_id'],result)
            expected=d['stages'][-1]['tests_run']
            assert result['tests_run']==expected,(d['run_id'],result['tests_run'],expected)
            results.append(result)
    assert len(results)==6
    print(json.dumps({'status':'passed','scope':'final snapshot acceptance only','isolation':isolation,
                      'snapshots':len(results),'assertions_as_test_methods':sum(r['tests_run'] for r in results),
                      'results':results},indent=2))


if __name__=='__main__':main()
