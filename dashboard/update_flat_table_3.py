import re

path = r"D:\project_1 imp docs\Forecast review\dashboard\js\dashboard2_app.js"
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Wrap renderQueueFlatTable body in try catch
target = """function renderQueueFlatTable(nodeName, levelName, filters) {"""
replacement = """function renderQueueFlatTable(nodeName, levelName, filters) {
    try {"""

content = content.replace(target, replacement)

target_end = """        tbody.appendChild(tr);
    });
}"""
replacement_end = """        tbody.appendChild(tr);
    });
    } catch(e) {
        document.getElementById('sa-flat-table-title').textContent = 'ERROR: ' + e.message;
        console.error(e);
    }
}"""

content = content.replace(target_end, replacement_end)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated to catch errors in renderQueueFlatTable.")
