const fs = require('fs');
const html = fs.readFileSync('dashboard/index.html', 'utf8');
const jsMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!jsMatch) {
  console.log("NO JS FOUND");
  process.exit(1);
}
const js = jsMatch[1];
const initFnParts = js.split('function initDashboard');
if (initFnParts.length < 2) {
  console.log("NO initDashboard");
  process.exit(1);
}
const initFn = initFnParts[1];

const regex = /getElementById\(['"]([^'"]+)['"]\)/g;
let match;
const missing = new Set();
while ((match = regex.exec(initFn)) !== null) {
  const id = match[1];
  // check if id exists in html
  if (!html.includes('id="' + id + '"') && !html.includes("id='" + id + "'")) {
    missing.add(id);
  }
}
console.log('MISSING IDs IN HTML:');
for (const id of missing) {
  console.log(id);
}
