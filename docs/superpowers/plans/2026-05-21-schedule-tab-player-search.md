# Schedule Tab Player Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a player search/picker to the Schedule tab that, when a player is selected, replaces the round-by-round table with a per-player schedule view (opponent, result, status per round, with BYEs marked).

**Architecture:** Single-file change to `Dashboard/index.html`. A new module-scoped `selectedPlayer` variable drives a dispatcher inside `renderSchedule()`. When null, the existing round table renders unchanged; when set, a new `renderPlayerScheduleHTML(name)` builds a per-round table using `leagueData.schedule` and `leagueData.rounds[i].pairings`. The search control is a combined text + dropdown picker rendered above the table.

**Tech Stack:** Plain HTML/CSS/JS, no build step, no JS test framework. Verification per task is via local browser served by `python -m http.server`.

---

## File Structure

- **Modify:** `Dashboard/index.html`
  - New CSS under the existing `/* ── Schedule ── */` section and a new player-view CSS block
  - New module-scoped variable: `selectedPlayer`
  - New functions: `renderScheduleSearchBar`, `renderSeasonScheduleHTML`, `renderPlayerScheduleHTML`, `getPlayerSchedule`, `getPlayerNames`, `selectPlayer`, `clearPlayer`, `openPlayerDropdown`, `closePlayerDropdown`, `togglePlayerDropdown`, `filterPlayerDropdown`
  - Modified function: `renderSchedule()` becomes a dispatcher

Single file, ~120 lines added.

## Testing Approach

This codebase has no JS test framework. For each task, verify behavior by:

1. From the repo root, run: `python -m http.server 8000 --directory Dashboard`
2. Open `http://localhost:8000` in a browser
3. Click the **Schedule** tab and follow the verification steps in each task
4. Use the browser DevTools console where called for

---

### Task 1: Refactor `renderSchedule()` into a dispatcher

**Files:**
- Modify: `Dashboard/index.html` (around line 1036)

Extracts the existing rendering into a helper and introduces a dispatcher + `selectedPlayer` state. No visible behavior change.

- [ ] **Step 1: Locate the current `renderSchedule` function**

Open `Dashboard/index.html` and find `function renderSchedule()` (around line 1036).

- [ ] **Step 2: Replace it with a dispatcher + extracted helper**

Replace the existing `function renderSchedule() { ... }` block with the following code. Place the `let selectedPlayer = null;` declaration immediately above the dispatcher.

```javascript
let selectedPlayer = null;

function renderSchedule() {
  const bodyHTML = selectedPlayer
    ? renderPlayerScheduleHTML(selectedPlayer)
    : renderSeasonScheduleHTML();
  document.getElementById('tab-schedule').innerHTML = bodyHTML;
}

function renderSeasonScheduleHTML() {
  const rows = leagueData.schedule.map(s => {
    const rd     = leagueData.rounds.find(r => r.round === s.round);
    const status = rd ? rd.status : 'upcoming';
    const statusHTML =
      status === 'complete'    ? '<span class="status-complete">Done</span>'     :
      status === 'in_progress' ? '<span class="status-current">Now</span>'       :
                                 '<span class="status-upcoming">Upcoming</span>';
    const rowCls = [
      status === 'in_progress' ? 'current-round' : status === 'complete' ? 'complete-round' : '',
      'clickable'
    ].join(' ').trim();
    return `<tr class="${rowCls}" id="round-row-${s.round}" onclick="toggleRound(${s.round})">
        <td>R${s.round}</td>
        <td>${s.dates}</td>
        <td>${s.bye}</td>
        <td>${statusHTML}</td>
      </tr>
      <tr class="schedule-expand-row hidden" id="round-expand-${s.round}">
        <td colspan="4">${renderRoundDetail(s.round)}</td>
      </tr>`;
  }).join('');
  return `<table class="schedule-table">
    <thead><tr><th>Round</th><th>Dates</th><th>BYE</th><th>Status</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

