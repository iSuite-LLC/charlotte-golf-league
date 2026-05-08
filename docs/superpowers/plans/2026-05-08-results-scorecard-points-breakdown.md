# Results Scorecard Points Breakdown — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a per-match 5-category points breakdown table inside the existing Results-tab scorecard dropdown panel, plus subtle vertical dividers in the scorecard table marking the First-3 / Middle-3 / Final-3 hole groups.

**Architecture:** All client-side. A new pure helper function in `Dashboard/index.html` computes points-per-category from each match's existing `net[]` arrays and `netTotal` values, and renders a compact horizontal table appended to the scorecard panel. A small Node verifier replays the same algorithm against `data.json` so the rules encoded in the dashboard stay in lockstep with the persisted points produced server-side by `process_scores.py`.

**Tech Stack:** Plain HTML/CSS/JS in a single static file (`Dashboard/index.html`). Node.js for verification (no test framework — a one-shot script with `process.exit(1)` on mismatch).

---

## Spec Reference

`docs/superpowers/specs/2026-05-08-results-scorecard-points-breakdown-design.md`

## Scoring Rules (Source of Truth)

A "won hole" requires strictly lower NET than the opponent. Tied holes count for neither player.

| Category   | Holes | Winner pts | Tie pts        |
|------------|-------|------------|----------------|
| First 3    | 1-3   | 2          | 1-1            |
| Middle 3   | 4-6   | 2          | 1-1            |
| Final 3    | 7-9   | 2          | 1-1            |
| Overall    | 1-9   | 1          | ½-½            |
| Net Score  | total | 1 (lower)  | ½-½            |

Max per match: 8 pts.

In code, holes 1-9 map to array indices 0-8. The First/Middle/Final/Overall categories aggregate hole-win counts; the Net Score category compares `netTotal` directly (lower wins).

## File Structure

- **Modify:** `Dashboard/index.html` — add `breakdownHTML(match)` helper, extend `scorecardHTML`, add CSS for breakdown table and hole-group dividers.
- **Create:** `tests/verify_breakdown.js` — Node script that recomputes breakdowns from `Dashboard/data.json` and asserts totals match each match's persisted `p1Pts`/`p2Pts`.

No other files change. No new dependencies. No build step.

---

## Task 1: Write the algorithm verifier

**Files:**
- Create: `tests/verify_breakdown.js`

This task encodes the scoring algorithm in a standalone Node script and verifies it against every played match in `data.json`. If the script's output is "All breakdown totals match persisted points," we have proven (against real data) that the algorithm correctly mirrors `process_scores.py`. The same algorithm shape will be reused inside `index.html` in Task 2.

- [ ] **Step 1: Create the verifier file**

Create `tests/verify_breakdown.js` with this exact content:

