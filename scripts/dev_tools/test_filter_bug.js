const fs = require('fs');
const vm = require('vm');

const reportCode = fs.readFileSync('dashboard/data/report.js', 'utf8');
const appCode = fs.readFileSync('dashboard/js/dashboard2_app.js', 'utf8');

function createDomElement(tagName) {
    const el = {
        tagName: tagName ? tagName.toUpperCase() : 'DIV',
        children: [],
        style: {},
        classList: {
            contains: (cls) => el._classes ? el._classes.includes(cls) : false,
            add: (cls) => { el._classes = el._classes || []; if(!el._classes.includes(cls)) el._classes.push(cls); },
            remove: (cls) => { if(el._classes) el._classes = el._classes.filter(c => c !== cls); }
        },
        dataset: {},
        _innerHTML: '',
        value: '',
        checked: false,
        listeners: {},
        remove: () => {},
        insertBefore: () => {},
        cloneNode: () => createDomElement(tagName),
        parentNode: { replaceChild: () => {}, insertBefore: () => {} },
        addEventListener: (evt, cb) => {
            el.listeners[evt] = el.listeners[evt] || [];
            el.listeners[evt].push(cb);
        },
        getAttribute: () => 'exec',
        querySelector: (sel) => el.querySelectorAll(sel)[0] || null,
        querySelectorAll: (sel) => {
            let res = [];
            el.children.forEach(c => {
                let match = false;
                if (sel === 'input[type="checkbox"]' && c.tagName === 'INPUT' && c.type === 'checkbox') match = true;
                else if (sel === 'input[type="text"]' && c.tagName === 'INPUT' && c.type === 'text') match = true;
                else if (sel === 'input' && c.tagName === 'INPUT') match = true;
                else if (sel === '.custom-select-option' && c.classList.contains('custom-select-option')) match = true;
                else if (sel === '.custom-select-options' && c.classList.contains('custom-select-options')) match = true;
                else if (sel === '.custom-select-btn' && c.classList.contains('custom-select-btn')) match = true;
                else if (sel === '.custom-select-menu' && c.classList.contains('custom-select-menu')) match = true;
                else if (sel === '.action-select-all' && c.classList.contains('action-select-all')) match = true;
                else if (sel === '.action-clear-all' && c.classList.contains('action-clear-all')) match = true;
                else if (sel === '.btn-text' && c.classList.contains('btn-text')) match = true;
                else if (sel === 'span' && c.tagName === 'SPAN') match = true;
                
                if (match) res.push(c);
                res = res.concat(c.querySelectorAll(sel));
            });
            return res;
        },
        appendChild: (child) => {
            el.children.push(child);
            child.parentNode = el;
            return child;
        },
        contains: (target) => {
            if (el === target) return true;
            return el.children.some(c => c.contains ? c.contains(target) : false);
        },
        focus: () => {}
    };

    Object.defineProperty(el, 'innerHTML', {
        get: () => el._innerHTML || '',
        set: (html) => {
            el._innerHTML = html;
            el.children = [];
            if (!html) return;
            
            // Add btn
            const btn = createDomElement('BUTTON'); btn.classList.add('custom-select-btn');
            const sp = createDomElement('SPAN'); sp.classList.add('btn-text');
            btn.appendChild(sp);
            el.appendChild(btn);

            // Add menu
            const menu = createDomElement('DIV'); menu.classList.add('custom-select-menu');
            
            const searchDiv = createDomElement('DIV');
            searchDiv.classList.add('custom-select-search');
            const inp = createDomElement('INPUT'); inp.type = 'text';
            searchDiv.appendChild(inp);
            menu.appendChild(searchDiv);

            const actDiv = createDomElement('DIV');
            actDiv.classList.add('custom-select-actions');
            const sa = createDomElement('SPAN'); sa.classList.add('action-select-all');
            const ca = createDomElement('SPAN'); ca.classList.add('action-clear-all');
            actDiv.appendChild(sa); actDiv.appendChild(ca);
            menu.appendChild(actDiv);

            const optionsDiv = createDomElement('DIV');
            optionsDiv.classList.add('custom-select-options');
            
            const optionMatches = html.match(/<label class="custom-select-option">[\s\S]*?<\/label>/gi);
            if (optionMatches) {
                optionMatches.forEach(optHtml => {
                    const optLabel = createDomElement('LABEL');
                    optLabel.classList.add('custom-select-option');
                    
                    const valMatch = optHtml.match(/value="([^"]+)"/);
                    const val = valMatch ? valMatch[1] : '';
                    const textMatch = optHtml.match(/<span>([^<]+)<\/span>/);
                    const txt = textMatch ? textMatch[1] : '';
                    
                    const inputCb = createDomElement('INPUT');
                    inputCb.type = 'checkbox';
                    inputCb.value = val;
                    
                    const spanTxt = createDomElement('SPAN');
                    spanTxt.innerHTML = txt;

                    optLabel.appendChild(inputCb);
                    optLabel.appendChild(spanTxt);
                    optionsDiv.appendChild(optLabel);
                });
            }
            menu.appendChild(optionsDiv);
            el.appendChild(menu);
        }
    });

    return el;
}

