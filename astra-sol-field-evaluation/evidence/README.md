# Task-dependent model economics: supporting evidence

Measurements from early-access **Vega-alpha versus GPT-5.6 Sol**, shared in the context of the GPT-6 Astra launch. **The released checkpoint was not retested.** The original tested aliases remain in every record. This is an exploratory, local study of selected tasks, not an official model benchmark or a representative estimate of customer production performance.

The useful finding is narrower than “the new model is cheaper”: output-token savings depend on the task, effort, execution environment, and success boundary. Some controlled reasoning tasks used much less output. Some coding tasks used more. Provider-reported output includes reasoning tokens; it is not the length of the final answer.

## Current presentation scope: 18.4 million recorded tokens

The public presentation excludes the existing `fde` and `synthetic-FDE` task lanes. Its **364 candidates / 182 pairs** comprise **322 API candidates and 42 Codex candidates**, totaling **18,419,092 recorded tokens**: 17,448,967 input plus 970,125 output. Input includes 13,375,899 cache-read and 3,899,585 cache-write tokens. These are provider/session accounting units across repeated requests, not 18.4 million newly generated tokens, unique words, or an actual dollar spend.

The exact classifier, included/excluded record keys, surface/model breakdowns, and filtered chart calculations are in [presentation-scope.json](data/presentation-scope.json). The **full historical 412-candidate ledger remains unchanged** for transparency. This narrower presentation omits 48 FDE-labeled candidates totaling 2,705,207 tokens; it does not relabel the historical tasks.

One chart changes with that scope: the original 15-pair objective API subset included FDE case F1. Excluding it leaves 14 pairs, both 14/14 passing, with **1.3% fewer Vega output tokens**—near parity. Its historical 15-pair result of 1.7% more remains in [claims.json](data/claims.json). The exact-reasoning, staged-coding, public-code, expanded success-rate, cap-follow-up, and long-context chart subsets contain no excluded lane rows.

## Start with these results

All percentages below use `1 − sum(Vega output) / sum(Sol output)`. A negative reduction means Vega used more. The API and Codex rows are separate experiments.

| Surface and subset | Designs / paired attempts | Sol output | Vega output | Observation |
|---|---:|---:|---:|---|
| API: exact constraint reasoning, high effort | 3 / 6 | 30,679 | 10,968 | 64.2% less; both passed all 6 |
| API: staged repository coding, high effort, clean | 3 / 3 | 34,579 | 48,660 | 40.7% more; both passed all 3 |
| API: initial objective tasks excluding FDE, high effort, first attempt | 14 / 14 | 6,654 | 6,565 | 1.3% less; both passed all 14 |
| API: adapted public coding subset, high effort | 16 / 16 | 5,656 | 5,717 | 1.1% more; both passed after the documented grader correction |
| Codex: coding, high effort, first attempt | 3 / 3 | 1,674 | 1,403 | 16.2% less; both passed all 3; unequal runtime context |
| Codex: reasoning, high effort, first attempt | 3 / 3 | 2,185 | 1,622 | 25.8% less; both passed all 3; unequal runtime context |

The [current presentation calculations](data/presentation-scope.json), full historical [claim calculations](data/claims.json), [paired table](data/pairs.csv), and [68-stratum table](data/strata.csv) include counterexamples, unresolved grades, repetitions, and conditional versus all-assigned metrics. Do not pool all workloads into one model ranking. Six repeated observations of three designs are not six independent unseen designs.

## Full historical study inventory

| Cohort | Surface | Candidate attempts |
|---|---|---:|
| pilot-v1 | Codex subagents; provisional FDE rubric | 12 |
| high-v1 | Codex subagents; ungraded | 12 |
| broad-v2 | Codex subagents; coding, debugging, reasoning, FDE | 56 |
| api-v1 | Direct Responses API packets | 58 |
| campaign-v3 | Responses API: public coding, exact constraints, context, compact repositories | 70 |
| campaign-v4 | Responses API: multiple efforts, exact/tool reasoning, vision, context, repositories | 200 |
| campaign-v4/cap-sensitivity | Separate Responses API response-budget follow-up | 4 |
| **Main inventory** | **80 Codex + 332 API; 206 matched pairs** | **412** |

Four fixed-output streaming probes are supplementary and appear only in [stream-probes.json](data/stream-probes.json). They are not four additional task-success trials. Three original invalidated/interrupted attempts appear separately in [infrastructure-attempts.json](data/infrastructure-attempts.json). Their known usage is included in the corresponding retry-inclusive fields; missing usage remains unknown. Judge calls, coordinator work, and human-review time are outside this candidate inventory.

The initial API packet comparisons supplied equal task prompts directly. The historical Codex assignments included different inherited/runtime context: first-high coding inputs totaled 222,134 Sol versus 194,634 Vega tokens. These results cannot identify whether API or Codex itself changes relative model performance. The API repository runs used a custom tool harness; they are not native Codex sessions. Autonomous subagent delegation was not measured: the 80 historical Codex candidates were fixed one-read packets, and the API harness did not expose agent spawning. The evaluator's parallel workers are not evidence that one candidate model chooses to delegate more.

## Reproduce the calculations locally

Python 3.10+ and its standard library suffice for arithmetic and exact-answer validation. No API key, provider account, network request, or new model call is needed. Run the commands below from this `evidence/` directory. The repository-root README provides commands with the full relative paths.

```sh
python3 -B recompute.py --check
python3 -B verify_examples.py
python3 -B verify_package.py
```

