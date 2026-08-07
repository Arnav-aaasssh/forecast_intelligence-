const fs = require('fs');
const path = require('path');

console.log("=========================================================");
console.log("PHASE 1 VERIFICATION: Validating Application Shell & JS");
console.log("=========================================================");

const htmlPath = path.join(__dirname, '../../index.html');
const html = fs.readFileSync(htmlPath, 'utf8');

// 1. AST Syntax Check across all script tags
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

if (errCount === 0) {
    console.log("OK: 100% Zero Syntax Errors across all script blocks!");
} else {
    console.error(`FAIL: Found ${errCount} script errors!`);
    process.exit(1);
}

// 2. Validate Session Controller & Tokens Presence
const requiredTokens = [
    'font-variant-numeric: tabular-nums',
    'id="header-dataset-selector"',
    'id="dataset-select-menu"',
    'id="header-btn-upload"',
    'id="header-btn-compare"',
    'window.SESSIONS',
    'switchDatasetSession'
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
    console.log("SUCCESS: Phase 1 Application Shell 100% Verified!");
    console.log("=========================================================");
} else {
    console.error(`FAIL: ${missingTokens} tokens missing!`);
    process.exit(1);
}
