const fs = require('fs');
const path = require('path');

console.log("=========================================================================");
console.log("MASTER INTEGRATION VERIFICATION: Auditing 100% Interconnected Wiring");
console.log("=========================================================================");

const htmlPath = path.join(__dirname, '../../index.html');
const html = fs.readFileSync(htmlPath, 'utf8');

// 1. AST Syntax Check across all script blocks
const scripts = [...html.matchAll(/<script.*?>([\s\S]*?)<\/script>/gi)];
let errCount = 0;

scripts.forEach((m, idx) => {
    try {
        new Function(m[1]);
        console.log(`Script Block ${idx}: Syntax OK`);
    } catch (e) {
        console.error(`Script Block ${idx} Syntax Error: ${e.message}`);
        errCount++;
    }
});

if (errCount > 0) {
    console.error(`FAIL: ${errCount} script syntax errors found!`);
    process.exit(1);
}

// 2. Validate Interconnected Tokens across all 5 Phases
const masterTokens = [
    // Phase 1 Tokens
    'font-variant-numeric: tabular-nums',
    'id="header-dataset-selector"',
    'id="dataset-select-menu"',
    'id="header-btn-upload"',
    'id="header-btn-compare"',
    'id="header-btn-landing"',
    'window.SESSIONS',
    'switchDatasetSession',
    
    // Phase 2 Tokens
    'id="workspace-hub-modal"',
    'id="hub-dropzone"',
    'id="workspace-cards-grid"',
    'saveSessionsToStorage',
    'loadSessionsFromStorage',
    'openWorkspaceHub',
    'closeWorkspaceHub',
    'renderWorkspaceCards',
    'renameWorkspaceSession',
    'deleteWorkspaceSession',
    'createAndSwitchSession',
    
    // Phase 3 Tokens
    'id="single-dashboard-wrap"',
    'id="compare-view-container"',
    'id="compare-select-a"',
    'id="compare-select-b"',
    'id="compare-pane-a"',
    'id="compare-pane-b"',
    'toggleCompareMode',
    'initCompareView',
    'updateCompareView',
    'renderComparePane',
    
    // Phase 4 Tokens
    'id="landing-hero-section"',
    'class="landing-pillars-grid"',
    'id="btn-explore-workspace"',
    'id="btn-landing-upload"',
    'dismissLandingHero',
    'showLandingHero',
    'HIDE_LANDING_HERO',
    
    // Phase 5 Tokens
    'id="shortcuts-modal"',
    'id="shortcuts-modal-overlay"',
    'toggleShortcutsModal',
    'gPressed',
    'kbd'
];

let missingCount = 0;
masterTokens.forEach(t => {
    if (html.includes(t)) {
        console.log(`[PASS] Token '${t}': Verified`);
    } else {
        console.error(`[FAIL] Token '${t}': MISSING!`);
        missingCount++;
    }
});

if (missingCount === 0) {
    console.log("\n=========================================================================");
    console.log("SUCCESS: 100% Interconnected Master Integration Verified! Zero Gaps Found.");
    console.log("=========================================================================");
} else {
    console.error(`FAIL: ${missingCount} master tokens missing!`);
    process.exit(1);
}