```javascript
const fs = require('fs');
const path = require('path');

const dataPath = path.join(__dirname, '..', 'Dashboard', 'data.json');
const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));

// Holes 1-3, 4-6, 7-9, all (array indices 0-8 ↔ holes 1-9)
const GROUPS = [[0,1,2], [3,4,5], [6,7,8], [0,1,2,3,4,5,6,7,8]];
const GROUP_PTS_WIN = [2, 2, 2, 1];
const GROUP_PTS_TIE = [1, 1, 1, 0.5];

function computeBreakdown(p1Net, p2Net, p1NetTotal, p2NetTotal) {
  for (let i = 0; i < 9; i++) {
    if (p1Net[i] == null || p2Net[i] == null) return null;
  }
  const p1 = [0, 0, 0, 0, 0];
  const p2 = [0, 0, 0, 0, 0];
  for (let g = 0; g < 4; g++) {
    let p1Won = 0, p2Won = 0;
    for (const i of GROUPS[g]) {
      if (p1Net[i] < p2Net[i]) p1Won++;
      else if (p1Net[i] > p2Net[i]) p2Won++;
    }
    if (p1Won > p2Won)      p1[g] = GROUP_PTS_WIN[g];
    else if (p2Won > p1Won) p2[g] = GROUP_PTS_WIN[g];
    else { p1[g] = GROUP_PTS_TIE[g]; p2[g] = GROUP_PTS_TIE[g]; }
  }
  if (p1NetTotal < p2NetTotal)      p1[4] = 1;
  else if (p2NetTotal < p1NetTotal) p2[4] = 1;
  else { p1[4] = 0.5; p2[4] = 0.5; }
  const p1Total = p1.reduce((a, b) => a + b, 0);
  const p2Total = p2.reduce((a, b) => a + b, 0);
  return { p1, p2, p1Total, p2Total };
}

let checked = 0;
const mismatches = [];

for (const round of data.rounds) {
  if (round.status === 'upcoming') continue;
  const matches = round.pairings || round.matches || [];
  for (const m of matches) {
    if (m.played === false) continue;
    const sc1 = m.p1Scorecard, sc2 = m.p2Scorecard;
    if (!sc1 || !sc2 || !sc1.net || !sc2.net) continue;
    const r = computeBreakdown(sc1.net, sc2.net, sc1.netTotal, sc2.netTotal);
    if (r === null) continue; // partial card — skip
    checked++;
    if (r.p1Total !== m.p1Pts || r.p2Total !== m.p2Pts) {
      mismatches.push({
        round: round.round,
        p1: m.p1, p2: m.p2,
        persisted: `${m.p1Pts}-${m.p2Pts}`,
        computed: `${r.p1Total}-${r.p2Total}`,
        breakdown: r
      });
    }
  }
}

console.log(`Checked ${checked} matches.`);
if (mismatches.length === 0) {
  console.log('All breakdown totals match persisted points. ✓');
  process.exit(0);
} else {
  console.error(`${mismatches.length} mismatch(es):`);
  for (const x of mismatches) {
    console.error(`  R${x.round} ${x.p1} vs ${x.p2}: persisted ${x.persisted}, computed ${x.computed}`);
    console.error(`    p1 by category: ${JSON.stringify(x.breakdown.p1)}`);
    console.error(`    p2 by category: ${JSON.stringify(x.breakdown.p2)}`);
  }
  process.exit(1);
}
```

- [ ] **Step 2: Run the verifier**

Run: `node tests/verify_breakdown.js`

Expected: prints `Checked N matches.` (where N matches the number of completed matches with full scorecards in `data.json`) followed by `All breakdown totals match persisted points. ✓` and exits 0.

If it prints any mismatch and exits 1: STOP. Either (a) the algorithm above has a bug — re-read the Scoring Rules table and the algorithm — or (b) `process_scores.py` and the documented rules disagree, which is a real finding worth raising before continuing. Do not proceed to Task 2 until this runs clean.

- [ ] **Step 3: Commit**

```bash
git add tests/verify_breakdown.js
git commit -m "Add verifier for results-tab points breakdown algorithm"
```

---

## Task 2: Add the `breakdownHTML` helper

**Files:**
- Modify: `Dashboard/index.html` (add new function immediately before the `/* ── Results ── */` section header at the existing line `/* ── Results ── */`, currently line 880)

The helper is a pure function: takes a `match` object, returns an HTML string (the breakdown `<table>`) or `''` if the breakdown can't be computed. Adding it in this task without wiring it in means the page renders identically to today; we wire it up in Task 3.

- [ ] **Step 1: Add the function**

In `Dashboard/index.html`, locate this line (currently around line 880):

```javascript
  /* ── Results ── */
```

Immediately *before* that comment, insert:

