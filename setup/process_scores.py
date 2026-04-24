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

import sys, os, re, io, openpyxl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

LEAGUE         = r"C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\2026 IMI Golf League.xlsx"
SHEET_PASSWORD = "steelers"
TOTAL_ROUNDS   = 9    # rounds 1-9 → columns D-L (4-12)

COL_TOTAL = 13      # M  League Total Score
COL_REC   = 14      # N  Match Record
COL_AVG   = 15      # O  Average NET Score

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
BLOCK_STARTS = [1, 14, 27]


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

    return updated


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: py -3 process_scores.py <source_xlsx> <tab_name>")
        sys.exit(1)
    process(sys.argv[1], sys.argv[2])
