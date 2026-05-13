# Most Pars or Better Breakdown — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show a per-player `xE · yB · zP` sub-line beneath each player's name in the Stats tab's "Most Pars or Better" record card.

**Architecture:** Pure client-side. Three edits in `Dashboard/index.html`: (1) extend `buildBirdiesAndDoublePars` to track three sub-counts per player and attach them to the existing return shape, (2) render the sub-line in the existing `birdieCard` template, (3) add one CSS rule for the sub-line.

**Tech Stack:** Plain HTML/CSS/JS in `Dashboard/index.html`. No new dependencies, no build step.

## Spec Reference

`docs/superpowers/specs/2026-05-13-most-pars-or-better-breakdown-design.md`

## File Structure

Single file modified: `Dashboard/index.html` — three distinct regions edited.

| Region | Approx line | Purpose |
|--------|-------------|---------|
| `buildBirdiesAndDoublePars` body | 1155-1184 | Add eagle/birdie-only/par-only tracking + extend `topEntries` |
| `birdieCard` template | 1324-1329 | Render breakdown line per name |
| Records-strip CSS block | 443-448 | Add `.record-breakdown` rule |

---

## Task 1: Extend the data layer with sub-counts

**Files:**
- Modify: `Dashboard/index.html` (function `buildBirdiesAndDoublePars`, currently lines 1155-1184)

The function currently returns `{ topBirdie: { count, names }, topDouble: { count, names } }`. After this task, `topBirdie` also carries a `breakdowns: { [name]: {e, b, p} }` map. The `topDouble` return shape is unchanged.

- [ ] **Step 1: Replace the function body**

In `Dashboard/index.html`, locate `function buildBirdiesAndDoublePars(playerFilter) {` (currently line 1155). Replace the entire function — from `function buildBirdiesAndDoublePars(playerFilter) {` through its closing `}` — with this exact code:

```javascript
  function buildBirdiesAndDoublePars(playerFilter) {
    const birdies = {}, doubles = {};
    const eagles = {}, birdieOnly = {}, parOnly = {};
    for (const round of (leagueData.rounds || [])) {
      for (const pairing of (round.pairings || [])) {
        if (!pairing.played) continue;
        const entries = [
          { name: pairing.p1, sc: pairing.p1Scorecard },
          { name: pairing.p2, sc: pairing.p2Scorecard }
        ];
        for (const { name, sc } of entries) {
          if (!name || !sc || !sc.gross || !sc.par) continue;
          if (playerFilter && name !== playerFilter) continue;
          birdies[name]    = birdies[name]    || 0;
          doubles[name]    = doubles[name]    || 0;
          eagles[name]     = eagles[name]     || 0;
          birdieOnly[name] = birdieOnly[name] || 0;
          parOnly[name]    = parOnly[name]    || 0;
          sc.gross.forEach((g, i) => {
            if (g == null || sc.par[i] == null) return;
            const d = g - sc.par[i];
            if (d <= -2)       { birdies[name]++; eagles[name]++; }
            else if (d === -1) { birdies[name]++; birdieOnly[name]++; }
            else if (d === 0)  { birdies[name]++; parOnly[name]++; }
            if (g === sc.par[i] * 2) doubles[name]++;
          });
        }
      }
    }
    function topEntries(map, subMaps) {
      if (!Object.keys(map).length) return null;
      const best  = Math.max(...Object.values(map));
      const names = Object.entries(map).filter(([, c]) => c === best).map(([n]) => n);
      const result = { count: best, names };
      if (subMaps) {
        result.breakdowns = {};
        for (const n of names) {
          result.breakdowns[n] = {
            e: subMaps.eagles[n]     || 0,
            b: subMaps.birdieOnly[n] || 0,
            p: subMaps.parOnly[n]    || 0,
          };
        }
      }
      return result;
    }
    return {
      topBirdie: topEntries(birdies, { eagles, birdieOnly, parOnly }),
      topDouble: topEntries(doubles)
    };
  }
```

