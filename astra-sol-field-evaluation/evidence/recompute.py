#!/usr/bin/env python3
"""Offline recomputation from exported candidate rows. Standard library; no model calls."""
import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
METRICS = ['input_tokens','output_tokens','reasoning_tokens','nonreasoning_tokens','total_tokens',
           'cache_read_tokens','cache_write_tokens','reference_cost_usd','cache_neutral_cost_usd',
           'elapsed_seconds','calls']
MODELS = ('gpt-5.6-sol','vega-alpha')


def fullsum(values):
    values = list(values)
    return sum(values) if all(x is not None for x in values) else None


def reduction(sol, vega):
    return 1 - vega / sol if sol not in (None, 0) and vega is not None else None


def median(values):
    values = [x for x in values if x is not None]
    return statistics.median(values) if values else None


def pair_rows(rows):
    groups = defaultdict(dict)
    for row in rows:
        key = row['cohort'], row['pair_id']
        assert row['model'] not in groups[key], ('duplicate candidate', key)
        groups[key][row['model']] = row
    pairs = []
    for key, group in sorted(groups.items()):
        assert set(group) == set(MODELS), ('incomplete pair', key)
        sol, vega = [group[m] for m in MODELS]
        fields = ['cohort','surface','lane','effort','treatment','case_id','design_id','repetition','pair_id']
        assert all(sol[x] == vega[x] for x in fields), ('mismatched pair', key)
        p = {x:sol[x] for x in fields}
        p.update(sol=sol, vega=vega, both_pass=sol['objective_success'] is True and vega['objective_success'] is True)
        pairs.append(p)
    return pairs


def metric_summary(pairs, metric, retry=False):
    def get(row):
        return row.get('retry_inclusive_' + metric, row.get(metric)) if retry else row.get(metric)
    sol_sum = fullsum(get(p['sol']) for p in pairs)
    vega_sum = fullsum(get(p['vega']) for p in pairs)
    valid = [p for p in pairs if get(p['sol']) is not None and get(p['vega']) is not None]
    designs = defaultdict(list)
    for p in valid:
        designs[p['design_id']].append(p)
    by_design = {d:reduction(sum(get(p['sol']) for p in ps), sum(get(p['vega']) for p in ps)) for d,ps in sorted(designs.items())}
    macro = [v for v in by_design.values() if v is not None]
    return {'sol_sum':sol_sum,'vega_sum':vega_sum,'aggregate_reduction':reduction(sol_sum,vega_sum),
            'paired_median_reduction':median(reduction(get(p['sol']),get(p['vega'])) for p in valid),
            'design_macro_mean_reduction':statistics.mean(macro) if macro else None,
            'design_reductions':by_design, 'valid_pairs':len(valid),
            'vega_lower_pairs':sum(get(p['vega']) < get(p['sol']) for p in valid),
            'equal_pairs':sum(get(p['vega']) == get(p['sol']) for p in valid),
            'vega_higher_pairs':sum(get(p['vega']) > get(p['sol']) for p in valid)}


def summarize(pairs, key):
    both = [p for p in pairs if p['both_pass']]
    result = {'key':key, 'pairs':len(pairs), 'designs':len({p['design_id'] for p in pairs}),
              'matched_pass_pairs':len(both),
              'all_assigned':{m:metric_summary(pairs,m) for m in METRICS},
              'matched_pass':{m:metric_summary(both,m) for m in METRICS},
              'retry_inclusive':{m:metric_summary(pairs,m,True) for m in METRICS}}
    for label in ('sol','vega'):
        rows = [p[label] for p in pairs]
        result[label] = {'passes':sum(r['objective_success'] is True for r in rows),
                         'failures':sum(r['objective_success'] is False for r in rows),
                         'ungraded_or_unresolved':sum(r['objective_success'] is None for r in rows),
                         'success_basis':dict(sorted(Counter(r['success_basis'] for r in rows).items())),
                         'median_elapsed_seconds':median(r['elapsed_seconds'] for r in rows)}
    return result


