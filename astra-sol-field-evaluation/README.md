# GPT-6 Astra vs GPT-5.6 Sol: early-access field evaluation

By Teja Juttu, Lead FDE at Eliza. September 2026.

**Selected early-access highlights: less output on reasoning, Codex coding and long-context tasks.** The clearest local result was 64.2% fewer output tokens on exact constraint reasoning, with both models passing the same six runs. The deck focuses on supported positives and keeps task-dependent results visible; the complete historical evidence remains available below.

The public presentation focuses on general technical tasks and excludes the historically labeled FDE lanes: **364 candidate attempts / 182 matched pairs, with 18,419,092 recorded input + output tokens across both models**. This includes repeated and cached input; it is not a count of generated tokens or an all-in project bill. The [presentation scope](evidence/data/presentation-scope.json) records the filter and exact subtotals. The complete 412-candidate historical ledger remains available for audit.

These measurements compare early-access Astra with GPT-5.6 Sol. The export uses `astra-early-access` and `gpt-5.6-sol` as public model labels, not provider routing identifiers. They are shared in the context of the [GPT-6 Astra launch](https://deploymentsafety.openai.com/gpt-6-astra). The released Astra checkpoint has not been retested here; no identity between its exact weights/serving configuration and our early-access runs is asserted.

## Read the findings

- [Eight-page PDF](deck/astra-sol-field-evaluation.pdf)
- [HTML source for the local interactive carousel](deck/index.html)
- [Post text](linkedin-post.md)
- [Evidence, methodology and reproduction instructions](evidence/README.md)
- [Every exported candidate](evidence/data/candidates.csv)
- [Paired comparisons](evidence/data/pairs.csv)
- [All 68 comparison strata](evidence/data/strata.csv)
- [Claim calculations and scopes](evidence/data/claims.json)

For immediate viewing on GitHub, open the PDF. GitHub displays the HTML as source: download or clone the repository, then open this package's `deck/index.html` locally and use the arrow keys or controls to move between pages. Fonts and images are bundled.

From this package directory (`astra-sol-field-evaluation/` in the repository), verify the exported calculations and selected answers with Python 3.10+:

```sh
python3 -B evidence/recompute.py --check
python3 -B evidence/verify_examples.py
python3 -B evidence/verify_package.py
```

These commands make no API calls and execute no model-generated code. See the evidence README for the separate optional staged-code replay.

Standalone SVG and PNG versions of the four charts are included under `deck/charts/`. To regenerate them from the bundled data, run `python3 deck/build_charts.py` with Matplotlib installed, then `python3 deck/build_deck.py`. The chart manifest records the Matplotlib version and source-data hash. Viewing the HTML and PDF requires no Python packages.

## Results at a glance

All changes below are early-access Astra output relative to Sol. Output includes reported reasoning tokens once. Each row has its own high-effort protocol and task scope.

| Surface / comparison | Designs / pairs | Passed Sol / Astra | Output change |
|---|---:|---:|---:|
| API: exact constraint reasoning | 3 / 6 | 6/6 / 6/6 | 64.2% less |
| API: long-context tasks | 2 / 4 | 4/4 / 4/4 | 29.0% less |
| Codex: coding packets | 3 / 3 | 3/3 / 3/3 | 16.2% less |
| Codex: reasoning packets | 3 / 3 | 3/3 / 3/3 | 25.8% less |
| API: staged repository changes, clean | 3 / 3 | 3/3 / 3/3 | 40.7% more |
| API: earlier objective technical packets, FDE case excluded | 14 / 14 | 14/14 / 14/14 | 1.3% less |

Long-context pairs cover two designs at two context sizes. The selected passing-pair comparisons above do not imply equal success across the full campaign. All assigned outcomes, including response-cap failures and later follow-up runs, remain in the [complete evidence](evidence/README.md). These are fixture outcomes, not production acceptance rates.

## Keep the boundaries visible

- **API and Codex are separate surfaces.** The public presentation scope contains 322 API attempts and 42 Codex assignments. The complete historical ledger contains 332 API and 80 Codex records; its additional 48 FDE-labeled attempts are excluded from the current presentation. Four fixed-output streaming probes and invalidated infrastructure attempts are separate records. API-backed custom tool workflows belong to the API group even though the evaluation was orchestrated from Codex.
- **Same effort is a setting, not equal compute.** Prompt/tool settings are documented per cohort; Codex runtime context and cache behavior are not fully controlled. An API/Codex comparison is descriptive, not a causal estimate of the interface.
- **Repeated attempts are not new designs.** Do not turn 412 candidate records into 412 independent tests. Task selection was exploratory and the groups are heterogeneous.
- **Quality and efficiency have different denominators.** Matched-success ratios condition on both candidates passing. All-attempt accounting retains failures; unknown grades and missing usage remain unknown. Grader amendments are identified in the evidence.
- **Pricing was not established.** The deck and post show output-token measurements without dollar estimates. Historical common-rate scenarios remain labeled in the evidence and are not actual Astra charges.
- **Early-access latency is not a GA speed ranking.** Serving conditions may affect elapsed time. The study did not isolate infrastructure from model behavior, so neither a speed conclusion nor an infrastructure explanation is established.
- **Reproducibility has a declared scope.** The package supports offline recalculation of exported measurements and selected synthetic examples. It is not a release of every original session, runtime instruction or model-serving environment, and it cannot recreate historical model draws. See the evidence README for the exact executable checks and omitted material.

The strongest operational use of these results is to select a representative workflow, fix its acceptance criteria, and measure correctness, all invoked resources, latency and human rework before choosing a model default.

The post also describes willingness to use subagents as a qualitative observation, not a scored result. The controlled Codex candidates were limited to packet tasks, and the API harness did not expose subagent spawning. This study does not establish that more delegation improves task success or reduces human supervision.
