# Corrections and exclusions preserved in the evidence

## HE096 grader correction

The campaign-v3 adapted public-code case HE096 initially rejected Sol's use of `bytearray` through an overrestrictive grader import/builtin guard. The correction allowed that valid implementation and regraded the existing answer; it did not regenerate the answer. Both models pass the corrected case. The Sol row retains `recorded_objective_success=false`, the original phase result, `adjudicated=true`, and an explicit `grading_amendment`. The 16-task public-code result uses the corrected outcome. This is an adapted subset, not a full benchmark result.

## Three archived infrastructure attempts

| Cohort / design | What happened | Treatment |
|---|---|---|
| campaign-v3 / RW1 / Sol | Continuation schema rejected with HTTP 400 | Original marked harness-invalid; fresh replacement; one request's usage unknown |
| campaign-v4 / RW2 / Vega | Stream ended without terminal usage | Original unresolved; fresh replacement; one request's usage unknown |
| campaign-v4 / LR3 medium clean / Vega | Collateral campaign stop | Original unresolved; fresh replacement; original usage known |

These three originals are outside the 412 active candidate rows and remain in the separate infrastructure ledger. Associated retry-inclusive fields account for them without pretending missing usage is zero. Infrastructure invalidation is not model-quality failure, but its known resource overhead matters for practical economics. The original and replacement status are not conflated.

## Two primary Vega task failures retained

In campaign-v4, two runs on compact-repository design RW3 reached the output response budget before a usable patch was delivered: high repetition 1 and xhigh repetition 2. They remain failures in the primary 98/100 Vega result. The subsequent four-candidate budget follow-up is a separate cohort. Its successful runs do not overwrite those primary failures and do not prove that the cap alone caused recovery, because timeout, execution scheduling, and stochastic generation also differed.

## Unresolved and provisional grades

Historical Codex high-v1 outcomes are ungraded. Pilot outcomes are provisional rubric judgments. Several API packet tasks require human/rubric judgment, so their automatic objective outcome remains null. The public export does not turn completion into acceptance or convert null into failure. Narrative model judges and limited human preference observations are not an independent proof of general quality equivalence.

## Presentation correction

An earlier presentation led with the strongest 64.2% exact-reasoning subset. The final framing emphasizes task dependence and puts the 40.7% staged-coding increase and 1.7% initial objective-API increase alongside it. The underlying exact-reasoning arithmetic was retained; its scope and counterevidence were made prominent. The original exploratory cohorts were not rewritten into a confirmatory study.
