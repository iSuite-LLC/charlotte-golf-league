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