// Placeholder — real implementation lands in Task 5
function renderPlayerScheduleHTML(name) {
  return renderSeasonScheduleHTML();
}
```

- [ ] **Step 3: Verify in browser**

From the repo root, start the server:
```
python -m http.server 8000 --directory Dashboard
```
Open `http://localhost:8000`, click the **Schedule** tab. Expected: identical to before — 9 rounds in a table, rows expand on click to show matchups.

- [ ] **Step 4: Commit**

```
git add Dashboard/index.html
git commit -m "Refactor renderSchedule into dispatcher (no behavior change)"
```

---

### Task 2: Add `getPlayerSchedule(name)` data helper

**Files:**
- Modify: `Dashboard/index.html`

Pure function that returns the structured data the player view will need. Verifiable from the browser console without DOM work.

- [ ] **Step 1: Add the helper function**

Add this function immediately after `renderPlayerScheduleHTML`:

```javascript
// Returns an array of 9 entries, one per round, shaped:
//   { round, dates, isBye, isCurrent, opponent?, played?, playerPts?, opponentPts?, status }
// status is one of: 'W' | 'L' | 'D' | 'Upcoming' | 'BYE'
function getPlayerSchedule(name) {
  return leagueData.schedule.map(s => {
    const rd      = leagueData.rounds.find(r => r.round === s.round);
    const pairing = rd && rd.pairings
      ? rd.pairings.find(p => p.p1 === name || p.p2 === name)
      : null;
    const isCurrent = !!(rd && rd.status === 'in_progress');

    if (!pairing) {
      return { round: s.round, dates: s.dates, isBye: true, isCurrent, status: 'BYE' };
    }

    const isP1        = pairing.p1 === name;
    const opponent    = isP1 ? pairing.p2    : pairing.p1;
    const playerPts   = isP1 ? pairing.p1Pts : pairing.p2Pts;
    const opponentPts = isP1 ? pairing.p2Pts : pairing.p1Pts;

    if (!pairing.played) {
      return { round: s.round, dates: s.dates, isBye: false, isCurrent, opponent, played: false, status: 'Upcoming' };
    }
    const status = pairing.winner === null ? 'D'
                 : pairing.winner === name  ? 'W' : 'L';
    return { round: s.round, dates: s.dates, isBye: false, isCurrent, opponent, played: true, playerPts, opponentPts, status };
  });
}
```

- [ ] **Step 2: Verify from the browser console**

Reload `http://localhost:8000` and open DevTools console. Run:

```
getPlayerSchedule('Curtis Lynn')
```

Expected (an array of 9 entries):
- Round 1: `{ opponent: 'Nick Coglianese', played: true, playerPts: 8, opponentPts: 0, status: 'W', ... }`
- Round 3: should have a valid pairing
- Round 7: `{ isBye: true, status: 'BYE', ... }`  (R7 BYE group is Palmer/Lynn/Linck per CLAUDE.md schedule)

Then run:

```
getPlayerSchedule('Ethan High')
```

Expected: Round 5 should have `isBye: true, status: 'BYE'` (R5 BYE group is Wojcio/High/R. Bass).

- [ ] **Step 3: Commit**

```
git add Dashboard/index.html
git commit -m "Add getPlayerSchedule data helper"
```

---

### Task 3: Add the search bar UI (markup + CSS, no selection behavior yet)

**Files:**
- Modify: `Dashboard/index.html`

Renders the search input + chevron + clear button + dropdown above the schedule body. Dropdown opens, closes, filters. Selection just logs to console — wiring happens in Task 4.

- [ ] **Step 1: Add CSS**

In the `<style>` block, immediately after the existing `/* ── Schedule ── */` rules (around line 279), add:

