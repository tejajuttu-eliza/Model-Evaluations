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
    'The early signals<br>are <em>promising.</em>',
    '<p class="cover-lede">Selected highlights from our<br>API and Codex evaluations at Eliza.</p>'
    '<p class="cover-scope"><b>364 candidate attempts</b> · <b>18.4M recorded tokens</b></p>'
    '<p class="cover-author">Early access, real experiments · Teja</p>',
    'Input + output, including cached and repeated context, across both models. Tested Vega-alpha, now named GPT-6 Astra. Selected exploratory findings; results vary by task.',
    'Companion evidence package · scope and model provenance', 'cover'))

exact = plot('exact-output',
    'Exact reasoning output tokens: Sol 30,679; Vega 10,968. Vega used 64.2% fewer output tokens, including reasoning. Three designs with two repetitions each; six high-effort pairs; both models passed all six.')
exact += '<p class="large-note">Same acceptance checks. <b>Both models passed every run in this slice.</b></p>'
slides.append(slide('exact', 'Direct API · Exact constraint reasoning',
    f'Exact reasoning.<br><em>{metric("exact"):.1f}% fewer output tokens.</em>', exact,
    'Matched passing pairs; change in summed output tokens, including reasoning. Three designs with two repetitions each. Same configured effort does not imply equal compute.',
    'Companion evidence package · exact reasoning claims and candidate ledger'))

codex = ('<p class="scope-line">Public comparison scope: <b>322 API attempts</b> · <b>42 Codex assignments</b></p>'
    '<p class="plot-kicker">Within Codex · output tokens including reasoning · Vega vs Sol</p>' +
    plot('codex-output',
    'Codex coding: Sol 1,674 output tokens, Vega 1,403, 16.2% less. Codex reasoning: Sol 2,185, Vega 1,622, 25.8% less. Three high-effort pairs per family; both models passed all three.', 'codex-plot'))
slides.append(slide('surfaces', 'API and Codex · Separate evidence surfaces',
    'Efficiency signals<br><em>in Codex, too.</em>', codex,
    'Codex used synthetic packet tasks with unequal runtime inputs. These selected high-effort comparisons are separate from API results; different tasks and context prevent a causal comparison between surfaces.',
    'Companion evidence package · surface inventory and Codex strata'))

context = plot('long-context-output',
    'Long-context output tokens: Sol 6,979; Vega 4,957. Vega used 29.0% fewer output tokens including reasoning. Two designs at two context sizes; four high-effort pairs; both models passed all four.')
context += '<p class="large-note"><b>Both models passed</b> across the two context sizes.</p>'
slides.append(slide('context', 'Direct API · Multi-turn long context',
    f'Long context.<br><em>{metric("context"):.1f}% fewer output tokens.</em>', context,
    'High vs high · 2 designs at nominal 96k and 192k context sizes · 4 passing pairs. This comparison is output only, including reasoning; input and cached context are excluded.',
    'Companion evidence package · long-context candidates and usage'))

delegation = ('<p class="observation-lede">Eliza teammates described Astra using<br>'
    '<b>subagents more naturally</b> and needing<br>'
    '<b>less steering</b> on longer implementations.</p>'
    '<div class="observation-flow" aria-label="Reported workflow: plan, delegate scoped tasks, coordinate implementation">'
    '<span>Plan</span><i aria-hidden="true">→</i><span>Delegate</span><i aria-hidden="true">→</i><span>Coordinate</span></div>'
    '<p class="observation-label">A practitioner signal worth testing next.</p>')
slides.append(slide('delegation', 'Practitioner observations · Codex',
    'A more natural<br><em>delegation workflow.</em>', delegation,
    'Qualitative reports from Eliza engineers, not a measured benchmark result. The candidate harness assigned scoped tasks; it did not measure autonomous subagent usage or coordination.',
    'Eliza practitioner observations · engineering feedback supplied for this evaluation'))

families = plot('api-output',
    'Vega output relative to Sol: exact reasoning 64.2% fewer; earlier technical API packets 1.3% fewer; public coding subset 1.1% more; staged repository work 40.7% more.')
families += '<p class="large-note">Same effort within each row: <b>high vs high.</b></p>'
slides.append(slide('task-fit', 'Direct API · Vega output relative to Sol',
    'Match the model<br><em>to the task.</em>', families,
    'Matched passing pairs; summed output tokens, including reasoning. These are separate task families, not a pooled effect. Efficiency gains vary by workload; repeats are not new designs.',
    'Companion evidence package · API claims and candidate ledger'))

method = ('<div class="method-steps"><div><span>01</span><h3>Task</h3><p>Save the prompt.<br>Define acceptance.<br>Record effort and limits.</p></div>'
    '<div><span>02</span><h3>Run</h3><p>Keep provider usage.<br>Separate API and Codex.<br>Record every outcome.</p></div>'
    '<div><span>03</span><h3>Review</h3><p>Inspect by task family.<br>Check human acceptance.<br>Share the evidence.</p></div></div>')
method += '<a class="artifact-link" href="https://github.com/tejajuttu-eliza/Model-Evaluations/tree/main/astra-sol-field-evaluation/evidence">View evidence on GitHub <span aria-hidden="true">↗</span></a>'
slides.append(slide('evidence', 'An inspectable evaluation',
    'The evidence should<br><em>travel with the claim.</em>', method,
    'Small exploratory samples and repeated designs cannot establish a universal ranking. Full outcomes, retries and measurement limits remain in the evidence package. Early-access results are not a GA retest.',
    'Companion evidence package · methodology, claims, candidates and strata'))

close = ('<p class="closing-lede">The exciting signal: <b>less generated output<br>with passing results</b> in selected<br>reasoning and coding comparisons.</p>'
    '<p class="closing-line">Next: longer workflows and more autonomous execution.<br>What are you seeing in your own builds?</p>')
slides.append(slide('takeaway', 'What we are excited to explore next',
    'More room<br>to <em>build.</em>', close,
    'An early-access field study of Vega-alpha and GPT-5.6 Sol. Evaluate your own acceptance criteria and current deployed versions before generalizing these selected findings.',
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
