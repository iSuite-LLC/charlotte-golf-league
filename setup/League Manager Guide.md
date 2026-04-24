# 2026 IMI Golf League — Manager Guide

## Folder Structure

```
C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\
└── 2026 IMI Golf League.xlsx            ← main workbook (Schedule + Scores 2026 tabs)
                                            shared via OneDrive view-only link for coworkers

C:\Users\ehigh\claude\Golf League\
├── process_scores.py                    ← parses a score tab and updates Scores 2026
├── watcher.py                           ← background monitor (runs automatically at login)
├── start_watcher.bat                    ← manually start the watcher if needed
├── processed_files.json                 ← auto-created; tracks which tabs were processed
├── League Manager Guide.md              ← this file
├── Scores/
│   └── Scores.xlsx                      ← all round scores; one tab per round (R1–R9)
└── setup/                               ← one-time setup scripts (already run; archive only)
    ├── golf_watcher_task.xml
    ├── register_task.bat
    ├── update_scores.py
    └── read_golf.py
```

---

## How Scores Work

### Match Points (max 8 pts per match)
| Category | Points Available |
|----------|-----------------|
| First 3 holes (holes 1–3) | 1 pt to winner |
| Middle 3 holes (holes 4–6) | 1 pt to winner |
| Final 3 holes (holes 7–9) | 1 pt to winner |
| Overall (most holes won) | 1 pt to winner |
| Net Score (lower net) | 1 pt to winner |
| Ties in any category | 0.5 pts each |

**Result thresholds:**
- **Win** = 4.5+ pts
- **Draw** = exactly 4.0 pts
- **Loss** = under 4.0 pts

### Match Record Format
`W-L-D`  (e.g., `2-1-0` = 2 wins, 1 loss, 0 draws)

---

## Players (Season 2026)

| # | Name | Handicap |
|---|------|----------|
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

15 players, 9 rounds. Each round: 7 matches + 1 BYE (odd player out).

---

## Scores 2026 Tab Layout

| Column | Content |
|--------|---------|
| D | Round 1 |
| E | Round 2 |
| F | Round 3 |
| G | Round 4 |
| H | Round 5 |
| I | Round 6 |
| J | Round 7 |
| K | Round 8 |
| L | Round 9 |
| M | League Total Score |
| N | Match Record (W-L-D) |
| O | Average NET Score |

Each player occupies **two rows**: match points row, then NET score row directly below.

---

## Auto-Update System

### How it works
1. `watcher.py` polls every **30 seconds** for changes to `Scores/Scores.xlsx`.
2. When a tab's score data changes, it calls `process_scores.py`, which:
   - Reads the round number from the tab name (e.g. `R3 Scores` → Round 3, column F)
   - Parses all matchup blocks in the Calculator format
   - **Unprotects** the Scores 2026 sheet, writes match points + NET scores into the correct round column, recomputes each player's League Total, Match Record, and Average NET from scratch, then **re-protects** the sheet before saving
3. A fingerprint of each tab's score rows is saved in `processed_files.json` so the same unchanged tab is never re-processed.

### Score file — Scores/Scores.xlsx
- One tab per round, pre-created for all 9 rounds: **R1 Scores** through **R9 Scores**
- Each tab uses the Calculator format with matchup summary blocks:
  - Block 1: columns B–M
  - Block 2: columns O–Z
  - Block 3: columns AB–AM
  - In each block: `Holes Won` row for P1 (has total pts in col +8 and +10), then `Holes Won` row for P2

### Tab naming — flexible
The round number is read from the tab name automatically. Any of these work:

| Tab name | Detected as |
|----------|-------------|
| `R2 Scores` | Round 2 |
| `Round 2` | Round 2 |
| `Week 2` | Round 2 |

### To enter a new round
1. Open `Scores/Scores.xlsx` and fill in the appropriate round tab
2. Save the file
3. The watcher picks it up within 30 seconds — no manual steps needed

---

## Sheet Protection

The main workbook has two protected tabs and one unprotected tab:

| Tab | Protected | Notes |
|-----|-----------|-------|
| Schedule | Yes — password: `steelers` | View-only for all coworkers |
| Scores 2026 | Yes — password: `steelers` | Auto-unlocked/re-locked by `process_scores.py` on each update |
| Calculator | No | Coworkers can use freely |

The scripts handle protection automatically — no manual steps needed when processing scores.

To manually protect/unprotect a tab in Excel: right-click the tab → **Protect Sheet** / **Unprotect Sheet** → enter `steelers`.

---

## Sharing with Coworkers

The main workbook lives on OneDrive and is shared via a **view-only link**. Coworkers can see real-time standings without any edit access.

- Share link type: **Anyone with the link can view** (not edit)
- Coworkers should open the link in a **browser (Excel Online)** — opening in the desktop Excel app can cause file lock conflicts with the auto-update scripts
- When `process_scores.py` saves the file, OneDrive syncs the update to the cloud within seconds

---

## Managing the Background Watcher

The watcher runs automatically at every Windows login via Task Scheduler.

### Task Scheduler commands (run in Command Prompt)
```bat
:: Check status
schtasks /Query /TN "IMI Golf League Watcher" /FO LIST

:: Start manually (if not already running)
schtasks /Run /TN "IMI Golf League Watcher"

:: Stop the running instance
schtasks /End /TN "IMI Golf League Watcher"

:: Disable auto-start (keeps task, won't run at login)
schtasks /Change /TN "IMI Golf League Watcher" /DISABLE

:: Re-enable auto-start
schtasks /Change /TN "IMI Golf League Watcher" /ENABLE

:: Remove the task entirely
schtasks /Delete /TN "IMI Golf League Watcher" /F
```

### Manual fallback
If the watcher isn't running, you can:
- Double-click `start_watcher.bat` to run it manually, OR
- Run a one-off update directly:
  ```
  py -3 process_scores.py "Scores\Scores.xlsx" "R2 Scores"
  ```

---

## Round Results (Reference)

Season starts **April 20, 2026**. Results will be logged here as rounds are completed.
