const fs = require('fs');
const path = require('path');
const vm = require('vm');

// 1. Load data
const reportPath = path.join(__dirname, '../../dashboard/data/report.json');
const reportData = JSON.parse(fs.readFileSync(reportPath, 'utf8'));

const appJsPath = path.join(__dirname, '../../dashboard/js/app.js');
const appJsCode = fs.readFileSync(appJsPath, 'utf8');

// Console capture
const consoleErrors = [];
const consoleLogs = [];
const customConsole = {
  log: (...args) => consoleLogs.push(args.join(' ')),
  error: (...args) => consoleErrors.push(args.join(' ')),
  warn: (...args) => consoleLogs.push('[WARN] ' + args.join(' ')),
  info: (...args) => consoleLogs.push('[INFO] ' + args.join(' '))
};

// 2. Setup mock DOM
class MockElement {
  constructor(id = '', tagName = 'div') {
    this.id = id;
    this.tagName = tagName.toUpperCase();
    this.textContent = '';
    this.innerHTML = '';
    this._value = 'all';
    this.classList = {
      classes: new Set(),
      add: (c) => this.classList.classes.add(c),
      remove: (c) => this.classList.classes.delete(c),
      toggle: (c, cond) => {
        if (cond === undefined) {
          if (this.classList.classes.has(c)) this.classList.classes.delete(c);
          else this.classList.classes.add(c);
        } else if (cond) {
          this.classList.classes.add(c);
        } else {
          this.classList.classes.delete(c);
        }
      },
      contains: (c) => this.classList.classes.has(c)
    };
    this.dataset = {};
    this.children = [];
    this.listeners = {};
    this.style = {};
  }

  get value() {
    return this._value;
  }
  set value(v) {
    this._value = v;
  }

  appendChild(child) {
    this.children.push(child);
    return child;
  }

  addEventListener(event, callback) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(callback);
  }

  trigger(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(cb => cb(data));
    }
  }
}

const elements = {};
const getElementById = (id) => {
  if (!elements[id]) {
    elements[id] = new MockElement(id);
  }
  return elements[id];
};

const createElement = (tagName) => {
  return new MockElement('', tagName);
};

const railItems = ['exec', 'q1', 'q2', 'q3', 'q4'].map(page => {
  const el = new MockElement('', 'div');
  el.classList.add('rail-item');
  el.dataset.page = page;
  return el;
});

const pages = ['exec', 'q1', 'q2', 'q3', 'q4'].map(page => {
  const el = getElementById('page-' + page);
  el.classList.add('page');
  return el;
});

const navCards = ['q1', 'q2', 'q3', 'q4'].map(nav => {
  const el = new MockElement('', 'div');
  el.classList.add('nav-card');
  el.dataset.nav = nav;
  return el;
});

const ths = ['rank', 'Model', 'CompositeScore', 'WAPE', 'Hit10', 'Bias', 'Stability', 'n_rows'].map(k => {
  const el = new MockElement('', 'th');
  el.dataset.k = k;
  return el;
});

const querySelectorAll = (selector) => {
  if (selector === '.rail-item') return railItems;
  if (selector === '.page') return pages;
  if (selector === '.nav-card') return navCards;
  if (selector === '#leaderboard-table th') return ths;
  return [];
};

const querySelector = (selector) => {
  const railMatch = selector.match(/\.rail-item\[data-page="([^"]+)"\]/);
  if (railMatch) {
    const page = railMatch[1];
    return railItems.find(item => item.dataset.page === page);
  }
  return null;
};

const docListeners = {};
const documentMock = {
  getElementById,
  querySelectorAll,
  querySelector,
  createElement,
  addEventListener: (event, cb) => {
    if (!docListeners[event]) docListeners[event] = [];
    docListeners[event].push(cb);
  },
  trigger: async (event, data) => {
    if (docListeners[event]) {
      for (const cb of docListeners[event]) {
        await cb(data);
      }
    }
  }
};

const windowMock = {
  scrollTo: () => {},
  document: documentMock
};

