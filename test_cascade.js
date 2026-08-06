const fs = require('fs');

let js = fs.readFileSync('dashboard/js/dashboard2_app.js', 'utf-8');

const cascadeFunc = `
function updateDropdownVisibility(filters) {
    const gfIds = ['Region', 'SubRegion', 'Country', 'Offering', 'Fiscal_Week', 'Channel'];
    gfIds.forEach(col => {
        const id = 'gf-' + col.toLowerCase() + '-container';
        const container = document.getElementById(id);
        if (!container) return;
        
        // Find valid values for this column based on ALL OTHER active filters
        let validData = RAW_LEVEL0;
        Object.keys(filters).forEach(fCol => {
            if (fCol !== col && filters[fCol].length > 0) {
                validData = validData.filter(r => filters[fCol].includes(String(r[fCol])));
            }
        });
        const validVals = new Set(validData.map(r => String(r[col])));
        
        const optionsContainer = container.querySelector('.custom-select-options');
        const searchInput = container.querySelector('input[type="text"]');
        const searchVal = searchInput ? searchInput.value.toLowerCase() : '';
        
        if (optionsContainer) {
            optionsContainer.querySelectorAll('.custom-select-option').forEach(opt => {
                const cb = opt.querySelector('input');
                const txt = opt.querySelector('span').textContent.toLowerCase();
                const matchesSearch = searchVal === '' || txt.includes(searchVal);
                const matchesCascade = validVals.has(String(cb.value));
                
                if (matchesSearch && matchesCascade) {
                    opt.style.display = 'flex';
                } else {
                    opt.style.display = 'none';
                }
                opt.dataset.cascadeHidden = matchesCascade ? "false" : "true";
            });
        }
    });
}
`;

if (!js.includes('function updateDropdownVisibility')) {
    js = js.replace('function applyAllFilters() {', cascadeFunc + '\nfunction applyAllFilters() {');
}
if (!js.includes('updateDropdownVisibility(filters);')) {
    js = js.replace('updateScope(currentNode, currentLevel, filters);', 'updateScope(currentNode, currentLevel, filters);\n    updateDropdownVisibility(filters);');
}

// Also update the search listener in populateGlobalFilters to respect cascadeHidden
const oldSearchListener = `        searchInput.addEventListener('input', (e) => {
            const val = e.target.value.toLowerCase();
            optionsContainer.querySelectorAll('.custom-select-option').forEach(opt => {
                const txt = opt.querySelector('span').textContent.toLowerCase();
                opt.style.display = txt.includes(val) ? 'flex' : 'none';
            });
        });`;
const newSearchListener = `        searchInput.addEventListener('input', (e) => {
            const val = e.target.value.toLowerCase();
            optionsContainer.querySelectorAll('.custom-select-option').forEach(opt => {
                const txt = opt.querySelector('span').textContent.toLowerCase();
                const matchesSearch = val === '' || txt.includes(val);
                const isCascadeHidden = opt.dataset.cascadeHidden === "true";
                if (matchesSearch && !isCascadeHidden) {
                    opt.style.display = 'flex';
                } else {
                    opt.style.display = 'none';
                }
            });
        });`;
if (js.includes(oldSearchListener)) {
    js = js.replace(oldSearchListener, newSearchListener);
}

fs.writeFileSync('dashboard/js/dashboard2_app.js', js, 'utf-8');
console.log("Updated dashboard2_app.js with cascading filter logic");
