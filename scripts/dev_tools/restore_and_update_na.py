import json

with open('dashboard/checkpoint_v2_20260716_1736/report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

level1 = data.get('level1', [])
amer_queues = [q for q in level1 if q.get('Region') == 'Americas']
print(f"Total Americas queues in checkpoint: {len(amer_queues)}")

subregions = {}
for q in amer_queues:
    sr = str(q.get('SubRegion'))
    subregions[sr] = subregions.get(sr, 0) + 1

for sr, count in sorted(subregions.items()):
    print(f"  - {sr}: {count} queues")

# Now apply PRECISE mapping:
# 1. Brazil stays Brazil (16)
# 2. LATAM stays LATAM (13)
# 3. Social Media QuickSilver stays Multiple AMER SubRegions (1)
# 4. All other Americas queues with None/null/Multiple AMER SubRegions become NA (44)

na_l1 = 0
multi_l1 = 0
for q in data.get('level1', []):
    if q.get('Region') == 'Americas':
        if q.get('Forecast_Name') == 'Social Media QuickSilver':
            q['SubRegion'] = 'Multiple AMER SubRegions'
            multi_l1 += 1
        elif q.get('SubRegion') in ('Brazil', 'LATAM'):
            pass # Keep Brazil & LATAM
        else:
            q['SubRegion'] = 'NA'
            na_l1 += 1

subregions_after = {}
for q in data.get('level1', []):
    if q.get('Region') == 'Americas':
        sr = str(q.get('SubRegion'))
        subregions_after[sr] = subregions_after.get(sr, 0) + 1

print("\nSubRegion counts AFTER precise mapping:")
for sr, count in sorted(subregions_after.items()):
    print(f"  - {sr}: {count} queues")

# Apply to level0
for q in data.get('level0', []):
    if q.get('Region') == 'Americas':
        if q.get('Forecast_Name') == 'Social Media QuickSilver':
            q['SubRegion'] = 'Multiple AMER SubRegions'
        elif q.get('SubRegion') in ('Brazil', 'LATAM'):
            pass
        else:
            q['SubRegion'] = 'NA'

# Write updated report.json
with open('dashboard/data/report.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

# Write updated report.js
js_content = "window.REPORT_DATA = " + json.dumps(data) + ";"
with open('dashboard/data/report.js', 'w', encoding='utf-8') as f:
    f.write(js_content)

print("\nSuccessfully updated report.json and report.js!")
