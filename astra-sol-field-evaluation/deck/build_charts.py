#!/usr/bin/env python3
"""Render standalone Matplotlib charts from the curated evidence snapshot.

Requires matplotlib. No API calls or external data access are performed.
"""
from pathlib import Path
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = Path(__file__).resolve().parent
OUT = HERE / 'charts'
OUT.mkdir(exist_ok=True)
data = json.loads((HERE / 'deck-data.json').read_text())
for weight in [400, 600, 700]:
    font_manager.fontManager.addfont(HERE / 'assets' / f'inter-{weight}.ttf')
plt.rcParams.update({'font.family':'Inter', 'font.size':16, 'text.color':'#3A3A3A',
                     'axes.edgecolor':'#D9D4D1', 'axes.labelcolor':'#3A3A3A',
                     'xtick.color':'#666666', 'ytick.color':'#3A3A3A',
                     'svg.fonttype':'path', 'svg.hashsalt':'eliza-field-evaluation',
                     'figure.facecolor':'none', 'axes.facecolor':'none'})
INK, ORANGE, PEACH, GRID = '#3A3A3A', '#D84D1E', '#F6D2C5', '#E8E3DF'
records = []


def reduction(key):
    g = data['groups'][key]
    return 1 - g['astra']['output_tokens'] / g['sol']['output_tokens']


def finish(fig, name, description):
    fig.savefig(OUT / f'{name}.svg', transparent=True,
                metadata={'Date':None, 'Description':description, 'Creator':'Matplotlib'})
    svg_path = OUT / f'{name}.svg'
    svg_path.write_text('\n'.join(line.rstrip() for line in svg_path.read_text().splitlines()) + '\n')
    fig.savefig(OUT / f'{name}.png', dpi=150, transparent=False, facecolor='white',
                metadata={'Description':description})
    plt.close(fig)
    records.append({'name':name, 'description':description,
                    'svg_sha256':hashlib.sha256(svg_path.read_bytes()).hexdigest()})


def clean(ax):
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis='both', length=0)
    ax.set_axisbelow(True)


def output_comparison(key, name, maximum, ticks, detail, description):
    """Show absolute output totals on a common zero-based axis."""
    fig = plt.figure(figsize=(11.64, 2.65), dpi=100)
    ax = fig.add_axes([.11, .24, .76, .57])
    clean(ax)
    g = data['groups'][key]
    vals = [g['sol']['output_tokens'], g['astra']['output_tokens']]
    ax.barh([1, 0], vals, height=.52, color=[INK, ORANGE])
    ax.set_xlim(0, maximum)
    ax.set_ylim(-.7, 1.7)
    ax.set_yticks([1, 0], ['Sol', 'Astra'])
    ax.tick_params(axis='y', labelsize=19, pad=16)
    ax.set_xticks(ticks, [f'{tick:,}' for tick in ticks])
    ax.tick_params(axis='x', labelsize=12, pad=8)
    ax.grid(axis='x', color=GRID, linewidth=.7)
    for y, value in zip([1, 0], vals):
        ax.text(value + maximum * .018, y, f'{value:,}', va='center', fontsize=22, weight=600)
    fig.text(.11, .985, 'Summed output tokens, including reasoning', fontsize=14, va='top')
    fig.text(.11, .025, detail, fontsize=14, va='bottom')
    finish(fig, name, description)


output_comparison('exact', 'exact-output', 35000, [0, 10000, 20000, 30000],
    'High reasoning effort · Matched tasks and acceptance checks',
    'Exact constraint reasoning output: Sol 30,679, Astra 10,968; 64.2% fewer Astra output tokens including reasoning. Selected matched high-effort tasks; full test scope is in the evidence.')

output_comparison('context', 'long-context-output', 8000, [0, 2000, 4000, 6000, 8000],
    'High reasoning effort · Matched tasks and acceptance checks',
    'Long-context output: Sol 6,979, Astra 4,957; 29.0% fewer Astra output tokens including reasoning. Selected matched high-effort tasks. Input and cached context excluded from this comparison; full test scope is in the evidence.')

# Codex families use the same token scale and remain separate from API tasks.
fig = plt.figure(figsize=(11.64, 2.75), dpi=100)
for i, (key, title) in enumerate([('codex_coding', 'Coding'), ('codex_reasoning', 'Reasoning')]):
    left = .075 + i * .50
    ax = fig.add_axes([left, .21, .335, .48])
    clean(ax)
    g = data['groups'][key]
    vals = [g['sol']['output_tokens'], g['astra']['output_tokens']]
    ax.barh([1, 0], vals, height=.5, color=[INK, ORANGE])
    ax.set_xlim(0, 2500)
    ax.set_ylim(-.7, 1.7)
    ax.set_yticks([1, 0], ['Sol', 'Astra'])
    ax.tick_params(axis='y', labelsize=15, pad=12)
    ax.set_xticks([0, 1000, 2000], ['0', '1,000', '2,000'])
    ax.tick_params(axis='x', labelsize=11)
    ax.grid(axis='x', color=GRID, linewidth=.7)
    for y, value in zip([1, 0], vals):
        ax.text(value + 48, y, f'{value:,}', va='center', fontsize=15, weight=600)
    fig.text(left, .96, title, fontsize=19, weight=600, va='top')
    fig.text(left + .335, .96, f'{100 * reduction(key):.1f}% less', fontsize=21,
             weight=600, color=ORANGE, ha='right', va='top')
    fig.text(left, .035, 'Matched high-effort comparison', fontsize=13, va='bottom')
finish(fig, 'codex-output',
    'Codex output tokens including reasoning. Coding: Sol 1,674, Astra 1,403. Reasoning: Sol 2,185, Astra 1,622. Selected matched high-effort tasks. Unequal runtime context; not an API-versus-Codex causal comparison.')

# Preserve the mixed picture across API families; zero is the explicit reference.
fig = plt.figure(figsize=(11.64, 2.75), dpi=100)
ax = fig.add_axes([.43, .09, .43, .77])
spec = [('exact', 'Exact constraint reasoning'),
        ('api', 'Earlier technical API packets'),
        ('public', 'Public coding subset'),
        ('staged', 'Staged repository work')]
ax.set_xlim(-70, 45)
ax.set_ylim(-.5, 3.5)
ax.axvline(0, color='#AAA29D', linewidth=1)
ax.set_xticks([])
ax.set_yticks([])
clean(ax)
for i, (key, label) in enumerate(spec):
    y = 3 - i
    change = -100 * reduction(key)
    ax.barh(y, change, color=ORANGE, height=.42)
    fy = .09 + .77 * (y + .5) / 4
    fig.text(.005, fy, label, fontsize=16.6, weight=600, va='center')
    fig.text(.992, fy, f'{change:+.1f}%', fontsize=25, weight=600, ha='right', va='center')
fig.text(.43, .97, 'Fewer Astra tokens', fontsize=12.8, va='top')
fig.text(.86, .97, 'More Astra tokens', fontsize=12.8, va='top', ha='right')
finish(fig, 'api-output',
    'Astra output relative to Sol at high effort. Exact reasoning -64.2%; earlier technical API -1.3%; public coding +1.1%; staged repositories +40.7%. Separate task families; output includes reasoning.')

(OUT / 'manifest.json').write_text(json.dumps({
    'tool':'Matplotlib', 'version':matplotlib.__version__,
    'deck_data_sha256':hashlib.sha256((HERE / 'deck-data.json').read_bytes()).hexdigest(),
    'charts':records}, indent=2) + '\n')
print(json.dumps({'charts':len(records), 'out':'charts/'}))
