const fs = require('fs');
const path = require('path');
const { AssertionError } = require('assert');

// Mock DOM classes
class MockElement {
  constructor(id, tagName = 'div') {
    this.id = id;
    this.tagName = tagName;
    this._textContent = '';
    this._innerHTML = '';
    this._value = 'all'; // Default selector value is 'all'
    this.style = {};
    this.children = [];
    this.dataset = {};
    this.classList = {
      classes: new Set(),
      add: (c) => this.classList.classes.add(c),
      remove: (c) => this.classList.classes.delete(c),
      toggle: (c, force) => {
        if (force !== undefined) {
          if (force) this.classList.classes.add(c);
          else this.classList.classes.delete(c);
        } else {
          if (this.classList.classes.has(c)) this.classList.classes.delete(c);
          else this.classList.classes.add(c);
        }
      },
      contains: (c) => this.classList.classes.has(c)
    };
    this.listeners = {};
  }

  get textContent() {
    return this._textContent;
  }
  set textContent(val) {
    this._textContent = String(val);
  }

  get innerHTML() {
    return this._innerHTML;
  }
  set innerHTML(val) {
    this._innerHTML = String(val);
  }

  get value() {
    return this._value;
  }
  set value(val) {
    this._value = String(val);
  }

  appendChild(child) {
    this.children.push(child);
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

  getContext() {
    return {
      beginPath: () => {},
      arc: () => {},
      fill: () => {},
      stroke: () => {},
    };
  }
}

// Setup elements registry
const elements = {};
function getElement(id) {
  if (!elements[id]) {
    elements[id] = new MockElement(id);
  }
  return elements[id];
}

// Setup JSDOM/browser environment mocks
global.window = global;
global.performance = {
  now: () => Date.now()
};
global.requestAnimationFrame = (callback) => {
  setTimeout(() => callback(performance.now()), 0);
};

global.document = {
  addEventListener: (event, callback) => {
    if (!document.listeners[event]) document.listeners[event] = [];
    document.listeners[event].push(callback);
  },
  listeners: {},
  getElementById: (id) => getElement(id),
  createElement: (tagName) => new MockElement('', tagName),
  querySelectorAll: (selector) => {
    if (selector === '.rail-item') {
      return ['exec', 'q1', 'q2', 'q3', 'q4'].map(p => {
        const el = getElement('rail-' + p);
        el.dataset = { page: p };
        return el;
      });
    }
    if (selector === '.page') {
      return ['exec', 'q1', 'q2', 'q3', 'q4'].map(p => getElement('page-' + p));
    }
    if (selector === '.nav-card') {
      return ['q1', 'q2', 'q3', 'q4'].map(p => {
        const el = getElement('navcard-' + p);
        el.dataset = { nav: p };
        return el;
      });
    }
    if (selector === '#leaderboard-table th') {
      return ['rank', 'Model', 'CompositeScore', 'WAPE', 'Hit10', 'Bias', 'Stability', 'n_rows'].map(k => {
        const th = new MockElement('', 'th');
        th.dataset = { k };
        return th;
      });
    }
    return [];
  },
  querySelector: (selector) => {
    if (selector.startsWith('.rail-item[data-page=')) {
      const page = selector.match(/"([^"]+)"/)[1];
      return getElement('rail-' + page);
    }
    return getElement(selector);
  }
};

global.fetch = async (url) => {
  if (url === 'data/report.json') {
    const reportPath = path.resolve(__dirname, '../data/report.json');
    const content = fs.readFileSync(reportPath, 'utf8');
    return {
      json: async () => JSON.parse(content)
    };
  }
  throw new Error(`Unknown fetch URL: ${url}`);
};

global.Chart = class MockChart {
  constructor(el, cfg) {
    this.el = el;
    this.cfg = cfg;
  }
  destroy() {}
};
global.Chart.defaults = {
  font: { family: '', size: 11 },
  color: ''
};

// Capture console errors
const consoleErrors = [];
const originalConsoleError = console.error;
console.error = (...args) => {
  consoleErrors.push(args.join(' '));
  originalConsoleError(...args);
};

