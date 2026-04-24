"""
generate_recap.py  —  IMI Golf League 2026
Generates a Round Recap email draft and saves it to Golf League/Recap Emails/.

Usage:
  python generate_recap.py           # auto-detects today's recap round
  python generate_recap.py <round>   # force a specific round (e.g. python generate_recap.py 1)

Runs every Monday via Task Scheduler; only generates a file on scheduled recap dates
(or when a round number is passed manually).
"""

import sys, io, os, re, datetime, random, openpyxl

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Paths ──────────────────────────────────────────────────────────────────────
LEAGUE     = r"C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\2026 IMI Golf League.xlsx"
OUTPUT_DIR = r"C:\Users\ehigh\OneDrive - IMI Companies\Documents\Golf League\Recap Emails"

# ── Round schedule ─────────────────────────────────────────────────────────────
ROUNDS = {
    1: {"start": datetime.date(2026, 4, 20), "end": datetime.date(2026, 5,  1),
        "bye_players": ["David Maddox"]},
    2: {"start": datetime.date(2026, 5,  4), "end": datetime.date(2026, 5, 15),
        "bye_players": ["Nick Coglianese"]},
    3: {"start": datetime.date(2026, 5, 18), "end": datetime.date(2026, 5, 29),
        "bye_players": ["Charlotte Hayes"]},
    4: {"start": datetime.date(2026, 6,  1), "end": datetime.date(2026, 6, 12),
        "bye_players": ["Jerome Martin"]},
    5: {"start": datetime.date(2026, 6, 15), "end": datetime.date(2026, 6, 26),
        "bye_players": ["Brian Wojcio", "Ethan High", "Rob Bass"]},
    6: {"start": datetime.date(2026, 6, 29), "end": datetime.date(2026, 7, 10),
        "bye_players": ["Carson Bass", "Michael McHugh", "Bruce Atkins"]},
    7: {"start": datetime.date(2026, 7, 13), "end": datetime.date(2026, 7, 24),
        "bye_players": ["Alex Palmer", "Curtis Lynn", "Ben Link"]},
    8: {"start": datetime.date(2026, 7, 27), "end": datetime.date(2026, 8,  7),
        "bye_players": ["Kaylan Adams"]},
    9: {"start": datetime.date(2026, 8, 10), "end": datetime.date(2026, 8, 21),
        "bye_players": ["Megan Serian"]},
}

# First Monday of each new round → round that JUST ended
RECAP_DATES = {
    datetime.date(2026, 5,  4): 1,
    datetime.date(2026, 5, 18): 2,
    datetime.date(2026, 6,  1): 3,
    datetime.date(2026, 6, 15): 4,
    datetime.date(2026, 6, 29): 5,
    datetime.date(2026, 7, 13): 6,
    datetime.date(2026, 7, 27): 7,
    datetime.date(2026, 8, 10): 8,
    datetime.date(2026, 8, 24): 9,   # season finale recap
}

# ── Roster: name → (match_pts_row, net_score_row) in Scores 2026 ──────────────
ROSTER = [
    ("Brian Wojcio",     3,  4),
    ("Ethan High",       5,  6),
    ("Rob Bass",         7,  8),
    ("Carson Bass",      9, 10),
    ("Michael McHugh",  11, 12),
    ("Bruce Atkins",    13, 14),
    ("Alex Palmer",     15, 16),
    ("Curtis Lynn",     17, 18),
    ("Ben Link",        19, 20),
    ("Charlotte Hayes", 21, 22),
    ("David Maddox",    23, 24),
    ("Jerome Martin",   25, 26),
    ("Kaylan Adams",    27, 28),
    ("Megan Serian",    29, 30),
    ("Nick Coglianese", 31, 32),
]

def round_col(r):
    return 3 + r   # R1=col4(D), R2=col5(E), ... R9=col12(L)

COL_TOTAL = 13   # M  — cumulative match points
COL_REC   = 14   # N  — W-L-D record
COL_AVG   = 15   # O  — avg NET score


