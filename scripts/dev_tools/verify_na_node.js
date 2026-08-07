const fs = require('fs');
const vm = require('vm');

const reportCode = fs.readFileSync('dashboard/data/report.js', 'utf8');
const appCode = fs.readFileSync('dashboard/js/dashboard2_app.js', 'utf8');

const listeners = {};
const createMock = () => ({ 
    addEventListener: () => {}, 
    style: {}, 
    classList: { add: () => {}, remove: () => {} }, 
    getAttribute: () => null,
    querySelector: () => createMock(),
    querySelectorAll: () => [],
    appendChild: () => {},
    insertBefore: () => {},
    cloneNode: () => createMock(),
    parentNode: { replaceChild: () => {}, insertBefore: () => {} },
    remove: () => {},
    dataset: {}
});

const sandbox = {
    window: {},
    document: {
        querySelectorAll: () => [],
        querySelector: () => createMock(),
        getElementById: () => createMock(),
        createElement: () => createMock(),
        addEventListener: (event, cb) => {
            listeners[event] = listeners[event] || [];
            listeners[event].push(cb);
        }
    },
    Chart: function() { return { destroy: () => {}, update: () => {} }; },
    localStorage: { setItem: () => {} },
    console: console
};
sandbox.window = sandbox;

vm.createContext(sandbox);
vm.runInContext(reportCode, sandbox);
vm.runInContext(appCode, sandbox);

// Trigger DOMContentLoaded
if (listeners['DOMContentLoaded']) {
    listeners['DOMContentLoaded'].forEach(cb => {
        try { cb(); } catch(e) { console.error('Error in DOMContentLoaded cb:', e); }
    });
}

const level1 = sandbox.RAW_LEVEL1 || [];
const amerQueues = level1.filter(q => q.Region === 'Americas');
console.log('\nTotal Americas queues in RAW_LEVEL1:', amerQueues.length);

const subregions = {};
amerQueues.forEach(q => {
    const sr = q.SubRegion;
    subregions[sr] = (subregions[sr] || 0) + 1;
});

console.log('\nAmericas SubRegions breakdown in RAW_LEVEL1:');
Object.keys(subregions).sort().forEach(sr => {
    console.log(`  - ${sr}: ${subregions[sr]} queues`);
});

// Check hierarchy rollup under Americas
if (typeof sandbox.computeHierarchyRollup === 'function') {
    const rollups = sandbox.computeHierarchyRollup(level1, 'SubRegion', {});
    const amerSubRollups = rollups.filter(r => r.Region === 'Americas');
    console.log('\nSubRegion Hierarchy Rollup under Americas:');
    amerSubRollups.forEach(r => {
        console.log(`  - Node '${r.Node}': ${r.Total_Queues} Queues | ML Wins: ${r.Queue_Wins_ML} | Manual Wins: ${r.Queue_Wins_Manual} | Decision: ${r.Decision_State}`);
    });
}
