"""
apply_overrides.py  —  IMI Golf League 2026

process_scores.py rebuilds Dashboard/data.json from the master workbook on
every run. The workbook has no concept of a mid-season withdrawal, so any
dashboard-only edits (Bruce Atkins's withdrawal, his "Replacement - TBD"
pairings, the corrected R6 bye) get silently wiped each time scores are
processed.

This script re-applies those dashboard-only overrides to data.json. It is
IDEMPOTENT — safe to run any number of times — and only touches UNPLAYED
pairings, so real recorded results are never altered.

Run it immediately AFTER process_scores.py, every round.

Usage:
  python setup/apply_overrides.py                 # default Dashboard/data.json
  python setup/apply_overrides.py path/to/data.json
"""

import sys, io, os, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Override config ──────────────────────────────────────────────────────────
# Withdrawn players → the placeholder name shown in their UNPLAYED pairings.
WITHDRAWN = {
    "Bruce Atkins": "Bruce Replacement - TBD",
}

# Round byes that must be corrected after a withdrawal (workbook can't express
# this). Keyed by round number → the exact bye string the dashboard should show.
BYE_OVERRIDES = {
    6: "C. Bass / McHugh",   # Bruce was the 3rd bye player here; now withdrawn.
}

DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Dashboard", "data.json"
)


def apply(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)

    changes = []

    # 1) withdrawn flag on each withdrawn player
    for p in d.get("players", []):
        if p.get("name") in WITHDRAWN and not p.get("withdrawn"):
            p["withdrawn"] = True
            changes.append(f"set withdrawn=true on {p['name']}")

    # 2) relabel withdrawn players in UNPLAYED pairings only
    for r in d.get("rounds", []):
        for m in r.get("pairings", []):
            if m.get("played") is False:
                for side in ("p1", "p2"):
                    repl = WITHDRAWN.get(m.get(side))
                    if repl:
                        m[side] = repl
                        changes.append(f"R{r.get('round')} {side}: {repl}")

    # 3) bye corrections (rounds[] and schedule[])
    for coll_name in ("rounds", "schedule"):
        for r in d.get(coll_name, []):
            want = BYE_OVERRIDES.get(r.get("round"))
            if want and r.get("bye") != want:
                r["bye"] = want
                changes.append(f"{coll_name} R{r.get('round')} bye → {want}")

    if changes:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        print(f"Applied {len(changes)} override(s) to {path}:")
        for c in changes:
            print(f"  - {c}")
    else:
        print(f"No overrides needed — {path} already up to date.")

    # Safety check: no withdrawn player should remain in an unplayed pairing.
    leftover = [
        (r.get("round"), side)
        for r in d.get("rounds", [])
        for m in r.get("pairings", [])
        if m.get("played") is False
        for side in ("p1", "p2")
        if m.get(side) in WITHDRAWN
    ]
    if leftover:
        print(f"WARNING: withdrawn player still in unplayed pairings: {leftover}")
        return 1
    return 0


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    sys.exit(apply(path))