# ── Comedy banks (seeded per round so each email has consistent personality) ──
OPENINGS = [
    "Another round in the books. Whether you played like a champion or like someone who "
    "borrowed clubs from a museum, your results have been immortalized below.",
    "Round {r} is officially done. The course survived. You survived. Mostly.",
    "Welcome back. Round {r} wrapped up Friday, and the numbers don't lie — though some "
    "of you may wish they did.",
    "The results are in. The excuses have already started. Let's get into it.",
    "Golf was played. Points were scored. Feelings may or may not have been hurt. Here's "
    "your Round {r} recap.",
    "Another Friday, another round complete. Time to see who's climbing and who's "
    "starring in their own cautionary tale.",
    "Round {r} done. Fairways were hit (some of them), putts were made (a few), and "
    "scores were submitted (eventually). Let's break it down.",
    "The leaderboard has been updated. Some of you will be pleased. Others will be "
    "revisiting your life choices. Either way — here we go.",
]

BEST_QUIPS = [
    "{first} was absolutely locked in. We're not saying they practiced, but we're "
    "not NOT saying it either. Well played.",
    "{first} carried the league's dignity this round. We didn't deserve it. "
    "Buy them a drink.",
    "{first} played a round so clean it made the rest of us look like we've never "
    "held a golf club. Respect.",
    "{first} was out here playing like the trophy already has their name on it. "
    "Confidence is a lifestyle.",
    "{first} went full business mode this week. Whatever they ate for breakfast — "
    "share the recipe.",
    "{first} showed up and showed out. Suspicious? A little. Impressive? Absolutely.",
    "{first} had a masterclass round. The course didn't stand a chance.",
    "{first} is single-handedly keeping this league's collective reputation intact. "
    "We appreciate the service.",
]

WORST_QUIPS = [
    "{first} had a rough one. The course won this week. It happens to the best of us. "
    "It just happened to {first} a little harder.",
    "{first} played like they had somewhere more important to be. Spoiler: they didn't.",
    "{first} left everything on the course — unfortunately 'everything' included their "
    "best golf.",
    "{first} offered the league a masterclass in what NOT to do. The bar has been set. "
    "Underground.",
    "{first} had the kind of round where the scorecard starts to feel personal. "
    "We're here for you, {first}.",
    "{first} played like the clubs were borrowed from a lost-and-found bin at a mini-golf "
    "course. We've seen smoother swings.",
    "{first} is featured this week in our ongoing 'it happens to everyone' segment. "
    "It really does. This was just extra.",
    "{first} gave 100 percent out there. Unfortunately golf sometimes requires 110.",
]

MISSING_QUIPS = [
    "Scores still pending. We believe in you. The deadline was Friday.",
    "Not yet submitted. You played. We know you played. The people need numbers.",
    "Ghost mode activated. Come back. We miss your points (and your presence).",
    "Still waiting. The suspense is fun for no one. Okay, it's a little fun. Submit your scores.",
]

CLOSINGS = [
    "Round {nr} is live — tee it up, keep score, and get those numbers in by "
    "Friday {end}. The leaderboard won't sort itself.",
    "Round {nr} is underway. May your drives be long, your putts drop, and your "
    "excuse game be strong (but hopefully unnecessary). Deadline: Friday {end}.",
    "Get after it in Round {nr}. Top spot is there for the taking. "
    "Submit scores by {end}.",
    "Round {nr} waits for no one. Make something happen out there — and "
    "submit by {end} so this doesn't become a thing.",
    "Let's go, Round {nr}! The only thing worse than a bad round is not submitting "
    "the scores. We're watching. Deadline: {end}.",
]


# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt_date(d):
    """Format date as 'May 1' — Windows-compatible (no %-d)."""
    return d.strftime("%b ") + str(d.day)


