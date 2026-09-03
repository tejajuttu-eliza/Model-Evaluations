#!/usr/bin/env python3
"""Build the public-facing carousel from the adjacent, curated evidence snapshot."""
from pathlib import Path
import json
import html
import hashlib

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / 'deck-data.json').read_text())
chart_manifest = json.loads((HERE / 'charts/manifest.json').read_text())
assert chart_manifest['deck_data_sha256'] == hashlib.sha256((HERE / 'deck-data.json').read_bytes()).hexdigest(), 'Rebuild the charts after changing the evidence snapshot.'
esc = lambda s: html.escape(str(s))
pct = lambda f: f'{100 * f:.1f}%'

def metric(key, field='output_tokens'):
    row = data['groups'][key]
    return 1 - row['vega'][field] / row['sol'][field]

def slide(key, eyebrow, title, body, note, sources, cls=''):
    return dict(key=key, eyebrow=eyebrow, title=title, body=body,
                note=note, sources=sources, cls=cls)

def stat(value, label, detail='', cls=''):
    return f'<div class="stat {cls}"><strong>{value}</strong><h3>{label}</h3><p>{detail}</p></div>'

def plot(name, alt, css=''):
    return f'<figure class="plot {css}"><img src="charts/{name}.svg" alt="{esc(alt)}"></figure>'

slides = []
slides.append(slide('cover', 'GPT-6 Astra vs GPT-5.6 Sol',
    'The task decides<br>the <em>upgrade.</em>',
    '<p class="cover-lede">Where the early-access model saved tokens.<br>Where the advantage disappeared.</p>'
    '<p class="cover-scope"><b>364 candidate attempts</b> · <b>18.4M recorded tokens</b></p>'
    '<p class="cover-author">An Eliza field evaluation · Teja</p>',
    'Input + output, including cached context, across both models. Early-access Vega-alpha vs GPT-5.6 Sol; not a launch-version retest. Attempts are not independent designs.',
    'Companion evidence package · scope and model provenance', 'cover'))

chart = plot('api-output','Vega output relative to Sol: exact reasoning 64.2% fewer; earlier technical API packets 1.3% fewer; public coding subset 1.1% more; staged repository work 40.7% more.')
chart += '<p class="large-note">Same effort within each row: <b>high vs high.</b></p>'
slides.append(slide('api-results', 'Direct API · Vega output relative to Sol',
    'One model.<br><em>Opposite</em> token results.', chart,
    'Matched passing pairs; change in summed output tokens, including reasoning. Separate task families, not a pooled model effect. Repeats are not new designs.',
    'Companion evidence package · API claims and candidate ledger'))

codex = ('<p class="scope-line">Public comparison scope: <b>322 API workflows</b> · <b>42 Codex assignments</b></p>'
    '<p class="plot-kicker">Within Codex · output tokens including reasoning · Vega vs Sol</p>' +
    plot('codex-output','Codex coding: Sol 1674 output tokens, Vega 1403, 16.2% less. Codex reasoning: Sol 2185, Vega 1622, 25.8% less. Three high-effort pairs per family; both models pass all three.', 'codex-plot'))
slides.append(slide('surfaces', 'Separate evidence surfaces',
    'API and Codex need<br><em>separate readouts.</em>', codex,
    'FDE-specific lanes excluded; full historical ledger preserved. Codex used synthetic packet tasks with unequal runtime inputs. Different tasks and runtime context prevent an API-versus-Codex causal comparison.',
    'Companion evidence package · surface inventory and Codex strata'))

quality = plot('quality-outcomes','One square per assigned attempt. Sol passed 100 of 100. Vega passed 98 of 100, with two response-cap failures.','quality-plot')
quality += '<p class="large-note"><b>Those two failures stay in the result.</b></p>'
slides.append(slide('quality', 'Quality before efficiency',
    'Token efficiency matters<br><em>after it works.</em>', quality,
    '200 assigned attempts across 22 selected designs and multiple effort settings. Both failures were one repository design at high / xhigh. This is not established production-quality equivalence.',
    'Companion evidence package · primary outcomes and failure ledger'))

cap = data['groups']['cap']
slower = cap['vega']['median_elapsed_seconds'] / cap['sol']['median_elapsed_seconds'] - 1
latest = plot('recent-index','Two measures indexed separately to Sol 100. Vega generated output index 95.9 and completion time index 137.9. Output sums 22529 versus 21603; median elapsed times 155.6 versus 214.5 seconds.','recent-plot')
latest += '<p class="large-note">A small token difference. <b>A longer wait.</b></p>'
slides.append(slide('recent', 'Recent completed follow-up',
    'The advantage can<br><em>get small.</em>', latest,
    'Fresh attempts used a larger budget, longer timeout and serial execution. Recovery does not prove the old cap caused the failures. Time is median end-to-end elapsed time, not decoding speed.',
    'Companion evidence package · response-budget follow-up'))

