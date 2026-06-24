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

# Roster replacements: a player's slot taken over mid-season by a named successor.
# The successor INHERITS the slot's standing (points/record/seed) and plays every
# round from `takeover_round` on — but rounds BEFORE that keep the ORIGINAL player's
# name in the per-round results, because they actually played them.
#   any_name      : every name the slot has ever used (matched in either direction,
#                   so this is robust no matter which name process_scores emits)
#   current       : standings-entry name + name shown for rounds >= takeover_round
#   historical    : name shown for rounds < takeover_round
ROSTER_RENAMES = [
    {
        "any_name": ("Ben Linck", "Preston Stoner"),
        "current": "Preston Stoner",
        "historical": "Ben Linck",
        "takeover_round": 4,   # Ben played R1-R3; Preston took over from R4 (2026-06-17)
    },
]

# Inherited-slot opponents the processor can't recover. When a slot changes hands
# mid-season, the early score-input tabs still record those rounds under the
# ORIGINAL player's name (e.g. "Ben Linck"), so process_scores can't link them to
# the successor's standings entry (now "Preston Stoner") and leaves the successor's
# OWN per-round opponents null. Restore them here — keyed by CURRENT name →
# {round: opponent} — for rounds the successor inherited. These are the opponents
# the slot actually faced; they survive in the committed data.json but get wiped
# on every score run. (Step 0's rename handles the reverse direction — other
# players whose opponent is the slot — this restores the slot's own opponents.)
INHERITED_OPPONENTS = {
    "Preston Stoner": {1: "Charlotte Hayes", 2: "Jerome Martin", 3: "Megan Serian"},
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

    # 0) roster replacements — current name on the standings entry and rounds
    #    >= takeover; original name preserved on earlier (already-played) rounds.
    def slot_for(name):
        for s in ROSTER_RENAMES:
            if name in s["any_name"]:
                return s
        return None

    def name_for_round(s, rno):
        return s["historical"] if (rno is not None and rno < s["takeover_round"]) else s["current"]

    n_renames = 0
    # player standings entry → current name
    for p in d.get("players", []):
        s = slot_for(p.get("name"))
        if s and p["name"] != s["current"]:
            p["name"] = s["current"]; n_renames += 1
    # per-round pairings + matches → round-appropriate name
    for rnd in d.get("rounds", []):
        rno = rnd.get("round")
        for coll in ("pairings", "matches"):
            for m in rnd.get(coll, []):
                for key in ("p1", "p2", "winner"):
                    s = slot_for(m.get(key))
                    if s:
                        want = name_for_round(s, rno)
                        if m.get(key) != want:
                            m[key] = want; n_renames += 1
    # opponent references inside each player's round list → round-appropriate name
    for p in d.get("players", []):
        for rd in p.get("rounds", []):
            s = slot_for(rd.get("opponent"))
            if s:
                want = name_for_round(s, rd.get("round"))
                if rd.get("opponent") != want:
                    rd["opponent"] = want; n_renames += 1
    if n_renames:
        changes.append(f"applied {n_renames} roster-replacement name fix(es) (Ben Linck/Preston Stoner)")

    # 0a) inherited-slot opponents wiped by the processor (by current name)
    n_opp = 0
    for p in d.get("players", []):
        want_map = INHERITED_OPPONENTS.get(p.get("name"))
        if not want_map:
            continue
        for rd in p.get("rounds", []):
            want = want_map.get(rd.get("round"))
            if want and rd.get("opponent") != want:
                rd["opponent"] = want
                n_opp += 1
    if n_opp:
        changes.append(f"restored {n_opp} inherited-slot opponent(s) (Preston Stoner R1-R3)")

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
