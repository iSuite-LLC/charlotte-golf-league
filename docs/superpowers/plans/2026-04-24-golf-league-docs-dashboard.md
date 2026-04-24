# Golf League Docs & Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create CLAUDE.md, README.md, and Dashboard/standings.md so Claude can act as league manager across sessions and standings are always one conversation away.

**Architecture:** Three static files written directly into the repo. No scripts added. CLAUDE.md gives Claude the full system map; README.md documents the repo for GitHub; standings.md is the persistent output Claude rewrites whenever scores are discussed. All existing automation (watcher, processor, recap generator) is untouched.

**Tech Stack:** Markdown only. No Python, no dependencies.

---

## File Map

| Action | Path |
|--------|------|
| Create | `CLAUDE.md` |
| Create | `README.md` |
| Create | `Dashboard/standings.md` |
| Commit + push | all three |

---

### Task 1: Create CLAUDE.md

**Files:**
- Create: `C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\CLAUDE.md`

- [ ] **Step 1: Write CLAUDE.md**

Full content — do not abbreviate or paraphrase, copy exactly:

```markdown
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
```

- [ ] **Step 2: Verify**

Open `CLAUDE.md` and confirm:
- Standing instructions section is first
- All 15 players appear in the row map
- All 9 rounds appear in the schedule
- Password `steelers` is present

- [ ] **Step 3: Commit**

```bash
cd "C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League"
git add CLAUDE.md
git commit -m "Add CLAUDE.md: league manager context for Claude across sessions"
```

---

### Task 2: Create README.md

**Files:**
- Create: `C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\README.md`

- [ ] **Step 1: Write README.md**

```markdown
# Charlotte Golf League

Automated scoring and recap system for the 2026 IMI Golf League — 15 players, 9 rounds (April–August 2026).

## How It Works

1. Scores entered into `Scores/Scores.xlsx` (one tab per round: R1 Scores … R9 Scores)
2. Score watcher detects saves and updates `2026 IMI Golf League.xlsx` automatically
3. Recap emails generated every Monday after a round closes and saved to `Recap Emails/`
4. Live standings maintained in `Dashboard/standings.md` — updated via Claude conversation

## Folder Structure

```
Golf League/
├── 2026 IMI Golf League.xlsx    # Source of truth — standings, schedule (OneDrive shared)
├── Score Calculator.xlsx         # Score entry calculator
├── IMI GOLF LEAGUE.doc          # League rules document
├── Scores/
│   └── Scores.xlsx              # Score input (R1 Scores … R9 Scores tabs)
├── Dashboard/
│   └── standings.md             # Live standings — updated via Claude
├── Recap Emails/                # Generated recap email drafts (.txt)
├── setup/
│   ├── watcher.py               # Watches Scores.xlsx, auto-processes on change
│   ├── process_scores.py        # Updates main workbook from a score tab
│   ├── generate_recap.py        # Builds recap email draft for a completed round
│   ├── League Manager Guide.md  # Full system reference
│   ├── golf_watcher_task.xml    # Task Scheduler definition (watcher at login)
│   └── register_recap_task.bat  # One-time: register Monday recap task
├── start_watcher.bat            # Manually start the score watcher
└── run_recap.bat                # Manually generate a recap email
```

## Prerequisites

- Python 3 (`py -3`)
- openpyxl: `pip install openpyxl`

## Usage

**Score watcher** starts automatically at Windows login via Task Scheduler. To start manually:

```
start_watcher.bat
```

**Generate a recap email:**

```
run_recap.bat          # auto-detects today's scheduled round
run_recap.bat 1        # force Round 1 recap
```

Drafts are saved to `Recap Emails/Round_XX_Recap_Draft_YYYY-MM-DD.txt`.

**View current standings:** Open `Dashboard/standings.md` — kept current via Claude conversation.

## Live Scoreboard

`2026 IMI Golf League.xlsx` is shared via OneDrive view-only link for league members to view standings and schedule.

## Reference

See `setup/League Manager Guide.md` for full system documentation including score format, Excel layout, and Task Scheduler setup.
```

