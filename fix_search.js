const fs = require('fs');

let js = fs.readFileSync('dashboard/js/dashboard2_app.js', 'utf-8');

const newSearchListener = `searchInput.addEventListener('input', (e) => {
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

// Find the start of the searchInput.addEventListener
const startStr = "searchInput.addEventListener('input', (e) => {";
const startIndex = js.indexOf(startStr);
if (startIndex !== -1) {
    // Find the end of it
    // We know it ends with `});` and then there is `const selectAllBtn` below it
    const endStr = "const selectAllBtn";
    const endIndex = js.indexOf(endStr, startIndex);
    
    if (endIndex !== -1) {
        // Extract the exact block
        // Actually, just substring and replace the whole block up to the line before selectAllBtn
        // A safer way is regex
        const regex = /searchInput\.addEventListener\('input', \(e\) => \{[\s\S]*?\}\);\s*(?=const selectAllBtn)/;
        if (regex.test(js)) {
            js = js.replace(regex, newSearchListener + "\n\n        ");
            fs.writeFileSync('dashboard/js/dashboard2_app.js', js, 'utf-8');
            console.log("SUCCESS: Replaced search listener.");
        } else {
            console.log("ERROR: Regex did not match!");
        }
    } else {
        console.log("ERROR: Could not find endStr!");
    }
} else {
    console.log("ERROR: Could not find startStr!");
}
