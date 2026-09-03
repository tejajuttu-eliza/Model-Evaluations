#!/usr/bin/env python3
"""Build the public carousel from the adjacent curated evidence snapshot."""
from pathlib import Path
import json
import html
import hashlib

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / 'deck-data.json').read_text())
chart_manifest = json.loads((HERE / 'charts/manifest.json').read_text())
assert chart_manifest['deck_data_sha256'] == hashlib.sha256((HERE / 'deck-data.json').read_bytes()).hexdigest(), 'Rebuild the charts after changing the evidence snapshot.'
esc = lambda value: html.escape(str(value))


def metric(key):
    row = data['groups'][key]
    return 100 * (1 - row['vega']['output_tokens'] / row['sol']['output_tokens'])


def slide(key, eyebrow, title, body, note, sources, cls=''):
    return dict(key=key, eyebrow=eyebrow, title=title, body=body,
                note=note, sources=sources, cls=cls)


def plot(name, alt, css=''):
    return f'<figure class="plot {css}"><img src="charts/{name}.svg" alt="{esc(alt)}"></figure>'


slides = []
slides.append(slide('cover', 'GPT-6 Astra vs GPT-5.6 Sol',
    'Where Astra improves<br><em>on Sol.</em>',
    '<p class="cover-lede">Selected early-access results from our<br>API and Codex evaluations at Eliza.</p>'
    '<p class="cover-scope"><b>364 candidate attempts</b> · <b>18.4M recorded tokens</b></p>'
    '<p class="cover-author">Early access, real experiments · Teja</p>',
    'Recorded tokens include input, output and cached/repeated context across both models. Vega-alpha is the early-access model; results vary by task.',
    'Companion evidence package · scope and model provenance', 'cover'))

exact = plot('exact-output',
    'Exact reasoning output tokens: Sol 30,679; Astra 10,968. Astra used 64.2% fewer output tokens, including reasoning. Three designs with two repetitions each; six high-effort pairs; both models passed all six.')
exact += '<p class="large-note">Compared with Sol. <b>The same acceptance checks passed.</b></p>'
slides.append(slide('exact', 'API · Astra vs Sol · Exact reasoning',
    f'Exact reasoning.<br><em>{metric("exact"):.1f}% fewer output tokens.</em>', exact,
    'Summed output includes reasoning. Small exploratory sample; the same effort setting does not imply equal compute.',
    'Companion evidence package · exact reasoning claims and candidate ledger'))

codex = ('<p class="scope-line">Public comparison scope: <b>322 API attempts</b> · <b>42 Codex assignments</b></p>'
    '<p class="plot-kicker">Astra vs Sol · Output tokens, including reasoning</p>' +
    plot('codex-output',
    'Codex coding: Sol 1,674 output tokens, Astra 1,403, 16.2% less. Codex reasoning: Sol 2,185, Astra 1,622, 25.8% less. Three high-effort pairs per family; both models passed all three.', 'codex-plot'))
slides.append(slide('surfaces', 'API and Codex · Separate evidence surfaces',
    'Less output than Sol.<br><em>In Codex, too.</em>', codex,
    'Synthetic packet tasks; runtime context differed by model. Read these results separately from the API tests.',
    'Companion evidence package · surface inventory and Codex strata'))

context = plot('long-context-output',
    'Long-context output tokens: Sol 6,979; Astra 4,957. Astra used 29.0% fewer output tokens including reasoning. Two designs at two context sizes; four high-effort pairs; both models passed all four.')
context += '<p class="large-note"><b>Both models passed</b> across the two context sizes.</p>'
slides.append(slide('context', 'API · Astra vs Sol · Long context',
    f'Long context.<br><em>{metric("context"):.1f}% fewer output tokens.</em>', context,
    'Nominal 96k and 192k context sizes. Output includes reasoning; input and cached context are excluded from this comparison.',
    'Companion evidence package · long-context candidates and usage'))

delegation = ('<p class="observation-lede">Eliza teammates described Astra using<br>'
    '<b>subagents more naturally</b> and needing<br>'
    '<b>less steering</b> on longer implementations.</p>'
    '<div class="observation-flow" aria-label="Reported workflow: plan, delegate scoped tasks, coordinate implementation">'
    '<span>Plan</span><i aria-hidden="true">→</i><span>Delegate</span><i aria-hidden="true">→</i><span>Coordinate</span></div>'
    '<p class="observation-label">A practitioner signal worth testing next.</p>')
