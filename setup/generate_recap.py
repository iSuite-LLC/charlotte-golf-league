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
        "bye_players": ["Alex Palmer", "Curtis Lynn", "Ben Linck"]},
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
    ("Ben Linck",       19, 20),
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


# ── Harsh comedy banks (savage tone — second draft generated every round) ─────
HARSH_OPENINGS = [
    "Round {r} is in the books, and the books should probably be burned. What happened "
    "out there wasn't golf — it was a hostage situation, and par was the hostage.",
    "Round {r} is over, and the scorecards read like a series of cries for help. "
    "Let's relive the carnage together.",
    "Welcome to the Round {r} recap, where dreams came to die and handicaps showed up "
    "purely to make excuses. Buckle up.",
    "Round {r} is done. A few of you played golf. The rest committed a string of "
    "unforced crimes against the sport. Let's name names.",
    "The Round {r} results are in, and frankly, several of you owe the game of golf "
    "a written apology.",
    "Round {r}: where 'fore' wasn't a warning — it was an average. Let's break down "
    "the wreckage.",
    "Grab a seat. Round {r} produced numbers so ugly they should be redacted for the "
    "children. Here we go.",
    "Round {r} has concluded and the course is pressing charges. Settle in for the "
    "damage report.",
]

HARSH_BEST_QUIPS = [
    "{first} was the lone competent human on the course this week. Everyone else appeared "
    "to be playing a different, worse sport with the same equipment. Congratulations on "
    "clearing a bar that is currently underground.",
    "{first} actually played golf this round, which — judging by everyone else — now "
    "qualifies as a rare and exotic talent. Soak it in. It won't last.",
    "{first} ran away with it while the rest of the field busied themselves losing balls "
    "and what was left of their dignity. Briefly, we salute you.",
    "{first} posted a round so good it's borderline suspicious. Either they practiced or "
    "they cheated. We've chosen to be impressed. For now.",
    "{first} single-handedly kept this league from being a total embarrassment this week. "
    "The other fourteen of you should send a thank-you note.",
    "{first} played like the trophy already has their name on it. The rest of you played "
    "like you were drafting your own apology tour.",
    "{first} embarrassed the entire field and didn't even have the decency to make it "
    "close. Beautiful work. Genuinely rude. We love it.",
    "{first} was the only person out there who looked like they'd held a club before "
    "today. Frankly, it was jarring to witness.",
]

HARSH_WORST_QUIPS = [
    "{first} didn't play a round of golf so much as assault a golf course and flee the "
    "scene. No points. No defense. The scorecard has been forwarded to the proper "
    "authorities and a grief counselor.",
    "{first} turned in a scorecard that belongs in a true-crime documentary. Genuinely "
    "heinous work out there. The course did not deserve this.",
    "{first} set a brand-new league standard this week — for what NOT to do. The bar is "
    "now somewhere in the parking lot.",
    "{first} gave us a round so bad it loops back around to performance art. Avant-garde. "
    "Unwatchable. Unforgettable.",
    "{first} proved, beyond reasonable doubt, that golf is a sport you can be actively, "
    "aggressively bad at. A lesson for us all.",
    "{first} spent the afternoon redecorating the rough and donating golf balls to the "
    "local wildlife. Generous. Catastrophic. But generous.",
    "{first} should seriously consider a restraining order between themselves and any "
    "golf course — for everyone's safety, including the course's.",
    "{first} had the kind of round where even the scorekeeper winced. We're not angry. "
    "We're just deeply, profoundly disappointed.",
]

HARSH_MISSING_QUIPS = [
    "Still no scores. We're not sure whether you're hiding from the league or from "
    "yourself. Either way — the numbers. Send them. Now.",
    "Scores still not submitted. Too ashamed or too lazy — at this point we'd respect "
    "either, if you'd just send them in.",
    "No scores turned in. The deadline was Friday. Time, like your golf game, has gotten "
    "completely away from you.",
    "Still missing. Hiding the evidence doesn't make the round un-happen. We know you "
    "played. Submit.",
]

