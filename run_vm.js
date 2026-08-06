const fs = require('fs');
const vm = require('vm');

const code = fs.readFileSync('dashboard/data/report.js', 'utf-8');
const context = { window: {} };
vm.createContext(context);
vm.runInContext(code, context);

const data = context.window.REPORT_DATA;
const l1 = data.level1 || [];

console.log("Total level1 Queues:", l1.length);
if (l1.length > 0) {
    console.log("Sample level1 record:", Object.keys(l1[0]));
}

let mlWins = 0;
let manWins = 0;
let totalVol = 0;
let totalMlErr = 0;
let totalManErr = 0;

l1.forEach(q => {
    const act = Number(q.Queue_Actual_Sum || 0);
    const mlErr = Number(q.Queue_ML_Err_Sum || 0);
    const manErr = Number(q.Queue_Manual_Err_Sum || 0);
    
    totalVol += act;
    totalMlErr += mlErr;
    totalManErr += manErr;
    
    const mlWape = act ? mlErr / act : 0;
    const manWape = act ? manErr / act : 0;
    
    if (mlWape <= manWape) mlWins++;
    else manWins++;
});

console.log("\n==============================================");
console.log("VERIFIED DASHBOARD METRICS FROM LEVEL1:");
console.log("==============================================");
console.log(`Total Monitored Queues: ${l1.length}`);
console.log(`ML Winner Queues: ${mlWins} (${(mlWins / l1.length * 100).toFixed(1)}%)`);
console.log(`Manual Winner Queues: ${manWins} (${(manWins / l1.length * 100).toFixed(1)}%)`);
console.log(`Total Actual Volume: ${Math.round(totalVol).toLocaleString()}`);
console.log(`ML Total Error Units: ${Math.round(totalMlErr).toLocaleString()} (${(totalMlErr / totalVol * 100).toFixed(1)}% WAPE)`);
console.log(`Manual Total Error Units: ${Math.round(totalManErr).toLocaleString()} (${(totalManErr / totalVol * 100).toFixed(1)}% WAPE)`);
console.log(`Absolute Volume Error Difference: ${Math.round(Math.abs(totalManErr - totalMlErr)).toLocaleString()} units`);

// Check Region & Country Aggregation from level1
const regionAgg = {};
l1.forEach(q => {
    const reg = q.Region || 'Unknown';
    if (!regionAgg[reg]) regionAgg[reg] = { act: 0, mlErr: 0, manErr: 0, count: 0, mlWins: 0 };
    const act = Number(q.Queue_Actual_Sum || 0);
    const mlErr = Number(q.Queue_ML_Err_Sum || 0);
    const manErr = Number(q.Queue_Manual_Err_Sum || 0);
    regionAgg[reg].act += act;
    regionAgg[reg].mlErr += mlErr;
    regionAgg[reg].manErr += manErr;
    regionAgg[reg].count += 1;
    if (mlErr <= manErr) regionAgg[reg].mlWins += 1;
});

console.log("\nRegion Level Performance:");
Object.keys(regionAgg).forEach(r => {
    const s = regionAgg[r];
    const mlW = (s.mlErr / s.act * 100).toFixed(1);
    const manW = (s.manErr / s.act * 100).toFixed(1);
    console.log(`  ${r.padEnd(8)}: Queues=${s.count}, ML Wins=${s.mlWins}, Manual WAPE=${manW}%, ML WAPE=${mlW}%, Vol=${Math.round(s.act).toLocaleString()}`);
});