`recompute.py --check` independently rebuilds the pair joins, all 68 strata, and named claim subsets from [candidates.json](data/candidates.json), then checks the distributed derived files. Without `--check`, it writes fresh derived JSON/CSV files. It does not execute candidate code.

`verify_examples.py` independently enumerates the three exact constraint instances, regrades all 12 high-effort answers behind the 64.2% result, rejects 36 deliberately invalid answer controls, and reconciles the 12 short API answer records with the normalized usage ledger. It executes no model-generated code. The grader verifies numerical feasibility/optimality and certificates; it does not verify the semantics of each free-text explanation.

An optional final-code replay uses the original macOS sandbox wrapper. It requires `/usr/bin/sandbox-exec` and Python at `/opt/homebrew/bin/python3` (the Apple Silicon Homebrew layout); the wrapper selects that exact interpreter. It is not portable to Intel or nonstandard Python installations without adapting and revalidating the isolation. It denies network access and private-file reads outside the supplied inputs, and confines writes to a temporary workspace. It stops if the sandbox is unavailable; there is no unsandboxed fallback.

```sh
python3 -B verify_staged.py
```

That replay executes six archived final code snapshots against the original public and stage-0/stage-1 acceptance tests: 21 test methods per snapshot, 126 total. It does **not** replay the model generations, tool sequence, elapsed time, all intermediate edits, or persistence continuity across model stages. Passing these narrow tests is not proof of general coding quality equivalence. See [VERIFICATION.json](VERIFICATION.json) for the recorded export checks.

## What is actually exported

The complete normalized candidate and pair ledgers are exported. The complete raw traces are not.

- **Exact reasoning:** all 3 designs and 12 answer records behind the campaign-v4 high-effort result, frozen objective data, grader, and an independently implemented exhaustive search.
- **Short API examples:** prompts and answers for 6 synthetic coding/reasoning designs, first high-effort pair only: 12 answers. Their recorded usage is reconciled; the complete original coding graders are not bundled.
- **Staged coding:** 3 two-stage synthetic contracts; 6 immutable final source snapshots for the clean high-effort comparison; recorded stage outcomes; the 9 acceptance-test files. Both retained candidate tests and archived scratch checks are included where present in the snapshots.
- **All other main rows:** normalized metrics, outcome fields, and protocol identity only. Public benchmark prompts, image inputs, long-context packets, original Codex contexts, full event streams, and full tool traces are not included. The public coding rows are an adapted 16-task subset, not a full HumanEval/EvalPlus score.

The selected examples were chosen after the exploratory results to expose the main positive result and its coding counterexample. They are supporting records, not a new blinded confirmatory sample. Twelve additional cases / 48 planned calls remained unrun and are absent from all outcome tables.

The [file allowlist](PUBLIC_FILES.json) names every distributable file and its SHA-256. Private collaboration sources, customer material, credentials, private documentation, local filesystem paths, request/response identifiers, and encrypted reasoning are excluded. Usage rows are exported observations rather than independently signed provider receipts. Hashes detect subsequent file changes; they do not authenticate the provider or prove which model weights produced a response.

## Interpretation and important corrections

1. **The quality gate matters.** Campaign-v4 has 100/100 Sol and 98/100 Vega primary workflow passes. The two Vega failures reached a response budget before delivering a usable patch on the same repository design. A later, separately configured follow-up passed 2/2 for each model; it does not erase the failures or isolate the cause of recovery.
2. **Recent tests showed smaller savings.** The separate budget follow-up used only 4.1% fewer Vega output tokens and 37.9% more elapsed time across two pairs. That result supports neither a universal token reduction nor a universal speed advantage.
3. **Retries can reverse apparent economics.** Fresh medium-effort staged coding used 18.6% fewer Vega output tokens. Including the archived collateral interruption changes this to 5.3% more output and 15.0% higher reference cost. The interruption is infrastructure overhead, not evidence that the model caused it.
4. **Tokens are not dollars or compute.** Reference costs apply the same Sol rates to both aliases. They are not actual Vega or released Astra bills, and reported reasoning tokens do not measure internal compute. The formula per million tokens is `4*(input−cache_read−cache_write) + 0.4*cache_read + 5*cache_write + 20*output`. Reasoning tokens are already part of output and are not charged twice. Rates are documented in the [Sol model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-sol).
5. **Input can dominate.** In the high-effort long-context subset, a 29.0% output reduction translated to about 1.4% lower reference cost. Cached-input behavior and request length also matter.
6. **Grading was not immutable in every exploratory cohort.** The HE096 Sol answer was initially rejected by an overrestrictive bytearray guard. The corrected grade, original recorded failure, and an explicit amendment flag remain in the data. Pilot labels are provisional; high-v1 is ungraded; rubric-only and unresolved outcomes remain `null`. Details are in [AMENDMENTS.md](AMENDMENTS.md).
7. **Small, selected samples limit generalization.** Effort, task design, treatment, response caps, and repetition stay separate. Aggregate savings weight large Sol outputs more heavily; paired medians and equal-design means can differ substantially. For example, the exact high-effort 64.2% aggregate reduction is 56.9% when averaging the three design-level reductions equally.

No confidence interval here establishes population-level noninferiority, broad task success equivalence, or a causal model-architecture explanation. The next useful evidence would be preregistered unseen tasks, a released-checkpoint retest, matched tool/runtime conditions, and measured human acceptance/editing time.