HARSH_CLOSINGS = [
    "Round {nr} is live. Statistically, most of you will not improve. But the deadline "
    "is Friday {end}, so at the very least be punctual about your mediocrity.",
    "Round {nr} is open. Top spot is up for grabs, assuming any of you can locate a "
    "fairway. Scores due {end}.",
    "Onto Round {nr}. Try to make it competitive — or at least make it funny. Deadline "
    "{end}. We've heard every excuse, so don't bother.",
    "Round {nr} awaits. Redemption is technically possible, if mathematically unlikely "
    "for most of you. Submit by {end}.",
    "Go get 'em in Round {nr}. The leaderboard is hungry and several of you are looking "
    "like easy meals. Scores in by {end}.",
]

# ── Tone registry: each generated round writes one draft per tone ─────────────
TONE_BANKS = {
    "friendly": {
        "openings": OPENINGS,
        "best":     BEST_QUIPS,
        "worst":    WORST_QUIPS,
        "missing":  MISSING_QUIPS,
        "closings": CLOSINGS,
        "all_submitted": (
            "None &mdash; everyone submitted their scores. This is historic. "
            "Frame this email. Put it in the trophy case."
        ),
    },
    "harsh": {
        "openings": HARSH_OPENINGS,
        "best":     HARSH_BEST_QUIPS,
        "worst":    HARSH_WORST_QUIPS,
        "missing":  HARSH_MISSING_QUIPS,
        "closings": HARSH_CLOSINGS,
        "all_submitted": (
            "Nobody, somehow &mdash; every last score came in on time. Mark the "
            "calendar; it's the one thing this group got right all round."
        ),
    },
}


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
        avg   = ws.cell(row=mp_row,  column=COL_AVG).value
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


