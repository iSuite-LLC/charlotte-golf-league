# Bruce Atkins Withdrawal & Pickup Rule — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert Bruce Atkins' incomplete/upcoming match slots to `Bruce Replacement - TBD`, freeze his results, mark him withdrawn on the live site, and document the new pickup/mulligan rule for the league.

**Architecture:** Pure data + presentation change. Edit `Dashboard/data.json` (slot renames, R6 bye, withdrawn flag), make a surgical `Dashboard/index.html` render change (WD badge, grey row, exclude from seed calc), rewrite `Dashboard/standings.md`, and add a league-notice draft. No Python/script changes; the protected master workbook is not touched. Spec: `docs/superpowers/specs/2026-06-11-bruce-withdrawal-replacement-design.md`.

**Tech Stack:** JSON, vanilla-JS HTML dashboard, Markdown. Verification by `python -m json.tool` (JSON validity) + manual browser eyeball.

---

## File Structure

- `Dashboard/data.json` — rename 6 Bruce opponent slots, drop Bruce from R6 bye, add `"withdrawn": true` to Bruce's player object.
- `Dashboard/index.html` — add `.withdrawn` row styling + `.wd-badge`; in `renderStandings()` show WD badge / grey row and compute rank only over active players; in `renderPlayoffs()` exclude withdrawn from the live seed list. Pass active-only list to the podium.
- `Dashboard/standings.md` — full rewrite: Bruce flagged withdrawn (no seed), active players renumbered 1–14, R6 bye fixed, replacement-rule note added.
- `Announcements/Bruce_Withdrawal_2026-06-11.md` — new league-notice draft (standalone, not auto-sent).

---

### Task 1: data.json — slot renames, R6 bye, withdrawn flag

**Files:**
- Modify: `Dashboard/data.json`

- [ ] **Step 1: Add the withdrawn flag to Bruce's player object**

Find Bruce's player entry and insert the flag after his handicap.

Old:
```json
      "name": "Bruce Atkins",
      "handicap": 24,
      "totalPts": 10,
```
New:
```json
      "name": "Bruce Atkins",
      "handicap": 24,
      "withdrawn": true,
      "totalPts": 10,
```