// Main test function
async function runTests() {
  console.log("Loading app.js...");
  const appPath = path.resolve(__dirname, 'app.js');
  let appContent = fs.readFileSync(appPath, 'utf8');

  // Inject helper hooks before evaluating app.js to expose internal renderDashboard variables/functions
  // We locate the closing brace of renderDashboard (the very last closing brace in the file)
  const lastBraceIndex = appContent.lastIndexOf('}');
  if (lastBraceIndex === -1) {
    throw new Error("Could not find closing brace in app.js");
  }
  
  const injectCode = `
  globalThis.getFilteredQ1Series = getFilteredQ1Series;
  globalThis.renderQ2 = renderQ2;
  globalThis.updateFilterPills = updateFilterPills;
  globalThis.updateDynamicTexts = updateDynamicTexts;
  globalThis.onFilterChange = onFilterChange;
`;
  appContent = appContent.substring(0, lastBraceIndex) + injectCode + appContent.substring(lastBraceIndex);

  // Evaluate the script (acts as runtime verification of syntax and execution)
  try {
    eval(appContent);
    console.log("PASS: app.js loaded and parsed successfully without syntax errors.");
  } catch (err) {
    console.error("FAIL: app.js failed to load/parse:", err);
    process.exit(1);
  }

  // Trigger DOMContentLoaded
  console.log("Simulating DOMContentLoaded event...");
  if (document.listeners['DOMContentLoaded']) {
    for (const callback of document.listeners['DOMContentLoaded']) {
      await callback();
    }
  }
  
  // Verify no console errors occurred during parsing/fetch override
  if (consoleErrors.length > 0) {
    console.error(`FAIL: Console errors detected:`, consoleErrors);
    process.exit(1);
  } else {
    console.log("PASS: No console errors during script initialization.");
  }

  // Assertions for filter logic
  const originalSeries = getFilteredQ1Series().series;
  const originalSeriesLength = originalSeries.length;
  const originalBiasLength = getFilteredQ1Series().biasSeries.length;
  console.log(`Original dataset has ${originalSeriesLength} weeks and ${originalBiasLength} bias entries.`);

  // Test 1: getFilteredQ1Series with active filters
  console.log("Test 1: Sub-Region Filter (ANZ)...");
  getElement('filter-subregion').value = 'ANZ';
  onFilterChange();
  const anzFiltered = getFilteredQ1Series();
  console.log(`ANZ filtered length: ${anzFiltered.series.length} weeks.`);
  
  // Assert ANZ has different values than original series for WAPE
  let isDifferent = false;
  for (let i = 0; i < originalSeriesLength; i++) {
    if (anzFiltered.series[i].manual_wape !== originalSeries[i].manual_wape) {
      isDifferent = true;
      break;
    }
  }
  if (!isDifferent) {
    throw new Error("ANZ filtering failed: WAPE values are identical to the global population.");
  }
  console.log("PASS: Sub-Region filtering yields a correct filtered subset.");

  // Reset and verify state
  console.log("Resetting filters...");
  getElement('filter-subregion').value = 'all';
  onFilterChange();
  if (getFilteredQ1Series().series.length !== originalSeriesLength) {
    throw new Error("Resetting filter failed to return dataset to original state.");
  }
  console.log("PASS: Reset returns dataset to original state.");

  // Test 2: Channel Filter (Voice)
  console.log("Test 2: Channel Filter (Voice)...");
  getElement('filter-channel').value = 'Voice';
  onFilterChange();
  const voiceFiltered = getFilteredQ1Series();
  console.log(`Voice filtered: ${voiceFiltered.series.length} weeks.`);
  if (voiceFiltered.series.length === 0) {
    throw new Error(`Voice filtering returned empty series.`);
  }

  // Reset
  getElement('filter-channel').value = 'all';
  onFilterChange();

  // Test 3: Fiscal Year Filter (2027)
  console.log("Test 3: Fiscal Year Filter (2027)...");
  getElement('filter-fiscalyear').value = '2027';
  onFilterChange();
  const fy2027Filtered = getFilteredQ1Series();
  console.log(`FY2027 filtered: ${fy2027Filtered.series.length} weeks, bias entries: ${fy2027Filtered.biasSeries.length}.`);
  if (fy2027Filtered.series.length === 0 || fy2027Filtered.biasSeries.length === 0) {
    throw new Error("FY2027 filtering returned empty series/biasSeries.");
  }
  // Check date prefix: All weeks in fy2027Filtered must start with "2027-" (or be part of the 2027 fiscal year)
  for (const d of fy2027Filtered.biasSeries) {
    if (!d.week.startsWith('2027-') && !d.week.startsWith('2028-01')) { // 2027 FY contains 2027 weeks and early 2028 weeks
      throw new Error(`Fiscal Year 2027 filter contained week from another year prefix: ${d.week}`);
    }
  }
  console.log("PASS: biasSeries is appropriately filtered by selected Fiscal Year weeks.");

  // Reset
  getElement('filter-fiscalyear').value = 'all';
  onFilterChange();

  // Test 4: Combined Filter (ANZ + Voice + 2027)
  console.log("Test 4: Combined Filter (ANZ + Voice + 2027)...");
  getElement('filter-subregion').value = 'ANZ';
  getElement('filter-channel').value = 'Voice';
  getElement('filter-fiscalyear').value = '2027';
  onFilterChange();
  const combinedFiltered = getFilteredQ1Series();
  console.log(`Combined filtered: ${combinedFiltered.series.length} weeks, bias entries: ${combinedFiltered.biasSeries.length}.`);
  if (combinedFiltered.series.length === 0) {
    throw new Error("Combined filter (ANZ + Voice + 2027) returned empty series.");
  }

  // Verify elements updated (like filter pills, text metrics)
  const pillsEl = getElement('filter-pills');
  console.log("Current filter pills innerHTML:", pillsEl.innerHTML);
  if (!pillsEl.innerHTML.includes('ANZ') || !pillsEl.innerHTML.includes('FY2027') || !pillsEl.innerHTML.includes('Voice')) {
    throw new Error("Filter pills failed to display active combined filters.");
  }
  console.log("PASS: Combined filter pills are correctly rendered.");

  // Test 5: Reset button click
  console.log("Test 5: Resetting all filters using reset button simulator...");
  const resetBtn = getElement('filter-reset');
  if (resetBtn.listeners['click']) {
    for (const cb of resetBtn.listeners['click']) {
      cb();
    }
  }
  const resetFiltered = getFilteredQ1Series();
  if (resetFiltered.series.length !== originalSeriesLength) {
    throw new Error(`Reset button failed to restore original state. Length: ${resetFiltered.series.length} instead of ${originalSeriesLength}`);
  }
  console.log("PASS: Reset button restores original state.");

  console.log("\nALL FRONTEND RUNTIME VERIFICATION TESTS PASSED SUCCESSFULLY!");
  process.exit(0);
}

runTests().catch(err => {
  console.error("FAIL: Test execution error:", err);
  process.exit(1);
});