let simulatedTime = 0;
const performanceMock = {
  now: () => {
    simulatedTime += 50;
    return simulatedTime;
  }
};

const requestAnimationFrameMock = (cb) => {
  simulatedTime += 200;
  cb(simulatedTime);
};

const fetchMock = (url) => {
  return Promise.resolve({
    json: () => Promise.resolve(reportData)
  });
};

const ChartMock = function(canvasId, config) {
  this.canvasId = canvasId;
  this.config = config;
  this.destroy = () => {};
};
ChartMock.defaults = { font: {}, color: '' };

// Create vm context sandbox
const sandbox = {
  console: customConsole,
  document: documentMock,
  window: windowMock,
  performance: performanceMock,
  requestAnimationFrame: requestAnimationFrameMock,
  fetch: fetchMock,
  Chart: ChartMock,
  DATA: null, // will be initialized by app.js
  setTimeout: setTimeout,
  clearTimeout: clearTimeout,
  setInterval: setInterval,
  clearInterval: clearInterval
};

const context = vm.createContext(sandbox);

console.log('--- STARTING VERIFICATION ---');

// Expose internal functions in-memory by modifying code before running
const modifiedCode = appJsCode.trim().replace(/\}$/, `
  globalThis.DATA = DATA;
  globalThis.getFilteredQ1Series = getFilteredQ1Series;
  globalThis.renderQ2 = renderQ2;
  globalThis.updateFilterPills = updateFilterPills;
  globalThis.updateDynamicTexts = updateDynamicTexts;
  globalThis.onFilterChange = onFilterChange;
}`);

// 1. Parsing & syntax verification
try {
  vm.runInNewContext(modifiedCode, context, { filename: 'app.js' });
  console.log('[PASS] Parse verification: Script parsed without syntax errors.');
} catch (err) {
  console.error('[FAIL] Parse verification: Syntax or early runtime error:', err);
  process.exit(1);
}