- [ ] **Step 2: Rename the R3 slot (Rob Bass's makeup)**

Old:
```json
          "p1": "Rob Bass",
          "p1Pts": null,
          "p1Net": null,
          "p2": "Bruce Atkins",
          "p2Pts": null,
          "p2Net": null,
          "winner": null,
          "played": false
```
New: same block but `"p2": "Bruce Replacement - TBD",`

- [ ] **Step 3: Rename the R4 slot (Carson Bass)**

Old block (R4 pairings) has `"p1": "Carson Bass", … "p2": "Bruce Atkins", … "played": false`. Change `"p2": "Bruce Atkins",` → `"p2": "Bruce Replacement - TBD",` within that block. Anchor on the Carson Bass / Bruce Atkins pair:
```json
          "p1": "Carson Bass",
          "p1Pts": null,
          "p1Net": null,
          "p2": "Bruce Atkins",
```
New: `"p2": "Bruce Replacement - TBD",`

- [ ] **Step 4: Rename the R5 slot (Alex Palmer) — Bruce is p1 here**

Old:
```json
          "p1": "Bruce Atkins",
          "p1Pts": null,
          "p1Net": null,
          "p2": "Alex Palmer",
```
New: `"p1": "Bruce Replacement - TBD",`

- [ ] **Step 5: Rename the R7 slot (Kaylan Adams) — Bruce is p1 here**

Old:
```json
          "p1": "Bruce Atkins",
          "p1Pts": null,
          "p1Net": null,
          "p2": "Kaylan Adams",
```
New: `"p1": "Bruce Replacement - TBD",`

- [ ] **Step 6: Rename the R8 slot (Brian Wojcio) — Bruce is p2**

Old:
```json
          "p1": "Brian Wojcio",
          "p1Pts": null,
          "p1Net": null,
          "p2": "Bruce Atkins",
```
New: `"p2": "Bruce Replacement - TBD",`

- [ ] **Step 7: Rename the R9 slot (Ethan High) — Bruce is p2**

Old:
```json
          "p1": "Ethan High",
          "p1Pts": null,
          "p1Net": null,
          "p2": "Bruce Atkins",
```
New: `"p2": "Bruce Replacement - TBD",`

- [ ] **Step 8: Drop Bruce from the R6 bye (two places: `rounds[]` and `schedule[]`)**

Replace both occurrences of the string `"bye": "C. Bass / McHugh / Atkins"` with `"bye": "C. Bass / McHugh"` (use replace_all).

- [ ] **Step 9: Verify JSON is still valid**

Run: `python -m json.tool "Dashboard/data.json" > NUL && echo OK`
Expected: prints `OK` (no parse error).

- [ ] **Step 10: Confirm Bruce no longer appears as a pairing participant in R3–R9**

Run: `python -c "import json;d=json.load(open('Dashboard/data.json'));print([(r['round'],p['p1'],p['p2']) for r in d['rounds'] for p in r.get('pairings',[]) if 'Bruce Atkins' in (p['p1'],p['p2'])])"`
Expected: `[]` (empty list — Bruce is gone from all pairings; his frozen results live only in `players[]` and the R1/R2 `matches`/`pairings` which used his name historically… note: R1/R2 pairings DO still reference "Bruce Atkins" as played history and MUST stay). 

Correction — the expected output should only contain the **played** R1/R2 entries. Re-run scoped to unplayed slots:
Run: `python -c "import json;d=json.load(open('Dashboard/data.json'));print([(r['round'],p['p1'],p['p2']) for r in d['rounds'] for p in r.get('pairings',[]) if 'Bruce Atkins' in (p['p1'],p['p2']) and not p.get('played')])"`
Expected: `[]`

---

### Task 2: index.html — WD treatment on the live site

**Files:**
- Modify: `Dashboard/index.html`

- [ ] **Step 1: Add CSS for withdrawn rows and the WD badge**

Insert near the existing `.player-row` / `.standings-table` styles (after line ~144, inside the same `<style>` block):
```css
    .player-row.withdrawn { opacity: 0.5; }
    .player-row.withdrawn .player-name { text-decoration: line-through; }
    .wd-badge { display:inline-block; margin-left:6px; padding:1px 5px; border-radius:4px;
                background:#3a2a2a; color:#c98; font-size:0.62rem; font-weight:700; vertical-align:middle; }
```

- [ ] **Step 2: In `renderStandings()`, compute rank over active players only and badge withdrawn rows**

Replace the desktop-table `ranked.forEach((p, i) => { … })` block (lines ~846–863) with:
```javascript
    let activeRank = 0;
    ranked.forEach((p) => {
      const wd = !!p.withdrawn;
      const rankCell = wd ? '<span class="wd-badge">WD</span>' : rankBadge(++activeRank);
      const nameExtra = wd ? '<span class="wd-badge">WD</span>' : '';
      tableHTML += `
        <tr class="player-row${wd ? ' withdrawn' : ''}" id="row-${p.id}" onclick="toggleExpand('${p.id}')">
          <td>${rankCell}</td>
          <td>
            <div class="player-name">${p.name}${nameExtra}</div>
            ${lastMatchHTML(p)}
          </td>
          <td class="hcp">${hcp(p)}</td>
          <td class="pts">${p.totalPts}</td>
          <td>${recordHTML(p.record)}</td>
          <td class="avg-net">${p.avgNet !== null ? p.avgNet.toFixed(1) : '—'}</td>
          <td>${streakHTML(p)}</td>
        </tr>
        <tr class="expand-row hidden" id="expand-${p.id}">
          <td colspan="7">${renderPlayerDetail(p)}</td>
        </tr>`;
    });
```

- [ ] **Step 3: In `renderStandings()`, do the same for the mobile cards block**

Replace the mobile `ranked.forEach((p, i) => { const rank = i + 1; … })` block (lines ~875–893) with:
```javascript
    let activeCardRank = 0;
    ranked.forEach((p) => {
      const wd = !!p.withdrawn;
      const rank = wd ? null : ++activeCardRank;
      const rankCell = wd ? '<span class="wd-badge">WD</span>' : rankBadge(rank);
      cardsHTML += `
        <div class="player-card ${(!wd && rank <= 3) ? 'rank-' + rank : ''}${wd ? ' withdrawn' : ''}" onclick="toggleCardExpand('${p.id}')">
          <div class="card-top">
            <span style="min-width:26px">${rankCell}</span>
            <span class="card-name">${p.name}</span>
            <span class="card-pts">${p.totalPts}</span>
          </div>
          <div class="card-bottom">
            <span>${recordHTML(p.record)}</span>
            <span class="hcp">HCP ${hcp(p)}</span>
            <span class="avg-net">${p.avgNet !== null ? p.avgNet.toFixed(1) : '—'} avg</span>
          </div>
          <div id="card-expand-${p.id}" class="card-expand hidden">
            ${renderPlayerDetail(p)}
          </div>
        </div>`;
    });
```

- [ ] **Step 4: Keep withdrawn players off the podium**

Change the podium call (line ~833) from:
```javascript
    const podiumHTML = renderPodium(ranked);
```
to:
```javascript
    const podiumHTML = renderPodium(ranked.filter(p => !p.withdrawn));
```

- [ ] **Step 5: Exclude withdrawn from the live playoff seed calc**

In `renderPlayoffs()`, change the ranked filter (line ~1746) from:
```javascript
      .filter(p => p.rounds.length > 0)
```
to:
```javascript
      .filter(p => p.rounds.length > 0 && !p.withdrawn)
```

- [ ] **Step 6: Verify the edits landed**

Run: `python -c "import io;s=open('Dashboard/index.html',encoding='utf-8').read();print('wd-badge' in s, 'activeRank' in s, 'activeCardRank' in s, s.count('!p.withdrawn'))"`
Expected: `True True True 3`  (badge CSS present, both rank counters present, withdrawn filter used in podium + 2 ranked lists = 3 occurrences of `!p.withdrawn`).

- [ ] **Step 7: Manual browser check**

Open `Dashboard/index.html` in a browser. Confirm: Bruce shows a grey, struck-through row with a "WD" badge instead of a rank number; the players below him are numbered with no gap; the podium shows only active players; Carson/Palmer/Adams/Wojcio/High show "Bruce Replacement - TBD / Upcoming" in their schedule. (User performs this; flag any issue before commit.)

---

### Task 3: standings.md — full rewrite

**Files:**
- Modify: `Dashboard/standings.md`

- [ ] **Step 1: Replace the entire file with the updated standings**

Active players renumbered 1–14 (same point order, Bruce removed from the seed list and shown as withdrawn), R6 bye fixed, replacement-rule note added. Write:
```markdown
# IMI Golf League 2026 — Standings

**Season:** 2026 | **Rounds:** 9 | **Players:** 14 active (1 withdrawn)
**Last updated:** 2026-06-11 via Claude (Bruce Atkins withdrawn; replacement/pickup rule in effect)

---

## Roster Change — Bruce Atkins Withdrawn

Bruce Atkins has withdrawn from the league. His played results (R1, R2) stand and remain on the board, but he is no longer an active contender and is not seeded. His incomplete/upcoming match slots (R3, R4, R5, R7, R8, R9) now read **"Bruce Replacement - TBD"**.

**Pickup rule:** the player who was scheduled against Bruce may invite any league member to a pickup match that round. The invited player plays twice that round; both results count. Any player who plays an extra (pickup) match may drop their lowest round — removed entirely from points, record, and avg NET — when it helps them.

---

## Current Round

**Round 4** | Jun 1 – Jun 12, 2026
BYE: Jerome Martin

> **Note:** Carson Bass's R4 opponent is now "Bruce Replacement - TBD." Rob Bass's R3 match is an outstanding makeup against a replacement. Standings shift as those come in.

---

## Standings

*R1 and R2 complete. R3 mostly complete (4 of 7 recorded; outstanding incl. Rob Bass's replacement makeup).*

| Seed | Player | Total Pts | Record | Avg NET |
|------|--------|-----------|--------|---------|
| 1 | Curtis Lynn | 21 | 3-0-0 | 37.3 |
| 2 | David Maddox | 15 | 2-0-0 | 47.5 |
| 3 | Ben Linck | 14.5 | 2-1-0 | 39.0 |
| 4 | Charlotte Hayes | 14 | 2-0-0 | 38.5 |
| 5 | Ethan High | 13 | 2-0-0 | 37.5 |
| 6 | Megan Serian | 10.5 | 1-2-0 | 48.3 |
| 7 | Alex Palmer | 10 | 1-2-0 | 45.3 |
| 8 | Carson Bass | 8 | 1-1-0 | 42.5 |
| 9 | Michael McHugh | 6 | 1-1-0 | 44.5 |
| 10 | Brian Wojcio | 6 | 0-1-1 | 41.5 |
| 11 | Rob Bass | 5 | 0-1-1 | 41.0 |
| 12 | Kaylan Adams | 5 | 0-2-1 | 53.0 |
| 13 | Jerome Martin | 5 | 0-2-1 | 54.0 |
| 14 | Nick Coglianese | 1 | 0-2-0 | 53.5 |
| — | ~~Bruce Atkins~~ (WD) | 10 | 1-1-0 | 36.0 |

*Ties broken by: best record (most W, fewest L) → lowest avg NET → name.*

---

## Schedule

| Round | Dates | BYE |
|-------|-------|-----|
| 1 | Apr 20 – May 1 | David Maddox |
| 2 | May 4 – May 15 | Nick Coglianese |
| 3 | May 18 – May 29 | Charlotte Hayes |
| **4 ← current** | Jun 1 – Jun 12 | Jerome Martin |
| 5 | Jun 15 – Jun 26 | Wojcio / High / R. Bass |
| 6 | Jun 29 – Jul 10 | C. Bass / McHugh |
| 7 | Jul 13 – Jul 24 | Palmer / Lynn / Linck |
| 8 | Jul 27 – Aug 7 | Kaylan Adams |
| 9 | Aug 10 – Aug 21 | Megan Serian |
```

Note: Bruce's frozen 10 pts would otherwise place him at seed 7 (tie with Palmer, broken by avg NET — Bruce 36.0 beats Palmer 45.3). Because he is withdrawn he is delisted from the seed column and shown on the trailing `—` row; active players are renumbered accordingly.

---

### Task 4: League-notice draft

**Files:**
- Create: `Announcements/Bruce_Withdrawal_2026-06-11.md`

- [ ] **Step 1: Write the standalone notice draft**

```markdown
# League Update — Roster Change & New Pickup Rule

Hey all,

Quick update on the league. **Bruce Atkins has had to step away and is withdrawing for the rest of the season.** His results from Rounds 1 and 2 stay on the board, but he won't be playing the back half of the schedule.

Rather than hand anyone free weeks, here's how we'll cover his open matches:

**If you were scheduled to play Bruce** (Carson R4, Alex R5, Kaylan R7, Brian R8, Ethan R9 — plus Rob's R3 makeup), your matchup now shows **"Bruce Replacement - TBD."** You get to **invite any other player in the league** to a pickup match that week. Just line it up and play.

**What's in it for the person you invite?** They'll play twice that round — their own match plus your pickup — and as a thank-you, **anyone who plays an extra match can drop their lowest round of the season.** If the pickup round goes well, it replaces your worst round; if it doesn't, no harm done. It only ever helps.

Both the scheduled player's result and the fill-in's pickup result count as real matches.

Standings and the website are updated to reflect all of this. Reach out with any questions, and let's keep it rolling.

— League Management
```

- [ ] **Step 2: Confirm the file exists**

Run: `python -c "import os;print(os.path.exists('Announcements/Bruce_Withdrawal_2026-06-11.md'))"`
Expected: `True`

---

### Task 5: Commit & push

**Files:** none (git only)

- [ ] **Step 1: Stage the changed files**

```bash
git add Dashboard/data.json Dashboard/index.html Dashboard/standings.md "Announcements/Bruce_Withdrawal_2026-06-11.md" "docs/superpowers/specs/2026-06-11-bruce-withdrawal-replacement-design.md" "docs/superpowers/plans/2026-06-11-bruce-withdrawal-replacement.md"
```

Note: do **not** stage `2026 IMI Golf League.xlsx` (the protected workbook is intentionally untouched) or `setup/processed_files.json`. Leave any pre-existing unrelated working-copy changes alone.

- [ ] **Step 2: Commit**

```bash
git commit -m "Bruce Atkins withdraws: replacement slots, WD on dashboard, pickup rule

- data.json: R3-R9 Bruce slots -> 'Bruce Replacement - TBD'; R6 bye
  drops Atkins; Bruce flagged withdrawn (R1/R2 results frozen)
- index.html: WD badge + greyed row, rank computed over active
  players only, withdrawn excluded from podium and live seed calc
- standings.md: Bruce delisted from seeds (shown WD), active players
  renumbered 1-14, R6 bye fixed, pickup/mulligan rule documented
- Announcements: league notice draft

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 3: Push**

```bash
git push
```
Expected: push succeeds; GitHub Pages redeploys `Dashboard/` automatically.

---

## Self-Review

**Spec coverage:**
- Freeze Bruce R1/R2 → Task 1 Step 1 (withdrawn flag; results untouched). ✅
- Six slots → `Bruce Replacement - TBD` (R3,R4,R5,R7,R8,R9) → Task 1 Steps 2–7. ✅
- R6 bye drops Atkins → Task 1 Step 8. ✅
- Dashboard "WD" treatment (badge, grey, exclude from seeds) → Task 2. ✅
- standings.md withdrawn marking + renumber + rule note → Task 3. ✅
- Dashboard authoritative / workbook untouched → Task 5 Step 1 note (no workbook staging). ✅
- League communication draft → Task 4. ✅
- Drop-lowest math → deferred per spec (no pickup played yet); documented in standings.md + notice, applied by hand later. No code task now — matches spec. ✅

**Placeholder scan:** No TBD/TODO left in logic. The only literal "TBD" is the intentional player-slot label `Bruce Replacement - TBD`.

**Consistency:** Withdrawn detection uses `p.withdrawn` everywhere (data.json field name matches all three index.html reads); badge class `wd-badge` and row class `withdrawn` are defined in Task 2 Step 1 and used in Steps 2–3; verification count of `!p.withdrawn` (3) matches Steps 4+5 (podium + 2 ranked lists).
