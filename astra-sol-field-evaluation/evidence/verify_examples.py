#!/usr/bin/env python3
"""Regrade the exported exact answers without executing model-generated source code."""
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def main():
    exact=ROOT/'examples/exact-reasoning'
    grader=load('public_exact_grader',exact/'grader.py')
    search=load('public_exact_search',exact/'verify_oracles.py')
    oracles=json.loads((exact/'oracles.json').read_text())
    for cid,o in oracles.items():
        observed=search.independent_search(o['family'],o['instance'])
        assert observed=={k:o[k] for k in observed},cid
    rows=json.loads((ROOT/'data/candidates.json').read_text())
    by_id={(r['cohort'],r['run_id']):r for r in rows}
    answers=json.loads((exact/'answers.json').read_text())
    positive=negative=0
    for answer in answers:
        cid=answer['case_id'];text=answer['answer_text']
        assert grader.grade(cid,text)['pass'] is True,answer['run_id']
        positive+=1
        altered=json.loads(text);altered['objective']+=1
        for bad in [json.dumps(altered),'{}','{"status":"optimal","objective":0,"objective":1}']:
            assert grader.grade(cid,bad)['pass'] is False,(answer['run_id'],'negative control')
            negative+=1
        row=by_id[('campaign-v4',answer['run_id'])]
        for k in ['input_tokens','output_tokens','reasoning_tokens']:
            assert answer[k]==row[k],(answer['run_id'],k)
    short=json.loads((ROOT/'examples/short-api/records.json').read_text())
    short_count=0
    for case in short:
        for answer in case['answers']:
            row=by_id[('api-v1',answer['run_id'])]
            for k in ['input_tokens','output_tokens','total_tokens']:
                assert answer['usage'][k]==row[k],(answer['run_id'],k)
            short_count+=1
    assert positive==12 and negative==36 and short_count==12
    print(json.dumps({'status':'passed','independently_enumerated_oracles':len(oracles),
                      'exact_answers_regraded':positive,'negative_grader_controls':negative,
                      'short_api_metadata_matches':short_count,
                      'short_api_generated_code_executed':False}))


if __name__=='__main__':main()
