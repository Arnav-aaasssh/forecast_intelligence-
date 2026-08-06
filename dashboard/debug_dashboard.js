const fs = require('fs');
const jsdom = require("jsdom");
const { JSDOM } = jsdom;

const html = fs.readFileSync('D:/project_1 imp docs/Forecast review/dashboard/index.html', 'utf8');
const dom = new JSDOM(html);
const window = dom.window;
const document = window.document;

global.window = window;
global.document = document;
global.navigator = window.navigator;
global.URL = { createObjectURL: () => '' };
global.Blob = class Blob {};
global.Chart = class Chart { constructor() { this.destroy = () => {}; } };

// Load data
const dataScript = fs.readFileSync('D:/project_1 imp docs/Forecast review/dashboard/data/report.js', 'utf8');
eval(dataScript);
global.REPORT_DATA = window.REPORT_DATA;

// Load app
const appScript = fs.readFileSync('D:/project_1 imp docs/Forecast review/dashboard/js/dashboard2_app.js', 'utf8');

try {
    eval(appScript);
    
    if (typeof init === 'function') {
        init();
    }
    
    // Simulate DOMContentLoaded
    const event = document.createEvent('Event');
    event.initEvent('DOMContentLoaded', true, true);
    document.dispatchEvent(event);
    
    const tbody = document.getElementById('sa-flat-table-body');
    console.log("Flat table row count:", tbody ? tbody.querySelectorAll('tr').length : "tbody not found");
    if (tbody && tbody.querySelectorAll('tr').length === 0) {
        console.log("RAW_LEVEL1 length:", RAW_LEVEL1.length);
        if (RAW_LEVEL1.length > 0) {
            console.log("First item in RAW_LEVEL1:", Object.keys(RAW_LEVEL1[0]).join(', '));
            console.log("Is renderQueueFlatTable called? Let's call it manually:");
            renderQueueFlatTable('Global', 'Global', {});
            console.log("Row count after manual call:", tbody.querySelectorAll('tr').length);
        }
    }
    
} catch (e) {
    console.error("CRASHED:", e);
}
