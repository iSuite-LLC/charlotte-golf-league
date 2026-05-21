# Schedule Tab — Player Search & Per-Player View

**Date:** 2026-05-21
**Status:** Approved, ready for plan

## Problem

The Schedule tab on the dashboard shows a round-by-round table. Each row expands to reveal that round's seven matchups. To answer the simple question *"what is my season schedule?"*, a user currently has to expand all nine rounds and visually scan for their own name. The goal is to make that answer one click away.

## Solution

Add a player search/picker to the top of the Schedule tab. When a player is selected, replace the round table with a per-round list scoped to that player: opponent, result, status, BYE rounds. When the search is cleared, the existing round table returns unchanged.

## Scope

In scope:
- New search control rendered above the schedule table inside `#tab-schedule`.
- New per-player schedule view that reuses `leagueData` already loaded by the dashboard.
- A small summary line above the per-player view showing season totals (record, points, avg NET).

Out of scope:
- Any change to `data.json` shape or any Python processor.
- Any change to other tabs (Standings, Stats, Results, etc.).
- Linking from a player's name on other tabs into this view (could be a follow-up).
- URL/hash deep-linking to a player's schedule.

## User Experience

### Search control

A single combined text + dropdown control rendered above the schedule table.

- Placeholder text: `Search player…`
- Right-side chevron icon toggles a dropdown listing all 15 player names, alphabetized by first name.
- Typing into the input filters the dropdown live (case-insensitive substring match against the player's full name).
- Clicking a name in the dropdown commits the selection: the input text becomes the player's full name, the dropdown closes, the view switches.
- A small `✕` button (visible only when a player is selected or text is present) clears the selection and restores the default round table.
- Pressing `Esc` while the dropdown is open closes it without committing. Clicking outside the control also closes it.

### Per-player view

When `selectedPlayer` is set, the round table is replaced with:

1. A one-line summary: `<Player Name> — <record>, <total> pts, <avgNet> avg NET`, pulled from `leagueData.players`.
2. A table with one row per round (R1–R9):

   | Round | Dates | Matchup | Result | Status |
   |-------|-------|---------|--------|--------|
   | R1 | Apr 20 – May 1 | vs Nick Coglianese | 8 – 0 | W |
   | R2 | May 4 – May 15 | vs Brian Wojcio | 6 – 2 | W |
   | R3 | May 18 – May 29 | vs Ethan High | — | Upcoming |
   | R5 | Jun 15 – Jun 26 | — | — | BYE |

   - **Matchup** column shows `vs <Opponent>` if the player has a pairing this round; otherwise `—`.
   - **Result** column shows `<playerPts> – <opponentPts>` if the match has been played; otherwise `—`.
   - **Status** column: `W` (win, green), `L` (loss, red), `D` (draw, neutral), `Upcoming` (muted), or `BYE` (muted).
   - The row for the current round is visually emphasized (same `current-round` styling as the existing schedule table).

### Default (unselected) state

The existing round table renders exactly as it does today. No visual change when no player is selected.

## Data Model & Logic

All data comes from existing `leagueData`:
- `leagueData.schedule` — array of `{ round, dates, bye }` for R1–R9.
- `leagueData.rounds` — array of round objects with `status` and `pairings[]`. Each pairing has `p1, p2, p1Pts, p2Pts, winner, played`.
- `leagueData.players` — used for the summary line (total points, record, avg NET).

### BYE detection

A round is a BYE for player X if X does not appear as `p1` or `p2` in any pairing of `rounds[i].pairings`. This works for both played and upcoming rounds because all 9 rounds have pre-populated pairings.

### Result formatting

For a pairing involving player X:
- If `played === false` → Matchup = `vs <opponent>`, Result = `—`, Status = `Upcoming`.
- If `played === true`:
  - If `winner === null` (draw) → Status = `D`.
  - Else if `winner === X` → Status = `W`.
  - Else → Status = `L`.
  - Result displays player's points first: `<X.pts> – <opponent.pts>`.

### Player list source

The 15 names for the dropdown are derived from `Object.keys(leagueData.players)` (or equivalent), sorted by first name. No hard-coded roster — keeps the control in sync if the roster ever changes.

## Implementation Notes

Single-file change to `Dashboard/index.html`:
- New CSS block under the existing `/* ── Schedule ── */` section for the search input, dropdown, summary line, and per-player table cell styling.
- New module-scoped variable `selectedPlayer` (default `null`).
- New functions:
  - `renderScheduleSearch()` — builds the search input + dropdown markup.
  - `renderPlayerSchedule(name)` — builds the per-player table.
  - `selectPlayer(name)`, `clearPlayer()`, `togglePlayerDropdown()`, `filterPlayerDropdown(text)` — UI handlers.
- The existing `renderSchedule()` becomes a dispatcher: it always renders the search control, then either the existing round table (if `selectedPlayer === null`) or the per-player view.

Approximate addition: ~120 lines (CSS + JS + markup).

No new dependencies. No build step. No changes outside `index.html`.

## Acceptance Criteria

1. With no player selected, the Schedule tab looks and behaves identically to today.
2. Typing `curt` into the search bar shows `Curtis Lynn` in the dropdown.
3. Clicking `Curtis Lynn` switches the view to his 9-round list with R5 marked BYE and played rounds showing correct W/L results matching the source data.
4. Clicking `✕` restores the default round table view.
5. The summary line for the selected player matches the values shown on the Standings tab.
6. The change is contained to `Dashboard/index.html`; no other files are modified.
