import re

with open('dashboard/data/report.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Find window.REPORT_DATA = {
start_idx = text.find('window.REPORT_DATA = {')
if start_idx != -1:
    # Find the end of the JSON object
    # Let's write a small JS script that evaluates `report.js` using node VM!
    pass

node_script = """
const fs = require('fs');
const vm = require('vm');

const code = fs.readFileSync('dashboard/data/report.js', 'utf-8');
const context = { window: {} };
vm.createContext(context);
vm.runInContext(code, context);

const data = context.window.REPORT_DATA;
console.log("Keys:", Object.keys(data));

const l0 = data.RAW_LEVEL0 || [];
console.log("Total level0 records:", l0.length);

// Group by Queue
const queues = {};
l0.forEach(r => {
    const qKey = r.Region + '|' + r.SubRegion + '|' + r.Country + '|' + r.Offering;
    if (!queues[qKey]) {
        queues[qKey] = { act: 0, mlErr: 0, manErr: 0 };
    }
    const act = Number(r.Actual_Offered || 0);
    const ml = Number(r.ML_Forecast || 0);
    const man = Number(r.Manual_Forecast || 0);
    queues[qKey].act += act;
    queues[qKey].mlErr += Math.abs(act - ml);
    queues[qKey].manErr += Math.abs(act - man);
});

let mlWins = 0;
let manWins = 0;
let totalVol = 0;
let totalMlErr = 0;
let totalManErr = 0;

Object.values(queues).forEach(q => {
    totalVol += q.act;
    totalMlErr += q.mlErr;
    totalManErr += q.manErr;
    if (q.mlErr <= q.manErr) mlWins++;
    else manWins++;
});

const qCount = Object.keys(queues).length;
console.log("\\n--- EXACT DASHBOARD VERIFIED NUMBERS ---");
console.log("Total Monitored Queues:", qCount);
console.log("ML Winner Queues:", mlWins, "(" + (mlWins/qCount*100).toFixed(1) + "%)");
console.log("Manual Winner Queues:", manWins, "(" + (manWins/qCount*100).toFixed(1) + "%)");
console.log("Total Actual Volume:", Math.round(totalVol).toLocaleString());
console.log("ML Total Error Units:", Math.round(totalMlErr).toLocaleString(), "(" + (totalMlErr/totalVol*100).toFixed(1) + "% WAPE)");
console.log("Manual Total Error Units:", Math.round(totalManErr).toLocaleString(), "(" + (totalManErr/totalVol*100).toFixed(1) + "% WAPE)");
console.log("Net Error Advantage (ML vs Manual):", Math.round(totalManErr - totalMlErr).toLocaleString(), "units lower error with ML");

// Let's check queues breakdown by Volume tier
let highVolMlWins = 0, highVolManWins = 0, highVolCount = 0;
let lowVolMlWins = 0, lowVolManWins = 0, lowVolCount = 0;

Object.values(queues).forEach(q => {
    if (q.act >= 10000) {
        highVolCount++;
        if (q.mlErr <= q.manErr) highVolMlWins++;
        else highVolManWins++;
    } else {
        lowVolCount++;
        if (q.mlErr <= q.manErr) lowVolMlWins++;
        else lowVolManWins++;
    }
});

console.log("\\nVolume Tier Split:");
console.log("  High-Volume Queues (>=10k units):", highVolCount, "-> Manual Wins:", highVolManWins, "ML Wins:", highVolMlWins);
console.log("  Long-Tail Queues (<10k units):", lowVolCount, "-> ML Wins:", lowVolMlWins, "Manual Wins:", lowVolManWins);
""";

fs.writeFileSync('run_vm.js', node_script);
"""

with open('extract_v1.py', 'w', encoding='utf-8') as f:
    f.write(node_script_gen := """
import subprocess
with open('run_vm.js', 'w', encoding='utf-8') as f:
    f.write('''""" + node_script + """''')

subprocess.run(['node', 'run_vm.js'])
""")