```css
/* Player search control */
.schedule-search {
  display: flex;
  align-items: center;
  margin: 14px 16px 12px;
  position: relative;
  max-width: 320px;
}
.schedule-search-input {
  flex: 1;
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text);
  font-size: 0.92rem;
  padding: 9px 56px 9px 12px;
  border-radius: 4px;
  outline: none;
  font-family: inherit;
}
.schedule-search-input:focus { border-color: var(--orange); }
.schedule-search-chevron,
.schedule-search-clear {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--muted);
  cursor: pointer;
  padding: 4px;
  font-size: 0.85rem;
}
.schedule-search-chevron { right: 8px; }
.schedule-search-clear   { right: 30px; display: none; }
.schedule-search.has-value .schedule-search-clear { display: block; }
.schedule-search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 4px;
  max-height: 280px;
  overflow-y: auto;
  z-index: 50;
  display: none;
}
.schedule-search-dropdown.open { display: block; }
.schedule-search-option {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 0.9rem;
}
.schedule-search-option:hover { background: var(--surface-hover); }
.schedule-search-option.empty { color: var(--muted); cursor: default; font-style: italic; }
.schedule-search-option.empty:hover { background: transparent; }
```

- [ ] **Step 2: Update the dispatcher to render the search bar above the body**

Replace the `renderSchedule()` function from Task 1 with this version (the body-rendering helpers stay as-is):

```javascript
function renderSchedule() {
  const searchHTML = renderScheduleSearchBar();
  const bodyHTML = selectedPlayer
    ? renderPlayerScheduleHTML(selectedPlayer)
    : renderSeasonScheduleHTML();
  document.getElementById('tab-schedule').innerHTML = searchHTML + bodyHTML;
}

function renderScheduleSearchBar() {
  const value       = selectedPlayer || '';
  const hasValueCls = value ? 'has-value' : '';
  return `<div class="schedule-search ${hasValueCls}" id="schedule-search">
    <input type="text" class="schedule-search-input" id="schedule-search-input"
           placeholder="Search player..." value="${value}"
           oninput="filterPlayerDropdown(this.value)"
           onfocus="openPlayerDropdown()"
           onkeydown="if(event.key==='Escape'){closePlayerDropdown();this.blur();}">
    <button class="schedule-search-clear" onclick="clearPlayer()" title="Clear">✕</button>
    <button class="schedule-search-chevron" onclick="togglePlayerDropdown()" title="Browse players">▾</button>
    <div class="schedule-search-dropdown" id="schedule-search-dropdown"></div>
  </div>`;
}
```

- [ ] **Step 3: Add player-list and dropdown control functions**

Add these functions next to the other helpers:

```javascript
function getPlayerNames() {
  return (leagueData.players || [])
    .map(p => p.name)
    .sort((a, b) => a.localeCompare(b));
}

function openPlayerDropdown() {
  const input = document.getElementById('schedule-search-input');
  filterPlayerDropdown(input ? input.value : '');
  document.getElementById('schedule-search-dropdown').classList.add('open');
}

function closePlayerDropdown() {
  document.getElementById('schedule-search-dropdown')?.classList.remove('open');
}

function togglePlayerDropdown() {
  const dd = document.getElementById('schedule-search-dropdown');
  if (dd.classList.contains('open')) closePlayerDropdown();
  else openPlayerDropdown();
}

function filterPlayerDropdown(text) {
  const search  = (text || '').toLowerCase();
  const matches = getPlayerNames().filter(n => n.toLowerCase().includes(search));
  const html = matches.length
    ? matches.map(n => {
        const safe = n.replace(/'/g, "\\'");
        return `<div class="schedule-search-option" onclick="selectPlayer('${safe}')">${n}</div>`;
      }).join('')
    : '<div class="schedule-search-option empty">No players match</div>';
  document.getElementById('schedule-search-dropdown').innerHTML = html;

  const wrap = document.getElementById('schedule-search');
  if (text) wrap.classList.add('has-value');
  else      wrap.classList.remove('has-value');
}

function selectPlayer(name) {
  console.log('selectPlayer:', name); // wired in Task 4
  closePlayerDropdown();
}

function clearPlayer() {
  document.getElementById('schedule-search-input').value = '';
  document.getElementById('schedule-search').classList.remove('has-value');
  closePlayerDropdown();
}

// Close dropdown when clicking outside the search control
document.addEventListener('click', (e) => {
  const wrap = document.getElementById('schedule-search');
  if (wrap && !wrap.contains(e.target)) closePlayerDropdown();
});
```

