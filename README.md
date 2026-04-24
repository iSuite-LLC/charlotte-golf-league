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
