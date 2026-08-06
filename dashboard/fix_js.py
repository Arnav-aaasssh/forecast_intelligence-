import re

path = r"D:\project_1 imp docs\Forecast review\dashboard\js\dashboard2_app.js"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = "    if (tWeek && tMonth) {"
replacement = """    if (tWeek && tMonth) {
        tWeek.addEventListener('click', () => {
            window.TIME_GRAIN = 'week';
            tWeek.className = 'pill active';
            tMonth.className = 'pill inactive';
            const activePage = document.querySelector('.rail-item.active').getAttribute('data-page');
            if(activePage === 'sa') renderTrendPanel(window.CURRENT_FILTERS.nodeName, window.CURRENT_FILTERS.levelName, window.CURRENT_FILTERS.filters);
            if(activePage === 'bc') renderBusinessContext();
        });
        tMonth.addEventListener('click', () => {
            window.TIME_GRAIN = 'month';
            tMonth.className = 'pill active';
            tWeek.className = 'pill inactive';
            const activePage = document.querySelector('.rail-item.active').getAttribute('data-page');
            if(activePage === 'sa') renderTrendPanel(window.CURRENT_FILTERS.nodeName, window.CURRENT_FILTERS.levelName, window.CURRENT_FILTERS.filters);
            if(activePage === 'bc') renderBusinessContext();
        });
    }

    const dimSwap = document.getElementById('sa-dim-swap');
    if (dimSwap) {
        dimSwap.addEventListener('change', (e) => {
            const val = e.target.value;
            if (val === 'default') {
                HIERARCHY_PATH = ['Global', 'Region', 'SubRegion', 'Country', 'Offering', 'Channel'];
            } else if (val === 'offering_first') {
                HIERARCHY_PATH = ['Global', 'Offering', 'Region', 'SubRegion', 'Country', 'Channel'];
            } else if (val === 'channel_first') {
                HIERARCHY_PATH = ['Global', 'Channel', 'Region', 'SubRegion', 'Country', 'Offering'];
            }
            // re-render the hierarchy table and clear expansion state to prevent errors
            expandedRows.clear();
            renderHierarchyTable();
        });
    }

});

function updateScope(nodeName, levelName, filters) {
    window.TIME_GRAIN = 'week';
    window.CURRENT_FILTERS = { nodeName, levelName, filters };
    
    // Update the UI
    
    // 1. Update Scope Pill
    const pill = document.getElementById('gf-scope-pill');
    const pillText = document.getElementById('gf-scope-text');
    if (pill && pillText) {
        if (levelName === 'Global') {
            pill.style.display = 'none';
        } else {
            pill.style.display = 'flex';"""

content = content.replace("    if (tWeek && tMonth) {\n            pillText.textContent = `Scope: ${nodeName}`;\n        }\n    }", replacement)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
