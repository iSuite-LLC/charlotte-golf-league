# Charlotte Golf League — Claude Manager Context

This folder is the working directory for the 2026 IMI Golf League. Claude acts as league manager across sessions — use this file for full context without re-briefing.

## Standing Instructions

When the user asks for standings, reports scores, or requests a refresh:
1. Read `2026 IMI Golf League.xlsx` → `Scores 2026` tab using openpyxl (`data_only=True, read_only=True`)
2. Rewrite `Dashboard/standings.md` in full with current standings
3. Commit and push the updated file

Do not modify `setup/watcher.py`, `setup/process_scores.py`, `setup/generate_recap.py`, `start_watcher.bat`, or `run_recap.bat` unless explicitly asked.

## Key Files

| File | Purpose |
|------|---------|
| `2026 IMI Golf League.xlsx` | Source of truth — Schedule tab + Scores 2026 tab (password: `steelers`) |
| `Scores/Scores.xlsx` | Score input — tabs R1 Scores through R9 Scores |
| `setup/process_scores.py` | Processes a score tab → updates Scores 2026 |
| `setup/watcher.py` | Auto-runs processor when Scores.xlsx changes (starts at login) |
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
| Ben Link | 19 | 20 |
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
| 7 | Alex Palmer | 27 |
| 8 | Curtis Lynn | 28 |
| 9 | Ben Link | 30 |
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
| 7 | Jul 13 – Jul 24 | Alex Palmer, Curtis Lynn, Ben Link (#7, #8, #9) |
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

## Scoring Rules

- **Format:** Each round = 7 matches + 1 BYE. Max 8 pts per match across: First 3 holes, Middle 3, Final 3, Overall, Net Score.
- **Win:** 4.5+ pts | **Draw:** 4.0 pts | **Loss:** < 4.0 pts
- **Record format:** W-L-D
- **Standings sort:** Total pts descending, then name ascending for ties
