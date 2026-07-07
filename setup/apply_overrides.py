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
    "Megan Serian": "Megan Replacement - TBD",
}

# Pickup slots: a withdrawn player's pairing slot that was actually filled and
# played by a named pickup. The match counts only for the SCHEDULED player (the
# pickup is the invited player's extra/dropped match — see
# project_pickup_clobber_repair), but it really was played, so surface it as a
# PLAYED pairing (Results + Schedule render from pairings, not matches) with the
# opponent shown as `label`. Using the label rather than the pickup's real name
# keeps it off the invited player's own schedule/record. Scores are pulled from
# the round's `matches` entry between `scheduled` and `opponent`.
# Keyed by (round, scheduled player) → {opponent: real name in matches, label}.
PICKUP_SLOTS = {
    (4, "Carson Bass"): {"opponent": "Ethan High", "label": "Bruce Replacement - Ethan"},
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
    9: "—",                       # Megan Serian was the sole R9 bye; now withdrawn → no bye.
}

# Frozen snapshot of inherited-slot per-round pairings the processor can't rebuild.
# process_scores builds rounds[].pairings from ROUND_PAIRINGS using the CURRENT
# Schedule-tab name ("Preston Stoner"), then looks up the played match by that
# name. The R1-R3 score tabs label slot #9 as "Ben Linck", so the lookup fails and
# those pairings come back played:false with no points/scorecards — hiding them
# from the Results tab and marking them MISSING on Preston's schedule. This file
# holds the correct pairing objects (with scorecards); apply_overrides splices them
# back every run. See setup/inherited_pairings.json for the data + provenance.
INHERITED_PAIRINGS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "inherited_pairings.json"
)

# Corrected scorecards parse_scorecards can't place because a player appears twice
# in one round (a pickup). It keys by name and keeps only the last block, so it
# mis-attaches the pickup card to the scheduled pairing and leaves the pickup
# pairing cardless. This snapshot holds the right cards; apply_overrides splices
# them. See setup/pickup_scorecards.json.
PICKUP_SCORECARDS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "pickup_scorecards.json"
)

# Mid-season handicap adjustment log — the same file the recap email reads. The
# workbook stores only the current handicap (no history), so the dashboard can't
# derive "what changed and when." Inject it into data.json as `handicapAdjustments`
# every run (the processor rebuilds data.json without it). See generate_recap.py's
# load_adjustments() for the read side and project_handicap_adjustments memory.
HANDICAP_ADJUSTMENTS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "handicap_adjustments.json"
)

DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Dashboard", "data.json"
)


