# Bruce Atkins Withdrawal — Replacement & Pickup Rule

**Date:** 2026-06-11
**Status:** Approved for implementation (pending user review of this spec)
**Context:** Bruce Atkins (#6) is withdrawing from the 2026 IMI Golf League mid-season. The league drops from 15 to 14 players. We are currently in R4 (Jun 1–12, in progress). This spec defines how to handle his exit without rebuilding the schedule.

## Decisions (from brainstorming)

1. **No new player joins.** Bruce's remaining matches are covered by existing league members on a per-round, opt-in basis.
2. **Keep Bruce's played results.** His R1 (W vs Michael McHugh, 8–0) and R2 (L vs Curtis Lynn, 2–6) stand. He stays in the standings as a withdrawn player, frozen at **10 pts, 1-1-0**, and accumulates nothing further. His R3 vs Rob Bass was never played — that slot is converted to a replacement too (see below), so Rob can arrange a makeup pickup.
3. **Minimal change — no schedule rebuild, no bye shifts.** Existing R4–R9 pairings and byes are untouched except for Bruce's own slots.

## The mechanic

### Placeholder slots
Bruce was scheduled to play in six rounds that did not complete. Each of those opponent slots becomes the literal placeholder **`Bruce Replacement - TBD`**:

| Round | Originally scheduled opponent | Notes |
|-------|------------------------------|-------|
| R3 | Rob Bass | Never played (R3 otherwise complete) — Rob's pickup is a **makeup** |
| R4 | Carson Bass | In progress (ends Jun 12) |
| R5 | Alex Palmer | |
| R7 | Kaylan Adams | |
| R8 | Brian Wojcio | |
| R9 | Ethan High | |

R6 needs **no change** — Bruce was already a bye that round, so R6 simply becomes a 2-player bye (C. Bass / McHugh) with 6 matches.

### Pickup match
Each round above, the orphaned (originally-scheduled) player invites **any** player in the league to a pickup match. The invited player plays **twice** that round: their own scheduled match *plus* the pickup. No byes move and no other matchup changes.

### Scoring
Both the orphaned player's result and the invited player's pickup result count as **real matches** — full points and record for everyone involved.

### The "mulligan" perk (drop lowest round)
Any player who plays an **extra** (pickup) match earns the right to **drop their single lowest round** — but only when it helps (i.e., the pickup round scored higher than their current worst round; otherwise they drop the pickup itself and nothing changes).

- Dropping a round removes it **entirely** — from total points, W-L-D record, **and** average NET, as if it had never been played.
- A player picked **multiple** times across the season drops **one round per extra match** played.
- Players who never play an extra match count **all** their rounds (no drop). The perk is the incentive to volunteer.

## Data model & file impact

### Constraint: one column per round
The protected master workbook (`2026 IMI Golf League.xlsx` → `Scores 2026`) has exactly **one column per round** per player. A player who plays twice in one round produces two results that cannot both occupy that single cell. Per the standing instructions, we **never write to this workbook directly** anyway.

**Resolution:** All pickup-match data and the drop-lowest adjustment live in the **dashboard layer** — `Dashboard/data.json` and `Dashboard/standings.md`. The workbook holds at most the single "official" round score; the dashboard carries the full record (including pickup matches) and the adjusted, drop-applied standings. This means the workbook total and the official dashboard total may diverge for players who played pickups; the **dashboard is authoritative** for standings once pickups exist. *(Confirmed by user 2026-06-11: this departure from "workbook is source of truth" is accepted.)*

### Today's changes (immediate)
1. **`Dashboard/data.json`** — rename Bruce's opponent slot to `Bruce Replacement - TBD` in the R3, R4, R5, R7, R8, R9 `pairings`. Remove Bruce from the R6 bye string. Leave Bruce's `players[]` entry frozen with his R1/R2 results. The R3 slot stays `played: false` (pending makeup).
2. **`Dashboard/standings.md`** — re-render with Bruce flagged as withdrawn (frozen stats, marked so he isn't read as an active contender).
3. **No workbook writes.** `Scores 2026` is left as-is; Bruce's row keeps his R1/R2 points.

### Deferred (kicks in when pickup scores arrive)
- When a pickup match is actually played, record **both** the scheduled match and the pickup match in `data.json` for that round.
- Apply the drop-lowest adjustment by hand at each standings refresh for any player who has played extra matches, removing their worst round from points, record, and avg NET.
- Re-sort standings per the usual order (total pts ↓, record, avg NET ↓, name ↑).

### League communication (in scope)
Draft a short, friendly note to the league explaining: Bruce has withdrawn; his upcoming/incomplete matches now show `Bruce Replacement - TBD`; the scheduled opponent may invite any league member to a pickup match (that member plays twice that round); and any player who plays an extra match may drop their lowest round. Deliver as a standalone draft for the user to send (not auto-sent).

## Out of scope
- No changes to `setup/process_scores.py`, `watcher.py`, `generate_recap.py`, or the `.bat` files (per CLAUDE.md). The drop-lowest logic is applied manually in the dashboard layer for now; automating it in the processor is a possible future task but not part of this change.
- No retroactive changes to any other player's already-played results.

## Open follow-ups (not blocking)
- Decide whether to eventually teach `process_scores.py` about multi-match rounds and the drop-lowest rule, vs. keeping it manual.
- Communicate the new pickup/mulligan rule to the league (a recap-email note or standalone message).
