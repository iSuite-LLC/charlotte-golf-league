# Results Tab — Scorecard Points Breakdown

**Date:** 2026-05-08
**Scope:** `Dashboard/index.html` only. No changes to `data.json`, `process_scores.py`, or any backend file.

## Problem

The Results tab dropdown currently shows a 9-hole scorecard for each match (par + gross + net for both players, with traditional notation — circles for birdie/eagle, squares for bogey/double). It does not show how the final match points were derived from those hole scores.

The league's scoring breaks each match into 5 categories totaling 8 points max:

- **First 3** (holes 1-3): 2 pts to winner of most holes (NET); tie = 1-1.
- **Middle 3** (holes 4-6): 2 pts to winner; tie = 1-1.
- **Final 3** (holes 7-9): 2 pts to winner; tie = 1-1.
- **Overall** (all 9 holes): 1 pt to winner; tie = ½-½.
- **Net Score** (lower `netTotal`): 1 pt; tie = ½-½.

A "won hole" requires strictly lower net than the opponent. Tied holes count for neither player.

Players see only the final match score (e.g., `2 — 6`) with no visibility into which categories drove that result.

## Goal

Inside the existing scorecard dropdown panel — directly below the 9-hole scorecard table — render a compact "Points Breakdown" table that shows the points each player earned in each of the 5 categories, totaling to the persisted match points.

Also add subtle vertical dividers in the existing scorecard table between holes 3/4 and 6/7, so the First-3 / Middle-3 / Final-3 hole groupings line up visually with the breakdown columns.

## Non-Goals

- No changes to the scorecard data model in `data.json`.
- No changes to `process_scores.py` or how points are calculated and persisted server-side.
- No generic rules explainer / legend / tooltip describing the scoring system. (The breakdown itself communicates the structure; explanatory copy is out of scope.)
- No replacement of the existing scorecard or its traditional notation.

## Design

### Layout

The breakdown table sits inside the existing `.scorecard-panel` container, after the existing `.sc-scroll` div that wraps the scorecard table. It reads horizontally — categories as columns, players as rows — matching the left-to-right reading flow of the scorecard above it.

```
                First 3   Middle 3   Final 3   Overall   Net   TOTAL
Brian              2          0         0         0       0      2
Ethan              0          2         2         1       1      6
```

Visual specifics:

- Player rows use first names only (matching the scorecard convention).
- Per category column: the player with more points has their cell rendered with the existing `.sc-p-winner` green color and bold weight. On a tie (1-1 or ½-½), both cells are rendered plain (no bolding, no color).
- TOTAL column has a left border matching the existing `.sc-total-col` style and heavier font weight. The winning total is also green-bolded.
- A draw match (4-4) renders normally — both TOTAL cells plain, no green.
- Half-points display as `½` (Unicode `½`, U+00BD), not `0.5`.
- Table sits flush below the scorecard with a small top margin (~10px) to separate the two visual blocks. No additional heading or label is required — context is provided by the surrounding panel.

### Hole-group dividers in scorecard

In the existing `.sc-table`, add a left border (`1px solid #2a2a2a`, matching existing column dividers) on the cells for hole 4 and hole 7 in every row (header, par row, gross rows, net rows). This creates two vertical lines that visually split the 9-hole grid into First 3 / Middle 3 / Final 3 groups.

The TOT column's existing left border (heavier, `.sc-total-col`) remains stronger than these group dividers, preserving the visual hierarchy.

### Computation

All client-side, computed on render from the data already in each match object.

Inputs (from `match` object in `data.json`):

- `match.p1Scorecard.net[0..8]`, `match.p2Scorecard.net[0..8]` — per-hole net scores (array indices 0-8 correspond to holes 1-9).
- `match.p1Scorecard.netTotal`, `match.p2Scorecard.netTotal` — net totals.
- `match.p1Pts`, `match.p2Pts` — persisted match points (used as a sanity check, not as the source of truth for the rendered breakdown).
- `match.p1`, `match.p2` — player full names; first names extracted via `name.split(' ')[0]`.

