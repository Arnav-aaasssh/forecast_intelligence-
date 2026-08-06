import re

path = r"D:\project_1 imp docs\Forecast review\dashboard\js\dashboard2_app.js"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update the flat table function to ensure it doesn't crash on undefined Forecast_Name
# and attaches the Excel download event listener.
target_fn = """function renderQueueFlatTable(nodeName, levelName, filters) {"""
new_fn = """
function downloadFlatTableCSV(queues) {
    if (!queues || queues.length === 0) return;
    
    const headers = ['Region', 'Sub-region', 'Country', 'Offering', 'Forecast Name', 'Class', 'Weeks', 'ML WAPE', 'Manual WAPE'];
    
    let csv = headers.join(',') + '\\n';
    
    queues.forEach(q => {
        const wapeML = (q.Queue_WAPE_ML * 100).toFixed(1) + '%';
        const wapeMan = (q.Queue_WAPE_Manual * 100).toFixed(1) + '%';
        const row = [
            q.Region || '',
            q.SubRegion || '',
            q.Country || '',
            q.Offering || '',
            q.Forecast_Name || '',
            q.Classification || '',
            q.Valid_Weeks_Count || 0,
            wapeML,
            wapeMan
        ].map(cell => {
            let str = String(cell);
            if (str.includes(',') || str.includes('"')) {
                str = '"' + str.replace(/"/g, '""') + '"';
            }
            return str;
        });
        csv += row.join(',') + '\\n';
    });
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'Forecast_Names_Detail.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function renderQueueFlatTable(nodeName, levelName, filters) {
"""

content = content.replace(target_fn, new_fn)

# Fix sorting to not crash
content = content.replace(
    "queues.sort((a, b) => a.Forecast_Name.localeCompare(b.Forecast_Name));",
    "queues.sort((a, b) => (a.Forecast_Name || '').localeCompare(b.Forecast_Name || ''));"
)

# Attach event listener to download button
attach_button_logic = """
    // Attach event listener for CSV download
    const btnDownload = document.getElementById('btn-download-excel');
    if (btnDownload) {
        // Remove existing listener if any by cloning
        const newBtn = btnDownload.cloneNode(true);
        btnDownload.parentNode.replaceChild(newBtn, btnDownload);
        newBtn.addEventListener('click', () => {
            downloadFlatTableCSV(queues);
        });
    }
"""

content = content.replace(
    "queues.sort((a, b) => (a.Forecast_Name || '').localeCompare(b.Forecast_Name || ''));",
    "queues.sort((a, b) => (a.Forecast_Name || '').localeCompare(b.Forecast_Name || ''));\n" + attach_button_logic
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updates applied successfully.")