```javascript
  /* ── Points Breakdown ── */
  function breakdownHTML(match) {
    const sc1 = match.p1Scorecard, sc2 = match.p2Scorecard;
    if (!sc1 || !sc2 || !sc1.net || !sc2.net) return '';
    for (let i = 0; i < 9; i++) {
      if (sc1.net[i] == null || sc2.net[i] == null) return '';
    }

    // Holes 1-3, 4-6, 7-9, all (indices 0-8 ↔ holes 1-9)
    const GROUPS = [[0,1,2], [3,4,5], [6,7,8], [0,1,2,3,4,5,6,7,8]];
    const GROUP_PTS_WIN = [2, 2, 2, 1];
    const GROUP_PTS_TIE = [1, 1, 1, 0.5];

    const p1Pts = [0, 0, 0, 0, 0];
    const p2Pts = [0, 0, 0, 0, 0];

    for (let g = 0; g < 4; g++) {
      let p1Won = 0, p2Won = 0;
      for (const i of GROUPS[g]) {
        if (sc1.net[i] < sc2.net[i]) p1Won++;
        else if (sc1.net[i] > sc2.net[i]) p2Won++;
      }
      if (p1Won > p2Won)      p1Pts[g] = GROUP_PTS_WIN[g];
      else if (p2Won > p1Won) p2Pts[g] = GROUP_PTS_WIN[g];
      else { p1Pts[g] = GROUP_PTS_TIE[g]; p2Pts[g] = GROUP_PTS_TIE[g]; }
    }

    if (sc1.netTotal < sc2.netTotal)      p1Pts[4] = 1;
    else if (sc2.netTotal < sc1.netTotal) p2Pts[4] = 1;
    else { p1Pts[4] = 0.5; p2Pts[4] = 0.5; }

    const p1Total = p1Pts.reduce((a, b) => a + b, 0);
    const p2Total = p2Pts.reduce((a, b) => a + b, 0);

    if (p1Total !== match.p1Pts || p2Total !== match.p2Pts) {
      console.warn(`[breakdown mismatch] ${match.p1} vs ${match.p2}: computed ${p1Total}-${p2Total}, persisted ${match.p1Pts}-${match.p2Pts}`);
    }

    const fmt = v => v === 0.5 ? '½' : String(v);
    const p1First = match.p1.split(' ')[0];
    const p2First = match.p2.split(' ')[0];
    const headers = ['First 3', 'Middle 3', 'Final 3', 'Overall', 'Net'];

    function playerRow(firstName, myPts, oppPts, myTotal, oppTotal) {
      const cells = myPts.map((v, i) => {
        const isWin = v > oppPts[i];
        return `<td${isWin ? ' class="sc-bd-winner"' : ''}>${fmt(v)}</td>`;
      }).join('');
      const totalIsWin = myTotal > oppTotal;
      const totalClass = 'sc-bd-total' + (totalIsWin ? ' sc-bd-winner' : '');
      return `<tr><td class="sc-td-label">${firstName}</td>${cells}<td class="${totalClass}">${fmt(myTotal)}</td></tr>`;
    }

    const headerCols = headers.map(h => `<th>${h}</th>`).join('');
    return `<table class="sc-breakdown">
      <thead><tr><th class="sc-th-label">&nbsp;</th>${headerCols}<th class="sc-bd-total">TOTAL</th></tr></thead>
      <tbody>
        ${playerRow(p1First, p1Pts, p2Pts, p1Total, p2Total)}
        ${playerRow(p2First, p2Pts, p1Pts, p2Total, p1Total)}
      </tbody>
    </table>`;
  }

```

- [ ] **Step 2: Sanity-check the page still loads**