Algorithm:

1. For each hole `i` (0-8): if `p1.net[i] < p2.net[i]` → p1 wins hole; if `p1.net[i] > p2.net[i]` → p2 wins; if equal → tie (neither wins).
2. Aggregate holes won by each player for the four hole-based categories:
   - First 3 → indices 0, 1, 2 (holes 1-3)
   - Middle 3 → indices 3, 4, 5 (holes 4-6)
   - Final 3 → indices 6, 7, 8 (holes 7-9)
   - Overall → indices 0-8 (all 9 holes)
3. Apply scoring per category:
   - First 3 / Middle 3 / Final 3: more holes won = 2 pts; tied holes-won count = 1-1.
   - Overall: more holes won = 1 pt; tied = ½-½.
   - Net Score: lower `netTotal` = 1 pt; tied `netTotal` = ½-½.
4. Sum each player's pts across the 5 categories → computed total.
5. Sanity check: if `computedP1Total !== match.p1Pts` or `computedP2Total !== match.p2Pts`, emit `console.warn` with the match identifiers. The rendered TOTAL uses the computed values. (If the warning ever fires, it indicates a real divergence between the persisted points in `data.json` and the rules as encoded in the dashboard — which is information worth surfacing during development.)

All comments and identifiers in code use hole numbers 1-9 in human-facing text (e.g., variable comments) and 0-indexed array math in operations.

### Edge cases

- **Both scorecards present, all 9 net values populated on each** — render breakdown normally.
- **Only one scorecard exists** — the existing scorecard renders one-sided as it does today; breakdown is skipped (cannot be computed without both sides).
- **Either scorecard has any `null` in `net[0..8]`** — breakdown is skipped (partial card cannot be reconciled with persisted points). The scorecard above still renders as-is.
- **Match is a draw** (`match.winner === null`, `p1Pts === p2Pts === 4`) — breakdown renders normally; the row-by-row pts sum to 4-4 and the TOTAL column shows 4-4 with neither side bolded.
- **Scorecards exist but `match.played === false`** — the existing render path already filters unplayed matches out of the Results tab, so this case does not reach the breakdown.

### Code changes

One file: `Dashboard/index.html`.

1. **New helper function** `breakdownHTML(match)` — returns the breakdown table HTML string, or `''` if the breakdown cannot be computed (per the edge cases above).
2. **Modify** `scorecardHTML(match, id)` — append the result of `breakdownHTML(match)` after the existing `.sc-scroll` div, still inside the same `.scorecard-panel`.
3. **Add CSS** in the `/* ── Scorecard panel ── */` block:
   - `.sc-breakdown` table styling (matching the dark-theme density of `.sc-table`: ~0.8rem font, thin row borders, label column on the left).
   - `.sc-bd-winner` for the bold/green winning-cell style (can reuse `.sc-p-winner` if a clean reuse is possible; otherwise a parallel class).
   - `.sc-bd-total` for the TOTAL column's left border + heavier weight.
   - Hole-group dividers: target the 5th and 8th `<th>`/`<td>` in each `.sc-table` row (1 label column + 3 holes = 4, so hole 4 sits at child-index 5; 1 + 6 = 7, so hole 7 sits at child-index 8) with `border-left: 1px solid #2a2a2a`. The existing `.sc-total-col` retains its stronger border via specificity / placement.

No changes to `data.json` schema, no new fields, no backend changes.

### Testing

This is a UI change; it will be verified by opening `Dashboard/index.html` in a browser, navigating to the Results tab, expanding several matches across different rounds, and confirming:

- Each match's breakdown TOTAL matches its displayed `p1Pts`/`p2Pts` header values.
- Hole-group dividers appear at the right positions in the scorecard.
- A match with only one scorecard renders the scorecard alone, no breakdown.
- A draw match renders 4-4 with neither side highlighted.
- No `console.warn` fires for any current match in `data.json`.
- Layout holds on narrow widths (mobile) — the breakdown table fits in the same horizontal scroll area as the scorecard if needed.
