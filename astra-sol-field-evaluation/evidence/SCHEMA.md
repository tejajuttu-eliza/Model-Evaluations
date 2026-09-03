# Export schemas

All JSON is UTF-8. CSV empty numeric/boolean cells represent unknown or unavailable values, not zero. JSON is canonical when this distinction matters.

## Candidate identity and quality

`data/candidates.json` contains 412 candidate workflow/packet/session observations. The unique key is `(cohort, run_id)`. Pairing uses `(cohort, pair_id)` and requires exactly one `gpt-5.6-sol` and one `vega-alpha` row with matching lane, design, effort, treatment, and repetition.

| Field | Meaning |
|---|---|
| `cohort`, `surface`, `lane` | Campaign, execution surface, and task family; never pooled as equivalent conditions |
| `design_id`, `case_id` | Authored design and case identity within the campaign; repeated IDs across campaigns need not be new designs |
| `effort`, `treatment`, `repetition` | Tested reasoning setting, harness condition, and repeat index |
| `model` | Alias actually used; no retrospective relabeling of the checkpoint |
| `objective_success` | Effective recorded outcome: true/false/null. Its strength is described by `success_basis` |
| `success_basis` | Objective tests, rubric, provisional judgment, or ungraded; these are not interchangeable |
| `recorded_objective_success`, `phase_success` | Earlier recorded outcome(s), before a documented grading amendment where applicable |
| `adjudicated`, `grading_amendment` | Explicit post-run grading change; currently the HE096 bytearray correction |
| `review_disputed`, `human_accepted` | Review metadata when available; absence/null does not mean rejected |
| `status` | Recorded completion/harness state; completion is not identical to quality success |

## Resource fields

| Field | Meaning |
|---|---|
| `input_tokens`, `output_tokens`, `total_tokens` | Provider/session-recorded consumption for the active candidate; total = input + output |
| `reasoning_tokens` | Reported reasoning subset of output |
| `nonreasoning_tokens` | Output minus reported reasoning; may include tool calls and other emitted text, not only final prose |
| `cache_read_tokens`, `cache_write_tokens` | Reported input categories; included within input, not added on top |
| `reference_cost_usd` | Same Sol reference-rate estimate applied to both tested aliases; never actual billing |
| `cache_neutral_cost_usd` | Counterfactual treating all input at ordinary-input rates, with unchanged observed output |
| `elapsed_seconds` | Candidate workflow/packet/session elapsed time; sums are not campaign wall time |
| `provider_seconds` | Sum of measured call durations when available; excludes portions of local orchestration |
| `calls`, `tool_calls`, `public_test_calls` | Recorded request/tool/test counts; definitions differ by surface |
| `missing_usage_calls` | Calls in that active observation without terminal usage |
| `known_*` | Known subtotals. A known subtotal is not the full amount when usage is missing |
| `retry_inclusive_*` | Active observation plus associated archived invalidated/interrupted attempt(s); null if any amount is unknown |
| `physical_attempts` | Number of original/replacement physical attempts represented when recorded |
| `first_request_input_tokens`, `maximum_request_input_tokens` | Per-request context diagnostics, not a claim of prompt equivalence |

Optional fields may be absent when a surface did not record them. Missing retry-inclusive fields mean no separately archived retry is associated and the active value is used by the recomputation. `data/infrastructure-attempts.json` retains three archived attempts individually; do not add them again after using retry-inclusive fields.

## Derived tables

`data/pairs.json/csv` contains 206 pairs with each candidate's values and reductions. `data/strata.json/csv` has 68 distinct cohort/lane/effort/treatment/first-or-repeat groups. CSV uses one row per metric and scope; its 2,244 metric rows are not 2,244 independent strata.

Three scopes are calculated:

- `all_assigned`: active recorded candidates, with failed/ungraded candidates retained.
- `matched_pass`: pairs for which both effective outcomes are true; a conditional subset, not a general success claim.
- `retry_inclusive`: all assigned plus associated archived attempt overhead; unknown amounts stay null.

`aggregate_reduction = 1 − sum(Vega) / sum(Sol)`. `paired_median_reduction` is the median of valid pair reductions. `design_macro_mean_reduction` first combines repeats within each design, then equally averages the valid design reductions. Zero Sol denominators yield null. A sum with an unknown component yields null, while explicitly labeled known subtotals remain available.

`data/claims.json` names 12 selected views and lists the exact `(cohort,pair_id)` keys used by each. Its campaign-wide view supplies success counts and an inventory; its heterogeneous resource aggregate should not be presented as a model ranking.

## Current public presentation selection

`data/presentation-scope.json` is an additional view over the unchanged full ledger. Its explicit classifier excludes the existing lane labels `fde` and `synthetic-FDE`, yielding 364 candidates and 182 pairs. It includes all selected and excluded candidate keys, input/output/cache totals, model and API/Codex breakdowns, and seven filtered chart views. Within a one-model breakdown, `pairs` means distinct contributing pair identifiers, not independently complete pairs.

The initial objective API chart is the only one of these seven views changed by the exclusion: 15 historical pairs become 14 after removing F1. `chart_claims` uses the same all-assigned/matched-pass/retry-inclusive schema as the historical claims, with the filtered pair identifiers. The source candidate-file hash ties the selection to the preserved ledger. `verify_package.py` recalculates the selection and filtered charts.

## Examples

Exact-reasoning `cases.json` supplies the full task prompt. `oracles.json` supplies the instance and exhaustively checked optimum. `answers.json` joins to candidates by run ID and includes only visible answers plus selected usage and text-stream telemetry, with all provider identifiers removed. The token-rate proxy is not the provider's internal decoding speed.

Short API records contain task prompts, visible answers, request settings, and provider usage fields. Staged-code records contain an explicit path-to-source map for the final snapshot plus recorded stage summaries. Snapshot paths are relative synthetic-project paths, not host paths. No provider raw response or encrypted reasoning object is included.
