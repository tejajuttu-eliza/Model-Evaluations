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
from matplotlib.patches import Rectangle

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

def reduction(key, field='output_tokens'):
    g=data['groups'][key]
    return 1-g['vega'][field]/g['sol'][field]

def finish(fig, name, description):
    fig.savefig(OUT/f'{name}.svg', transparent=True, metadata={'Date':None,'Description':description,'Creator':'Matplotlib'})
    svg_path = OUT / f'{name}.svg'
    svg_path.write_text('\n'.join(line.rstrip() for line in svg_path.read_text().splitlines()) + '\n')
    fig.savefig(OUT/f'{name}.png', dpi=150, transparent=False, facecolor='white', metadata={'Description':description})
    plt.close(fig)
    records.append({'name':name,'description':description,'svg_sha256':hashlib.sha256((OUT/f'{name}.svg').read_bytes()).hexdigest()})

def clean(ax):
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(axis='both',length=0)
    ax.set_axisbelow(True)

# Change direction across separate API families; zero is an explicit reference.
fig=plt.figure(figsize=(11.64,2.75),dpi=100)
ax=fig.add_axes([.43,.09,.43,.77])
spec=[('exact','Exact constraint reasoning','3 designs · 6 passing pairs'),
      ('api','Earlier technical API packets','14 designs · 14 passing pairs'),
      ('public','Public coding subset','16 designs · 16 passing pairs'),
      ('staged','Staged repository work','3 clean workflows · 3 passing pairs')]
ax.set_xlim(-70,45);ax.set_ylim(-.5,3.5)
ax.axvline(0,color='#AAA29D',linewidth=1)
ax.set_xticks([]);ax.set_yticks([]);clean(ax)
for i,(key,label,detail) in enumerate(spec):
    y=3-i; change=-100*reduction(key)
    ax.barh(y,change,color=ORANGE,height=.42)
    fy=.09+.77*(y+.5)/4
    fig.text(.005,fy+.027,label,fontsize=16.6,weight=600,va='center')
    fig.text(.005,fy-.046,detail,fontsize=12.2,color='#666666',va='center')
    fig.text(.992,fy,f'{change:+.1f}%'.replace('-','−'),fontsize=25,weight=600,ha='right',va='center')
fig.text(.43,.97,'Fewer Vega tokens',fontsize=12.8,va='top')
fig.text(.86,.97,'More Vega tokens',fontsize=12.8,va='top',ha='right')
finish(fig,'api-output','Vega output relative to Sol at high effort. Exact reasoning minus64.2%; earlier technical API minus1.3%; public coding plus1.1%; staged repositories plus40.7%. Separate task families; output includes reasoning.')

# Two Codex families use the same token scale, but are not pooled with API tasks.
fig=plt.figure(figsize=(11.64,2.75),dpi=100)
for i,(key,title) in enumerate([('codex_coding','Coding'),('codex_reasoning','Reasoning')]):
    left=.075+i*.50
    ax=fig.add_axes([left,.21,.335,.48]);clean(ax)
    g=data['groups'][key]
    vals=[g['sol']['output_tokens'],g['vega']['output_tokens']]
    ax.barh([1,0],vals,height=.5,color=[INK,ORANGE])
    ax.set_xlim(0,2500);ax.set_ylim(-.7,1.7)
    ax.set_yticks([1,0],['Sol','Vega']);ax.tick_params(axis='y',labelsize=15,pad=12)
    ax.set_xticks([0,1000,2000],['0','1,000','2,000']);ax.tick_params(axis='x',labelsize=11)
    ax.grid(axis='x',color=GRID,linewidth=.7)
    for y,v in zip([1,0],vals):ax.text(v+48,y,f'{v:,}',va='center',fontsize=15,weight=600)
    fig.text(left,.96,title,fontsize=19,weight=600,va='top')
    fig.text(left+.335,.96,f'{100*reduction(key):.1f}% less',fontsize=21,weight=600,color=ORANGE,ha='right',va='top')
    fig.text(left,.035,'3 high-effort pairs · both models 3 / 3 pass',fontsize=13,va='bottom')
finish(fig,'codex-output','Codex output tokens including reasoning. Coding: Sol1674,Vega1403. Reasoning: Sol2185,Vega1622. Each3high-effort pairs,both3/3pass. Unequal runtime context; not an API-versus-Codex causal comparison.')

