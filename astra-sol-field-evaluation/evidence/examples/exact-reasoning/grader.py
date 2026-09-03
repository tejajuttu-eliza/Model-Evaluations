#!/usr/bin/env python3
"""Deterministic feasibility/optimality checker; no model calls or prose-keyword scoring."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def integer(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and int(x) == x


def unique_object(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError("duplicate JSON key: " + k)
        d[k] = v
    return d


def grade(case_id, answer_text):
    """Return pass/objective_pass, errors, and computed metrics for a frozen case."""
    oracle = json.loads((ROOT / "oracles.json").read_text())[case_id]
    d, family, expected = oracle["instance"], oracle["family"], oracle["objective"]
    errors, metrics = [], {}

    def check(condition, reason):
        if not condition:
            errors.append(reason)

    def numeric(actual, wanted, label):
        check(integer(actual) and actual == wanted, label + " is incorrect")

    def numeric_map(actual, wanted, label):
        check(isinstance(actual, dict) and set(actual) == set(wanted)
              and all(integer(actual[k]) and actual[k] == wanted[k] for k in wanted),
              label + " is incorrect or incomplete")

    try:
        a = json.loads(answer_text, object_pairs_hook=unique_object,
                       parse_constant=lambda s: (_ for _ in ()).throw(ValueError("nonfinite JSON number")))
        if not isinstance(a, dict):
            raise ValueError("answer must be one JSON object")
        check(isinstance(a.get("explanation"), str) and bool(a["explanation"].strip()), "missing short explanation")
        if expected is None:
            check(a.get("status") == "infeasible", "instance is infeasible")
            c = a.get("certificate", {})
            jobs = c.get("jobs", [])
            if not isinstance(jobs, list) or not jobs or len(set(jobs)) != len(jobs) or not set(jobs).issubset(d["jobs"]):
                raise ValueError("certificate jobs must be a nonempty, distinct subset of instance jobs")
            if family == "assignment":
                check(c.get("kind") == "subset_capacity", "wrong certificate kind")
                union = sorted(set(m for j in jobs for m in d["jobs"][j]["allowed"]))
                machines = c.get("machines", [])
                check(isinstance(machines, list) and len(set(machines)) == len(machines)
                      and sorted(machines) == union, "certificate machines must equal union of allowed machines")
                need = sum(d["jobs"][j]["load"] for j in jobs)
                capacity = sum(d["machines"][m]["capacity"] for m in union)
                numeric(c.get("required_load"), need, "certificate required load")
                numeric(c.get("available_capacity"), capacity, "certificate available capacity")
                check(need > capacity, "certificate does not establish strict overload")
                metrics.update(required_load=need, available_capacity=capacity)
            elif family == "scheduling":
                check(c.get("kind") == "window_capacity", "wrong certificate kind")
                resource, window = c.get("resource"), c.get("window")
                if resource not in d["capacity"] or not isinstance(window, list) or len(window) != 2 \
                        or not all(integer(x) for x in window) or window[0] >= window[1]:
                    raise ValueError("invalid certificate resource or window")
                lo, hi = window
                check(all(d["jobs"][j]["release"] >= lo and d["jobs"][j]["deadline"] <= hi for j in jobs),
                      "listed jobs are not all confined to the certificate window")
                need = sum(d["jobs"][j]["duration"] * d["jobs"][j]["resources"].get(resource, 0) for j in jobs)
                capacity = d["capacity"][resource] * (hi - lo)
                numeric(c.get("required_work"), need, "certificate required work")
                numeric(c.get("available_work"), capacity, "certificate available work")
                check(need > capacity, "certificate does not establish strict overload")
                metrics.update(required_work=need, available_work=capacity)
            else:
                raise ValueError("unsupported infeasible family")
        else:
            check(a.get("status") == "optimal", "status must be optimal")
            checks = a.get("checks", {})
            if not isinstance(checks, dict):
                raise ValueError("checks must be an object")
            if family == "assignment":
                assignments = a.get("assignment", {})
                if not isinstance(assignments, dict) or set(assignments) != set(d["jobs"]):
                    raise ValueError("assignment must include every job exactly once")
                if not all(isinstance(m, str) and m in d["machines"] for m in assignments.values()):
                    raise ValueError("unknown assignment machine")
                check(all(assignments[j] in d["jobs"][j]["allowed"] for j in assignments), "disallowed assignment")
                check(all(assignments[x] != assignments[y] for x, y in d["separate"]), "separate pair violation")
                check(all(assignments[x] == assignments[y] for x, y in d["together"]), "together pair violation")
                loads = {m: sum(d["jobs"][j]["load"] for j in assignments if assignments[j] == m) for m in d["machines"]}
                check(all(loads[m] <= d["machines"][m]["capacity"] for m in loads), "machine capacity exceeded")
                opened = sorted(set(assignments.values()))
                variable = sum(d["jobs"][j]["costs"][assignments[j]] for j in assignments)
                fixed = sum(d["machines"][m]["fixed_cost"] for m in opened)
                computed = variable + fixed
                numeric_map(checks.get("loads"), loads, "machine loads")
                got_opened = checks.get("opened")
                check(isinstance(got_opened, list) and len(set(got_opened)) == len(got_opened)
                      and sorted(got_opened) == opened, "opened machines incorrect")
                numeric(checks.get("variable_cost"), variable, "variable cost")
                numeric(checks.get("fixed_cost"), fixed, "fixed cost")
                metrics.update(loads=loads, variable_cost=variable, fixed_cost=fixed)
            elif family == "scheduling":
                starts = a.get("starts", {})
                if not isinstance(starts, dict) or set(starts) != set(d["jobs"]) or not all(integer(x) for x in starts.values()):
                    raise ValueError("starts must contain an integer start for every job")
                completion = {j: starts[j] + d["jobs"][j]["duration"] for j in starts}
                for j, t in d["jobs"].items():
                    check(starts[j] >= 0 and starts[j] >= t["release"], j + " violates release")
                    check(completion[j] <= min(t["deadline"], d["horizon"]), j + " violates deadline/horizon")
                    check(all(starts[j] >= completion[p] for p in t["after"]), j + " violates dependency")
                    check(all(starts[j] >= hi or completion[j] <= lo for lo, hi in t.get("blocked", [])), j + " overlaps blocked interval")
                for r, cap in d["capacity"].items():
                    for time in range(d["horizon"]):
                        demand = sum(d["jobs"][j]["resources"].get(r, 0) for j in starts if starts[j] <= time < completion[j])
                        check(demand <= cap, r + " capacity exceeded at time " + str(time))
                makespan = max(completion.values())
                weighted = sum(d["jobs"][j]["weight"] * completion[j] for j in starts)
                computed = d["makespan_multiplier"] * makespan + weighted
                numeric_map(checks.get("completion_times"), completion, "completion times")
                numeric(checks.get("makespan"), makespan, "makespan")
                numeric(checks.get("weighted_completion"), weighted, "weighted completion")
                metrics.update(makespan=makespan, weighted_completion=weighted)
            else:
                selected = a.get("selected")
                if not isinstance(selected, list) or not all(isinstance(x, str) for x in selected) \
                        or len(set(selected)) != len(selected) or not set(selected).issubset(d["projects"]):
                    raise ValueError("selected must be distinct known project IDs")
                selected = set(selected)
                check(not selected.intersection(d["prohibited"]), "prohibited project selected")
                check(all(set(d["projects"][p]["requires"]).issubset(selected) for p in selected), "project dependency missing")
                check(all(len(selected.intersection(g)) <= 1 for g in d["exclusive"]), "exclusive group violation")
                check(all(len(selected.intersection(g)) == 1 for g in d["exactly_one"]), "exactly-one group violation")
                check(all(selected.intersection(g) for g in d["at_least_one"]), "at-least-one group violation")
                totals = {r: sum(d["projects"][p][r] for p in selected) for r in d["limits"]}
                check(all(totals[r] <= d["limits"][r] for r in totals), "authoritative resource limit exceeded")
                base = sum(d["projects"][p]["value"] for p in selected)
                bonus = sum(b["value"] for b in d["bonuses"] if set(b["all_of"]).issubset(selected))
                computed = base + bonus
                numeric_map(checks.get("resource_totals"), totals, "resource totals")
                numeric(checks.get("base_value"), base, "base value")
                numeric(checks.get("bonus_value"), bonus, "bonus value")
                check(checks.get("authoritative_sources") == d["authority"], "wrong authoritative source IDs")
                metrics.update(resource_totals=totals, base_value=base, bonus_value=bonus)
            numeric(a.get("objective"), computed, "reported objective")
            check(computed == expected, "feasible objective is not globally optimal")
            metrics.update(computed_objective=computed, optimal_objective=expected)
    except (ValueError, TypeError, KeyError, OverflowError) as e:
        errors.append("malformed answer: " + str(e))
    passed = not errors
    return {"pass": passed, "objective_pass": passed, "errors": errors, "metrics": metrics,
            "prose_review": "Explanation text retained but not semantically machine-graded; checks/certificates are verified."}


if __name__ == "__main__":
    import sys
    print(json.dumps(grade(sys.argv[1], Path(sys.argv[2]).read_text()), indent=2))