// 2. DOMContentLoaded execution
async function run() {
  try {
    await documentMock.trigger('DOMContentLoaded');
    console.log('[PASS] DOMContentLoaded trigger: Successfully fetched and patched report.json.');
  } catch (err) {
    console.error('[FAIL] DOMContentLoaded execution failed:', err);
    process.exit(1);
  }

  // Verify console errors during parsing/patching
  if (consoleErrors.length > 0) {
    console.log('[FAIL] Console errors captured:', consoleErrors);
  } else {
    console.log('[PASS] No console errors reported during script load/DOMContentLoaded.');
  }

  // 3. Test filter combinations in getFilteredQ1Series
  console.log('\n--- TESTING getFilteredQ1Series() ---');
  
  const getFilteredQ1Series = sandbox.getFilteredQ1Series;
  const DATA = sandbox.DATA;

  if (typeof getFilteredQ1Series !== 'function') {
    console.error('[FAIL] getFilteredQ1Series is still not a function or not exposed!');
    process.exit(1);
  }

  // Initial state check
  const original = getFilteredQ1Series();
  console.log(`Original Series length: ${original.series.length} (Expected: 99)`);
  console.log(`Original BiasSeries length: ${original.biasSeries.length} (Expected: 99)`);
  
  // A. Sub-Region ANZ
  getElementById('filter-subregion').value = 'ANZ';
  getElementById('filter-fiscalyear').value = 'all';
  getElementById('filter-channel').value = 'all';
  
  let result = getFilteredQ1Series();
  console.log(`Filter [Sub-Region=ANZ]: series length = ${result.series.length}, bias length = ${result.biasSeries.length}`);
  
  // Verify ANZ weeks match
  const anzExpectedWeeks = DATA.q1.slices_subregion['ANZ'].map(d => d.week);
  const resultWeeks = result.series.map(d => d.week);
  let allMatch = resultWeeks.every((w, idx) => w === anzExpectedWeeks[idx]);
  console.log(`Filter [Sub-Region=ANZ] match validation: ${allMatch ? 'PASS' : 'FAIL'}`);

  // B. Channel Voice
  getElementById('filter-subregion').value = 'all';
  getElementById('filter-channel').value = 'Voice';
  getElementById('filter-fiscalyear').value = 'all';
  result = getFilteredQ1Series();
  console.log(`Filter [Channel=Voice]: series length = ${result.series.length}, bias length = ${result.biasSeries.length}`);
  const voiceExpectedWeeks = DATA.q1.slices_channel['Voice'].map(d => d.week);
  allMatch = result.series.map(d => d.week).every((w, idx) => w === voiceExpectedWeeks[idx]);
  console.log(`Filter [Channel=Voice] match validation: ${allMatch ? 'PASS' : 'FAIL'}`);

  // C. Combined filters: Sub-Region=ANZ, Channel=Voice
  getElementById('filter-subregion').value = 'ANZ';
  getElementById('filter-channel').value = 'Voice';
  getElementById('filter-fiscalyear').value = 'all';
  result = getFilteredQ1Series();
  console.log(`Filter [Sub-Region=ANZ, Channel=Voice]: series length = ${result.series.length}`);
  
  // Check the math of combining Sub-Region + Channel:
  // manual_wape should be (ANZ.manual_wape + Voice.manual_wape) / 2
  const anzMap = new Map(DATA.q1.slices_subregion['ANZ'].map(d => [d.week, d]));
  const voiceMap = new Map(DATA.q1.slices_channel['Voice'].map(d => [d.week, d]));
  
  let mathMatch = true;
  for (let i = 0; i < Math.min(result.series.length, 5); i++) {
    const entry = result.series[i];
    const anzVal = anzMap.get(entry.week).manual_wape;
    const voiceVal = voiceMap.get(entry.week).manual_wape;
    const expectedAvg = (anzVal + voiceVal) / 2;
    if (Math.abs(entry.manual_wape - expectedAvg) > 1e-7) {
      mathMatch = false;
      console.log(`Math Mismatch at week ${entry.week}: Got ${entry.manual_wape}, Expected ${expectedAvg}`);
    }
  }
  console.log(`Filter Combination Math (Average) validation: ${mathMatch ? 'PASS' : 'FAIL'}`);

  // D. Combined filters with Fiscal Year: Sub-Region=ANZ, Channel=Voice, Fiscal Year=2027
  getElementById('filter-subregion').value = 'ANZ';
  getElementById('filter-channel').value = 'Voice';
  getElementById('filter-fiscalyear').value = '2027';
  result = getFilteredQ1Series();
  console.log(`Filter [Sub-Region=ANZ, Channel=Voice, FY=2027]: series length = ${result.series.length}, bias length = ${result.biasSeries.length}`);
  
  // Verify that all returned weeks belong to FY2027
  const fy2027Weeks = new Set(DATA.q1.slices_fiscalyear['2027'].map(d => d.week));
  const allInFY2027 = result.series.every(d => fy2027Weeks.has(d.week)) && result.biasSeries.every(d => fy2027Weeks.has(d.week));
  console.log(`Filter [FY=2027] weeks validation: ${allInFY2027 ? 'PASS' : 'FAIL'}`);

  // 4. Assert biasSeries is filtered appropriately by date prefix based on Fiscal Year
  console.log('\n--- TESTING Fiscal Year Date Prefix Filtering for biasSeries ---');
  
  // Let's check FY2027
  getElementById('filter-subregion').value = 'all';
  getElementById('filter-channel').value = 'all';
  getElementById('filter-fiscalyear').value = '2027';
  let fyResult = getFilteredQ1Series();
  
  // We expect FY2027 dates to span from 2026-03-13 to 2027-01-29. Let's assert that all start with "2026-" or "2027-01-".
  let fy2027PrefixCorrect = fyResult.biasSeries.every(d => {
    const is2026 = d.week.startsWith('2026-');
    const isJan2027 = d.week.startsWith('2027-01-');
    return is2026 || isJan2027;
  });
  console.log(`FY2027 BiasSeries weeks date prefix check (should only contain 2026 or Jan 2027): ${fy2027PrefixCorrect ? 'PASS' : 'FAIL'}`);

  // Let's check FY2028
  getElementById('filter-fiscalyear').value = '2028';
  fyResult = getFilteredQ1Series();
  
  // We expect FY2028 dates to span from 2027-02-05 to 2028-01-28. Let's assert that all start with "2027-" (except 2028-01-).
  let fy2028PrefixCorrect = fyResult.biasSeries.every(d => {
    const is2027 = d.week.startsWith('2027-');
    const isJan2028 = d.week.startsWith('2028-01-');
    return is2027 || isJan2028;
  });
  console.log(`FY2028 BiasSeries weeks date prefix check (should only contain 2027 or Jan 2028): ${fy2028PrefixCorrect ? 'PASS' : 'FAIL'}`);

  // 5. Verify resetting the filters returns the dataset back to its original state
  console.log('\n--- TESTING Reset Filters ---');
  
  // Apply filters first
  getElementById('filter-subregion').value = 'ANZ';
  getElementById('filter-channel').value = 'Voice';
  getElementById('filter-fiscalyear').value = '2027';
  
  // Call reset trigger (which mocks reset button click)
  const resetBtn = getElementById('filter-reset');
  let isResetSuccess = false;
  if (resetBtn.listeners['click']) {
    resetBtn.trigger('click');
    
    // Assert selectors value reset to 'all'
    const srVal = getElementById('filter-subregion').value;
    const fyVal = getElementById('filter-fiscalyear').value;
    const chVal = getElementById('filter-channel').value;
    
    const resetResult = getFilteredQ1Series();
    
    console.log(`Reset result: Sub-Region = ${srVal}, FY = ${fyVal}, Channel = ${chVal}`);
    console.log(`Reset Series length = ${resetResult.series.length} (Expected: 99)`);
    console.log(`Reset BiasSeries length = ${resetResult.biasSeries.length} (Expected: 99)`);
    
    isResetSuccess = (srVal === 'all' && fyVal === 'all' && chVal === 'all' && 
                      resetResult.series.length === 99 && resetResult.biasSeries.length === 99);
    console.log(`Reset Validation: ${isResetSuccess ? 'PASS' : 'FAIL'}`);
  } else {
    console.log('[FAIL] Reset button click listener not registered.');
  }

  // 6. Test other render and update functions
  console.log('\n--- TESTING OTHER APP FUNCTIONS ---');
  
  // Test renderQ2
  let renderQ2Success = false;
  try {
    sandbox.renderQ2('ANZ', '2027', 'All');
    console.log('[PASS] renderQ2 runs successfully without throwing exceptions.');
    renderQ2Success = true;
  } catch (err) {
    console.error('[FAIL] renderQ2 failed:', err);
  }

  // Test updateFilterPills
  let updateFilterPillsSuccess = false;
  try {
    sandbox.updateFilterPills();
    console.log('[PASS] updateFilterPills runs successfully without throwing exceptions.');
    console.log(`Pills InnerHTML: ${getElementById('filter-pills').innerHTML}`);
    updateFilterPillsSuccess = true;
  } catch (err) {
    console.error('[FAIL] updateFilterPills failed:', err);
  }

  // Test updateDynamicTexts (corresponds to updateTextMetrics)
  let updateDynamicTextsSuccess = false;
  try {
    sandbox.updateDynamicTexts();
    console.log('[PASS] updateDynamicTexts runs successfully without throwing exceptions.');
    updateDynamicTextsSuccess = true;
  } catch (err) {
    console.error('[FAIL] updateDynamicTexts failed:', err);
  }

  // Let's summarize the overall verdict
  console.log('\n--- VERIFICATION VERDICT ---');
  const allTestsPassed = 
    consoleErrors.length === 0 &&
    allMatch &&
    mathMatch &&
    allInFY2027 &&
    fy2027PrefixCorrect &&
    fy2028PrefixCorrect &&
    isResetSuccess &&
    renderQ2Success &&
    updateFilterPillsSuccess &&
    updateDynamicTextsSuccess;
  
  if (allTestsPassed) {
    console.log('Verdict: PASS');
  } else {
    console.log('Verdict: FAIL');
  }
}

run();