Open `Dashboard/index.html` in a browser. Open DevTools console. Reload. Confirm:
- The page renders normally (Standings tab loads, Results tab works).
- No JavaScript errors in the console.
- No `[breakdown mismatch]` warnings (the function isn't being called yet, so this should be silent — but if you see one, something else is wrong).

- [ ] **Step 3: Commit**

```bash
git add Dashboard/index.html
git commit -m "Add breakdownHTML helper for per-match points breakdown"
```

---

## Task 3: Add CSS for the breakdown table

**Files:**
- Modify: `Dashboard/index.html` — add CSS rules in the `/* ── Scorecard panel ── */` block (currently ends at line 254 with `.sc-table td { padding: 5px 9px; }`)

This adds the styling the helper produced in Task 2 expects. Doing this before wiring (Task 4) means the breakdown will render correctly the moment we hook it in.

- [ ] **Step 1: Add CSS rules**

In `Dashboard/index.html`, locate this line (currently line 254):

```css
    .sc-table td { padding: 5px 9px; }
```

Immediately *after* that line (still inside the `/* ── Scorecard panel ── */` block, before the `/* ── Schedule ── */` block), insert:

```css
    .sc-breakdown { border-collapse: collapse; font-size: 0.78rem; margin-top: 12px; white-space: nowrap; }
    .sc-breakdown th, .sc-breakdown td { padding: 5px 10px; text-align: center; }
    .sc-breakdown thead th { color: var(--muted); font-size: 0.66rem; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; padding-bottom: 4px; border-bottom: 1px solid #222; }
    .sc-breakdown .sc-th-label, .sc-breakdown .sc-td-label { text-align: left !important; font-size: 0.7rem; color: var(--muted); font-weight: 600; min-width: 52px; }
    .sc-breakdown tbody td { font-weight: 600; color: #ccc; border-bottom: 1px solid #1c1c1c; }
    .sc-breakdown td.sc-bd-winner { color: var(--green); font-weight: 700; }
    .sc-breakdown .sc-bd-total { border-left: 1px solid #2a2a2a; font-weight: 700; }
```

- [ ] **Step 2: Sanity-check page still loads**

Reload `Dashboard/index.html` in the browser. Confirm no rendering regressions on the existing scorecards (the new CSS classes aren't in any DOM yet, so nothing visible should change).

- [ ] **Step 3: Commit**

```bash
git add Dashboard/index.html
git commit -m "Add CSS for points breakdown table"
```

---

## Task 4: Wire the breakdown into `scorecardHTML`

**Files:**
- Modify: `Dashboard/index.html`, function `scorecardHTML` (currently lines 814-878)

This is the moment the breakdown becomes visible. Append the helper's output after the existing `.sc-scroll` div, still inside the `.scorecard-panel`.

- [ ] **Step 1: Modify the return statement of `scorecardHTML`**

Locate this block in `Dashboard/index.html` (currently lines 865-877):

```javascript
    return `<div id="${id}" class="scorecard-panel hidden">
      <div class="sc-meta">${metaLine}</div>
      <div class="sc-scroll"><table class="sc-table">
        <thead>
          <tr><th class="sc-th-label">Hole</th>${holeHdrs}<th class="sc-hole-num sc-total-col">TOT</th></tr>
          ${parHTML}
        </thead>
        <tbody>
          ${playerRowsHTML(p1First, sc1, match.winner === match.p1)}
          ${playerRowsHTML(p2First, sc2, match.winner === match.p2)}
        </tbody>
      </table></div>
    </div>`;
```

Replace with:

```javascript
    return `<div id="${id}" class="scorecard-panel hidden">
      <div class="sc-meta">${metaLine}</div>
      <div class="sc-scroll"><table class="sc-table">
        <thead>
          <tr><th class="sc-th-label">Hole</th>${holeHdrs}<th class="sc-hole-num sc-total-col">TOT</th></tr>
          ${parHTML}
        </thead>
        <tbody>
          ${playerRowsHTML(p1First, sc1, match.winner === match.p1)}
          ${playerRowsHTML(p2First, sc2, match.winner === match.p2)}
        </tbody>
      </table></div>
      ${breakdownHTML(match)}
    </div>`;
```

(Single-line addition: `${breakdownHTML(match)}` between the closing `</div>` of `.sc-scroll` and the closing `</div>` of `.scorecard-panel`.)

- [ ] **Step 2: Verify in browser**

Reload `Dashboard/index.html`. Click the Results tab. Click on any completed match (e.g., Round 1 → Brian Wojcio vs Ethan High) to expand the scorecard. Confirm:
- The 9-hole scorecard still renders as before (par, gross with circles/squares, net).
- A new compact horizontal table appears below it with columns: First 3, Middle 3, Final 3, Overall, Net, TOTAL.
- Two rows: one per player, first names only.
- The TOTAL column values match the match's header score (e.g., for the `2 — 6` match, the TOTAL column reads `2` and `6`).
- The winner of each category column is colored green and bolded; tied cells are plain.
- No `[breakdown mismatch]` warnings in the console.

- [ ] **Step 3: Spot-check 3 more matches across different rounds**

Expand at least three more matches across at least two different rounds. For each, confirm the TOTAL column matches the displayed match score in the Results header.

- [ ] **Step 4: Commit**

```bash
git add Dashboard/index.html
git commit -m "Wire points breakdown into scorecard dropdown"
```

---

## Task 5: Add hole-group dividers in the scorecard

**Files:**
- Modify: `Dashboard/index.html` — one CSS rule in the `/* ── Scorecard panel ── */` block

Adds vertical lines between holes 3/4 and 6/7 in the existing `.sc-table` so the First-3 / Middle-3 / Final-3 groupings line up visually with the breakdown columns below.

- [ ] **Step 1: Add the divider CSS**

In `Dashboard/index.html`, locate the line you added in Task 3 (the last line of the `.sc-breakdown` CSS block):

```css
    .sc-breakdown .sc-bd-total { border-left: 1px solid #2a2a2a; font-weight: 700; }
```

Immediately *after* that line, insert:

```css
    .sc-table th:nth-child(5), .sc-table td:nth-child(5),
    .sc-table th:nth-child(8), .sc-table td:nth-child(8) { border-left: 1px solid #2a2a2a; }
```

(Note: cell positions — 1st child is the row label, 2nd-10th are holes 1-9, 11th is TOT. So 5th child = hole 4, 8th child = hole 7. The TOT column's existing `.sc-total-col` border remains as-is.)

- [ ] **Step 2: Verify in browser**

Reload. Expand any match in Results. Confirm:
- A thin vertical divider sits between hole 3 and hole 4 in the scorecard table.
- A thin vertical divider sits between hole 6 and hole 7.
- The TOT column's left border is still visibly present (and at least as strong as the new dividers — the existing `!important` on `.sc-total-col` ensures this).
- Dividers appear consistently across all rows: header (Hole), Par row, both players' Gross rows, both players' Net rows.
- The breakdown table below now visually echoes the scorecard groupings.

- [ ] **Step 3: Commit**

```bash
git add Dashboard/index.html
git commit -m "Add hole-group dividers to scorecard between holes 3/4 and 6/7"
```

---

## Task 6: Edge-case verification

**Files:** None modified. Browser verification only.

Confirm the design's edge-case behavior holds against real data. If any check fails, fix it inline and amend the relevant earlier commit; otherwise no commit needed.

- [ ] **Step 1: Verify draw matches**

Find a draw match in Results (look for any match where the two scores are `4 — 4`, or where `match.winner === null` in `data.json`). If one exists in current `data.json`, expand it. Confirm:
- TOTAL column reads `4` and `4`, neither side highlighted green.
- The category rows sum to 4-4 and tell a coherent story (e.g., one side won First 3 outright, the other won Middle 3 outright, etc.).

If no draw match currently exists in `data.json`, skip this step and note it in the commit message of any later fix.

- [ ] **Step 2: Verify one-sided scorecard handling**

Search `Dashboard/data.json` for any played match where exactly one of `p1Scorecard` / `p2Scorecard` exists. If found, expand it in the Results tab. Confirm:
- The existing one-sided scorecard renders as before.
- No breakdown table appears below it (because `breakdownHTML` returns `''`).
- No `[breakdown mismatch]` warnings.

If no such match exists in the current data, skip this step.

- [ ] **Step 3: Verify partial-card handling**

If any match has `null` values inside `p1Scorecard.net` or `p2Scorecard.net`, expand it. Confirm scorecard renders, breakdown does not. If no such match exists, skip.

- [ ] **Step 4: Mobile-width check**

Resize the browser window to ~360px wide (or use DevTools device emulation). Expand a match. Confirm:
- The scorecard remains horizontally scrollable inside `.sc-scroll` as before.
- The breakdown table either fits within the viewport or scrolls horizontally without breaking layout.
- The breakdown table is readable at narrow widths.

If layout breaks at narrow widths, wrap the breakdown table in a `<div class="sc-scroll">` and re-test. If a fix is required, commit it as:

```bash
git add Dashboard/index.html
git commit -m "Wrap breakdown table in scroll container for narrow viewports"
```

- [ ] **Step 5: Final verifier rerun**

Run: `node tests/verify_breakdown.js`

Expected: still passes (the verifier doesn't care about UI changes; it just guards the algorithm). This is a quick guard against any accidental edits to the algorithm logic during the previous tasks.

- [ ] **Step 6: Push**

```bash
git push
```
