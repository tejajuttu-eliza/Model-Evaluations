#!/usr/bin/env python3
"""Build the public-facing carousel from the adjacent, curated evidence snapshot."""
from pathlib import Path
import json
import html

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / 'deck-data.json').read_text())
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

slides = []
slides.append(slide('cover', 'GPT-6 Astra vs GPT-5.6 Sol',
    'The task decides<br>the <em>upgrade.</em>',
    '<p class="cover-lede">Where the early-access model saved tokens.<br>Where the advantage disappeared.</p>'
    '<p class="cover-author">An Eliza field evaluation · Teja</p>',
    'Findings from early-access Vega-alpha testing against GPT-5.6 Sol. The launch version has not been retested.',
    'Companion evidence package · scope and model provenance', 'cover'))

rows = [
    ('exact', 'Exact constraint reasoning', '3 designs · 6 passing pairs'),
    ('api', 'Earlier API task packets', '15 designs · 15 passing pairs'),
    ('public', 'Public coding subset', '16 designs · 16 passing pairs'),
    ('staged', 'Staged repository work', '3 clean workflows · 3 passing pairs'),
]
chart = '<div class="chart" role="img" aria-label="Vega output change relative to Sol. The direction changes across the four task families."><div class="chart-axis"><span>Fewer tokens</span><b>Same</b><span>More tokens</span></div>'
for key, label, detail in rows:
    v = metric(key)
    w = abs(v) / .7 * 50
    left = 50-w if v > 0 else 50
    signed = f'{-100*v:+.1f}%'.replace('-', '−')
    chart += f'<div class="chart-row"><div class="chart-label"><b>{label}</b><span>{detail}</span></div><div class="track"><div class="zero"></div><div class="bar" style="left:{left:.3f}%;width:{w:.3f}%"></div></div><strong>{signed}</strong></div>'
chart += '</div><p class="large-note">Same effort within each row: <b>high vs high.</b></p>'
slides.append(slide('api-results', 'Direct API · Vega output relative to Sol',
    'One model.<br><em>Opposite</em> token results.', chart,
    'Matched passing pairs; change in summed output tokens, including reasoning. Separate task families, not a pooled model effect. Repeats are not new designs.',
    'Companion evidence package · API claims and candidate ledger'))

codex = (f'<div class="surface-grid"><div><h3>Direct API</h3><div class="surface-count">332 <span>candidate workflows</span></div>'
    '<p>Explicit prompts and settings.<br>Provider usage and task-specific checks.</p></div>'
    '<div><h3>Codex</h3><div class="surface-count">80 <span>candidate assignments</span></div>'
    '<p>Model + app context + tools + cache.<br>Captured inputs differed by model.</p></div></div>'
    '<div class="codex-readout"><div class="readout-label">Vega vs Sol in Codex<br><span>Selected high-effort subsets</span></div>' +
    stat(pct(metric('codex_coding'))+' less', 'coding output', '3 designs / pairs · both 3 / 3 pass') +
    stat(pct(-metric('codex_fde'))+' more', 'FDE task output', '3 designs / pairs · recorded passes 2 / 3 each') + '</div>')
slides.append(slide('surfaces', 'Separate evidence surfaces',
    'API and Codex answer<br><em>different questions.</em>', codex,
    'Codex examples are synthetic packet tasks, not long repository work. FDE grading included model rubrics. Different tasks and runtime context prevent an API-versus-Codex causal comparison.',
    'Companion evidence package · surface inventory and Codex strata'))

quality = '<div class="quality-grid">' + stat('100 / 100', 'Sol objective passes', 'Expanded API campaign · assigned tasks') + stat('98 / 100', 'Vega objective passes', 'Expanded API campaign · assigned tasks') + '</div>'
quality += '<div class="statement"><b>Two Vega attempts hit the response cap.</b><span>Those failures stay in the result.</span></div>'
slides.append(slide('quality', 'Quality before efficiency',
    'Token efficiency matters<br><em>after it works.</em>', quality,
    '200 assigned attempts across 22 selected designs and multiple effort settings. Both failures were one repository design at high / xhigh. This is not established production-quality equivalence.',
    'Companion evidence package · primary outcomes and failure ledger'))

cap = data['groups']['cap']
slower = cap['vega']['median_elapsed_seconds'] / cap['sol']['median_elapsed_seconds'] - 1
latest = '<div class="two-stats">'+ stat(pct(metric('cap')), 'fewer Vega output tokens', 'One repository design · 2 pairs · high') + stat(pct(slower), 'longer completion time', 'Both models passed 2 / 2') + '</div>'
latest += '<p class="large-note">The latest follow-up showed <b>a small token difference.</b></p>'
slides.append(slide('recent', 'Recent completed follow-up',
    'The advantage can<br><em>get small.</em>', latest,
    'Fresh attempts used a larger budget, longer timeout and serial execution. Recovery does not prove the old cap caused the failures. Time is median end-to-end elapsed time, not decoding speed.',
    'Companion evidence package · response-budget follow-up'))

cost = '<div class="cost-flow">' + stat(f'{metric("context")*100:.0f}%', 'fewer Vega output tokens', 'Versus Sol · long-context workflows') + '<span class="arrow" aria-hidden="true">→</span>' + stat(f'~{metric("context", "reference_cost_usd")*100:.1f}%', 'lower reference cost', 'Same price assumptions for both') + '</div>'
cost += '<p class="large-note">Here, input dominated<br>the <b>provider cost estimate.</b></p>'
slides.append(slide('economics', 'Task economics',
    'Measure the full<br><em>cost of the task.</em>', cost,
    'High · 2 designs · 4 passing pairs. Shared Sol-rate scenario; Vega pricing was unverified. Provider calls only: review, tool hosting and orchestration costs are excluded.',
    'Companion evidence package · cost formula, input/cache/output accounting'))

method = '<div class="method-steps"><div><span>01</span><h3>Task</h3><p>Save the prompt.<br>Define acceptance.<br>Record effort and limits.</p></div><div><span>02</span><h3>Run</h3><p>Keep provider usage.<br>Separate API and Codex.<br>Count failures and retries.</p></div><div><span>03</span><h3>Review</h3><p>Inspect by task family.<br>Check human acceptance.<br>Publish the limitations.</p></div></div>'
method += '<a class="artifact-link" href="../evidence/README.md">Companion evidence package <span aria-hidden="true">↗</span></a>'
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
