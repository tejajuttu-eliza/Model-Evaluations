# GPT-6 Astra vs GPT-5.6 Sol: early-access field evaluation

By Teja Juttu, Lead FDE at Eliza. September 2026.

**The task decides the upgrade.** The clearest local result was lower output-token usage on exact constraint reasoning. That advantage did not generalize to every task: high-effort staged coding used more output, and the earlier broad API objective set was approximately flat.

These measurements compare the early-access `vega-alpha` alias with `gpt-5.6-sol`. They are shared in the context of the [GPT-6 Astra launch](https://deploymentsafety.openai.com/gpt-6-astra). The released Astra checkpoint has not been retested here; no identity between its exact weights/serving configuration and our early-access runs is asserted.

## Read the findings

- [Eight-page PDF](deck/astra-sol-field-evaluation.pdf)
- [Interactive HTML carousel](deck/index.html)
- [Post text](linkedin-post.md)
- [Evidence, methodology and reproduction instructions](evidence/README.md)
- [Every exported candidate](evidence/data/candidates.csv)
- [Paired comparisons](evidence/data/pairs.csv)
- [All 68 comparison strata](evidence/data/strata.csv)
- [Claim calculations and scopes](evidence/data/claims.json)

The HTML runs locally with bundled fonts and images. Open `deck/index.html`; use the arrow keys or controls to move between pages. The PDF is the document attachment for the post.

## Results at a glance

All changes below are early-access Vega output relative to Sol. Output includes reported reasoning tokens once. Each row has its own high-effort protocol and task scope.

| API comparison | Designs / pairs | Passed Sol / Vega | Output change |
|---|---:|---:|---:|
| Exact constraint reasoning | 3 / 6 | 6/6 / 6/6 | 64.2% less |
| Staged repository changes, clean | 3 / 3 | 3/3 / 3/3 | 40.7% more |
| Earlier broad objective packets | 15 / 15 | 15/15 / 15/15 | 1.7% more |

The expanded 200-attempt campaign spans several efforts and task families: Sol passes 100/100 and Vega 98/100 under its frozen checks. These are fixture outcomes, not production acceptance rates. Both Vega failures occur on one repository design at high/xhigh effort under the response budget.

## Keep the boundaries visible

- **API and Codex are separate surfaces.** The candidate ledger contains 332 API attempts and 80 Codex attempts. Four fixed-output streaming probes and invalidated infrastructure attempts are separate records. API-backed custom tool workflows belong to the API group even though the evaluation was orchestrated from Codex.
- **Same effort is a setting, not equal compute.** Prompt/tool settings are documented per cohort; Codex runtime context and cache behavior are not fully controlled. An API/Codex comparison is descriptive, not a causal estimate of the interface.
- **Repeated attempts are not new designs.** Do not turn 412 candidate records into 412 independent tests. Task selection was exploratory and the groups are heterogeneous.
- **Quality and efficiency have different denominators.** Matched-success ratios condition on both candidates passing. All-attempt accounting retains failures; unknown grades and missing usage remain unknown. Grader amendments are identified in the evidence.
- **Tokens are not actual bills.** Reference costs apply a stated common Sol-price scenario to both models. Actual early-access billing, human review and repair time, and full orchestration cost were not established.
- **Reproducibility has a declared scope.** The package supports offline recalculation of exported measurements and selected synthetic examples. It is not a release of every original session, runtime instruction or model-serving environment, and it cannot recreate historical model draws. See the evidence README for the exact executable checks and omitted material.

The strongest operational use of these results is to select a representative workflow, fix its acceptance criteria, and measure correctness, all invoked resources, latency and human rework before choosing a model default.
