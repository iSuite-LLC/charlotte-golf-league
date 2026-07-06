# Design: Handicap Adjustments section in recap emails

**Date:** 2026-07-06
**Author:** Claude (League Manager) + Ethan High

## Goal

Add a "Handicap Adjustments" section to the generated round-recap emails
(`setup/generate_recap.py`) that announces mid-season handicap changes to the
league.

## Decisions (from brainstorming)

- **Content:** *Announce adjustments made* — a transparency note listing who was
  bumped, by how much, and when it took effect. (Not a "candidates for review"
  list.)
- **Scope:** *Cumulative to date* — every recap shows a running list of all
  adjustments that have taken effect by the time the upcoming round starts, not
  just the newest one.
- **Placement:** Right after the Standings table (contextualizes the numbers the
  reader just saw). *Default — chosen while user was away; easily moved.*
- **Tone:** Tone-flavored intro line (friendly vs. harsh), factual table
  identical in both drafts. Ribbing stays on golf performance, not personal
  traits. *Default — chosen while user was away.*

## Data source

The workbook stores only *current* handicaps (Schedule tab, col D) — no history.
Adjustment history currently lives only as prose in `Dashboard/standings.md` and
git commits. So we add a structured manual log:

**`setup/handicap_adjustments.json`** — array of adjustment records, appended by
hand whenever an adjustment is made:

```json
[
  {"player": "Carson Bass",    "from": 20, "to": 24, "effective_round": 4},
  {"player": "Michael McHugh", "from": 22, "to": 25, "effective_round": 4},
  {"player": "Alex Palmer",    "from": 27, "to": 30, "effective_round": 4}
]
```

Fields: `player` (exact roster name), `from`/`to` (integer handicaps),
`effective_round` (1–9, the first round the new HC applied). Seeded with the
three known 2026 adjustments.

## Components

### `load_adjustments(round_num)`
- Reads `setup/handicap_adjustments.json`.
- Returns records with `effective_round <= round_num + 1` (adjustments that have
  taken effect by the round players are about to start), sorted by
  `(effective_round, player)`.
- Returns `[]` gracefully on missing file / JSON error / bad shape — mirrors the
  defensive style of `load_withdrawn()`. The section is simply omitted then.

Boundary rationale: the R{n} recap previews R{n+1}. An adjustment effective
R{n+1} has just taken effect and is announced; one effective R{n+2} is still in
the future and is withheld. So R1/R2 recaps show nothing (R4-effective bumps
haven't happened); R3 recap onward shows all three cumulatively.

### Renderer (inside `generate_email`)
- Red section bar via existing `_sec("⚖️", "HANDICAP ADJUSTMENTS")`.
- One tone-flavored intro `<p>` chosen from a new per-tone bank.
- A compact table: **Player | Change | Effective**, e.g.
  `Alex Palmer | 27 → 30 | Round 4`. Uses the existing `TD`/`TH` cell styles and
  zebra striping for consistency.
- Rendered only when `load_adjustments()` returns a non-empty list.
- Inserted immediately after the standings `</table>`.

### Tone banks
Add to each entry of `TONE_BANKS`:
- `"hc_intro"`: friendly — matter-of-fact "the committee evened things out";
  harsh — "the committee took pity". Single string each (not randomized) to keep
  scope tight; can grow into a list later if desired.

## Out of scope / YAGNI

- No auto-detection of *candidate* players (the ≥3-matches / avg-NET>40 rule) —
  adjustments remain a manual decision logged by hand.
- No reading handicaps from the workbook — the JSON log is authoritative for the
  recap's purposes.
- No editing of `standings.md` from this feature.

## Testing

- Generate R3 recap (`python setup/generate_recap.py 3`) → section present with
  all three adjustments, both drafts.
- Generate R1 recap → section absent (no adjustments effective by R2).
- Temporarily rename/remove the JSON → generator still runs, section absent.