def _h(text):
    """Minimal HTML-escape for cell content."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _sec(icon, label):
    """Red section header bar."""
    return (
        f'<div style="background:#cc2027;color:#fff;padding:9px 14px;'
        f'font-family:Arial,sans-serif;font-size:14px;font-weight:bold;'
        f'margin-top:22px;">{icon}&nbsp;&nbsp;{_h(label)}</div>'
    )


def generate_email(round_num, today=None, tone="friendly"):
    if today is None:
        today = datetime.date.today()

    r_info   = ROUNDS[round_num]
    bye_set  = set(r_info["bye_players"])
    has_next = (round_num + 1) in ROUNDS
    banks    = TONE_BANKS[tone]
    rng      = random.Random(round_num * 13337 + sum(ord(c) for c in tone))

    data = load_data(round_num)

    played  = [p for p in data if p["round_mp"] is not None and p["name"] not in bye_set]
    missing = [p for p in data if p["round_mp"] is None and p["name"] not in bye_set]

    best  = max(played, key=lambda x: x["round_mp"]) if played else None
    worst = min(played, key=lambda x: x["round_mp"]) if played else None
    if best and worst and best["name"] == worst["name"]:
        worst = None

    standings = sorted(data, key=lambda x: (-x["total"], x["name"]))

    subject = (
        f"&#127949;&#65039; IMI Golf League — Round {round_num} Recap | "
        f"{fmt_date(r_info['start'])} – {fmt_date(r_info['end'])}"
    )

    BASE = "font-family:Arial,sans-serif;font-size:14px;color:#222;"
    TD   = "padding:7px 10px;border-bottom:1px solid #e0e0e0;"
    TH   = "padding:7px 10px;border-bottom:2px solid #cc2027;text-align:{a};font-weight:bold;background:#f5f5f5;"

    H = []  # html lines

    H.append("<!DOCTYPE html>")
    H.append('<html><head><meta charset="utf-8"></head>')
    H.append(f'<body style="{BASE}margin:0;padding:0;">')
    H.append(f'<div style="max-width:600px;margin:0 auto;padding:0 8px;">')

    # ── Instructions block (not part of email body) ───────────────────────────
    H.append(
        '<div style="background:#fff8dc;border:1px solid #e6c700;padding:10px 14px;'
        'margin-bottom:16px;font-size:12px;color:#555;">'
        '<strong>HOW TO SEND:</strong> Open this file in your browser &rarr; '
        'select everything <em>below this box</em> &rarr; Ctrl+C &rarr; paste into Outlook.<br>'
        f'<strong>SUBJECT:</strong> {subject}'
        '</div>'
    )

    # ── Header banner ─────────────────────────────────────────────────────────
    H.append(
        '<div style="background:#cc2027;color:#fff;padding:18px 20px;text-align:center;">'
        f'<div style="font-size:20px;font-weight:bold;">&#127949;&#65039;&nbsp;'
        f'IMI GOLF LEAGUE &mdash; ROUND {round_num} RECAP</div>'
        f'<div style="font-size:13px;margin-top:5px;opacity:0.9;">'
        f'{fmt_date(r_info["start"])} &ndash; {fmt_date(r_info["end"])}'
        f'&nbsp;&nbsp;|&nbsp;&nbsp;Round {round_num} of 9</div>'
        '</div>'
    )

    # ── Opening ───────────────────────────────────────────────────────────────
    opening = rng.choice(banks["openings"]).format(r=round_num)
    H.append(f'<p style="margin:16px 0 0;">{_h(opening)}</p>')

    # ── Standings ─────────────────────────────────────────────────────────────
    H.append(_sec("📊", f"OVERALL STANDINGS  (After Round {round_num} of 9)"))
    H.append('<table style="width:100%;border-collapse:collapse;margin-top:0;">')
    H.append(
        f'<tr>'
        f'<th style="{TH.format(a="center")}">#</th>'
        f'<th style="{TH.format(a="left")}">Player</th>'
        f'<th style="{TH.format(a="center")}">Total Pts</th>'
        f'<th style="{TH.format(a="center")}">Record</th>'
        f'<th style="{TH.format(a="center")}">Avg NET</th>'
        f'</tr>'
    )
    for i, p in enumerate(standings, 1):
        pts_str = f"{p['total']:.1f}" if p["total"] != int(p["total"]) else str(int(p["total"]))
        avg_str = f"{p['avg_net']:.1f}" if p["avg_net"] is not None else "&mdash;"
        bg = "background:#fafafa;" if i % 2 == 0 else ""
        H.append(
            f'<tr style="{bg}">'
            f'<td style="{TD}text-align:center;">{i}</td>'
            f'<td style="{TD}">{_h(p["name"])}</td>'
            f'<td style="{TD}text-align:center;font-weight:bold;">{pts_str}</td>'
            f'<td style="{TD}text-align:center;">{_h(p["record"])}</td>'
            f'<td style="{TD}text-align:center;">{avg_str}</td>'
            f'</tr>'
        )
    H.append('</table>')

    # ── Round scores ──────────────────────────────────────────────────────────
    H.append(_sec("⛳", f"ROUND {round_num} SCORES"))
    H.append('<table style="width:100%;border-collapse:collapse;margin-top:0;">')
    H.append(
        f'<tr>'
        f'<th style="{TH.format(a="left")}">Player</th>'
        f'<th style="{TH.format(a="center")}">Match Pts</th>'
        f'<th style="{TH.format(a="center")}">Net Score</th>'
        f'</tr>'
    )

    def sort_key(p):
        if p["name"] in bye_set:  return (-0.5, p["name"])
        if p["round_mp"] is None: return (-0.1, p["name"])
        return (-p["round_mp"], p["name"])

    for i, p in enumerate(sorted(data, key=sort_key), 1):
        if p["name"] in bye_set:
            mp_str  = '<em style="color:#888;">BYE</em>'
            net_str = '<em style="color:#888;">BYE</em>'
        elif p["round_mp"] is None:
            mp_str  = '<span style="color:#cc2027;font-weight:bold;">MISSING</span>'
            net_str = '<span style="color:#cc2027;font-weight:bold;">MISSING</span>'
        else:
            mp_str  = f"{p['round_mp']:.1f}"
            net_str = str(int(p["round_net"])) if p["round_net"] is not None else "&mdash;"
        bg = "background:#fafafa;" if i % 2 == 0 else ""
        H.append(
            f'<tr style="{bg}">'
            f'<td style="{TD}">{_h(p["name"])}</td>'
            f'<td style="{TD}text-align:center;font-weight:bold;">{mp_str}</td>'
            f'<td style="{TD}text-align:center;">{net_str}</td>'
            f'</tr>'
        )
    H.append('</table>')

    # ── MVP ───────────────────────────────────────────────────────────────────
    if best:
        H.append(_sec("🏆", f"ROUND {round_num} MVP — {best['name'].upper()}  ({best['round_mp']:.1f} pts)"))
        quip = rng.choice(banks["best"]).format(first=best["first"])
        H.append(f'<p style="margin:10px 0 0;">{_h(quip)}</p>')

    # ── Participation award ───────────────────────────────────────────────────
    if worst:
        H.append(_sec("🪣", f"ROUND {round_num} PARTICIPATION AWARD — {worst['name'].upper()}  ({worst['round_mp']:.1f} pts)"))
        quip = rng.choice(banks["worst"]).format(first=worst["first"])
        H.append(f'<p style="margin:10px 0 0;">{_h(quip)}</p>')

    # ── Missing scores ────────────────────────────────────────────────────────
    H.append(_sec("⚠️", "MISSING SCORES"))
    if missing:
        names_html = "".join(f'<li>{_h(p["name"])}</li>' for p in missing)
        quip = rng.choice(banks["missing"])
        H.append(f'<ul style="margin:8px 0 4px 20px;">{names_html}</ul>')
        H.append(f'<p style="margin:6px 0 0;">{_h(quip)}</p>')
    else:
        H.append(f'<p style="margin:10px 0 0;">{banks["all_submitted"]}</p>')

    # ── BYE notice ────────────────────────────────────────────────────────────
    bye_label = " &amp; ".join(_h(b) for b in r_info["bye_players"])
    H.append(
        f'<p style="margin:18px 0 0;padding:8px 12px;background:#f5f5f5;'
        f'border-left:4px solid #cc2027;">'
        f'<strong>BYE this round:</strong> {bye_label}</p>'
    )

    # ── Next round / closing ──────────────────────────────────────────────────
    if has_next:
        nr     = round_num + 1
        nr_inf = ROUNDS[nr]
        nr_bye = " &amp; ".join(_h(b) for b in nr_inf["bye_players"])
        H.append(_sec("📅", f"UP NEXT: ROUND {nr}  ({fmt_date(nr_inf['start'])} – {fmt_date(nr_inf['end'])})"))
        closing = rng.choice(banks["closings"]).format(nr=nr, end=fmt_date(nr_inf["end"]))
        H.append(
            f'<p style="margin:10px 0 0;">{_h(closing)}</p>'
            f'<p style="margin:6px 0 0;"><strong>BYE:</strong> {nr_bye}</p>'
        )
    else:
        H.append(_sec("🏁", "THAT'S A WRAP ON THE 2026 SEASON!"))
        H.append(
            '<p style="margin:10px 0 0;">Season final standings are above. '
            'Trophy ceremony details to follow. Someone is about to be very proud &mdash; '
            'and someone else is going to pretend they\'re fine with where they finished. '
            'We see you. Great season, everyone.</p>'
        )

    H.append('<p style="margin:22px 0 16px;color:#555;">&mdash; Your League Manager</p>')
    H.append('</div></body></html>')

    return "\n".join(H)


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

    for tone, tag in (("friendly", ""), ("harsh", "HARSH_")):
        text     = generate_email(round_num, today, tone)
        filename = f"Round_{round_num:02d}_Recap_{tag}Draft_{today.isoformat()}.htm"
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"Saved ({tone}): {filepath}")


if __name__ == "__main__":
    main()
