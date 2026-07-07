# Design: Website — Outstanding Matches tracker + Handicap Adjustments

**Date:** 2026-07-06
**Author:** Claude (League Manager) + Ethan High

Two mid-season additions to the dashboard (`Dashboard/index.html`, fed by
`Dashboard/data.json`).

## Feature A — Outstanding Matches tracker

**Purpose:** surface un-played matches (makeups + replacement slots) so players
know what's still owed. Mid-season the league has several open matches.

**Data:** No schema change. Derived at render time from existing
`rounds[].pairings[]` where `played === false`. A pairing is a "replacement/TBD"
slot when either name contains `"Replacement"` or `"TBD"` (case-insensitive).

**Current outstanding (for reference):**
- R3 — Rob Bass vs Bruce Replacement - TBD *(replacement)*
- R4 — Rob Bass vs Curtis Lynn *(makeup)*
- R5 — Carson Bass vs Michael McHugh *(makeup)*; Bruce Replacement - TBD vs Alex Palmer *(replacement)*; Charlotte Hayes vs David Maddox *(makeup)*

**Rendering:** A panel at the **top of the Results tab**, above the round list.
- Title: "⏳ Outstanding Matches" with a count badge (total unplayed).
- One row per unplayed pairing: `R{n}  ·  {p1}  vs  {p2}`, grouped/sorted by round.
- Replacement-TBD slots are **shown but clearly tagged** — muted text plus a small
  "pickup-eligible" pill — so they read as not-a-fixed-match. Real makeups render
  in normal emphasis.
- Empty state: green note "All scheduled matches are in — no makeups outstanding."
  (panel still renders, so its absence never looks like a bug).

**Isolation:** new `renderOutstanding()` returns an HTML string; `renderResults()`
prepends it to the Results tab markup. Pure function of `leagueData.rounds`.

## Feature B — Handicap Adjustments (card + HC badge)

**Purpose:** show mid-season handicap changes on the site, consistent with the
recap email.

**Data source & flow:** the site reads only `data.json`, which currently lacks
the adjustment log. `apply_overrides.py` will read `setup/handicap_adjustments.json`
(the same file the recap uses) and inject a top-level `handicapAdjustments` array
into `data.json`. This runs after `process_scores.py` (which rebuilds/​wipes
`data.json`), so the data survives every score run — apply_overrides is the
established home for dashboard-only injections. `apply_overrides.py` is not in the
CLAUDE.md do-not-modify list, so editing it is in-bounds.

Injected shape (copied verbatim from the log, sorted by effective_round then
player):
```json
"handicapAdjustments": [
  {"player": "Carson Bass", "from": 20, "to": 24, "effective_round": 4},
  ...
]
```

**Rendering (two parts):**
1. **Card under the Standings table** (mirrors the email placement): "⚖️ Handicap
   Adjustments" with a compact table — Player | Change (`X → Y`) | Effective
   (`Round n`). Rendered only when the array is non-empty.
2. **HC badge in the standings table:** for any player with an adjustment, their
   Hcp cell shows a marker (e.g. `30*`) with a `title` tooltip ("Adjusted from 27,
   eff. R4"). The `*` visually links the cell to the card below.

**Isolation:** new `renderHcAdjustments()` returns the card HTML; `renderStandings()`
appends it after the table and consults a lookup (name → adjustment) when building
the Hcp cell.

## Out of scope / YAGNI
- No new tab (both features embed in existing tabs).
- No auto-detection of adjustment *candidates* — the log stays manual.
- Outstanding tracker does not attempt to predict pickup matches; it only reports
  the current unplayed pairings.

## Testing
- Load the dashboard locally against the current `data.json`:
  - Results tab: Outstanding panel lists all 5 current unplayed pairings, with the
    2 replacement slots tagged and 3 makeups in normal emphasis; count badge = 5.
  - Standings tab: Handicap Adjustments card shows the 3 bumps; Carson/Michael/Alex
    Hcp cells show the `*` marker with tooltip; others unmarked.
- Run `apply_overrides.py` and confirm `data.json` gains `handicapAdjustments`
  with 3 entries; re-run to confirm idempotence.
- Temporarily empty the outstanding set (all played) → green "all in" note.