def derive():
    rows = json.loads((ROOT/'data/candidates.json').read_text())
    pairs = pair_rows(rows)
    groups = defaultdict(list)
    for p in pairs:
        key = ' / '.join([p['cohort'],p['lane'],p['effort'],p['treatment'],
                          'first' if p['repetition'] == 1 else 'repeat'])
        groups[key].append(p)
    strata = [summarize(ps,key) for key,ps in sorted(groups.items())]
    assert (len(rows),len(pairs),len(strata)) == (412,206,68)
    selectors = {
        'api_initial_high_objective':lambda p:p['cohort']=='api-v1' and p['effort']=='high' and p['repetition']==1 and p['sol']['success_basis']=='objective',
        'api_public_code_high':lambda p:p['cohort']=='campaign-v3' and p['lane']=='public-code',
        'api_exact_reasoning_high':lambda p:p['cohort']=='campaign-v4' and p['lane']=='frontier-reasoning' and p['effort']=='high',
        'api_compact_repo_medium':lambda p:p['cohort']=='campaign-v4' and p['lane']=='frontier-repo' and p['effort']=='medium',
        'api_staged_code_high_clean':lambda p:p['cohort']=='campaign-v4' and p['lane']=='staged-repo' and p['effort']=='high' and p['treatment']=='clean',
        'api_staged_code_medium_clean':lambda p:p['cohort']=='campaign-v4' and p['lane']=='staged-repo' and p['effort']=='medium' and p['treatment']=='clean',
        'api_long_context_high':lambda p:p['cohort']=='campaign-v4' and p['lane']=='context-extension' and p['effort']=='high',
        'api_v4_all_assigned':lambda p:p['cohort']=='campaign-v4',
        'api_cap_followup_high':lambda p:p['cohort']=='campaign-v4/cap-sensitivity',
        'codex_coding_high_first':lambda p:p['cohort']=='broad-v2' and p['lane']=='coding' and p['effort']=='high' and p['repetition']==1,
        'codex_reasoning_high_first':lambda p:p['cohort']=='broad-v2' and p['lane']=='reasoning' and p['effort']=='high' and p['repetition']==1,
        'codex_fde_high_first':lambda p:p['cohort']=='broad-v2' and p['lane']=='fde' and p['effort']=='high' and p['repetition']==1,
    }
    claims = {key:summarize([p for p in pairs if fn(p)],key) for key,fn in selectors.items()}
    for key,fn in selectors.items():
        claims[key]['pair_keys'] = [[p['cohort'],p['pair_id']] for p in pairs if fn(p)]
    assert claims['api_initial_high_objective']['pairs'] == 15
    assert claims['api_staged_code_high_clean']['pairs'] == 3
    assert claims['api_exact_reasoning_high']['pairs'] == 6
    return rows,pairs,strata,claims


def write_json(path, value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def write_csv(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,keys);w.writeheader()
        w.writerows({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in r.items()} for r in rows)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    rows,pairs,strata,claims=derive()
    flat=[]
    for p in pairs:
        item={k:v for k,v in p.items() if k not in ('sol','vega')}
        for label in ('sol','vega'):
            item[label+'_run_id']=p[label]['run_id']
            item[label+'_success']=p[label]['objective_success']
            for m in METRICS:item[label+'_'+m]=p[label].get(m)
        for m in METRICS:item[m+'_reduction']=reduction(p['sol'].get(m),p['vega'].get(m))
        flat.append(item)
    matrix=[]
    for s in strata:
        for scope in ('all_assigned','matched_pass','retry_inclusive'):
            for m in METRICS:
                matrix.append({'stratum':s['key'],'pairs':s['pairs'],'designs':s['designs'],
                               'matched_pass_pairs':s['matched_pass_pairs'],'scope':scope,'metric':m,
                               **s[scope][m]})
    outputs={'pairs.json':flat,'strata.json':strata,'claims.json':claims}
    for name,value in outputs.items():
        path=ROOT/'data'/name
        if args.check:assert json.loads(path.read_text())==value,('derived file mismatch',name)
        else:write_json(path,value)
    if not args.check:
        write_csv(ROOT/'data/pairs.csv',flat);write_csv(ROOT/'data/strata.csv',matrix)
    print(json.dumps({'status':'passed','candidates':len(rows),'pairs':len(pairs),'strata':len(strata),
                      'claims':len(claims),'mode':'check' if args.check else 'recompute'}))


if __name__=='__main__':main()
