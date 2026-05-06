"""
process_scores.py — general round processor for the 2026 IMI Golf League

Usage: py -3 process_scores.py <source_xlsx> <tab_name>

  <source_xlsx>  Path to the score file (e.g. Scores/Scores.xlsx)
  <tab_name>     Name of the tab to read (e.g. "R3 Scores")

Reads Calculator-format score data from the given tab, detects the round
number from the tab name, then updates Scores 2026 in the main workbook
with match points, NET scores, totals, records, and averages.

Round detection from tab name (case-insensitive):
  "R3 Scores", "Round 3", "R3", "Week 3"  → Round 3
  Falls back to the next unfilled round in Scores 2026.
"""

import sys, os, re, io, json, openpyxl
from datetime import date as _date, datetime as _datetime
if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

LEAGUE         = r"C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\2026 IMI Golf League.xlsx"
SHEET_PASSWORD = "steelers"
TOTAL_ROUNDS   = 9    # rounds 1-9 → columns D-L (4-12)

COL_TOTAL = 13      # M  League Total Score
COL_REC   = 14      # N  Match Record
COL_AVG   = 15      # O  Average NET Score

DASHBOARD_JSON = r"C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\Dashboard\data.json"
SCORES_XLSX    = r"C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\Scores\Scores.xlsx"

SCHEDULE = [
    {'round': 1, 'dates': 'Apr 20 – May 1',  'bye': 'David Maddox'},
    {'round': 2, 'dates': 'May 4 – May 15',  'bye': 'Nick Coglianese'},
    {'round': 3, 'dates': 'May 18 – May 29', 'bye': 'Charlotte Hayes'},
    {'round': 4, 'dates': 'Jun 1 – Jun 12',  'bye': 'Jerome Martin'},
    {'round': 5, 'dates': 'Jun 15 – Jun 26', 'bye': 'Wojcio / High / R. Bass'},
    {'round': 6, 'dates': 'Jun 29 – Jul 10', 'bye': 'C. Bass / McHugh / Atkins'},
    {'round': 7, 'dates': 'Jul 13 – Jul 24', 'bye': 'Palmer / Lynn / Linck'},
    {'round': 8, 'dates': 'Jul 27 – Aug 7',  'bye': 'Kaylan Adams'},
    {'round': 9, 'dates': 'Aug 10 – Aug 21', 'bye': 'Megan Serian'},
]

# Expected match count per round (rounds 5-7 have 3-way BYEs → 6 matches each)
ROUND_MATCH_COUNTS = {1: 7, 2: 7, 3: 7, 4: 7, 5: 6, 6: 6, 7: 6, 8: 7, 9: 7}

# Full round-by-round pairing schedule (player numbers, from Schedule tab)
ROUND_PAIRINGS = {
    1: [(1,2),(3,4),(5,6),(7,8),(9,10),(12,13),(14,15)],
    2: [(1,3),(2,4),(5,7),(6,8),(9,12),(10,13),(11,14)],
    3: [(1,4),(2,5),(3,6),(7,13),(8,15),(9,14),(11,12)],
    4: [(1,5),(2,7),(3,8),(4,6),(9,13),(10,14),(11,15)],
    5: [(4,5),(6,7),(8,9),(10,11),(12,15),(13,14)],
    6: [(1,8),(2,3),(7,10),(9,11),(12,14),(13,15)],
    7: [(1,10),(2,11),(3,12),(4,15),(5,14),(6,13)],
    8: [(1,6),(2,8),(3,5),(4,14),(7,11),(9,15),(10,12)],
    9: [(1,9),(2,6),(3,7),(4,8),(5,12),(10,15),(11,13)],
}

def round_col(r):
    return 3 + r    # R1→4(D), R2→5(E), ... R9→12(L)

# player_num → (match_pts_row, net_score_row) in Scores 2026
PLAYER_ROWS = {
     1: ( 3,  4),   # Brian Wojcio
     2: ( 5,  6),   # Ethan High
     3: ( 7,  8),   # Rob Bass
     4: ( 9, 10),   # Carson Bass
     5: (11, 12),   # Michael McHugh
     6: (13, 14),   # Bruce Atkins
     7: (15, 16),   # Alex Palmer
     8: (17, 18),   # Curtis Lynn
     9: (19, 20),   # Ben Link
    10: (21, 22),   # Charlotte Hayes
    11: (23, 24),   # David Maddox
    12: (25, 26),   # Jerome Martin
    13: (27, 28),   # Kaylan Adams
    14: (29, 30),   # Megan Serian
    15: (31, 32),   # Nick Coglianese
}

