# Most Pars or Better — Eagle/Birdie/Par Breakdown — Design Spec

**Date:** 2026-05-13
**Scope:** Stats tab → "Most Pars or Better" record card on `Dashboard/index.html`.

## Goal

Beneath each player's name inside the "Most Pars or Better" record card, show a one-line breakdown of how many eagles, birdies, and pars make up that player's total count.

Example for a player with 12 "pars or better":

```
   Most Pars or Better
           12
        Ethan High
       1E · 3B · 8P
```

The three sub-counts always sum exactly to the big number above (eagle + birdie + par = total).

## Non-Goals

- No change to the "Most Double Pars" card. Double-par is a single category by definition (`gross === par × 2`) and has nothing to break down.
- No change to `Dashboard/data.json` structure or any Python scripts. Pure client-side change in `Dashboard/index.html`.
- No change to filtering behavior (the existing per-player Stats filter continues to work unchanged — when filtered to one player, the card just shows that player's breakdown).

## Category Definitions

Use the same definitions the dashboard already applies in the Scoring Distribution chart (`index.html:1147`):

| Category | Condition (`d = gross - par`) |
|----------|-------------------------------|
| Eagle    | `d ≤ -2` (includes albatross and hole-in-one on par 4+) |
| Birdie   | `d === -1` |
| Par      | `d === 0` |

A hole only counts toward at most one of these three categories. Holes with `gross > par` are not counted (they're outside "pars or better").

By construction: `eagleCount + birdieCount + parCount === parsOrBetterCount` for every player.

## Data Layer

Extend `buildBirdiesAndDoublePars(playerFilter)` at `Dashboard/index.html:1155` so it tracks three per-player sub-counts alongside the existing `birdies` map.

Inside the existing `sc.gross.forEach` loop, replace the single `if (g <= sc.par[i]) birdies[name]++` with branching that increments both the total and the matching sub-count. Keep the existing `doubles[name]++` line intact — the loop becomes:

```javascript
sc.gross.forEach((g, i) => {
  if (g == null || sc.par[i] == null) return;
  const d = g - sc.par[i];
  if (d <= -2)      { birdies[name]++; eagles[name]++; }
  else if (d === -1){ birdies[name]++; birdieOnly[name]++; }
  else if (d === 0) { birdies[name]++; parOnly[name]++; }
  if (g === sc.par[i] * 2) doubles[name]++;
});
```

(`birdies` retains its current name to minimize the diff; it represents "pars or better." The three new maps are `eagles`, `birdieOnly`, `parOnly`. Naming the par-only map `parOnly` avoids confusion with golf "par" the category vs. the variable `par`.)

Extend `topEntries(map)` (currently at `index.html:1177`) to optionally accept breakdown-maps and attach a per-player `breakdowns` object to its return value:

```javascript
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
```

The return value becomes:

```javascript
return {
  topBirdie: topEntries(birdies, { eagles, birdieOnly, parOnly }),
  topDouble: topEntries(doubles),
};
```

The double-par call passes no `subMaps`, so `topDouble` is unchanged shape-wise — keeps the Most Double Pars card path identical.

## Render Layer

In the birdieCard template at `index.html:1324-1329`, change the player line so each name is followed by its breakdown sub-line:

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

Notes:
- Names are no longer `.join('<br>')`-ed — each name + breakdown is a block, the `<div class="record-breakdown">` provides its own line break and `<div>` between names provides separation.
- Always show all three counts including zeros (e.g., `0E · 4B · 8P`). Keeps the layout rhythm consistent and makes the sum-to-total relationship visible.
- Use `&middot;` (·) as the separator to match the dot character already used in the Low/High Round cards (`${name} &middot; R${round}`).

## Styling

Add one CSS rule in the existing `.record-card` / `.records-strip` block in `index.html`. The rule:

```css
.record-breakdown {
  font-size: 0.68rem;
  color: var(--muted);
  margin-top: 2px;
  margin-bottom: 4px;
  font-weight: 500;
  letter-spacing: 0.02em;
}
```

`margin-bottom: 4px` provides spacing between tied players' breakdowns when multiple names appear in the card.

## Edge Cases

| Case | Behavior |
|------|----------|
| No matches played yet (`topBirdie === null`) | Card is omitted (current behavior, unchanged). |
| Single leader | One name, one breakdown line. |
| Tie (2+ players with same total) | Each tied player gets their own name + breakdown line. |
| Player has 0 in a category | Shown as `0E`, `0B`, or `0P`. |
| Player filter active | Same code path — breakdown reflects the filtered player's counts. |

## Files Changed

- `Dashboard/index.html` — three regions:
  - `buildBirdiesAndDoublePars` (~lines 1155-1184): add sub-count tracking + extend `topEntries`.
  - `birdieCard` template (~lines 1324-1329): render breakdown per name.
  - CSS (`.record-card` block): add `.record-breakdown` rule.

No other files affected.

## Verification

1. Open the dashboard locally / on Pages and navigate to Stats.
2. Confirm the "Most Pars or Better" card now shows `<player name>` followed by `xE · yB · zP` beneath it.
3. Confirm `x + y + z === <big number>` for every name shown.
4. Toggle the player filter to a specific player; confirm the breakdown updates to that player's counts.
5. Confirm "Most Double Pars" card is visually unchanged.
6. Confirm narrow-viewport (~360px) layout is not broken by the extra line.
