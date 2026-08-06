import re

path = r"D:\project_1 imp docs\Forecast review\dashboard\js\dashboard2_app.js"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Inject renderQueueFlatTable call in updateScope
content = re.sub(
    r"(if \(thisNode && \(thisNode\.GroupClass === 'Hybrid' \|\| thisNode\.Classification === 'Hybrid'\)\) \{.*?const rc = document\.getElementById\('root-cause-panel'\);\n            if\(rc\) rc\.style\.display = 'none';\n        \}\n    \})",
    r"\1\n    renderQueueFlatTable(nodeName, levelName, filters);",
    content,
    flags=re.DOTALL
)

# 2. Update renderRow signature
content = content.replace(
    "function renderRow(tbody, data, nodeName, levelName, indentLevel, accumulatedFilters) {",
    "function renderRow(tbody, data, nodeName, levelName, indentLevel, accumulatedFilters, overrideBg = '') {"
)

# 3. Add overrideBg usage
bg_target = """    // Maintain selection highlight
    if (window.CURRENT_FILTERS.nodeName === nodeName && window.CURRENT_FILTERS.levelName === levelName) {
        tr.style.backgroundColor = 'var(--teal-soft)';
    }"""
bg_replacement = """    // Maintain selection highlight
    if (window.CURRENT_FILTERS.nodeName === nodeName && window.CURRENT_FILTERS.levelName === levelName) {
        tr.style.backgroundColor = 'var(--teal-soft)';
    } else if (overrideBg) {
        tr.style.backgroundColor = overrideBg;
    }"""
content = content.replace(bg_target, bg_replacement)

# 4. Pass overrideBg recursively and in renderHierarchyTable
content = content.replace(
    "children.forEach(child => {\n        renderRow(tbody, child, child.Node, nextLevelName, 0, {});\n    });",
    "children.forEach((child, idx) => {\n        renderRow(tbody, child, child.Node, nextLevelName, 0, {}, idx % 2 === 1 ? '#f8f9fa' : '');\n    });"
)
content = content.replace(
    "childData.forEach(child => {\n            renderRow(tbody, child, child.Node, childLevel, indentLevel + 1, childFilters);\n        });",
    "childData.forEach(child => {\n            renderRow(tbody, child, child.Node, childLevel, indentLevel + 1, childFilters, overrideBg);\n        });"
)

# 5. Add renderQueueFlatTable function
flat_table_fn = """
function renderQueueFlatTable(nodeName, levelName, filters) {
    const tbody = document.getElementById('sa-flat-table-body');
    const title = document.getElementById('sa-flat-table-title');
    if (!tbody || !title) return;
    
    title.textContent = levelName === 'Global' ? '(Global)' : `(${nodeName})`;
    
    let queues = RAW_LEVEL1;
    if (levelName !== 'Global') {
        queues = queues.filter(r => String(r[levelName]) === String(nodeName));
    }
    
    // Also apply global filters if any
    for (const [k, v] of Object.entries(filters)) {
        if (k !== levelName) {
            queues = queues.filter(r => String(r[k]) === String(v));
        }
    }
    
    tbody.innerHTML = '';
    if (queues.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align:center; padding: 20px;">No forecast names found.</td></tr>';
        return;
    }
    
    queues.sort((a, b) => a.Forecast_Name.localeCompare(b.Forecast_Name));
    
    queues.forEach(q => {
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid var(--line)';
        
        let bg = '';
        let classBadge = `<span style="color:var(--text-2);">-</span>`;
        if (q.Classification === 'Strong ML') {
            bg = 'background-color: color-mix(in srgb, var(--teal) 10%, transparent);';
            classBadge = `<div class="chip high" style="margin: 0 auto; width: 60px;">Strong ML</div>`;
        } else if (q.Classification === 'Manual') {
            bg = 'background-color: color-mix(in srgb, var(--rust) 10%, transparent);';
            classBadge = `<div class="chip low" style="margin: 0 auto; width: 60px;">Manual</div>`;
        } else if (q.Classification === 'Hybrid') {
            bg = 'background-color: color-mix(in srgb, var(--amber) 10%, transparent);';
            classBadge = `<div class="chip medium" style="margin: 0 auto; width: 60px;">Hybrid</div>`;
        }
        
        if (bg) tr.style = bg;
        
        const wapeML = (q.Queue_WAPE_ML * 100).toFixed(1) + '%';
        const wapeMan = (q.Queue_WAPE_Manual * 100).toFixed(1) + '%';
        
        tr.innerHTML = `
            <td style="padding: 10px;">${q.Region || '-'}</td>
            <td style="padding: 10px;">${q.SubRegion || '-'}</td>
            <td style="padding: 10px;">${q.Country || '-'}</td>
            <td style="padding: 10px;">${q.Offering || '-'}</td>
            <td style="padding: 10px; font-weight: 500; color: var(--navy);">${q.Forecast_Name}</td>
            <td style="padding: 10px; text-align:center;">${classBadge}</td>
            <td class="num" style="padding: 10px; text-align:right;">${q.Valid_Weeks_Count}</td>
            <td class="num" style="padding: 10px; text-align:right;">${wapeML}</td>
            <td class="num" style="padding: 10px; text-align:right;">${wapeMan}</td>
        `;
        tbody.appendChild(tr);
    });
}
"""
content += flat_table_fn

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updates applied successfully.")