def _load_inherited_pairings():
    try:
        with open(INHERITED_PAIRINGS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _load_pickup_scorecards():
    try:
        with open(PICKUP_SCORECARDS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _load_handicap_adjustments():
    """Full adjustment log, sorted by (effective_round, player). [] if unreadable."""
    try:
        with open(HANDICAP_ADJUSTMENTS_FILE, encoding="utf-8") as f:
            recs = json.load(f)
        recs = [r for r in recs if isinstance(r, dict) and r.get("effective_round") is not None]
        recs.sort(key=lambda r: (int(r["effective_round"]), str(r.get("player", ""))))
        return recs
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return []


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

    # 0c) inherited-slot pairings the processor can't rebuild (wrong name →
    #     played:false, scorecards dropped). Splice the frozen snapshot back into
    #     rounds[].pairings so the Results tab and player schedule show them.
    snap = _load_inherited_pairings()
    if snap and snap.get("rounds"):
        slot_names = set(snap.get("slot_any_name", []))
        n_pair = 0
        for r in d.get("rounds", []):
            want = snap["rounds"].get(str(r.get("round")))
            if not want:
                continue
            pairings = r.setdefault("pairings", [])
            idx = next(
                (i for i, p in enumerate(pairings)
                 if {p.get("p1"), p.get("p2")} & slot_names),
                None,
            )
            want_copy = json.loads(json.dumps(want))
            if idx is None:
                pairings.append(want_copy); n_pair += 1
            elif pairings[idx] != want_copy:
                pairings[idx] = want_copy; n_pair += 1
        if n_pair:
            changes.append(f"restored {n_pair} inherited-slot pairing(s) w/ scorecards (Ben Linck R1-R3)")

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

    # 2b) surface a filled replacement slot as a PLAYED pairing built from the real
    #     match. Runs after step 2, so it replaces the generic "- TBD" placeholder
    #     (only a replacement placeholder, never a real opponent) with the played
    #     result; the opponent shows as `label` to keep it off the pickup's own row.
    for r in d.get("rounds", []):
        rno = r.get("round")
        matches = r.get("matches", [])
        for (prno, sched), cfg in PICKUP_SLOTS.items():
            if prno != rno:
                continue
            opp, label = cfg["opponent"], cfg["label"]
            match = next((m for m in matches
                          if {m.get("p1"), m.get("p2")} == {sched, opp}), None)
            if not match:
                continue
            # orient so the scheduled player is p1, opponent (label) is p2
            if match["p1"] == sched:
                sp, sn, op, on = match["p1Pts"], match["p1Net"], match["p2Pts"], match["p2Net"]
            else:
                sp, sn, op, on = match["p2Pts"], match["p2Net"], match["p1Pts"], match["p1Net"]
            winner = sched if sp > op else (label if op > sp else None)
            new_pair = {"p1": sched, "p1Pts": sp, "p1Net": sn,
                        "p2": label, "p2Pts": op, "p2Net": on,
                        "winner": winner, "played": True}
            pairings = r.setdefault("pairings", [])
            idx = next((i for i, m in enumerate(pairings)
                        if sched in (m.get("p1"), m.get("p2"))
                        and ("Replacement" in str(m.get("p1")) or "Replacement" in str(m.get("p2")))),
                       None)
            if idx is not None:
                # preserve scorecards already attached (by 2c) so this stays idempotent
                for k in ("p1Scorecard", "p2Scorecard"):
                    if k in pairings[idx] and k not in new_pair:
                        new_pair[k] = pairings[idx][k]
                if pairings[idx] != new_pair:
                    pairings[idx] = new_pair
                    changes.append(f"R{rno} pickup pairing (played): {sched} {sp}-{op} {label}")
            elif new_pair not in pairings:
                pairings.append(new_pair)
                changes.append(f"R{rno} pickup pairing (played, appended): {sched} {sp}-{op} {label}")

    # 2c) fix scorecards the name-keyed parse mis-placed for double-played rounds.
    pcards = _load_pickup_scorecards()
    if pcards:
        by_round = {r.get("round"): r for r in d.get("rounds", [])}
        # (a) restore the scheduled player's correct card on their REAL pairing
        #     (the played pairing where they appear by name).
        for fix in pcards.get("scheduled_fixes", []):
            r = by_round.get(fix["round"])
            if not r:
                continue
            for m in r.get("pairings", []):
                if not m.get("played"):
                    continue
                side = "p1Scorecard" if m.get("p1") == fix["player"] else (
                       "p2Scorecard" if m.get("p2") == fix["player"] else None)
                if side and m.get(side) != fix["scorecard"]:
                    m[side] = fix["scorecard"]
                    changes.append(f"R{fix['round']} scorecard fix: {fix['player']} ({side})")
        # (b) attach both cards to the pickup pairing (matched by scheduled player).
        for pc in pcards.get("pickup_cards", []):
            r = by_round.get(pc["round"])
            if not r:
                continue
            for m in r.get("pairings", []):
                if m.get("played") and m.get("p1") == pc["scheduled"] and "Replacement" in str(m.get("p2")):
                    for side in ("p1Scorecard", "p2Scorecard"):
                        if pc.get(side) and m.get(side) != pc[side]:
                            m[side] = pc[side]
                            changes.append(f"R{pc['round']} pickup scorecard: {pc['scheduled']} pairing ({side})")

        # (c) restore a player's counting round + recompute their totals. A pickup
        #     makes the invited player appear twice in a round; process_scores writes
        #     the (dropped) pickup result to that round and miscomputes their season
        #     totals. This rewrites the round to the counting result and recomputes
        #     totalPts / record / avgNet from the player's rounds (drop-lowest = the
        #     pickup simply isn't among the counting rounds). Master fix is separate;
        #     see project_pickup_clobber_repair.
        def _outcome(pts):
            if pts is None: return None
            if pts >= 4.5:  return "W"
            if pts >= 4.0:  return "D"
            return "L"
        for fix in pcards.get("player_round_fixes", []):
            player = next((p for p in d.get("players", []) if p.get("name") == fix["player"]), None)
            if not player:
                continue
            rd = next((x for x in player.get("rounds", []) if x.get("round") == fix["round"]), None)
            if rd is None:
                continue
            want = {"matchPts": fix["matchPts"], "net": fix["net"],
                    "opponent": fix["opponent"], "result": fix["result"]}
            if any(rd.get(k) != v for k, v in want.items()):
                rd.update(want)
                changes.append(f"R{fix['round']} round fix: {fix['player']} -> {fix['result']} {fix['matchPts']}pts vs {fix['opponent']}")
            # recompute season aggregates from the (now-correct) counting rounds
            pts_list = [x.get("matchPts") for x in player["rounds"] if x.get("matchPts") is not None]
            nets     = [x.get("net") for x in player["rounds"] if isinstance(x.get("net"), (int, float))]
            total    = sum(pts_list)
            total    = int(total) if total == int(total) else total
            w = sum(1 for x in pts_list if _outcome(x) == "W")
            l = sum(1 for x in pts_list if _outcome(x) == "L")
            dr = sum(1 for x in pts_list if _outcome(x) == "D")
            rec = f"{w}-{l}-{dr}"
            avg = round(sum(nets) / len(nets), 1) if nets else None
            if player.get("totalPts") != total or player.get("record") != rec or player.get("avgNet") != avg:
                player["totalPts"], player["record"], player["avgNet"] = total, rec, avg
                changes.append(f"{fix['player']} totals -> {total} / {rec} / {avg}")

    # 3) bye corrections (rounds[] and schedule[])
    for coll_name in ("rounds", "schedule"):
        for r in d.get(coll_name, []):
            want = BYE_OVERRIDES.get(r.get("round"))
            if want and r.get("bye") != want:
                r["bye"] = want
                changes.append(f"{coll_name} R{r.get('round')} bye → {want}")

    # 4) inject the mid-season handicap adjustment log for the dashboard to render.
    adjustments = _load_handicap_adjustments()
    if d.get("handicapAdjustments") != adjustments:
        d["handicapAdjustments"] = adjustments
        changes.append(f"handicapAdjustments → {len(adjustments)} entry(ies)")

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
