const fs = require('fs');
let content = fs.readFileSync('d:/project_1 imp docs/Forecast review/dashboard/data/report.js', 'utf8');

// Replace "window.REPORT_DATA =" with "global.REPORT_DATA =" to make it accessible
content = content.replace('window.REPORT_DATA =', 'global.REPORT_DATA =');

// Execute the JS
eval(content);

let data = global.REPORT_DATA || RAW_LEVEL0;

let weeksOld = {};
let weeksNew = {};

data.forEach(row => {
    let w = row.Week_Ending;
    if (!weeksOld[w]) weeksOld[w] = {act: 0, man: 0, ml: 0};
    weeksOld[w].act += (row.Actual_Offered || 0);
    weeksOld[w].man += (parseFloat(row.Manual_Forecast) || 0);
    weeksOld[w].ml += (parseFloat(row.ML_Forecast) || 0);
    
    if (!weeksNew[w]) weeksNew[w] = {act: 0, manErr: 0, mlErr: 0};
    weeksNew[w].act += (row.Actual_Offered || 0);
    weeksNew[w].manErr += (row.Manual_Abs_Err || 0);
    weeksNew[w].mlErr += (row.ML_Abs_Err || 0);
});

// Old Logic (Net Error)
let wapesOld = [];
for (let w in weeksOld) {
    if (weeksOld[w].act > 0) {
        let err = Math.abs(weeksOld[w].act - weeksOld[w].man); 
        wapesOld.push(err / weeksOld[w].act);
    }
}
let meanOld = wapesOld.reduce((a,b)=>a+b,0) / wapesOld.length;
let varOld = wapesOld.reduce((a,b)=>a+Math.pow(b-meanOld,2),0) / (wapesOld.length-1);
let stdOld = Math.sqrt(varOld);

// New Logic (Absolute Error)
let wapesNew = [];
for (let w in weeksNew) {
    if (weeksNew[w].act > 0) {
        let err = weeksNew[w].manErr; 
        wapesNew.push(err / weeksNew[w].act);
    }
}
let meanNew = wapesNew.reduce((a,b)=>a+b,0) / wapesNew.length;
let varNew = wapesNew.reduce((a,b)=>a+Math.pow(b-meanNew,2),0) / (wapesNew.length-1);
let stdNew = Math.sqrt(varNew);

console.log('--- OLD LOGIC (Canceled Errors) ---');
console.log('Mean WAPE: ' + (meanOld*100).toFixed(1) + '%');
console.log('StdDev: ' + (stdOld*100).toFixed(1) + '%');

console.log('\n--- NEW LOGIC (True Volume-Weighted) ---');
console.log('Mean WAPE: ' + (meanNew*100).toFixed(1) + '%');
console.log('StdDev: ' + (stdNew*100).toFixed(1) + '%');