- [ ] **Step 2: Sanity-check the page still loads**

Open `Dashboard/index.html` in a browser (or open the live URL after pushing). Navigate to the Stats tab. Confirm:
- The "Most Pars or Better" card still renders as it did before (no visual change yet — the breakdown isn't wired into the template).
- The "Most Double Pars" card is unchanged.
- DevTools console shows no JavaScript errors.

- [ ] **Step 3: Commit**

```bash
git add Dashboard/index.html
git commit -m "Track per-player eagle/birdie/par sub-counts for top-birdie record"
```

---

## Task 2: Render the breakdown line in the card

**Files:**
- Modify: `Dashboard/index.html` (`birdieCard` template, currently lines 1324-1329)

After this task, the breakdown shows up on the live card.

- [ ] **Step 1: Replace the birdieCard template**

In `Dashboard/index.html`, locate this block (currently around line 1324):

```javascript
      const birdieCard = spec.topBirdie
        ? `<div class="record-card birdie-card">
             <div class="record-label">Most Pars or Better</div>
             <div class="record-value">${spec.topBirdie.count}</div>
             <div class="record-who">${spec.topBirdie.names.join('<br>')}</div>
           </div>` : '';
```

Replace it with:

```javascript
      const birdieCard = spec.topBirdie
        ? `<div class="record-card birdie-card">
             <div class="record-label">Most Pars or Better</div>
             <div class="record-value">${spec.topBirdie.count}</div>
             <div class="record-who">${spec.topBirdie.names.map(n => {
               const b = spec.topBirdie.breakdowns[n];
               return `${n}<div class="record-breakdown">${b.e}E &middot; ${b.b}B &middot; ${b.p}P</div>`;
             }).join('')}</div>
           </div>` : '';
```

- [ ] **Step 2: Verify in browser**

Reload the dashboard. Go to Stats. In the "Most Pars or Better" card, confirm:
- Beneath each player's name there is a small sub-line: `<num>E · <num>B · <num>P`.
- The three numbers in each sub-line sum to the big number above (the total).
- If two or more players are tied, each player gets their own sub-line.
- Use the player-filter dropdown to switch to a single player; the breakdown updates to that player's counts.
- The "Most Double Pars" card is visually unchanged.
- DevTools console shows no JavaScript errors.

The styling will look ugly/unstyled at this point — that's expected, fixed in Task 3.

- [ ] **Step 3: Commit**

```bash
git add Dashboard/index.html
git commit -m "Render eagle/birdie/par breakdown beneath name in top-birdie card"
```

---

## Task 3: Add the breakdown CSS

**Files:**
- Modify: `Dashboard/index.html` — add a CSS rule in the records-strip block (currently lines 432-448)

- [ ] **Step 1: Add the `.record-breakdown` rule**

In `Dashboard/index.html`, locate this line (currently line 443):

```css
    .record-who  { font-size: 0.72rem; color: var(--muted); }
```

Immediately *after* that line, insert:

```css
    .record-breakdown { font-size: 0.68rem; color: var(--muted); margin-top: 2px; margin-bottom: 4px; font-weight: 500; letter-spacing: 0.02em; }
```

- [ ] **Step 2: Verify in browser**

Reload. In the Stats tab → "Most Pars or Better" card, confirm:
- The breakdown sub-line is smaller and slightly muted relative to the player name above it.
- A small gap (~4px) separates one tied player's breakdown from the next player's name.
- The card height fits the new content without overflowing or overlapping the cards on either side.
- The card width and layout match the other record cards.

- [ ] **Step 3: Mobile-width check**

Resize the browser to ~360px wide (or use DevTools device emulation). Confirm:
- The "Most Pars or Better" card still renders cleanly with the breakdown text on a single line.
- The other record cards in the strip are unaffected.

- [ ] **Step 4: Commit and push**

```bash
git add Dashboard/index.html
git commit -m "Style record-breakdown line beneath player name"
git push
```

After the push, GitHub Actions will redeploy the dashboard. Verify the live site shows the breakdown lines as expected.
