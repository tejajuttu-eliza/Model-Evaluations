#!/usr/bin/env python3
"""A second search implementation cross-checks every oracle without using prepare.py."""
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def independent_search(family, d):
    count, best, ties = 0, None, 0

    def accept(value):
        nonlocal count, best, ties
        count += 1
        better = best is None or (value > best if family == "project_selection" else value < best)
        if better:
            best, ties = value, 1
        elif value == best:
            ties += 1

    if family == "assignment":
        # Reverse-order recursive placement and incremental loads, unlike Cartesian-product preparation.
        order = list(d["jobs"])[::-1]
        placed, loads = {}, {m: 0 for m in d["machines"]}

        def visit(i):
            if i == len(order):
                used = set(placed.values())
                accept(sum(d["jobs"][j]["costs"][m] for j, m in placed.items())
                       + sum(d["machines"][m]["fixed_cost"] for m in used))
                return
            j = order[i]
            for m in d["jobs"][j]["allowed"]:
                if loads[m] + d["jobs"][j]["load"] > d["machines"][m]["capacity"]:
                    continue
                placed[j] = m
                valid = all(placed[x] != placed[y] for x, y in d["separate"] if x in placed and y in placed)
                valid = valid and all(placed[x] == placed[y] for x, y in d["together"] if x in placed and y in placed)
                if valid:
                    loads[m] += d["jobs"][j]["load"]
                    visit(i + 1)
                    loads[m] -= d["jobs"][j]["load"]
                del placed[j]
        visit(0)
    elif family == "scheduling":
        # Reverse dependency order, checking intervals against placed jobs rather than a resource-use table.
        order = list(d["jobs"])[::-1]
        starts = {}
        successors = {j: [q for q in d["jobs"] if j in d["jobs"][q]["after"]] for j in d["jobs"]}

        def visit(i):
            if i == len(order):
                completions = {j: starts[j] + d["jobs"][j]["duration"] for j in starts}
                accept(d["makespan_multiplier"] * max(completions.values())
                       + sum(d["jobs"][j]["weight"] * completions[j] for j in starts))
                return
            j = order[i]
            task = d["jobs"][j]
            high = min([task["deadline"], d["horizon"]] + [starts[q] for q in successors[j] if q in starts]) - task["duration"]
            for s in range(task["release"], high + 1):
                if any(s < hi and s + task["duration"] > lo for lo, hi in task["blocked"]):
                    continue
                starts[j] = s
                valid = True
                for r, cap in d["capacity"].items():
                    for t in range(s, s + task["duration"]):
                        total = sum(d["jobs"][q]["resources"].get(r, 0) for q, qs in starts.items()
                                    if qs <= t < qs + d["jobs"][q]["duration"])
                        if total > cap:
                            valid = False
                            break
                    if not valid:
                        break
                if valid:
                    visit(i + 1)
                del starts[j]
        visit(0)
    else:
        # Enumerate combinations by cardinality instead of bit masks.
        ids = list(d["projects"])
        for size in range(len(ids) + 1):
            for selected_tuple in itertools.combinations(ids, size):
                s = set(selected_tuple)
                if s.intersection(d["prohibited"]):
                    continue
                if any(any(p not in s for p in d["projects"][j]["requires"]) for j in s):
                    continue
                if any(sum(j in s for j in group) > 1 for group in d["exclusive"]):
                    continue
                if any(sum(j in s for j in group) != 1 for group in d["exactly_one"]):
                    continue
                if any(sum(j in s for j in group) < 1 for group in d["at_least_one"]):
                    continue
                if any(sum(d["projects"][j][r] for j in s) > cap for r, cap in d["limits"].items()):
                    continue
                accept(sum(d["projects"][j]["value"] for j in s)
                       + sum(b["value"] for b in d["bonuses"] if all(j in s for j in b["all_of"])))
    return {"feasible_count": count, "objective": best, "optimal_count": ties}


def main():
    oracles = json.loads((ROOT / "oracles.json").read_text())
    results = []
    for cid, oracle in oracles.items():
        observed = independent_search(oracle["family"], oracle["instance"])
        expected = {k: oracle[k] for k in observed}
        assert observed == expected, (cid, observed, expected)
        results.append({"case_id": cid, "independent_result": observed, "matches_frozen_oracle": True})
    (ROOT / "ORACLE_VERIFICATION.json").write_text(json.dumps({"status": "passed", "results": results}, indent=2) + "\n")
    print(json.dumps({"status": "passed", "cross_checked_oracles": len(results)}))


if __name__ == "__main__":
    main()
