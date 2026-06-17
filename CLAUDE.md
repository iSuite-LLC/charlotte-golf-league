# Charlotte Golf League — Claude Manager Context

This folder is the working directory for the 2026 IMI Golf League. Claude acts as league manager across sessions — use this file for full context without re-briefing.

## Standing Instructions

When the user reports that new scores are in the Scores folder (or otherwise asks for a refresh), follow these steps **every time, in order**:

1. **Identify the round** — figure out which round tab the new scores are on (e.g., `R2 Scores`). Ask the user if unclear.
2. **Run the processor** — `python setup/process_scores.py "Scores/Scores.xlsx" "R{n} Scores"`. This is the only thing that syncs `Scores 2026` tab and `Dashboard/data.json`. Never skip this step.
2b. **Re-apply dashboard overrides** — `python setup/apply_overrides.py`. The processor rebuilds `data.json` from the workbook and WIPES dashboard-only edits (Bruce Atkins's withdrawal, his "Replacement - TBD" pairings, the corrected R6 bye). This idempotent script restores them. Never skip — run it immediately after step 2, every time.
3. **Read the round tab** — open `Scores/Scores.xlsx` → `R{n} Scores` and note the actual matchups (paired by adjacent player blocks). Needed so the commit/recap text describes results accurately instead of guessing.
4. **Read the master totals** — open `2026 IMI Golf League.xlsx` → `Scores 2026` tab (`data_only=True, read_only=True`) and pull every player's total points, W-L-D record, and avg NET.
5. **Rewrite `Dashboard/standings.md` in full** — sort by:
   1. Total points descending
   2. Best record (most wins, then fewest losses) — ties for playoff seeding break here
   3. Lowest average NET score
   4. Name ascending (final tiebreaker only)
6. **Commit and push** — stage `2026 IMI Golf League.xlsx`, `Dashboard/standings.md`, `Dashboard/data.json`, `Scores/Scores.xlsx`, `Score Calculator.xlsx`, `setup/processed_files.json`. Commit message must list the actual matchups from step 3, then push.
7. **Website** — GitHub Pages auto-deploys from `Dashboard/` on push. No extra action needed.

Do not modify `setup/process_scores.py`, `setup/generate_recap.py`, or `run_recap.bat` unless explicitly asked.

## Key Files

| File | Purpose |
|------|---------|
| `2026 IMI Golf League.xlsx` | Source of truth — Schedule tab + Scores 2026 tab (password: `steelers`) |
| `Scores/Scores.xlsx` | Score input — tabs R1 Scores through R9 Scores |
| `setup/process_scores.py` | Processes a score tab → updates Scores 2026 |
| `setup/apply_overrides.py` | Re-applies dashboard-only overrides (Bruce withdrawal/TBD pairings/R6 bye) wiped by the processor — run after every score run |
| `setup/generate_recap.py` | Generates round recap email draft → Recap Emails/ |
| `Dashboard/standings.md` | Live standings — Claude rewrites this via conversation |
| `setup/League Manager Guide.md` | Full system reference |

## Excel Layout — Scores 2026 Tab

Sheet protected with password `steelers`. Read with openpyxl `data_only=True, read_only=True` — never write to this workbook directly.

**Columns:**

| Col Index | Letter | Content |
|-----------|--------|---------|
| 4 | D | Round 1 match pts |
| 5 | E | Round 2 match pts |
| 6 | F | Round 3 match pts |
| 7 | G | Round 4 match pts |
| 8 | H | Round 5 match pts |
| 9 | I | Round 6 match pts |
| 10 | J | Round 7 match pts |
| 11 | K | Round 8 match pts |
| 12 | L | Round 9 match pts |
| 13 | M | Season total pts |
| 14 | N | W-L-D record |
| 15 | O | Avg NET score |

Each player = 2 consecutive rows: match points row then NET score row directly below.

**Player row map:**

| Player | MP Row | NET Row |
|--------|--------|---------|
| Brian Wojcio | 3 | 4 |
| Ethan High | 5 | 6 |
| Rob Bass | 7 | 8 |
| Carson Bass | 9 | 10 |
| Michael McHugh | 11 | 12 |
| Bruce Atkins | 13 | 14 |
| Alex Palmer | 15 | 16 |
| Curtis Lynn | 17 | 18 |
| Preston Stoner | 19 | 20 |
| Charlotte Hayes | 21 | 22 |
| David Maddox | 23 | 24 |
| Jerome Martin | 25 | 26 |
| Kaylan Adams | 27 | 28 |
| Megan Serian | 29 | 30 |
| Nick Coglianese | 31 | 32 |

## Roster

| # | Name | HC |
|---|------|----|
| 1 | Brian Wojcio | 12 |
| 2 | Ethan High | 12 |
| 3 | Rob Bass | 15 |
| 4 | Carson Bass | 20 |
| 5 | Michael McHugh | 22 |
| 6 | Bruce Atkins | 24 |
| 7 | Alex Palmer | 30 |
| 8 | Curtis Lynn | 28 |
| 9 | Preston Stoner | 28 |
| 10 | Charlotte Hayes | 36 |
| 11 | David Maddox | 36 |
| 12 | Jerome Martin | 36 |
| 13 | Kaylan Adams | 36 |
| 14 | Megan Serian | 36 |
| 15 | Nick Coglianese | 36 |

## Schedule

| Round | Dates | BYE |
|-------|-------|-----|
| 1 | Apr 20 – May 1 | David Maddox (#11) |
| 2 | May 4 – May 15 | Nick Coglianese (#15) |
| 3 | May 18 – May 29 | Charlotte Hayes (#10) |
| 4 | Jun 1 – Jun 12 | Jerome Martin (#12) |
| 5 | Jun 15 – Jun 26 | Brian Wojcio, Ethan High, Rob Bass (#1, #2, #3) |
| 6 | Jun 29 – Jul 10 | Carson Bass, Michael McHugh, Bruce Atkins (#4, #5, #6) |
| 7 | Jul 13 – Jul 24 | Alex Palmer, Curtis Lynn, Preston Stoner (#7, #8, #9) |
| 8 | Jul 27 – Aug 7 | Kaylan Adams (#13) |
| 9 | Aug 10 – Aug 21 | Megan Serian (#14) |

## Recap Email Schedule

| Recap Date | Round Recapped | Next Round Starts |
|------------|---------------|-------------------|
| May 4 | R1 | R2 |
| May 18 | R2 | R3 |
| Jun 1 | R3 | R4 |
| Jun 15 | R4 | R5 |
| Jun 29 | R5 | R6 |
| Jul 13 | R6 | R7 |
| Jul 27 | R7 | R8 |
| Aug 10 | R8 | R9 |
| Aug 24 | R9 (finale) | Season end |

`generate_recap.py` writes **two drafts per round**: a friendly one (`Round_NN_Recap_Draft_<date>.htm`) and a savage/roast one (`Round_NN_Recap_HARSH_Draft_<date>.htm`). The user picks which to send. Both tones live in `TONE_BANKS` in the script.

## Scoring Rules

- **Format:** Each round = 7 matches + 1 BYE. Max 8 pts per match across: First 3 holes, Middle 3, Final 3, Overall, Net Score.
- **Win:** 4.5+ pts | **Draw:** 4.0 pts | **Loss:** < 4.0 pts
- **Record format:** W-L-D
- **Standings sort (playoff seeding order):**
  1. Total pts descending
  2. Best record (most wins, then fewest losses)
  3. Lowest average NET score
  4. Name ascending (final tiebreaker only)