- [ ] **Step 4: Verify in browser**

Reload `http://localhost:8000` and click **Schedule** tab. Check:

- Search bar appears above the round table.
- Round table still renders below it normally.
- Click the chevron `▾` — dropdown opens listing 15 names alphabetized (Alex Palmer, Ben Linck, Brian Wojcio, Bruce Atkins, Carson Bass, Charlotte Hayes, Curtis Lynn, David Maddox, Ethan High, Jerome Martin, Kaylan Adams, Megan Serian, Michael McHugh, Nick Coglianese, Rob Bass).
- Click the chevron again — dropdown closes.
- Click an empty area of the page — dropdown closes.
- Focus the input and press `Esc` — dropdown closes.
- Type `cur` — only `Curtis Lynn` shown.
- Type `xyz` — `No players match` shown.
- Click a name — console logs `selectPlayer: <name>`, dropdown closes.

- [ ] **Step 5: Commit**

```
git add Dashboard/index.html
git commit -m "Add player search bar UI to Schedule tab"
```

---

### Task 4: Wire selection to switch the view

**Files:**
- Modify: `Dashboard/index.html`

Make `selectPlayer()` set `selectedPlayer` and re-render. Make `clearPlayer()` reset it.

- [ ] **Step 1: Replace `selectPlayer` and `clearPlayer`**

Replace the two placeholder functions with:

```javascript
function selectPlayer(name) {
  selectedPlayer = name;
  closePlayerDropdown();
  renderSchedule();
}

function clearPlayer() {
  selectedPlayer = null;
  closePlayerDropdown();
  renderSchedule();
}
```

- [ ] **Step 2: Verify in browser**

Reload and go to Schedule tab.

