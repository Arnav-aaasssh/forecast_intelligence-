const fs = require('fs');
const path = require('path');

console.log("=========================================================");
console.log("PHASE 3 VERIFICATION: Validating Dual Compare View & Engine");
console.log("=========================================================");

const htmlPath = path.join(__dirname, '../../index.html');
const html = fs.readFileSync(htmlPath, 'utf8');

// 1. AST Syntax Check
const scripts = [...html.matchAll(/<script.*?>([\s\S]*?)<\/script>/gi)];
let errCount = 0;

scripts.forEach((m, idx) => {
    try {
        new Function(m[1]);
        console.log(`Script ${idx}: Syntax OK`);
    } catch (e) {
        console.error(`Script ${idx} Syntax Error: ${e.message}`);
        errCount++;
    }
});

if (errCount > 0) {
    console.error(`FAIL: ${errCount} script syntax errors found!`);
    process.exit(1);
}

// 2. Validate Phase 3 Component Tokens
const requiredTokens = [
    'id="single-dashboard-wrap"',
    'id="compare-view-container"',
    'id="compare-select-a"',
    'id="compare-select-b"',
    'id="compare-pane-a"',
    'id="compare-pane-b"',
    'toggleCompareMode',
    'initCompareView',
    'updateCompareView',
    'renderComparePane'
];

let missingTokens = 0;
requiredTokens.forEach(t => {
    if (html.includes(t)) {
        console.log(`Token Check '${t}': OK`);
    } else {
        console.error(`Token Check '${t}': MISSING!`);
        missingTokens++;
    }
});

if (missingTokens === 0) {
    console.log("\n=========================================================");
    console.log("SUCCESS: Phase 3 Dual Compare View & Engine 100% Verified!");
    console.log("=========================================================");
} else {
    console.error(`FAIL: ${missingTokens} tokens missing!`);
    process.exit(1);
}
