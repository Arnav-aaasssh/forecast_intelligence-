const fs = require('fs');

const content = fs.readFileSync('dashboard/data/report.js', 'utf-8');
const jsonStr = content.replace(/^window\.REPORT_DATA\s*=\s*/, '').replace(/;\s*$/, '');
const data = JSON.parse(jsonStr);

const l0 = data.RAW_LEVEL0 || [];

// Group by Queue (Region, SubRegion, Country, Offering)
const queueAgg = {};
l0.forEach(r => {
    const qKey = `${r.Region}|${r.SubRegion}|${r.Country}|${r.Offering}`;
    if (!queueAgg[qKey]) {
        queueAgg[qKey] = {
            Region: r.Region,
            SubRegion: r.SubRegion,
            Country: r.Country,
            Offering: r.Offering,
            Actual_Sum: 0,
            ML_Err_Sum: 0,
            Manual_Err_Sum: 0
        };
    }
    const act = Number(r.Actual_Offered || r.Actual || 0);
    const ml = Number(r.ML_Forecast || r.ML_FC || 0);
    const man = Number(r.Manual_Forecast || r.Manual_FC || 0);
    queueAgg[qKey].Actual_Sum += act;
    queueAgg[qKey].ML_Err_Sum += Math.abs(act - ml);
    queueAgg[qKey].Manual_Err_Sum += Math.abs(act - man);
});

const queuesList = Object.values(queueAgg).map(q => {
    const mlWape = q.Actual_Sum ? q.ML_Err_Sum / q.Actual_Sum : 0;
    const manWape = q.Actual_Sum ? q.Manual_Err_Sum / q.Actual_Sum : 0;
    return {
        ...q,
        Queue_Actual_Sum: q.Actual_Sum,
        Queue_ML_Err_Sum: q.ML_Err_Sum,
        Queue_Manual_Err_Sum: q.Manual_Err_Sum,
        Queue_WAPE_ML: mlWape,
        Queue_WAPE_Manual: manWape,
        Queue_Winner_By_WAPE: mlWape <= manWape ? 'ML' : 'Manual'
    };
});

let queueWinsML = 0;
let queueWinsManual = 0;
let totalVolume = 0;
let totalMlErr = 0;
let totalManErr = 0;

queuesList.forEach(q => {
    if (q.Queue_Winner_By_WAPE === 'ML') queueWinsML++;
    else queueWinsManual++;
    totalVolume += q.Queue_Actual_Sum;
    totalMlErr += q.Queue_ML_Err_Sum;
    totalManErr += q.Queue_Manual_Err_Sum;
});

console.log("Global Rollup Results:");
console.log("  Total Queues:", queuesList.length);
console.log("  Queue Wins ML:", queueWinsML, `(${((queueWinsML/queuesList.length)*100).toFixed(1)}%)`);
console.log("  Queue Wins Manual:", queueWinsManual, `(${((queueWinsManual/queuesList.length)*100).toFixed(1)}%)`);
console.log("  Total Actual Volume:", Math.round(totalVolume).toLocaleString());
console.log("  Global ML WAPE:", (totalMlErr / totalVolume * 100).toFixed(2) + "%");
console.log("  Global Manual WAPE:", (totalManErr / totalVolume * 100).toFixed(2) + "%");
console.log("  ML Absolute Error (Units):", Math.round(totalMlErr).toLocaleString());
console.log("  Manual Absolute Error (Units):", Math.round(totalManErr).toLocaleString());
