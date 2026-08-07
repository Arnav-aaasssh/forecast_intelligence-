const fs = require('fs');
const content = fs.readFileSync('dashboard/data/report.js', 'utf-8');
const start = content.indexOf('window.REPORT_DATA = ') + 'window.REPORT_DATA = '.length;
let end = content.indexOf(';\nwindow.BACKEND_VOLUME_DATA');
if (end === -1) end = content.length;
const RAW_LEVEL0 = JSON.parse(content.substring(start, end)).level0 || [];

function updateDropdownVisibility(filters) {
    const gfIds = ['Region', 'SubRegion', 'Country', 'Offering', 'Fiscal_Week', 'Channel'];
    gfIds.forEach(col => {
        let validData = RAW_LEVEL0;
        Object.keys(filters).forEach(fCol => {
            if (fCol !== col && filters[fCol].length > 0) {
                validData = validData.filter(r => filters[fCol].includes(String(r[fCol])));
            }
        });
        const validVals = new Set(validData.map(r => String(r[col])));
        if (col === 'SubRegion') {
            console.log('SubRegion validVals:', Array.from(validVals));
            console.log('Has Brazil?', validVals.has('Brazil'));
        }
    });
}

updateDropdownVisibility({ Region: ['APJ'] });
