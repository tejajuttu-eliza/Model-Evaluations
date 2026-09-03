# GPT-6 Astra vs GPT-5.6 Sol: early-access field evaluation

By Teja Juttu, Lead FDE at Eliza. September 2026.

**The task decides the upgrade.** The clearest local result was lower output-token usage on exact constraint reasoning. That advantage did not generalize to every task: high-effort staged coding used more output, and the earlier broad API objective set was approximately flat.

The public presentation focuses on general technical tasks and excludes the historically labeled FDE lanes: **364 candidate attempts / 182 matched pairs, with 18,419,092 recorded input + output tokens across both models**. This includes repeated and cached input; it is not a count of generated tokens or an all-in project bill. The [presentation scope](evidence/data/presentation-scope.json) records the filter and exact subtotals. The complete 412-candidate historical ledger remains available for audit.

These measurements compare the early-access `vega-alpha` alias with `gpt-5.6-sol`. They are shared in the context of the [GPT-6 Astra launch](https://deploymentsafety.openai.com/gpt-6-astra). The released Astra checkpoint has not been retested here; no identity between its exact weights/serving configuration and our early-access runs is asserted.

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

Standalone SVG and PNG versions of the five charts are included under `deck/charts/`. To regenerate them from the bundled data, run `python3 deck/build_charts.py` with Matplotlib installed, then `python3 deck/build_deck.py`. The chart manifest records the Matplotlib version and source-data hash. Viewing the HTML and PDF requires no Python packages.

## Results at a glance

All changes below are early-access Vega output relative to Sol. Output includes reported reasoning tokens once. Each row has its own high-effort protocol and task scope.

| API comparison | Designs / pairs | Passed Sol / Vega | Output change |
|---|---:|---:|---:|
| Exact constraint reasoning | 3 / 6 | 6/6 / 6/6 | 64.2% less |
| Staged repository changes, clean | 3 / 3 | 3/3 / 3/3 | 40.7% more |
| Earlier objective technical packets, FDE case excluded | 14 / 14 | 14/14 / 14/14 | 1.3% less |

The expanded 200-attempt campaign spans several efforts and task families: Sol passes 100/100 and Vega 98/100 under its frozen checks. These are fixture outcomes, not production acceptance rates. Both Vega failures occur on one repository design at high/xhigh effort under the response budget.

## Keep the boundaries visible

- **API and Codex are separate surfaces.** The public presentation scope contains 322 API attempts and 42 Codex assignments. The complete historical ledger contains 332 API and 80 Codex records; its additional 48 FDE-labeled attempts are excluded from the current presentation. Four fixed-output streaming probes and invalidated infrastructure attempts are separate records. API-backed custom tool workflows belong to the API group even though the evaluation was orchestrated from Codex.
- **Same effort is a setting, not equal compute.** Prompt/tool settings are documented per cohort; Codex runtime context and cache behavior are not fully controlled. An API/Codex comparison is descriptive, not a causal estimate of the interface.
- **Repeated attempts are not new designs.** Do not turn 412 candidate records into 412 independent tests. Task selection was exploratory and the groups are heterogeneous.
- **Quality and efficiency have different denominators.** Matched-success ratios condition on both candidates passing. All-attempt accounting retains failures; unknown grades and missing usage remain unknown. Grader amendments are identified in the evidence.
- **Tokens are not actual bills.** Reference costs apply a stated common Sol-price scenario to both models. Actual early-access billing, human review and repair time, and full orchestration cost were not established.
- **Reproducibility has a declared scope.** The package supports offline recalculation of exported measurements and selected synthetic examples. It is not a release of every original session, runtime instruction or model-serving environment, and it cannot recreate historical model draws. See the evidence README for the exact executable checks and omitted material.

The strongest operational use of these results is to select a representative workflow, fix its acceptance criteria, and measure correctness, all invoked resources, latency and human rework before choosing a model default.

The post also describes willingness to use subagents as a qualitative observation, not a scored result. The controlled Codex candidates were limited to packet tasks, and the API harness did not expose subagent spawning. This study does not establish that more delegation improves task success or reduces human supervision.
