const fs = require('fs');

const content = fs.readFileSync('dashboard/data/report.js', 'utf-8');
const jsonStr = content.replace(/^window\.REPORT_DATA\s*=\s*/, '').replace(/;\s*$/, '');
const data = JSON.parse(jsonStr);

console.log("Keys:", Object.keys(data));
const l0 = data.RAW_LEVEL0 || [];
console.log("Total records:", l0.length);

let totalAct = 0;
let totalMlErr = 0;
let totalManErr = 0;

const queuesMap = {};
const offeringMap = {};
const countryMap = {};

l0.forEach(r => {
    const qKey = `${r.Region}|${r.SubRegion}|${r.Country}|${r.Offering}`;
    const act = Number(r.Actual || 0);
    const ml = Number(r.ML_FC || 0);
    const man = Number(r.Manual_FC || 0);

    totalAct += act;
    totalMlErr += Math.abs(act - ml);
    totalManErr += Math.abs(act - man);

    if (!queuesMap[qKey]) {
        queuesMap[qKey] = { act: 0, mlErr: 0, manErr: 0, mlWins: 0, manWins: 0 };
    }
    queuesMap[qKey].act += act;
    queuesMap[qKey].mlErr += Math.abs(act - ml);
    queuesMap[qKey].manErr += Math.abs(act - man);
    if (Math.abs(act - ml) < Math.abs(act - man)) {
        queuesMap[qKey].mlWins++;
    } else {
        queuesMap[qKey].manWins++;
    }

    const off = r.Offering || 'Unknown';
    if (!offeringMap[off]) offeringMap[off] = { act: 0, mlErr: 0, manErr: 0 };
    offeringMap[off].act += act;
    offeringMap[off].mlErr += Math.abs(act - ml);
    offeringMap[off].manErr += Math.abs(act - man);

    const c = r.Country || 'Unknown';
    if (!countryMap[c]) countryMap[c] = { act: 0, mlErr: 0, manErr: 0 };
    countryMap[c].act += act;
    countryMap[c].mlErr += Math.abs(act - ml);
    countryMap[c].manErr += Math.abs(act - man);
});

const queues = Object.keys(queuesMap);
console.log("Total Queues:", queues.length);
console.log("Total Actual Volume:", Math.round(totalAct).toLocaleString());
console.log("Total ML Error Units:", Math.round(totalMlErr).toLocaleString(), `(WAPE: ${(totalMlErr/totalAct*100).toFixed(1)}%)`);
console.log("Total Manual Error Units:", Math.round(totalManErr).toLocaleString(), `(WAPE: ${(totalManErr/totalAct*100).toFixed(1)}%)`);

let mlChampCount = 0;
let manChampCount = 0;
let tieCount = 0;

queues.forEach(q => {
    const qData = queuesMap[q];
    if (qData.mlErr < qData.manErr) mlChampCount++;
    else if (qData.manErr < qData.mlErr) manChampCount++;
    else tieCount++;
});

console.log("\nQueue Champion Distribution Across 360 Queues:");
console.log(`  ML Champion: ${mlChampCount} queues (${(mlChampCount/queues.length*100).toFixed(1)}%)`);
console.log(`  Manual Champion: ${manChampCount} queues (${(manChampCount/queues.length*100).toFixed(1)}%)`);
console.log(`  Tie/Hybrid: ${tieCount} queues (${(tieCount/queues.length*100).toFixed(1)}%)`);

console.log("\nOffering Breakdown:");
Object.keys(offeringMap).forEach(off => {
    const s = offeringMap[off];
    const mlWape = (s.mlErr / s.act * 100).toFixed(1);
    const manWape = (s.manErr / s.act * 100).toFixed(1);
    console.log(`  ${off}: ML WAPE = ${mlWape}%, Manual WAPE = ${manWape}%, Volume = ${Math.round(s.act).toLocaleString()}`);
});

console.log("\nWorst 5 Countries by WAPE:");
const sortedC = Object.keys(countryMap).sort((a,b) => (countryMap[b].manErr/countryMap[b].act) - (countryMap[a].manErr/countryMap[a].act));
sortedC.slice(0, 5).forEach(c => {
    const s = countryMap[c];
    const mlWape = (s.mlErr / s.act * 100).toFixed(1);
    const manWape = (s.manErr / s.act * 100).toFixed(1);
    console.log(`  ${c}: ML WAPE = ${mlWape}%, Manual WAPE = ${manWape}%, Volume = ${Math.round(s.act).toLocaleString()}`);
});