- [ ] **Step 2: Verify**

Open `README.md` and confirm:
- Folder structure matches actual files on disk
- Both bat files documented
- Dashboard/standings.md mentioned as Claude-maintained

- [ ] **Step 3: Commit**

```bash
cd "C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League"
git add README.md
git commit -m "Add README.md: repo overview and usage guide"
```

---

### Task 3: Create Dashboard/standings.md

**Files:**
- Create: `C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\Dashboard\standings.md`

- [ ] **Step 1: Create the Dashboard folder and write standings.md**

Round 1 is in progress (Apr 20 – May 1, 2026). No scores submitted yet — season started April 20, all test data cleared April 15.

```markdown
# IMI Golf League 2026 — Standings

**Season:** 2026 | **Rounds:** 9 | **Players:** 15
**Last updated:** 2026-04-24 via Claude

---

## Current Round

**Round 1** | Apr 20 – May 1, 2026
BYE: David Maddox

---

## Standings

*Round 1 in progress — no scores submitted yet.*

| Rank | Player | Total Pts | Record | Avg NET |
|------|--------|-----------|--------|---------|
| — | Brian Wojcio | 0 | 0-0-0 | — |
| — | Ethan High | 0 | 0-0-0 | — |
| — | Rob Bass | 0 | 0-0-0 | — |
| — | Carson Bass | 0 | 0-0-0 | — |
| — | Michael McHugh | 0 | 0-0-0 | — |
| — | Bruce Atkins | 0 | 0-0-0 | — |
| — | Alex Palmer | 0 | 0-0-0 | — |
| — | Curtis Lynn | 0 | 0-0-0 | — |
| — | Ben Link | 0 | 0-0-0 | — |
| — | Charlotte Hayes | 0 | 0-0-0 | — |
| — | David Maddox | 0 | 0-0-0 | — |
| — | Jerome Martin | 0 | 0-0-0 | — |
| — | Kaylan Adams | 0 | 0-0-0 | — |
| — | Megan Serian | 0 | 0-0-0 | — |
| — | Nick Coglianese | 0 | 0-0-0 | — |

---

## Schedule

| Round | Dates | BYE |
|-------|-------|-----|
| **1 ← current** | Apr 20 – May 1 | David Maddox |
| 2 | May 4 – May 15 | Nick Coglianese |
| 3 | May 18 – May 29 | Charlotte Hayes |
| 4 | Jun 1 – Jun 12 | Jerome Martin |
| 5 | Jun 15 – Jun 26 | Wojcio / High / R. Bass |
| 6 | Jun 29 – Jul 10 | C. Bass / McHugh / Atkins |
| 7 | Jul 13 – Jul 24 | Palmer / Lynn / Link |
| 8 | Jul 27 – Aug 7 | Kaylan Adams |
| 9 | Aug 10 – Aug 21 | Megan Serian |
```

- [ ] **Step 2: Verify**

Open `Dashboard/standings.md` and confirm:
- All 15 players listed
- Current round marked
- "Last updated" date is today (2026-04-24)

- [ ] **Step 3: Commit and push all**

```bash
cd "C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League"
git add Dashboard/standings.md
git commit -m "Add Dashboard/standings.md: initial standings (Round 1 in progress)"
git push
```

- [ ] **Step 4: Verify push**

```bash
git log --oneline -5
```

Expected: three new commits visible (CLAUDE.md, README.md, Dashboard/standings.md) at the top.

---

## Self-Review

**Spec coverage:**
- CLAUDE.md with standing instructions — Task 1
- README.md for GitHub — Task 2
- Dashboard/standings.md initial state — Task 3
- Existing automation untouched — no tasks modify setup/ or bat files

**Placeholders:** None. All file content is written in full.

**Type consistency:** N/A — markdown only, no code interfaces.