const elementsMap = {};
const gfIds = ['region', 'subregion', 'country', 'offering', 'fiscal_week', 'channel', 'classification'];
gfIds.forEach(id => {
    elementsMap['gf-' + id + '-container'] = createDomElement('DIV');
});

const activeTabMock = createDomElement('DIV');
activeTabMock.classList.add('rail-item');
activeTabMock.classList.add('active');

const headMock = createDomElement('HEAD');

const sandbox = {
    window: {},
    document: {
        head: headMock,
        querySelectorAll: (sel) => {
            if (sel === '.custom-select-menu') {
                return Object.values(elementsMap).map(e => e.querySelector('.custom-select-menu')).filter(Boolean);
            }
            return [];
        },
        querySelector: (sel) => {
            if (sel === '.rail-item.active') return activeTabMock;
            return createDomElement('DIV');
        },
        getElementById: (id) => elementsMap[id] || createDomElement('DIV'),
        createElement: (tag) => createDomElement(tag),
        addEventListener: () => {}
    },
    Chart: function() { return { destroy: () => {}, update: () => {} }; },
    jsVectorMap: function() { return { destroy: () => {} }; },
    setTimeout: (cb) => cb(),
    clearTimeout: () => {},
    localStorage: { setItem: () => {} },
    console: console
};
sandbox.window = sandbox;

vm.createContext(sandbox);
vm.runInContext(reportCode, sandbox);
vm.runInContext(appCode, sandbox);

// Setup RAW_LEVEL0
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
sandbox.ORIGINAL_RAW_LEVEL1 = [...sandbox.RAW_LEVEL1];

// Run populateGlobalFilters
sandbox.populateGlobalFilters();

console.log('--- Global Filters Populated ---');

const regionContainer = elementsMap['gf-region-container'];
const subregionContainer = elementsMap['gf-subregion-container'];
const countryContainer = elementsMap['gf-country-container'];

const regionCbs = regionContainer.querySelectorAll('input[type="checkbox"]');
const subregionCbs = subregionContainer.querySelectorAll('input[type="checkbox"]');

console.log('Region Options Count:', regionCbs.length, regionCbs.map(c => c.value));
console.log('SubRegion Options Count:', subregionCbs.length, subregionCbs.map(c => c.value));

// Step 1: Check APJ in Region
const apjCb = regionCbs.find(cb => cb.value === 'APJ');
if (apjCb) apjCb.checked = true;

// Step 2: Check ANZ in SubRegion
const anzCb = subregionCbs.find(cb => cb.value === 'ANZ');
if (anzCb) anzCb.checked = true;

// Run applyAllFilters
sandbox.applyAllFilters();

console.log('\n--- After Selecting APJ & ANZ ---');
const subOptsAfterApj = subregionContainer.querySelectorAll('.custom-select-option');
console.log('Visible SubRegion options under APJ:', subOptsAfterApj.filter(o => o.style.display !== 'none').map(o => o.querySelector('span').innerHTML));

// Step 3: Now change Region from APJ to Americas!
if (apjCb) apjCb.checked = false;
const amerCb = regionCbs.find(cb => cb.value === 'Americas');
if (amerCb) amerCb.checked = true;

// Run applyAllFilters
sandbox.applyAllFilters();

console.log('\n--- After Changing Region to Americas (while ANZ remains checked in DOM) ---');
const subOptsAfterAmer = subregionContainer.querySelectorAll('.custom-select-option');
console.log('Visible SubRegion options under Americas:', subOptsAfterAmer.filter(o => o.style.display !== 'none').map(o => o.querySelector('span').innerHTML));

const countryOptsAfterAmer = countryContainer.querySelectorAll('.custom-select-option');
const visibleCountryAfterAmer = countryOptsAfterAmer.filter(opt => opt.style.display !== 'none');
console.log('Visible Country options under Americas + STALE ANZ:', visibleCountryAfterAmer.map(o => o.querySelector('span').innerHTML));
