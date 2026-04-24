# Golf League Docs & Dashboard Design
**Date:** 2026-04-24
**Project:** Charlotte Golf League (iSuite-LLC/charlotte-golf-league)
**Status:** Approved

## Overview

Add three artifacts to the Golf League working folder:
1. `CLAUDE.md` — makes Claude an effective league manager across sessions
2. `README.md` — repo-level documentation for GitHub
3. `Dashboard/standings.md` — live standings maintained by Claude via conversation

The existing watcher/processor/recap automation is untouched and remains fully operational. The conversational interface via Claude is additive; the old system will be decommissioned in a future phase.

## CLAUDE.md

**Location:** `C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\CLAUDE.md`

**Purpose:** Gives Claude everything needed to act as league manager without being re-briefed each session.

**Contents:**
- Project description and season overview (2026, 9 rounds, 15 players)
- All key file paths (main workbook, Scores.xlsx, scripts, Dashboard/)
- Excel layout: Scores 2026 tab, column map (R1=D through R9=L, Total=M, Record=N, Avg NET=O), player row map (mp/net pairs 3–32)
- Full roster with player numbers and handicaps
- Round schedule with date windows and BYE assignments
- Sheet protection password (`steelers`)
- Standing instruction: when asked for standings or scores, read `2026 IMI Golf League.xlsx` and update `Dashboard/standings.md`
- Standing instruction: old scripts (watcher, process_scores, generate_recap) remain operational — do not modify them

## README.md

**Location:** `C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\README.md`

**Purpose:** Public-facing repo documentation on GitHub.

**Contents:**
- What the system does (automated golf league scoring and recap generation)
- Folder structure overview
- Prerequisites (Python 3, openpyxl)
- How to start the score watcher (`start_watcher.bat`)
- How to run the recap generator (`run_recap.bat` or `run_recap.bat <round>`)
- Note that live standings are maintained via Claude conversation and reflected in `Dashboard/standings.md`
- Link to League Manager Guide (`setup/League Manager Guide.md`) for full reference

## Dashboard/standings.md

**Location:** `C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\Dashboard\standings.md`

**Purpose:** The persistent, human-readable standings file. Claude rewrites this file in full whenever the user asks for standings or reports scores via conversation.

**Structure:**
- Header: league name, current date, current round + date window
- Standings table: rank | name | total pts | record | avg NET — sorted by total pts descending, then name ascending
- BYE note for the current round
- Round schedule summary (all 9 rounds, dates, BYE players)
- Footer: "Last updated via Claude on YYYY-MM-DD"

**Update trigger:** Any conversation where the user asks for standings, reports scores, or requests a refresh. Claude reads the live Excel and rewrites the file in full.

## What Is Not Changing

- `setup/watcher.py` — untouched
- `setup/process_scores.py` — untouched
- `setup/generate_recap.py` — untouched
- `start_watcher.bat`, `run_recap.bat` — untouched
- `Scores/Scores.xlsx` — remains the score input source
- `2026 IMI Golf League.xlsx` — remains the source of truth; Claude reads it, does not write it

## Future Phase (Out of Scope Now)

- Decommission watcher and bat-based score processing in favor of fully conversational score entry
- Upgrade `Dashboard/standings.md` to an HTML dashboard
