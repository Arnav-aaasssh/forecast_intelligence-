import json

with open('dashboard/data/report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Keys in report.json:", list(data.keys()))

# Check level1
l1_count = 0
for q in data.get('level1', []):
    if q.get('Region') == 'Americas':
        if q.get('Forecast_Name') == 'Social Media QuickSilver':
            q['SubRegion'] = 'Multiple AMER SubRegions'
        else:
            q['SubRegion'] = 'NA'
            l1_count += 1

print(f"Updated {l1_count} NA queues in level1")

# Check level0
l0_count = 0
for q in data.get('level0', []):
    if q.get('Region') == 'Americas':
        if q.get('Forecast_Name') == 'Social Media QuickSilver':
            q['SubRegion'] = 'Multiple AMER SubRegions'
        else:
            q['SubRegion'] = 'NA'
            l0_count += 1

print(f"Updated {l0_count} NA rows in level0")

# Write updated JSON back to report.json
with open('dashboard/data/report.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

# Write updated report.js
js_content = "window.REPORT_DATA = " + json.dumps(data) + ";"
with open('dashboard/data/report.js', 'w', encoding='utf-8') as f:
    f.write(js_content)

print("Successfully updated report.json and report.js!")