# One tile represents one assigned workflow attempt, preserving the two failures.
fig=plt.figure(figsize=(11.64,2.65),dpi=100)
for i,model in enumerate(['sol','vega']):
    x=.025+i*.52
    ax=fig.add_axes([x,.02,.17,.93]);ax.set_aspect('equal');ax.set_xlim(0,10);ax.set_ylim(0,10);ax.axis('off')
    q=data['quality'][model]
    assert q['assigned']==100
    for n in range(100):
        failed=n>=q['passed'];col=n%10;row=9-n//10
        ax.add_patch(Rectangle((col+.04,row+.04),.84,.84,facecolor='white' if failed else INK,
                               edgecolor=ORANGE if failed else INK,linewidth=1.4 if failed else 0))
        if failed:
            ax.plot([col+.2,col+.72],[row+.2,row+.72],color=ORANGE,lw=1.3)
            ax.plot([col+.2,col+.72],[row+.72,row+.2],color=ORANGE,lw=1.3)
    fig.text(x+.215,.79,f'{q["passed"]} / {q["assigned"]}',fontsize=39,weight=600,color=ORANGE,va='center')
    fig.text(x+.215,.53,f'{model.title()} objective passes',fontsize=16.8,weight=600,va='center')
    fig.text(x+.215,.30,'0 failed' if model=='sol' else '2 response-cap failures',fontsize=15,va='center')
fig.text(.025,.995,'Each square = one assigned attempt',fontsize=12.5,color='#666666',va='top')
finish(fig,'quality-outcomes','Expanded API campaign: Sol100of100passed; Vega98of100passed with2response-cap failures. Each of200tiles represents one assigned attempt across22selected designs; not independent designs.')

# Normalize each measure to its own Sol value; no mixing of tokens and seconds.
fig=plt.figure(figsize=(11.64,2.9),dpi=100)
g=data['groups']['cap']
for i,(field,title,detail) in enumerate([
    ('output_tokens','Output tokens','22,529 → 21,603 tokens · sum over 2 pairs'),
    ('median_elapsed_seconds','Elapsed time','155.6 → 214.5 seconds · median elapsed')]):
    left=.075+i*.50;ax=fig.add_axes([left,.27,.335,.43]);clean(ax)
    ratio=g['vega'][field]/g['sol'][field];vals=[100,100*ratio]
    ax.barh([1,0],vals,height=.5,color=[INK,ORANGE])
    ax.set_xlim(0,160);ax.set_ylim(-.7,1.7)
    ax.set_yticks([1,0],['Sol','Vega']);ax.tick_params(axis='y',labelsize=15,pad=12)
    ax.set_xticks([0,50,100,150]);ax.tick_params(axis='x',labelsize=11)
    ax.grid(axis='x',color=GRID,linewidth=.7)
    for y,v in zip([1,0],vals):ax.text(v+3,y,f'{v:.1f}' if y==0 else '100',va='center',fontsize=15,weight=600)
    fig.text(left,.96,title,fontsize=19,weight=600,va='top')
    delta=(ratio-1)*100
    fig.text(left+.335,.96,f'{abs(delta):.1f}% '+('less' if delta<0 else 'longer'),fontsize=21,weight=600,color=ORANGE,ha='right',va='top')
    fig.text(left,.10,detail,fontsize=12.4,va='bottom')
fig.text(.045,.008,'Within each measure, Sol = 100. One repository design · 2 high-effort pairs · both models 2 / 2 pass.',fontsize=12.5,va='bottom')
finish(fig,'recent-index','Recent response-budget follow-up,2pairs. Output sum Sol22529,Vega21603:4.1%lessVega. Median elapsed Sol155.5715s,Vega214.5022s:37.9%longerVega. Separate axes normalized to Sol100.')

# Dollar stacks show the provider-reference input and output components, not bills.
fig=plt.figure(figsize=(11.64,1.9),dpi=100)
ax=fig.add_axes([.065,.25,.68,.59]);clean(ax)
g=data['groups']['context']
ax.set_xlim(0,3.6);ax.set_ylim(-.65,1.65)
for y,model in zip([1,0],['sol','vega']):
    c=g[model];inp=c['reference_input_cost_usd'];out=c['reference_output_cost_usd']
    ax.barh(y,inp,color=INK,height=.45)
    ax.barh(y,out,left=inp,color=ORANGE,height=.45)
    ax.text(inp/2,y,f'Input + cache  ${inp:.3f}',ha='center',va='center',color='white',fontsize=14,weight=600)
    fig.text(.77,.25+.59*(y+.65)/2.3,f'Output  ${out:.3f}',fontsize=14,weight=600,va='center',color=ORANGE)
ax.set_yticks([1,0],['Sol','Vega']);ax.tick_params(axis='y',labelsize=15,pad=14)
ax.set_xticks([0,1,2,3],['$0','$1','$2','$3']);ax.tick_params(axis='x',labelsize=11);ax.grid(axis='x',color=GRID,linewidth=.7)
fig.text(.065,.99,'Reference provider cost across 4 workflow pairs',fontsize=13,va='top')
finish(fig,'context-cost','Reference provider cost across4high-effort long-context workflow pairs. Sol input/cache3.3424462,output.13958,total3.4820262USD. Vega input/cache3.3326824,output.09914,total3.4318224USD. Shared Sol-rate scenario; not actual Vega billing.')

(OUT/'manifest.json').write_text(json.dumps({'tool':'Matplotlib','version':matplotlib.__version__,
    'deck_data_sha256':hashlib.sha256((HERE/'deck-data.json').read_bytes()).hexdigest(),
    'charts':records},indent=2)+'\n')
print(json.dumps({'charts':len(records),'out':'charts/'}))
