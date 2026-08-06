const fs = require('fs');
const vm = require('vm');

const reportCode = fs.readFileSync('dashboard/data/report.js', 'utf8');
const appCode = fs.readFileSync('dashboard/js/dashboard2_app.js', 'utf8');

const sandbox = {
    window: {},
    document: {
        querySelectorAll: () => [],
        querySelector: () => null,
        getElementById: () => null,
        addEventListener: () => {}
    },
    localStorage: { setItem: () => {} },
    console: console
};
sandbox.window = sandbox;

vm.createContext(sandbox);
vm.runInContext(reportCode, sandbox);
vm.runInContext(appCode, sandbox);

// Manually trigger RAW_LEVEL0 setup
sandbox.RAW_LEVEL0 = sandbox.REPORT_DATA.level0 || [];
sandbox.RAW_LEVEL0.forEach(row => {
    if (!row.SubRegion || row.SubRegion === 'None' || row.SubRegion === 'null') {
        if (row.Region === 'Americas') {
            if (row.Forecast_Name === 'Social Media QuickSilver') row.SubRegion = 'Multiple AMER SubRegions';
            else row.SubRegion = 'NA';
        }
    }
});

sandbox.RAW_LEVEL1 = sandbox.rebuildLevel1(sandbox.RAW_LEVEL0);

const level1 = sandbox.RAW_LEVEL1;
const amerQueues = level1.filter(q => q.Region === 'Americas');
console.log('Total Americas queues in RAW_LEVEL1:', amerQueues.length);

const subregions = {};
amerQueues.forEach(q => {
    const sr = q.SubRegion;
    subregions[sr] = (subregions[sr] || 0) + 1;
});

console.log('\nAmericas SubRegions breakdown in RAW_LEVEL1:');
Object.keys(subregions).sort().forEach(sr => {
    console.log(`  - ${sr}: ${subregions[sr]} queues`);
});

const rollups = sandbox.computeHierarchyRollup(level1, 'SubRegion', {});
const amerSubRollups = rollups.filter(r => r.Region === 'Americas');
console.log('\nSubRegion Hierarchy Rollup under Americas:');
amerSubRollups.forEach(r => {
    console.log(`  - Node '${r.Node}': ${r.Total_Queues} Queues | ML Wins: ${r.Queue_Wins_ML} | Manual Wins: ${r.Queue_Wins_Manual} | Decision: ${r.Decision_State}`);
});