cost = '<div class="cost-metrics">' + stat(f'{metric("context")*100:.0f}%', 'fewer Vega output tokens') + stat(f'~{metric("context", "reference_cost_usd")*100:.1f}%', 'lower reference cost') + '</div>'
cost += plot('context-cost','Provider-reference cost across four long-context pairs: Sol input and cache $3.342, output $0.140; Vega input and cache $3.333, output $0.099. Input dominates.','cost-plot')
cost += '<p class="cost-conclusion">Input dominated the provider cost estimate.</p>'
slides.append(slide('economics', 'Task economics',
    'Measure the full<br><em>cost of the task.</em>', cost,
    'High · 2 designs · 4 passing pairs. Shared Sol-rate scenario; Vega pricing was unverified. Provider calls only: review, tool hosting and orchestration costs are excluded.',
    'Companion evidence package · cost formula, input/cache/output accounting'))

method = '<div class="method-steps"><div><span>01</span><h3>Task</h3><p>Save the prompt.<br>Define acceptance.<br>Record effort and limits.</p></div><div><span>02</span><h3>Run</h3><p>Keep provider usage.<br>Separate API and Codex.<br>Count failures and retries.</p></div><div><span>03</span><h3>Review</h3><p>Inspect by task family.<br>Check human acceptance.<br>Publish the limitations.</p></div></div>'
method += '<a class="artifact-link" href="https://github.com/tejajuttu-eliza/Model-Evaluations/tree/main/astra-sol-field-evaluation/evidence">View evidence on GitHub <span aria-hidden="true">↗</span></a>'
slides.append(slide('evidence', 'An inspectable evaluation',
    'The evidence should<br><em>travel with the claim.</em>', method,
    'Small exploratory samples and repeated designs cannot establish a universal model ranking. The package separates candidate outcomes, measurement boundaries and public-release limitations.',
    'Companion evidence package · methodology, claims, candidates and strata'))

close = '<p class="closing-lede">At Eliza, the decision is the workflow:<br><b>accepted result, elapsed time,<br>and total cost including repair.</b></p>'
close += '<p class="closing-line">Route by task.<br>Keep the failures in the ledger.</p>'
slides.append(slide('takeaway', 'What this changes for delivery',
    'Test the workflow.<br><em>Then choose the model.</em>', close,
    'An early-access field study of Vega-alpha and GPT-5.6 Sol. The next decision should use your own acceptance criteria and current deployed versions.',
    'Eliza · technical delivery and model evaluation', 'closing'))

frames = []
for i, s in enumerate(slides, 1):
    frames.append(f'''<section class="slide {s['cls']}" id="{s['key']}" aria-label="Slide {i} of {len(slides)}: {esc(s['title'].replace('<br>', ' ').replace('<em>','').replace('</em>',''))}">
      <header><p class="eyebrow">{s['eyebrow']}</p><img class="logo" src="assets/eliza-logo-black.png" alt="Eliza"></header>
      <h1>{s['title']}</h1><div class="body">{s['body']}</div>
      <aside class="note">{s['note']}</aside>
      <footer><span class="provenance">Tested: Vega-alpha vs GPT-5.6 Sol · Early access · Not a GA retest</span><span>{i:02} / {len(slides):02}</span></footer>
      <span class="source" data-source="{esc(s['sources'])}"></span>
    </section>''')

page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GPT-6 Astra vs GPT-5.6 Sol — Eliza early-access field evaluation</title><meta name="description" content="An exploratory early-access model evaluation: token savings change by task family, execution surface and acceptance criteria."><link rel="stylesheet" href="deck.css"></head><body><main>''' + '\n'.join(frames) + '''</main><nav class="controls" aria-label="Presentation controls"><button id="prev" aria-label="Previous slide">←</button><span id="counter" aria-live="polite">1 / 8</span><button id="next" aria-label="Next slide">→</button><button id="overview" aria-pressed="false">Overview</button><button id="fullscreen">Full screen</button><a href="astra-sol-field-evaluation.pdf">Download PDF</a><a href="../evidence/README.md">Evidence</a></nav><script src="deck.js"></script></body></html>'''
(HERE/'index.html').write_text(page)
(HERE/'slides.json').write_text(json.dumps([{k:v for k,v in s.items() if k != 'body'} for s in slides], indent=2)+'\n')
print(json.dumps({'slides':len(slides),'html':'index.html'}))
