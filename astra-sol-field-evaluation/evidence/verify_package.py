#!/usr/bin/env python3
"""Validate the allowlist, payload hashes, ledger identities, nulls, and privacy exclusions."""
import hashlib
import json
import math
import re
from pathlib import Path
from recompute import pair_rows, summarize

ROOT=Path(__file__).resolve().parent


def main():
    manifest=json.loads((ROOT/'PUBLIC_FILES.json').read_text())
    expected={x['path'] for x in manifest['files']}|{'PUBLIC_FILES.json'}
    present={str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    assert present==expected,('allowlist mismatch',sorted(present-expected),sorted(expected-present))
    for item in manifest['files']:
        p=ROOT/item['path'];assert p.resolve().is_relative_to(ROOT) and not p.is_symlink()
        content=p.read_bytes()
        assert len(content)==item['bytes'],('file size',item['path'])
        assert hashlib.sha256(content).hexdigest()==item['sha256'],('file hash',item['path'])
    forbidden=[r'/Users/[^/\s"\\]+/',r'/private/(?:tmp|var/folders)/[^\s"\\]+',
               r'\b(?:req|resp|rs)_[a-f0-9]{16,}\b',r'\bsk-[A-Za-z0-9_-]{16,}\b',
               r'https://preview[^\s"\\]*\.vercel\.app',r'\.slack\.com',r'encrypted_content\s*[:=]']
    hits=[]
    for name in expected:
        if name in ('verify_package.py','PUBLIC_FILES.json'):continue
        content=(ROOT/name).read_text()
        for pattern in forbidden:
            if re.search(pattern,content):hits.append((name,pattern))
    assert not hits,('excluded payload detected',hits)
    rows=json.loads((ROOT/'data/candidates.json').read_text())
    checks=0
    for r in rows:
        assert r['objective_success'] is None or isinstance(r['objective_success'],bool)
        assert r['total_tokens']==r['input_tokens']+r['output_tokens'];checks+=1
        assert r['nonreasoning_tokens']==r['output_tokens']-r['reasoning_tokens'];checks+=1
        assert r['cache_read_tokens']+r['cache_write_tokens']<=r['input_tokens'];checks+=1
        cost=(4*(r['input_tokens']-r['cache_read_tokens']-r['cache_write_tokens'])
              +.4*r['cache_read_tokens']+5*r['cache_write_tokens']+20*r['output_tokens'])/1e6
        assert math.isclose(cost,r['reference_cost_usd'],abs_tol=1e-10),(r['run_id'],'cost');checks+=1
    corrected=[r for r in rows if r['grading_amendment']]
    assert len(corrected)==1 and corrected[0]['recorded_objective_success'] is False and corrected[0]['objective_success'] is True
    archived=json.loads((ROOT/'data/infrastructure-attempts.json').read_text())
    assert len(archived)==3 and sum(r['missing_usage_calls'] for r in archived)==2
    assert all(r['input_tokens'] is None and r['reference_cost_usd'] is None for r in archived if r['missing_usage_calls'])
    scope=json.loads((ROOT/'data/presentation-scope.json').read_text())
    assert scope['excluded_lane_ids']==['fde','synthetic-FDE']
    selected=[r for r in rows if r['lane'] not in scope['excluded_lane_ids']]
    assert len(selected)==364 and len(pair_rows(selected))==182
    assert scope['source_candidate_sha256']==hashlib.sha256((ROOT/'data/candidates.json').read_bytes()).hexdigest()
    assert {tuple(x) for x in scope['included_candidate_keys']}=={(r['cohort'],r['run_id']) for r in selected}
    for key in ['input_tokens','output_tokens','total_tokens','reasoning_tokens','nonreasoning_tokens','cache_read_tokens','cache_write_tokens','calls']:
        assert scope['totals'][key]==sum(r.get(key,0) or 0 for r in selected),('presentation total',key)
        for label,flag in [('Codex',True),('Responses API',False)]:
            subset=[r for r in selected if (r['surface']=='Codex subagent')==flag]
            assert scope['by_surface'][label][key]==sum(r.get(key,0) or 0 for r in subset),('presentation surface',label,key)
            for model in scope['by_model']:
                model_rows=[r for r in subset if r['model']==model]
                assert scope['by_surface_and_model'][label][model][key]==sum(r.get(key,0) or 0 for r in model_rows)
        for model in scope['by_model']:
            assert scope['by_model'][model][key]==sum(r.get(key,0) or 0 for r in selected if r['model']==model)
    selected_pairs=pair_rows(selected)
    for key,view in scope['chart_claims'].items():
        wanted={tuple(x) for x in view['pair_keys']}
        pairs=[p for p in selected_pairs if (p['cohort'],p['pair_id']) in wanted]
        observed=summarize(pairs,key);observed['pair_keys']=[[p['cohort'],p['pair_id']] for p in pairs]
        assert observed==view,('presentation chart',key)
    print(json.dumps({'status':'passed','allowlisted_files':len(expected),'ledger_checks':checks,
                      'excluded_payload_hits':0,'amendment_preserved':True,'unknown_usage_preserved':True,
                      'presentation_candidates':364,'presentation_tokens':scope['totals']['total_tokens']}))


if __name__=='__main__':main()
