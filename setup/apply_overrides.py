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

# Roster replacements: a departed player's slot taken over by a named successor
# for all remaining AND missing rounds. The successor INHERITS the slot — including
# already-played results — so this is a straight name swap applied to every exact
# occurrence in data.json (player name, pairings, opponents, winners). Once the
# workbook Schedule tab (col C) is renamed to match, this override becomes a no-op.
NAME_OVERRIDES = {
    "Ben Linck": "Preston Stoner",   # Ben moved away; Preston takes over from R4 on (2026-06-17)
}

# Mid-season handicap overrides (current roster/display handicap only), keyed by
# the player's CURRENT name. Used when the workbook Schedule tab (col D) doesn't
# yet reflect the value. Display-only: future strokes come from the handicap typed
# on each score-input scorecard. Remove an entry once the Schedule tab shows the
# same number (then the workbook is sole source, as with Alex Palmer's 30).
HANDICAP_OVERRIDES = {
    "Preston Stoner": 28,   # Preston took over Ben Linck's slot; plays at HC 28 (2026-06-17)
}

# Round byes that must be corrected (workbook can't express these).
# Keyed by round number → the exact bye string the dashboard should show.
BYE_OVERRIDES = {
    6: "C. Bass / McHugh",        # Bruce was the 3rd bye player here; now withdrawn.
    7: "Palmer / Lynn / Stoner",  # Ben Linck replaced by Preston Stoner.
}

DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Dashboard", "data.json"
)


def apply(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)

    changes = []

    # 0) roster name replacements — swap every exact-match occurrence (player
    #    name, pairings, opponents, winners, matches). No-op once the workbook
    #    Schedule tab is renamed to match.
    name_swaps = []
    def swap_names(obj):
        if isinstance(obj, dict):
            return {k: swap_names(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [swap_names(v) for v in obj]
        if isinstance(obj, str) and obj in NAME_OVERRIDES:
            name_swaps.append(obj)
            return NAME_OVERRIDES[obj]
        return obj
    d = swap_names(d)
    for old in sorted(set(name_swaps)):
        changes.append(f"renamed {name_swaps.count(old)}x '{old}' -> '{NAME_OVERRIDES[old]}'")

    # 0b) roster handicap overrides (by current name)
    for p in d.get("players", []):
        want = HANDICAP_OVERRIDES.get(p.get("name"))
        if want is not None and p.get("handicap") != want:
            old = p.get("handicap")
            p["handicap"] = want
            changes.append(f"{p['name']} handicap {old} -> {want}")

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