# 0-indexed col where each side-by-side matchup block begins.
# Within each block: +0=name, +1='Holes Won', +6=NET, +8=P1_pts, +10=P2_pts
BLOCK_STARTS = [1, 15, 29]


# ── Helpers ───────────────────────────────────────────────────────────────────

def build_name_map():
    """player_name → player_number from Schedule tab (rows 15-29 = players 1-15)."""
    wb = openpyxl.load_workbook(LEAGUE, data_only=True, read_only=True)
    ws = wb['Schedule']
    name_to_num = {}
    for player_num, row in enumerate(
        ws.iter_rows(min_row=15, max_row=29, values_only=True), start=1
    ):
        name = row[2]   # col C
        if name is not None:
            name_to_num[str(name).strip()] = player_num
    wb.close()
    return name_to_num


def detect_round(tab_name, player_nums):
    """
    1. Parse round number from tab name: "R3 Scores" / "Round 3" / "R3" / "Week 3" → 3.
    2. Fallback: first round where any of the given players has no data in Scores 2026.
    """
    m = re.search(r'(?:round|week|r)\s*(\d+)', tab_name, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r'\b(\d+)\b', tab_name)
    if m:
        return int(m.group(1))

    # Infer from Scores 2026
    wb = openpyxl.load_workbook(LEAGUE, data_only=True, read_only=True)
    ws = wb['Scores 2026']
    result = None
    for r in range(1, TOTAL_ROUNDS + 1):
        col = round_col(r)
        for num in player_nums:
            mp_row, _ = PLAYER_ROWS[num]
            if ws.cell(row=mp_row, column=col).value is None:
                result = r
                break
        if result:
            break
    wb.close()

    if result:
        return result
    raise ValueError(
        f"Cannot determine round for tab {tab_name!r} — all rounds appear complete."
    )


def parse_scores(ws):
    """
    Parse a Calculator-format worksheet.
    Returns dict: player_name → {'match_pts': float, 'net': int}

    Each matchup block layout (0-indexed offsets from block start):
      +0 = player name       +1 = 'Holes Won'
      +6 = NET score         +8 = P1 total pts   +10 = P2 total pts (on P1 row only)
    """
    results    = {}
    pending_p2 = {}   # block_start → p2_pts stashed from P1 row

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
                results[name] = {'match_pts': p1_pts, 'net': net}
                pending_p2[bs] = p2_pts
            elif bs in pending_p2 and pending_p2[bs] is not None:
                results[name] = {'match_pts': pending_p2[bs], 'net': net}
                del pending_p2[bs]

    return results


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
                # Calculator format carries p2's total pts on the P1 row (+10); P2 row has None at +8/+10.
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


def parse_scorecards(ws):
    """
    Parse hole-by-hole scorecard data from a Calculator-format worksheet.
    Returns dict: player_name → {course, nine, par, parTotal, gross, grossTotal, net, netTotal}

    Detects scorecard blocks by rows where row[bs+1] == 'Handicap:' (bs ∈ BLOCK_STARTS).
    Row offsets from Handicap row: +2=PAR, +4=GROSS, +6=NET.
    Hole values occupy cols bs+1 through bs+9; total at bs+10.
    """
    scorecards = {}
    rows = [list(r) for r in ws.iter_rows(values_only=True)]

    def safe_get(row, cols):
        return [row[c] if c < len(row) else None for c in cols]

    def total_at(row, col):
        return row[col] if col < len(row) else None

    for i, row in enumerate(rows):
        for bs in BLOCK_STARTS:
            if len(row) <= bs + 8:
                continue
            if row[bs + 1] != 'Handicap:':
                continue
            name = row[bs]
            if not isinstance(name, str) or not name.strip():
                continue
            name = name.strip()
            nine = row[bs + 8] if len(row) > bs + 8 else None

            # Find course name by searching backward for block header row ('First 3' at bs+2)
            course = None
            for j in range(i - 1, max(i - 25, -1), -1):
                pr = rows[j]
                if len(pr) > bs + 2 and pr[bs + 2] == 'First 3':
                    course = pr[bs] if len(pr) > bs else None
                    break

            if i + 6 >= len(rows):
                continue

            hole_cols = list(range(bs + 1, bs + 10))   # 9 values: bs+1 .. bs+9
            tot_col   = bs + 10

            par_row   = rows[i + 2]
            gross_row = rows[i + 4]
            net_row   = rows[i + 6]

            scorecards[name] = {
                'course':     course,
                'nine':       nine,
                'handicap':   row[bs + 2] if len(row) > bs + 2 else None,
                'par':        safe_get(par_row,   hole_cols),
                'parTotal':   total_at(par_row,   tot_col),
                'gross':      safe_get(gross_row, hole_cols),
                'grossTotal': total_at(gross_row, tot_col),
                'net':        safe_get(net_row,   hole_cols),
                'netTotal':   total_at(net_row,   tot_col),
            }

    return scorecards