slides.append(slide('delegation', 'Practitioner observations · Codex',
    'A more natural<br><em>delegation workflow.</em>', delegation,
    'Qualitative Eliza engineering feedback. Autonomous delegation and coordination were not measured in the benchmark.',
    'Eliza practitioner observations · engineering feedback supplied for this evaluation'))

families = plot('api-output',
    'Astra output relative to Sol: exact reasoning 64.2% fewer; earlier technical API packets 1.3% fewer; public coding subset 1.1% more; staged repository work 40.7% more.')
families += '<p class="large-note">Same effort within each row: <b>high vs high.</b></p>'
slides.append(slide('task-fit', 'Direct API · Astra output relative to Sol',
    'Match the model<br><em>to the task.</em>', families,
    'Separate task families and matched passing pairs. Output includes reasoning. Gains vary by workload; repeats are not new designs.',
    'Companion evidence package · API claims and candidate ledger'))

method = ('<div class="method-steps"><div><span>01</span><h3>Task</h3><p>Save the prompt.<br>Define acceptance.<br>Record effort and limits.</p></div>'
    '<div><span>02</span><h3>Run</h3><p>Keep provider usage.<br>Separate API and Codex.<br>Record every outcome.</p></div>'
    '<div><span>03</span><h3>Review</h3><p>Inspect by task family.<br>Check human acceptance.<br>Share the evidence.</p></div></div>')
method += '<a class="artifact-link" href="https://github.com/tejajuttu-eliza/Model-Evaluations/tree/main/astra-sol-field-evaluation/evidence">View evidence on GitHub <span aria-hidden="true">↗</span></a>'
slides.append(slide('evidence', 'An inspectable evaluation',
    'The evidence should<br><em>travel with the claim.</em>', method,
    'Full outcomes, retries and limits are linked. Small exploratory samples and repeated runs do not establish a universal ranking.',
    'Companion evidence package · methodology, claims, candidates and strata'))

close = ('<p class="closing-lede">On selected tasks, Astra used<br><b>fewer output tokens than Sol<br>with the same checks passed.</b></p>'
    '<p class="closing-line">Next: longer workflows and more autonomous execution.<br>What are you seeing in your own builds?</p>')
slides.append(slide('takeaway', 'What we are excited to explore next',
    'A promising upgrade.<br><em>For the right tasks.</em>', close,
    'Validate the current models on your own tasks and acceptance criteria before generalizing these early-access findings.',
    'Eliza · technical delivery and model evaluation', 'closing'))

frames = []
for i, s in enumerate(slides, 1):
    frames.append(f'''<section class="slide {s['cls']}" id="{s['key']}" aria-label="Slide {i} of {len(slides)}: {esc(s['title'].replace('<br>', ' ').replace('<em>', '').replace('</em>', ''))}">
      <header><p class="eyebrow">{s['eyebrow']}</p><img class="logo" src="assets/eliza-logo-black.png" alt="Eliza"></header>
      <h1>{s['title']}</h1><div class="body">{s['body']}</div>
      <aside class="note">{s['note']}</aside>
      <footer><span class="provenance">Tested: Vega-alpha vs GPT-5.6 Sol · Early access · Not a GA retest</span><span>{i:02} / {len(slides):02}</span></footer>
      <span class="source" data-source="{esc(s['sources'])}"></span>
    </section>''')

page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GPT-6 Astra vs GPT-5.6 Sol - Eliza early-access field evaluation</title><meta name="description" content="Selected early-access evaluation highlights: output-token efficiency in reasoning, long context and Codex, with task-level evidence and clear measurement boundaries."><link rel="stylesheet" href="deck.css"></head><body><main>''' + '\n'.join(frames) + '''</main><nav class="controls" aria-label="Presentation controls"><button id="prev" aria-label="Previous slide">←</button><span id="counter" aria-live="polite">1 / 8</span><button id="next" aria-label="Next slide">→</button><button id="overview" aria-pressed="false">Overview</button><button id="fullscreen">Full screen</button><a href="astra-sol-field-evaluation.pdf">Download PDF</a><a href="../evidence/README.md">Evidence</a></nav><script src="deck.js"></script></body></html>'''
(HERE / 'index.html').write_text(page)
(HERE / 'slides.json').write_text(json.dumps([{k:v for k,v in s.items() if k != 'body'} for s in slides], indent=2) + '\n')
print(json.dumps({'slides':len(slides), 'html':'index.html'}))
