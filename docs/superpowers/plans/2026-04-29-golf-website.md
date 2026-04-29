# Golf League Website Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a GitHub Pages site for the 2026 IMI Golf League with standings, results, and schedule tabs, auto-updating on every score push.

**Architecture:** `process_scores.py` is extended with `parse_matches()` and `write_dashboard_json()` which write `Dashboard/data.json` on every run. A single `Dashboard/index.html` fetches that JSON at page load and renders three tabs with vanilla JS. GitHub Pages serves the `Dashboard/` folder.

**Tech Stack:** Python 3 + openpyxl (existing), vanilla HTML/CSS/JS, GitHub Pages.

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `setup/process_scores.py` | Modify | Add `parse_matches()`, `write_dashboard_json()`, call at end of `process()` |
| `setup/tests/__init__.py` | Create | Empty — makes `tests/` a package for pytest |
| `setup/tests/test_process_scores.py` | Create | Unit test for `parse_matches()`; integration test for `write_dashboard_json()` |
| `Dashboard/index.html` | Create | Complete static site — HTML, CSS, all JS rendering |
| `Dashboard/data.json` | Generated | Written by processor; committed alongside standings.md |
| `.gitignore` | Create | Exclude `.superpowers/`, `__pycache__/`, `*.pyc` |

---

## Task 1: Repo hygiene — .gitignore + test scaffold

**Files:**
- Create: `.gitignore`
- Create: `setup/tests/__init__.py`

- [ ] **Step 1: Create `.gitignore`**

File: `C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\.gitignore`

```
.superpowers/
__pycache__/
*.pyc
*.pyo
```

- [ ] **Step 2: Create empty test package init**

File: `C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\setup\tests\__init__.py`

Contents: (empty file)

- [ ] **Step 3: Commit**

```bash
cd "C:/Users/ehigh/OneDrive - IMI Companies/Documents/Golf League"
git add .gitignore setup/tests/__init__.py
git commit -m "chore: add .gitignore and test package scaffold"
```

---

## Task 2: Add `parse_matches()` with unit test

**Files:**
- Modify: `setup/process_scores.py` — add `parse_matches()` after `parse_scores()`
- Create: `setup/tests/test_process_scores.py`

- [ ] **Step 1: Write the failing test**

File: `C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\setup\tests\test_process_scores.py`

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import openpyxl
from process_scores import parse_matches


def _make_ws(rows):
    """Build an in-memory worksheet from a list of row tuples."""
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(list(row))
    return ws


def test_parse_matches_single_match():
    # P1 row: bs=1 → name, 'Holes Won', F3, M3, Final3, Overall, net, None, p1_pts, None, p2_pts
    # Pad to at least 12 columns (index 0-11)
    p1_row = [None, 'Ethan High',    'Holes Won', 2, 1, 1, 4, 39, None, 6, None, 2] + [None]*18
    p2_row = [None, 'Brian Wojcio',  'Holes Won', 1, 2, 2, 5, 43, None, None, None, None] + [None]*18
    ws = _make_ws([p1_row, p2_row])

    matches = parse_matches(ws)

    assert len(matches) == 1
    m = matches[0]
    assert m['p1']    == 'Ethan High'
    assert m['p1Pts'] == 6
    assert m['p1Net'] == 39
    assert m['p2']    == 'Brian Wojcio'
    assert m['p2Pts'] == 2
    assert m['p2Net'] == 43
    assert m['winner'] == 'Ethan High'


def test_parse_matches_draw():
    p1_row = [None, 'Jerome Martin', 'Holes Won', 0, 0, 0, 0, 54, None, 4, None, 4] + [None]*18
    p2_row = [None, 'Kaylan Adams',  'Holes Won', 0, 0, 0, 0, 54, None, None, None, None] + [None]*18
    ws = _make_ws([p1_row, p2_row])

    matches = parse_matches(ws)

    assert len(matches) == 1
    assert matches[0]['winner'] is None
    assert matches[0]['p1Pts'] == 4
    assert matches[0]['p2Pts'] == 4


def test_parse_matches_empty_sheet():
    ws = _make_ws([[None] * 30])
    assert parse_matches(ws) == []