def load_data(round_num):
    """Read all player data from Scores 2026 for the given round."""
    try:
        wb = openpyxl.load_workbook(LEAGUE, data_only=True, read_only=True)
    except PermissionError:
        print("ERROR: Could not open Excel file — close it in Excel and re-run.")
        sys.exit(1)

    ws  = wb["Scores 2026"]
    col = round_col(round_num)
    data = []
    for name, mp_row, net_row in ROSTER:
        mp    = ws.cell(row=mp_row,  column=col).value
        net   = ws.cell(row=net_row, column=col).value
        total = ws.cell(row=mp_row,  column=COL_TOTAL).value
        rec   = ws.cell(row=mp_row,  column=COL_REC).value
        avg   = ws.cell(row=net_row, column=COL_AVG).value
        data.append({
            "name":      name,
            "first":     name.split()[0],
            "round_mp":  float(mp)    if mp    is not None else None,
            "round_net": float(net)   if net   is not None else None,
            "total":     float(total) if total is not None else 0.0,
            "record":    str(rec)     if rec   is not None else "0-0-0",
            "avg_net":   float(avg)   if isinstance(avg, (int, float)) else None,
        })
    wb.close()
    return data


def generate_email(round_num, today=None):
    if today is None:
        today = datetime.date.today()

    r_info     = ROUNDS[round_num]
    bye_set    = set(r_info["bye_players"])
    has_next   = (round_num + 1) in ROUNDS
    rng        = random.Random(round_num * 13337)   # deterministic per round

    data = load_data(round_num)

    # Classify players
    played        = [p for p in data if p["round_mp"] is not None and p["name"] not in bye_set]
    bye_players   = [p for p in data if p["name"] in bye_set]
    missing       = [p for p in data if p["round_mp"] is None and p["name"] not in bye_set]

    # Best / worst this round
    best  = max(played, key=lambda x: x["round_mp"]) if played else None
    worst = min(played, key=lambda x: x["round_mp"]) if played else None
    if best and worst and best["name"] == worst["name"]:
        worst = None   # only one player with scores

    # Standings: sort by total desc, then name asc
    standings = sorted(data, key=lambda x: (-x["total"], x["name"]))

    # ── Build email text ───────────────────────────────────────────────────────
    W   = 58
    SEP = "━" * W
    sep = "─" * W
    out = []

    # Subject line (top of file for easy copy)
    out.append(
        f"SUBJECT: 🏌️ IMI Golf League — Round {round_num} Recap | "
        f"{fmt_date(r_info['start'])} – {fmt_date(r_info['end'])}"
    )
    out.append("")

    # Header banner
    out.append(SEP)
    title = f"  🏌️  IMI GOLF LEAGUE — ROUND {round_num} RECAP"
    sub   = f"  {fmt_date(r_info['start'])} – {fmt_date(r_info['end'])}  |  Round {round_num} of 9"
    out.append(title)
    out.append(sub)
    out.append(SEP)
    out.append("")

    # Opening
    opening = rng.choice(OPENINGS).format(r=round_num)
    out.append(opening)
    out.append("")

    # ── Standings ──────────────────────────────────────────────────────────────
    out.append(SEP)
    out.append(f"📊  OVERALL STANDINGS  (After Round {round_num} of 9)")
    out.append(SEP)
    out.append("")
    out.append(f"  {'':>3}  {'Player':<20}  {'Total':>6}  {'Record':<9}  {'Avg NET':>7}")
    out.append(f"  {sep}")
    for i, p in enumerate(standings, 1):
        pts_str = f"{p['total']:.1f}" if p["total"] != int(p["total"]) else f"{int(p['total'])}"
        avg_str = f"{p['avg_net']:.1f}" if p["avg_net"] is not None else "  —  "
        out.append(
            f"  {i:>3}. {p['name']:<20}  {pts_str:>6}  {p['record']:<9}  {avg_str:>7}"
        )
    out.append("")

    # ── Round snapshot ─────────────────────────────────────────────────────────
    out.append(SEP)
    out.append(f"⛳  ROUND {round_num} SCORES")
    out.append(SEP)
    out.append("")
    out.append(f"  {'Player':<20}  {'Match Pts':>10}  {'Net Score':>10}")
    out.append(f"  {sep}")

    # Sort by round_mp desc (BYE at bottom, missing at very bottom)
    def sort_key(p):
        if p["name"] in bye_set:     return (-0.5, p["name"])
        if p["round_mp"] is None:    return (-0.1, p["name"])
        return (-p["round_mp"], p["name"])

    for p in sorted(data, key=sort_key):
        if p["name"] in bye_set:
            mp_str  = "     BYE"
            net_str = "     BYE"
        elif p["round_mp"] is None:
            mp_str  = " MISSING"
            net_str = " MISSING"
        else:
            mp_str  = f"{p['round_mp']:.1f}"
            net_str = f"{int(p['round_net'])}" if p["round_net"] is not None else "  —"
        out.append(f"  {p['name']:<20}  {mp_str:>10}  {net_str:>10}")
    out.append("")

    # ── MVP ────────────────────────────────────────────────────────────────────
    if best:
        out.append(SEP)
        out.append(
            f"🏆  ROUND {round_num} MVP — {best['name'].upper()}   "
            f"({best['round_mp']:.1f} pts)"
        )
        out.append(SEP)
        out.append("")
        quip = rng.choice(BEST_QUIPS).format(first=best["first"])
        out.append(f"  {quip}")
        out.append("")

    # ── Participation award ────────────────────────────────────────────────────
    if worst:
        out.append(SEP)
        out.append(
            f"🪣  ROUND {round_num} PARTICIPATION AWARD — {worst['name'].upper()}   "
            f"({worst['round_mp']:.1f} pts)"
        )
        out.append(SEP)
        out.append("")
        quip = rng.choice(WORST_QUIPS).format(first=worst["first"])
        out.append(f"  {quip}")
        out.append("")

    # ── Missing scores ─────────────────────────────────────────────────────────
    out.append(SEP)
    out.append("⚠️   MISSING SCORES")
    out.append(SEP)
    out.append("")
    if missing:
        for p in missing:
            out.append(f"  • {p['name']}")
        out.append("")
        quip = rng.choice(MISSING_QUIPS)
        out.append(f"  {quip}")
    else:
        out.append("  None — everyone submitted their scores. This is historic.")
        out.append("  Frame this email. Put it in the trophy case.")
    out.append("")

    # ── BYE notice ─────────────────────────────────────────────────────────────
    bye_label = " & ".join(r_info["bye_players"])
    out.append(sep)
    out.append(f"  BYE this round: {bye_label}")
    out.append(sep)
    out.append("")

    # ── Next round / closing ───────────────────────────────────────────────────
    out.append(SEP)
    if has_next:
        nr     = round_num + 1
        nr_inf = ROUNDS[nr]
        nr_bye = " & ".join(nr_inf["bye_players"])
        out.append(
            f"📅  UP NEXT: ROUND {nr}  "
            f"({fmt_date(nr_inf['start'])} – {fmt_date(nr_inf['end'])})"
        )
        out.append(f"    BYE: {nr_bye}")
        out.append(SEP)
        out.append("")
        closing = rng.choice(CLOSINGS).format(
            nr=nr, end=fmt_date(nr_inf["end"])
        )
        out.append(closing)
    else:
        out.append("🏁  THAT'S A WRAP ON THE 2026 SEASON!")
        out.append(SEP)
        out.append("")
        out.append(
            "Season final standings are above. Trophy ceremony details to follow.\n"
            "Someone is about to be very proud — and someone else is going to pretend\n"
            "they're fine with where they finished. We see you. Great season, everyone."
        )
    out.append("")
    out.append("— Your League Manager")
    out.append("")

    return "\n".join(out)


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    today = datetime.date.today()

    # Manual round override
    if len(sys.argv) > 1:
        try:
            round_num = int(sys.argv[1])
        except ValueError:
            print("Usage: python generate_recap.py [round_number]")
            sys.exit(1)
        if round_num not in ROUNDS:
            print(f"Invalid round number {round_num}. Must be 1-9.")
            sys.exit(1)
    else:
        round_num = RECAP_DATES.get(today)
        if round_num is None:
            print(f"Today ({today}) is not a scheduled recap date. Exiting.")
            print("To force a recap, run: python generate_recap.py <round>")
            sys.exit(0)

    print(f"Generating Round {round_num} recap (today: {today})...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    text     = generate_email(round_num, today)
    filename = f"Round_{round_num:02d}_Recap_Draft_{today.isoformat()}.txt"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Saved: {filepath}")


if __name__ == "__main__":
    main()
