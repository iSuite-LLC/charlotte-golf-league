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