```

- [ ] **Step 2: Run test — confirm it fails**

```bash
cd "C:/Users/ehigh/OneDrive - IMI Companies/Documents/Golf League"
py -3 -m pytest setup/tests/test_process_scores.py::test_parse_matches_single_match -v
```

Expected: `ImportError` or `AttributeError: module 'process_scores' has no attribute 'parse_matches'`

- [ ] **Step 3: Add `parse_matches()` to `process_scores.py`**

Insert after the closing of `parse_scores()` (around line 141), before `def outcome(`:

```python
def parse_matches(ws):
    """
    Parse match pairings from a Calculator-format worksheet.
    Returns list of {p1, p1Pts, p1Net, p2, p2Pts, p2Net, winner}.
    """
    matches = []
    pending = {}   # block_start → {p1, p1Pts, p1Net, p2Pts}

    for row in ws.iter_rows(values_only=True):
        row = list(row)
        for bs in BLOCK_STARTS:
            if len(row) <= bs + 10:
                continue
            if row[bs + 1] != 'Holes Won':
                continue
            name = row[bs]
            if not isinstance(name, str) or not name.strip():
                continue
            name   = name.strip()
            net    = row[bs + 6]
            p1_pts = row[bs + 8]
            p2_pts = row[bs + 10]

            if p1_pts is not None:
                pending[bs] = {'p1': name, 'p1Pts': p1_pts, 'p1Net': net, 'p2Pts': p2_pts}
            elif bs in pending and pending[bs].get('p2Pts') is not None:
                p      = pending.pop(bs)
                winner = p['p1'] if p['p1Pts'] > p['p2Pts'] else (
                    name if p['p2Pts'] > p['p1Pts'] else None
                )
                matches.append({
                    'p1': p['p1'], 'p1Pts': p['p1Pts'], 'p1Net': p['p1Net'],
                    'p2': name,    'p2Pts': p['p2Pts'],  'p2Net': net,
                    'winner': winner,
                })

    return matches

```

- [ ] **Step 4: Run all three tests — confirm they pass**

```bash
cd "C:/Users/ehigh/OneDrive - IMI Companies/Documents/Golf League"
py -3 -m pytest setup/tests/test_process_scores.py -v
```

Expected:
```
test_parse_matches_single_match PASSED
test_parse_matches_draw PASSED
test_parse_matches_empty_sheet PASSED
```

- [ ] **Step 5: Commit**

```bash
git add setup/process_scores.py setup/tests/test_process_scores.py
git commit -m "feat: add parse_matches() with unit tests"
```

---

## Task 3: Add `write_dashboard_json()` with integration test

**Files:**
- Modify: `setup/process_scores.py` — add constants + `write_dashboard_json()` after `parse_matches()`
- Modify: `setup/tests/test_process_scores.py` — add integration test

- [ ] **Step 1: Add imports and constants to top of `process_scores.py`**

Change the existing import line from:
```python
import sys, os, re, io, openpyxl
```
To:
```python
import sys, os, re, io, json, openpyxl
from datetime import date as _date
```

After the existing `COL_AVG = 15` line, add:

```python
DASHBOARD_JSON = r"C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\Dashboard\data.json"
SCORES_XLSX    = r"C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\Scores\Scores.xlsx"

SCHEDULE = [
    {'round': 1, 'dates': 'Apr 20 – May 1',  'bye': 'David Maddox'},
    {'round': 2, 'dates': 'May 4 – May 15',  'bye': 'Nick Coglianese'},
    {'round': 3, 'dates': 'May 18 – May 29', 'bye': 'Charlotte Hayes'},
    {'round': 4, 'dates': 'Jun 1 – Jun 12',  'bye': 'Jerome Martin'},
    {'round': 5, 'dates': 'Jun 15 – Jun 26', 'bye': 'Wojcio / High / R. Bass'},
    {'round': 6, 'dates': 'Jun 29 – Jul 10', 'bye': 'C. Bass / McHugh / Atkins'},
    {'round': 7, 'dates': 'Jul 13 – Jul 24', 'bye': 'Palmer / Lynn / Link'},
    {'round': 8, 'dates': 'Jul 27 – Aug 7',  'bye': 'Kaylan Adams'},
    {'round': 9, 'dates': 'Aug 10 – Aug 21', 'bye': 'Megan Serian'},
]

# Expected match count per round (rounds 5-7 have 3-way BYEs → 6 matches each)
ROUND_MATCH_COUNTS = {1: 7, 2: 7, 3: 7, 4: 7, 5: 6, 6: 6, 7: 6, 8: 7, 9: 7}
```

- [ ] **Step 2: Write the integration test (before implementing)**

Append to `setup/tests/test_process_scores.py`:

```python
def test_write_dashboard_json_structure():
    """Integration test — writes real data.json and validates structure."""
    import json as _json
    from process_scores import write_dashboard_json, build_name_map

    name_to_num = build_name_map()
    write_dashboard_json(1, name_to_num)

    with open(
        r"C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\Dashboard\data.json",
        encoding='utf-8'
    ) as f:
        data = _json.load(f)

    assert data['season'] == 2026
    assert isinstance(data['lastUpdated'], str)
    assert len(data['players']) == 15
    assert len(data['rounds'])  == 9
    assert len(data['schedule']) == 9

    for p in data['players']:
        assert 'id' in p
        assert 'name' in p
        assert 'totalPts' in p
        assert 'record' in p
        assert isinstance(p['rounds'], list)

    for r in data['rounds']:
        assert r['status'] in ('complete', 'in_progress', 'upcoming')
        assert isinstance(r['matches'], list)
```

- [ ] **Step 3: Run integration test — confirm it fails**

```bash
py -3 -m pytest setup/tests/test_process_scores.py::test_write_dashboard_json_structure -v
```

Expected: `AttributeError: module 'process_scores' has no attribute 'write_dashboard_json'`

- [ ] **Step 4: Add `write_dashboard_json()` to `process_scores.py`**

Insert after `parse_matches()`, before `def outcome(`:

```python
def write_dashboard_json(rnd, name_to_num):
    """Write Dashboard/data.json from current workbook state + Scores.xlsx match tabs."""
    num_to_name = {v: k for k, v in name_to_num.items()}

    # Read all player stats from Scores 2026
    wb_main   = openpyxl.load_workbook(LEAGUE, data_only=True, read_only=True)
    ws_scores = wb_main['Scores 2026']

    players = []
    for num in range(1, 16):
        name                      = num_to_name.get(num, f'Player {num}')
        total_pts, record, avg_net = compute_stats(ws_scores, num)
        mp_row, net_row           = PLAYER_ROWS[num]

        rounds_data = []
        for r in range(1, TOTAL_ROUNDS + 1):
            col = round_col(r)
            pts = ws_scores.cell(row=mp_row,  column=col).value
            net = ws_scores.cell(row=net_row, column=col).value
            if pts is not None:
                rounds_data.append({
                    'round':    r,
                    'matchPts': pts,
                    'net':      net,
                    'opponent': None,
                    'result':   outcome(pts),
                })

        players.append({
            'id':       num,
            'name':     name,
            'totalPts': total_pts,
            'record':   record,
            'avgNet':   avg_net,
            'rounds':   rounds_data,
        })

    wb_main.close()

    # Read match pairings from each score tab; fill in opponents
    wb_src     = openpyxl.load_workbook(SCORES_XLSX, data_only=True)
    rounds_out = []

    for r in range(1, TOTAL_ROUNDS + 1):
        tab      = f'R{r} Scores'
        sched    = SCHEDULE[r - 1]
        matches  = []
        expected = ROUND_MATCH_COUNTS[r]

        if tab in wb_src.sheetnames:
            for m in parse_matches(wb_src[tab]):
                matches.append({
                    'p1': m['p1'], 'p1Pts': m['p1Pts'], 'p1Net': m['p1Net'],
                    'p2': m['p2'], 'p2Pts': m['p2Pts'], 'p2Net': m['p2Net'],
                    'winner': m['winner'],
                })
                for player in players:
                    for rd in player['rounds']:
                        if rd['round'] == r:
                            if player['name'] == m['p1']:
                                rd['opponent'] = m['p2']
                            elif player['name'] == m['p2']:
                                rd['opponent'] = m['p1']

        n      = len(matches)
        status = 'upcoming' if n == 0 else ('complete' if n >= expected else 'in_progress')

        rounds_out.append({
            'round':   r,
            'dates':   sched['dates'],
            'bye':     sched['bye'],
            'status':  status,
            'matches': matches,
        })

    wb_src.close()

    data = {
        'season':       2026,
        'lastUpdated':  _date.today().isoformat(),
        'currentRound': rnd,
        'players':      players,
        'rounds':       rounds_out,
        'schedule':     SCHEDULE,
    }

    with open(DASHBOARD_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Dashboard JSON: {DASHBOARD_JSON}")

```

- [ ] **Step 5: Run all tests — confirm they pass**

```bash
cd "C:/Users/ehigh/OneDrive - IMI Companies/Documents/Golf League"
py -3 -m pytest setup/tests/ -v
```

Expected: 4 tests, all PASSED. Also verify `Dashboard/data.json` was created.

- [ ] **Step 6: Commit**

```bash
git add setup/process_scores.py setup/tests/test_process_scores.py
git commit -m "feat: add write_dashboard_json() — generates Dashboard/data.json on score updates"
```

---

## Task 4: Wire `write_dashboard_json()` into `process()`

**Files:**
- Modify: `setup/process_scores.py` — call `write_dashboard_json()` at end of `process()`

- [ ] **Step 1: Add call at end of `process()`**

In `process_scores.py`, find the `return updated` line at the end of `process()`. Change it from:

```python
    return updated
```

To:

```python
    write_dashboard_json(rnd, name_to_num)
    return updated
```

- [ ] **Step 2: Run processor end-to-end**

```bash
cd "C:/Users/ehigh/OneDrive - IMI Companies/Documents/Golf League"
py -3 setup/process_scores.py "Scores/Scores.xlsx" "R1 Scores"
```

Expected output includes the existing player lines plus a new line:
```
Dashboard JSON: C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\Dashboard\data.json
```

- [ ] **Step 3: Inspect generated JSON**

```bash
py -3 -c "
import json
with open('Dashboard/data.json', encoding='utf-8') as f:
    d = json.load(f)
print('Players:', len(d['players']))
print('Rounds:', len(d['rounds']))
r1 = d['rounds'][0]
print('R1 status:', r1['status'])
print('R1 matches:', len(r1['matches']))
# Print first match
if r1['matches']:
    print('First match:', r1['matches'][0])
# Print Ethan High rounds
ethan = next(p for p in d['players'] if p['name'] == 'Ethan High')
print('Ethan:', ethan['totalPts'], 'pts', ethan['record'], ethan['rounds'])
"
```

Expected: 15 players, 9 rounds, R1 status `in_progress`, 5 matches, Ethan's opponent populated.

- [ ] **Step 4: Run all tests — still passing**

```bash
py -3 -m pytest setup/tests/ -v
```

- [ ] **Step 5: Commit**

```bash
git add setup/process_scores.py Dashboard/data.json
git commit -m "feat: auto-generate data.json on every score processing run"
```

---

## Task 5: Build `Dashboard/index.html`

**Files:**
- Create: `Dashboard/index.html`

- [ ] **Step 1: Create `Dashboard/index.html`**

File: `C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\Dashboard\index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IMI Golf League 2026</title>
  <style>
    :root {
      --bg:           #111111;
      --surface:      #1e1e1e;
      --surface-hover:#252525;
      --border:       #333333;
      --text:         #ffffff;
      --muted:        #888888;
      --red:          #cc2027;
      --blue:         #1a6fc4;
      --green:        #5aaa35;
      --orange:       #e87722;
      --silver:       #aaaaaa;
      --bronze:       #cd7f32;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      font-size: 15px;
      min-height: 100vh;
    }
    /* ── Header ── */
    .site-header {
      background: #000;
      border-bottom: 2px solid var(--orange);
      padding: 14px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .header-left  { display: flex; align-items: center; gap: 12px; }
    .imi-dots     { display: flex; gap: 5px; }
    .dot          { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
    .header-title-group h1 {
      font-size: 1.1rem; font-weight: 700;
      letter-spacing: 0.06em; text-transform: uppercase; line-height: 1.1;
    }
    .header-title-group .year {
      font-size: 0.72rem; color: var(--orange);
      font-weight: 600; letter-spacing: 0.1em;
    }
    .header-right { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
    .round-badge {
      background: var(--orange); color: #000;
      font-size: 0.68rem; font-weight: 700;
      padding: 3px 8px; border-radius: 3px;
      text-transform: uppercase; letter-spacing: 0.05em;
    }
    .last-updated { font-size: 0.68rem; color: var(--muted); }
    /* ── Tabs ── */
    .tab-nav {
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      display: flex;
    }
    .tab-btn {
      background: none; border: none; color: var(--muted);
      cursor: pointer; font-size: 0.82rem; font-weight: 600;
      letter-spacing: 0.05em; padding: 12px 24px;
      text-transform: uppercase; transition: color 0.15s;
      border-bottom: 3px solid transparent; margin-bottom: -1px;
    }
    .tab-btn:hover { color: var(--text); }
    .tab-btn.active { color: var(--text); border-bottom-color: var(--blue); }
    /* ── Content ── */
    .content { max-width: 900px; margin: 0 auto; padding: 24px 16px; }
    .hidden  { display: none !important; }
    /* ── Standings Table ── */
    .standings-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    .standings-table thead th {
      color: var(--muted); font-size: 0.68rem; font-weight: 600;
      letter-spacing: 0.08em; padding: 8px 12px;
      text-align: left; text-transform: uppercase;
      border-bottom: 1px solid var(--border);
    }
    .player-row { cursor: pointer; transition: background 0.1s; }
    .player-row:hover { background: var(--surface-hover); }
    .player-row.expanded { background: var(--surface); }
    .player-row td {
      padding: 11px 12px;
      border-bottom: 1px solid var(--border);
      vertical-align: middle;
    }
    .player-row.muted td { color: var(--muted); cursor: default; }
    .rank-badge {
      display: inline-block; width: 26px; height: 26px;
      border-radius: 50%; background: var(--surface);
      color: var(--muted); font-size: 0.75rem; font-weight: 700;
      line-height: 26px; text-align: center;
    }
    .rank-badge.gold   { background: var(--orange); color: #000; }
    .rank-badge.silver { background: var(--silver);  color: #000; }
    .rank-badge.bronze { background: var(--bronze);  color: #fff; }
    .player-name { font-weight: 600; }
    .pts   { font-weight: 700; font-size: 1rem; color: var(--orange); }
    .rec-w { color: var(--red);   font-weight: 600; }
    .rec-l { color: var(--muted); }
    .rec-d { color: var(--green); font-weight: 600; }
    .avg-net { color: var(--muted); }
    /* ── Player expand panel ── */
    .expand-row td {
      padding: 0; background: #181818;
      border-bottom: 2px solid var(--blue);
    }
    .player-detail { padding: 12px 16px; }
    .detail-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
    .detail-table th {
      color: var(--muted); font-size: 0.67rem; font-weight: 600;
      letter-spacing: 0.08em; padding: 6px 10px;
      text-align: left; text-transform: uppercase;
    }
    .detail-table td { padding: 7px 10px; border-top: 1px solid #2a2a2a; }
    .result-W { color: var(--red);   font-weight: 700; }
    .result-D { color: var(--green); font-weight: 700; }
    .result-L { color: var(--muted); }
    /* ── Results ── */
    .round-section {
      background: var(--surface); border-radius: 6px;
      margin-bottom: 16px; overflow: hidden;
    }
    .round-header {
      background: #1a1a1a; border-left: 4px solid var(--orange);
      display: flex; align-items: center; gap: 12px; padding: 12px 16px;
    }
    .round-label {
      font-size: 0.85rem; font-weight: 700;
      text-transform: uppercase; letter-spacing: 0.05em;
    }
    .round-dates { color: var(--muted); font-size: 0.8rem; }
    .badge {
      font-size: 0.65rem; font-weight: 700;
      padding: 3px 7px; border-radius: 3px;
      text-transform: uppercase; letter-spacing: 0.05em; margin-left: auto;
    }
    .badge.in-progress { background: var(--orange); color: #000; }
    .badge.complete    { background: #2a2a2a; color: var(--green); }
    .round-bye {
      color: var(--muted); font-size: 0.78rem;
      padding: 6px 16px; border-bottom: 1px solid var(--border);
    }
    .matches { padding: 8px 0; }
    .match {
      display: flex; align-items: center; gap: 12px; padding: 8px 16px;
    }
    .match + .match { border-top: 1px solid #2a2a2a; }
    .match-winner { font-weight: 700; flex: 1; }
    .match-loser  { color: var(--muted); flex: 1; text-align: right; }
    .match-score  { color: var(--orange); font-size: 0.85rem; font-weight: 700; white-space: nowrap; }
    /* ── Schedule ── */
    .schedule-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
    .schedule-table thead th {
      color: var(--muted); font-size: 0.68rem; font-weight: 600;
      letter-spacing: 0.08em; padding: 8px 12px;
      text-align: left; text-transform: uppercase;
      border-bottom: 1px solid var(--border);
    }
    .schedule-table td { padding: 11px 12px; border-bottom: 1px solid var(--border); }
    .schedule-table tr.current-round td  { background: #1e1e1e; }
    .schedule-table tr.complete-round td { color: var(--muted); }
    .status-complete { color: var(--green);  font-weight: 600; }
    .status-current  { color: var(--orange); font-weight: 600; }
    .status-upcoming { color: #555; }
    /* ── Responsive ── */
    @media (max-width: 600px) {
      .site-header { flex-direction: column; align-items: flex-start; gap: 8px; }
      .header-right { align-items: flex-start; }
      .tab-btn { padding: 10px 14px; font-size: 0.75rem; }
      .standings-table thead th:nth-child(4),
      .standings-table .player-row td:nth-child(4) { display: none; }
    }
  </style>
</head>
<body>

<header class="site-header">
  <div class="header-left">
    <div class="imi-dots">
      <span class="dot" style="background:#cc2027"></span>
      <span class="dot" style="background:#1a6fc4"></span>
      <span class="dot" style="background:#5aaa35"></span>
      <span class="dot" style="background:#e87722"></span>
    </div>
    <div class="header-title-group">
      <h1>IMI Golf League</h1>
      <div class="year">2026 Season</div>
    </div>
  </div>
  <div class="header-right">
    <span id="current-round-badge" class="round-badge" style="display:none"></span>
    <span id="last-updated" class="last-updated"></span>
  </div>
</header>

<nav class="tab-nav">
  <button class="tab-btn active"  onclick="showTab('standings', this)">Standings</button>
  <button class="tab-btn"         onclick="showTab('results', this)">Results</button>
  <button class="tab-btn"         onclick="showTab('schedule', this)">Schedule</button>
</nav>

<main class="content">
  <div id="tab-standings" class="tab-pane"></div>
  <div id="tab-results"   class="tab-pane hidden"></div>
  <div id="tab-schedule"  class="tab-pane hidden"></div>
</main>

<script>
  let leagueData = null;

  async function init() {
    try {
      const resp = await fetch('data.json');
      if (!resp.ok) throw new Error('fetch failed');
      leagueData = await resp.json();
      renderAll();
    } catch (e) {
      document.querySelector('.content').innerHTML =
        '<p style="color:#555;text-align:center;padding:60px 0">Could not load league data.</p>';
    }
  }

  function renderAll() {
    renderHeader();
    renderStandings();
    renderResults();
    renderSchedule();
  }

  function showTab(name, btn) {
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + name).classList.remove('hidden');
    btn.classList.add('active');
  }

  /* ── Header ── */
  function renderHeader() {
    document.getElementById('last-updated').textContent = 'Updated: ' + leagueData.lastUpdated;
    const cur  = leagueData.rounds.find(r => r.status === 'in_progress');
    const last = [...leagueData.rounds].reverse().find(r => r.status === 'complete');
    const badge = document.getElementById('current-round-badge');
    if (cur) {
      badge.textContent    = 'Round ' + cur.round + ' In Progress';
      badge.style.display  = 'inline-block';
    } else if (last) {
      badge.textContent    = 'Round ' + last.round + ' Complete';
      badge.style.display  = 'inline-block';
    }
  }

  /* ── Standings ── */
  function rankBadge(rank) {
    const cls = rank === 1 ? 'gold' : rank === 2 ? 'silver' : rank === 3 ? 'bronze' : '';
    return `<span class="rank-badge ${cls}">${rank}</span>`;
  }

  function recordHTML(record) {
    const [w, l, d] = record.split('-');
    return `<span class="rec-w">${w}W</span> <span class="rec-l">${l}L</span> <span class="rec-d">${d}D</span>`;
  }

  function renderPlayerDetail(player) {
    if (!player.rounds.length) {
      return '<div class="player-detail"><p style="color:#555;font-size:0.8rem;padding:4px 0">No rounds played yet.</p></div>';
    }
    const rows = player.rounds.map(r => `
      <tr>
        <td>R${r.round}</td>
        <td>${r.opponent || '—'}</td>
        <td class="result-${r.result}">${r.result}</td>
        <td>${r.matchPts}</td>
        <td>${r.net !== null ? r.net : '—'}</td>
      </tr>`).join('');
    return `<div class="player-detail">
      <table class="detail-table">
        <thead><tr><th>Rd</th><th>Opponent</th><th>Result</th><th>Pts</th><th>NET</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  }

  function toggleExpand(playerId) {
    document.getElementById('expand-' + playerId).classList.toggle('hidden');
    document.getElementById('row-'    + playerId).classList.toggle('expanded');
  }

  function renderStandings() {
    const ranked = leagueData.players
      .filter(p => p.rounds.length > 0)
      .sort((a, b) => b.totalPts - a.totalPts || (a.avgNet || 999) - (b.avgNet || 999));
    const unranked = leagueData.players.filter(p => p.rounds.length === 0);

    let html = `<table class="standings-table">
      <thead><tr>
        <th>Rank</th><th>Player</th><th>Pts</th><th>Record</th><th>Avg NET</th>
      </tr></thead><tbody>`;

    ranked.forEach((p, i) => {
      html += `
        <tr class="player-row" id="row-${p.id}" onclick="toggleExpand(${p.id})">
          <td>${rankBadge(i + 1)}</td>
          <td class="player-name">${p.name}</td>
          <td class="pts">${p.totalPts}</td>
          <td>${recordHTML(p.record)}</td>
          <td class="avg-net">${p.avgNet !== null ? p.avgNet.toFixed(1) : '—'}</td>
        </tr>
        <tr class="expand-row hidden" id="expand-${p.id}">
          <td colspan="5">${renderPlayerDetail(p)}</td>
        </tr>`;
    });

    unranked.forEach(p => {
      html += `<tr class="player-row muted">
        <td>—</td><td class="player-name">${p.name}</td>
        <td>—</td><td>—</td><td>—</td>
      </tr>`;
    });

    html += '</tbody></table>';
    document.getElementById('tab-standings').innerHTML = html;
  }

  /* ── Results ── */
  function renderResults() {
    const rounds = leagueData.rounds.slice().reverse();  // most recent first

    const html = rounds.map(r => {
      if (r.status === 'upcoming') {
        return `<div class="round-section" style="opacity:0.4">
          <div class="round-header">
            <span class="round-label">Round ${r.round}</span>
            <span class="round-dates">${r.dates}</span>
            <span class="badge" style="background:#2a2a2a;color:#555;margin-left:auto">Upcoming</span>
          </div>
          <div class="round-bye">BYE: ${r.bye}</div>
        </div>`;
      }
      const badgeCls = r.status === 'in_progress' ? 'in-progress' : 'complete';
      const badgeTxt = r.status === 'in_progress' ? 'In Progress' : '✓ Complete';
      const matchRows = r.matches.map(m => {
        const draw = m.winner === null;
        return `<div class="match">
          <span class="${!draw && m.winner === m.p1 ? 'match-winner' : 'match-loser'}">${m.p1}</span>
          <span class="match-score">${m.p1Pts} – ${m.p2Pts}</span>
          <span class="${!draw && m.winner === m.p2 ? 'match-winner' : 'match-loser'}">${m.p2}</span>
        </div>`;
      }).join('');
      return `<div class="round-section">
        <div class="round-header">
          <span class="round-label">Round ${r.round}</span>
          <span class="round-dates">${r.dates}</span>
          <span class="badge ${badgeCls}">${badgeTxt}</span>
        </div>
        <div class="round-bye">BYE: ${r.bye}</div>
        <div class="matches">${matchRows}</div>
      </div>`;
    }).join('');

    document.getElementById('tab-results').innerHTML = html;
  }

  /* ── Schedule ── */
  function renderSchedule() {
    const rows = leagueData.schedule.map(s => {
      const rd     = leagueData.rounds.find(r => r.round === s.round);
      const status = rd ? rd.status : 'upcoming';
      const statusHTML =
        status === 'complete'    ? '<span class="status-complete">✓ Done</span>'  :
        status === 'in_progress' ? '<span class="status-current">● Now</span>'    :
                                   '<span class="status-upcoming">Upcoming</span>';
      const rowCls = status === 'in_progress' ? 'current-round'
                   : status === 'complete'    ? 'complete-round' : '';
      return `<tr class="${rowCls}">
        <td>R${s.round}</td>
        <td>${s.dates}</td>
        <td>${s.bye}</td>
        <td>${statusHTML}</td>
      </tr>`;
    }).join('');

    document.getElementById('tab-schedule').innerHTML = `
      <table class="schedule-table">
        <thead><tr><th>Round</th><th>Dates</th><th>BYE</th><th>Status</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
  }

  init();
</script>
</body>
</html>
```

- [ ] **Step 2: Start a local server to test**

```bash
cd "C:/Users/ehigh/OneDrive - IMI Companies/Documents/Golf League/Dashboard"
py -3 -m http.server 8080
```

Open `http://localhost:8080` in a browser. (Must use the server — `fetch('data.json')` won't work from `file://`.)

- [ ] **Step 3: Verify Standings tab**

- League table loads with all 10 players who have scores
- Rank badges: gold for 1st, silver for 2nd, bronze for 3rd
- Click any ranked player row — detail panel expands showing round-by-round results with opponent names
- Unranked players (Alex Palmer, Curtis Lynn, etc.) appear at bottom with dashes
- Header shows "Round 1 In Progress" orange badge and last-updated date

- [ ] **Step 4: Verify Results tab**

Click Results tab:
- Round 1 section appears with "In Progress" badge
- All 5 matches listed: winner bold white, loser muted gray
- Draw match (Jerome Martin 4 – Kaylan Adams 4): both names appear as `match-loser` (neither bold since `winner === null`)

- [ ] **Step 5: Verify Schedule tab**

Click Schedule tab:
- All 9 rounds listed
- Round 1 row highlighted, shows "● Now"
- Rounds 2–9 show "Upcoming"

- [ ] **Step 6: Stop local server (Ctrl+C) and commit**

```bash
cd "C:/Users/ehigh/OneDrive - IMI Companies/Documents/Golf League"
git add Dashboard/index.html
git commit -m "feat: add Dashboard/index.html — IMI sports-dark standings site"
```

---

## Task 6: Update commit workflow + push everything live

**Files:**
- Modify: `Dashboard/standings.md` — update the "Last updated" line to note site is live

- [ ] **Step 1: Push current branch to GitHub**

```bash
cd "C:/Users/ehigh/OneDrive - IMI Companies/Documents/Golf League"
git push
```

- [ ] **Step 2: Enable GitHub Pages (one-time, done in browser)**

1. Go to `https://github.com/iSuite-LLC/charlotte-golf-league`
2. Click **Settings** → **Pages** (left sidebar)
3. Under **Source**, select branch `main`, folder `/Dashboard`
4. Click **Save**

GitHub will show: "Your site is being built." Wait ~60 seconds.

- [ ] **Step 3: Verify site is live**

Open `https://isuite-llc.github.io/charlotte-golf-league/`

All three tabs should work identically to the local test in Task 5.

- [ ] **Step 4: Update score-update commit workflow**

From now on, every score-update commit should include `Dashboard/data.json`:

```bash
git add Dashboard/standings.md Dashboard/data.json setup/process_scores.py
git commit -m "R1 scores update ..."
git push
```

(The processor writes `data.json` automatically — just make sure to `git add` it.)

---

## Updated Score-Update Workflow (after this plan)

When Claude processes scores, the full commit will be:

```bash
git add Dashboard/standings.md Dashboard/data.json setup/process_scores.py
git commit -m "RN scores update ..."
git push
```

`index.html` only needs to be committed when the site design changes, not on every score update.