- Open dropdown, select **Curtis Lynn**. Expect: input shows "Curtis Lynn", an `✕` button is now visible, and the body below the search bar is still the round table (because `renderPlayerScheduleHTML` is still a placeholder — that's expected until Task 5).
- Click `✕`. Expect: input clears, `✕` disappears, body returns to round table.

- [ ] **Step 3: Commit**

```
git add Dashboard/index.html
git commit -m "Wire player selection to schedule re-render"
```

---

### Task 5: Implement the per-player view

**Files:**
- Modify: `Dashboard/index.html`

Real implementation of `renderPlayerScheduleHTML` — summary line + 9-row per-round table with status formatting.

- [ ] **Step 1: Add CSS for the per-player view**

Add to the `<style>` block, after the search CSS from Task 3:

```css
/* Per-player schedule view */
.player-schedule-summary {
  margin: 0 16px 12px;
  padding: 10px 14px;
  background: var(--surface);
  border-left: 3px solid var(--orange);
  border-radius: 3px;
  font-size: 0.9rem;
}
.player-schedule-summary .name  { font-weight: 700; color: var(--text); }
.player-schedule-summary .stats { color: var(--muted); margin-left: 8px; }

.player-schedule-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
.player-schedule-table thead th {
  text-align: left;
  padding: 9px 12px;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted);
  border-bottom: 1px solid var(--border);
}
.player-schedule-table td { padding: 11px 12px; border-bottom: 1px solid var(--border); }
.player-schedule-table tr.current td { background: #1e1e1e; }
.player-schedule-table tr.bye td     { color: var(--muted); }
.ps-status              { font-weight: 700; }
.ps-status.W            { color: var(--green); }
.ps-status.L            { color: var(--red); }
.ps-status.D            { color: var(--silver); }
.ps-status.upcoming     { color: var(--muted); font-weight: 400; }
.ps-status.bye          { color: var(--muted); font-weight: 400; }
```

- [ ] **Step 2: Replace the placeholder `renderPlayerScheduleHTML`**

Replace the placeholder version from Task 1 with:

```javascript
function renderPlayerScheduleHTML(name) {
  const schedule = getPlayerSchedule(name);

  const playerObj    = (leagueData.players || []).find(p => p.name === name) || {};
  const record       = playerObj.record  ?? '';
  const totalPts     = playerObj.totalPts ?? '';
  const avgNet       = playerObj.avgNet  ?? '';
  const summaryStats = [
    record,
    totalPts !== '' ? `${totalPts} pts`        : '',
    avgNet   !== '' ? `${avgNet} avg NET`      : '',
  ].filter(Boolean).join(' · ');

  const summary = `<div class="player-schedule-summary">
    <span class="name">${name}</span>
    <span class="stats">${summaryStats}</span>
  </div>`;

  const rows = schedule.map(s => {
    const rowCls = [s.isCurrent ? 'current' : '', s.isBye ? 'bye' : ''].filter(Boolean).join(' ');
    if (s.isBye) {
      return `<tr class="${rowCls}">
        <td>R${s.round}</td>
        <td>${s.dates}</td>
        <td>—</td>
        <td>—</td>
        <td><span class="ps-status bye">BYE</span></td>
      </tr>`;
    }
    if (!s.played) {
      return `<tr class="${rowCls}">
        <td>R${s.round}</td>
        <td>${s.dates}</td>
        <td>vs ${s.opponent}</td>
        <td>—</td>
        <td><span class="ps-status upcoming">Upcoming</span></td>
      </tr>`;
    }
    return `<tr class="${rowCls}">
      <td>R${s.round}</td>
      <td>${s.dates}</td>
      <td>vs ${s.opponent}</td>
      <td>${s.playerPts} – ${s.opponentPts}</td>
      <td><span class="ps-status ${s.status}">${s.status}</span></td>
    </tr>`;
  }).join('');

  return summary + `<table class="player-schedule-table">
    <thead><tr><th>Round</th><th>Dates</th><th>Matchup</th><th>Result</th><th>Status</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}
```

- [ ] **Step 3: Verify in browser**

Reload and go to Schedule tab. Run through each case below:

**Curtis Lynn:**
- Summary: `Curtis Lynn · 3-0-0 · 21 pts · 37.3 avg NET`
- R1: vs Nick Coglianese, 8 – 0, W (green)
- R2: vs Brian Wojcio, 6 – 2, W (green)
- R3: vs Nick Coglianese, 8 – 0, W (green) — and this row should be subtly highlighted (current round background)
- R4, R5, R6 (post-R3 rounds with opponents): Upcoming
- R7: BYE
- R8, R9: Upcoming

**Ethan High:**
- R5 should be BYE.

**Nick Coglianese:**
- R2 should be BYE (Nick is the R2 BYE per CLAUDE.md).

**Clear:**
- Click `✕` — returns to season schedule table.

**Cross-check:** Open the Standings tab and confirm the values in each player's summary line (record, total pts, avg NET) match.

- [ ] **Step 4: Commit**

```
git add Dashboard/index.html
git commit -m "Implement per-player schedule view"
```

---

### Task 6: Acceptance pass + push

**Files:**
- None modified (verification only)

- [ ] **Step 1: Walk through the spec's acceptance criteria**

In the browser, on the Schedule tab:

1. With no player selected, the tab looks identical to before (round table, click-to-expand). ✓
2. Type `curt` — only `Curtis Lynn` in the dropdown. ✓
3. Select `Curtis Lynn` — 9-round list, R7 marked BYE, R1–R3 with results matching `data.json`. ✓
4. Click `✕` — restores the default round table. ✓
5. The summary line matches Standings values. ✓
6. `git status` shows only `Dashboard/index.html` modified.

If any criterion fails, fix it before the push.

- [ ] **Step 2: Push**

```
git push
```

GitHub Pages auto-deploys; the change goes live within ~1 minute.