def write_dashboard_json(rnd, name_to_num):
    """Write Dashboard/data.json from current workbook state + Scores.xlsx match tabs."""
    num_to_name = {v: k for k, v in name_to_num.items()}

    # Read all player stats from Scores 2026 and handicaps from Schedule
    wb_main   = openpyxl.load_workbook(LEAGUE, data_only=True, read_only=True)
    ws_scores = wb_main['Scores 2026']
    handicaps = {}
    for player_num, row in enumerate(
        wb_main['Schedule'].iter_rows(min_row=15, max_row=29, values_only=True), start=1
    ):
        handicaps[player_num] = row[3]   # col D

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
            'id':        num,
            'name':      name,
            'handicap':  handicaps.get(num),
            'totalPts':  total_pts,
            'record':    record,
            'avgNet':    avg_net,
            'rounds':    rounds_data,
        })

    wb_main.close()

    # Read match pairings from each score tab; fill in opponents
    wb_src     = openpyxl.load_workbook(SCORES_XLSX, data_only=True)   # not read_only: both parse fns need to iterate
    rounds_out = []

    for r in range(1, TOTAL_ROUNDS + 1):
        tab        = f'R{r} Scores'
        sched      = SCHEDULE[r - 1]
        matches    = []
        scorecards = {}
        expected   = ROUND_MATCH_COUNTS[r]

        if tab in wb_src.sheetnames:
            ws_tab     = wb_src[tab]
            scorecards = parse_scorecards(ws_tab)
            for m in parse_matches(ws_tab):
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
        status = round_status(sched['dates'], n, expected)

        # Build full pairings list (played + unplayed) from the known schedule
        pairings = []
        for p1_num, p2_num in ROUND_PAIRINGS.get(r, []):
            p1_name = num_to_name.get(p1_num, f'Player {p1_num}')
            p2_name = num_to_name.get(p2_num, f'Player {p2_num}')
            played = next(
                (m for m in matches
                 if (m['p1'] == p1_name and m['p2'] == p2_name) or
                    (m['p1'] == p2_name and m['p2'] == p1_name)),
                None
            )
            if played:
                entry = {**played, 'played': True}
                sc1 = scorecards.get(played['p1'])
                sc2 = scorecards.get(played['p2'])
                if sc1: entry['p1Scorecard'] = sc1
                if sc2: entry['p2Scorecard'] = sc2
                pairings.append(entry)
            else:
                pairings.append({
                    'p1': p1_name, 'p1Pts': None, 'p1Net': None,
                    'p2': p2_name, 'p2Pts': None, 'p2Net': None,
                    'winner': None, 'played': False,
                })

        rounds_out.append({
            'round':    r,
            'dates':    sched['dates'],
            'bye':      sched['bye'],
            'status':   status,
            'matches':  matches,
            'pairings': pairings,
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

    os.makedirs(os.path.dirname(DASHBOARD_JSON), exist_ok=True)
    with open(DASHBOARD_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Dashboard JSON: {DASHBOARD_JSON}")


def parse_round_dates(dates_str):
    """Return (start_date, end_date) from a string like 'Apr 20 – May 1'."""
    parts = re.split(r'\s*[–—-]\s*', dates_str.strip())
    start = _datetime.strptime(parts[0].strip() + ' 2026', '%b %d %Y').date()
    end   = _datetime.strptime(parts[1].strip() + ' 2026', '%b %d %Y').date()
    return start, end


def round_status(dates_str, match_count, expected):
    """Determine round status using calendar dates, not just match count."""
    today         = _date.today()
    start, end    = parse_round_dates(dates_str)
    if today > end:
        return 'complete'
    if today >= start:
        return 'in_progress'
    return 'upcoming'


def outcome(pts):
    if pts is None: return None
    if pts >= 4.5:  return 'W'
    if pts >= 4.0:  return 'D'
    return 'L'


def compute_stats(ws_scores, player_num):
    """Recompute total, W-L-D record, and avg NET by reading all round columns."""
    mp_row, net_row = PLAYER_ROWS[player_num]
    wins = losses = draws = 0
    total_pts  = 0
    net_scores = []

    for r in range(1, TOTAL_ROUNDS + 1):
        col     = round_col(r)
        pts     = ws_scores.cell(row=mp_row,  column=col).value
        net_val = ws_scores.cell(row=net_row, column=col).value

        if pts is not None:
            o = outcome(pts)
            if   o == 'W': wins   += 1
            elif o == 'L': losses += 1
            elif o == 'D': draws  += 1
            total_pts += pts

        if isinstance(net_val, (int, float)):
            net_scores.append(net_val)

    total_pts = int(total_pts) if total_pts == int(total_pts) else total_pts
    record    = f"{wins}-{losses}-{draws}"
    avg       = round(sum(net_scores) / len(net_scores), 1) if net_scores else None
    return total_pts, record, avg


# ── Main ─────────────────────────────────────────────────────────────────────

def process(source_path, tab_name):
    # Read score data from source file with data_only so formula results are visible
    wb_src = openpyxl.load_workbook(source_path, data_only=True)
    scores = parse_scores(wb_src[tab_name])
    wb_src.close()

    if not scores:
        print(f"  No score data found in {tab_name!r} — nothing to update.")
        return []

    name_to_num = build_name_map()
    player_nums = [name_to_num[n] for n in scores if n in name_to_num]
    rnd         = detect_round(tab_name, player_nums)
    col         = round_col(rnd)
    print(f"Round {rnd}  →  column {chr(64 + col)}  (tab: {tab_name!r})")

    # Open main workbook for writing (no data_only keeps existing formulas intact)
    wb = openpyxl.load_workbook(LEAGUE)
    ws = wb['Scores 2026']
    ws.protection.sheet = False   # unprotect before writing

    updated = []
    skipped = []
    for name, data in scores.items():
        num = name_to_num.get(name)
        if num is None:
            skipped.append(f"  SKIP (not on roster): {name!r}")
            continue

        mp_row, net_row = PLAYER_ROWS[num]
        match_pts = data['match_pts']
        net_score = data['net']

        ws.cell(row=mp_row,  column=col).value = match_pts
        ws.cell(row=net_row, column=col).value = net_score

        total, record, avg = compute_stats(ws, num)
        ws.cell(row=mp_row, column=COL_TOTAL).value = total
        ws.cell(row=mp_row, column=COL_REC  ).value = record
        ws.cell(row=mp_row, column=COL_AVG  ).value = avg if avg is not None else 'N/A'

        line = f"  #{num:>2} {name:<18}  {match_pts} pts  NET {net_score}  {record}"
        updated.append(line)
        print(line)

    for s in skipped:
        print(s)

    try:
        ws.protection.sheet = True        # re-protect before saving
        ws.protection.password = SHEET_PASSWORD
        wb.save(LEAGUE)
        wb.close()
        print(f"\nSaved: {LEAGUE}")
    except PermissionError:
        wb.close()
        print(f"\nERROR: Could not save — close the file in Excel and re-run.")
        return []

    write_dashboard_json(rnd, name_to_num)
    return updated


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: py -3 process_scores.py <source_xlsx> <tab_name>")
        sys.exit(1)
    process(sys.argv[1], sys.argv[2])
