import json, re

with open('dashboard_standalone_v2.html', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'window\.REPORT_DATA\s*=\s*(\{.*?\});\n', text, re.DOTALL)
if not m:
    print("Could not find window.REPORT_DATA in standalone HTML")
else:
    json_str = m.group(1)
    data = json.loads(json_str)
    level1 = data.get('level1', [])
    amer_queues = [q for q in level1 if q.get('Region') == 'Americas']
    print(f"Extracted {len(level1)} queues, Americas queues: {len(amer_queues)}")
    
    subregions = {}
    for q in amer_queues:
        sr = str(q.get('SubRegion'))
        subregions[sr] = subregions.get(sr, 0) + 1
    
    print("\nOriginal Americas SubRegions:")
    for sr, count in sorted(subregions.items()):
        print(f"  - {sr}: {count} queues")

    # Apply precise NA reclassification
    for q in data.get('level1', []):
        if q.get('Region') == 'Americas':
            if q.get('Forecast_Name') == 'Social Media QuickSilver':
                q['SubRegion'] = 'Multiple AMER SubRegions'
            elif q.get('SubRegion') in ('Brazil', 'LATAM'):
                pass
            else:
                q['SubRegion'] = 'NA'

    for q in data.get('level0', []):
        if q.get('Region') == 'Americas':
            if q.get('Forecast_Name') == 'Social Media QuickSilver':
                q['SubRegion'] = 'Multiple AMER SubRegions'
            elif q.get('SubRegion') in ('Brazil', 'LATAM'):
                pass
            else:
                q['SubRegion'] = 'NA'

    subregions_after = {}
    for q in data.get('level1', []):
        if q.get('Region') == 'Americas':
            sr = str(q.get('SubRegion'))
            subregions_after[sr] = subregions_after.get(sr, 0) + 1

    print("\nSubRegions AFTER NA reclassification:")
    for sr, count in sorted(subregions_after.items()):
        print(f"  - {sr}: {count} queues")

    # Save to dashboard/data/report.json and dashboard/data/report.js
    with open('dashboard/data/report.json', 'w', encoding='utf-8') as out:
        json.dump(data, out, indent=2)

    with open('dashboard/data/report.js', 'w', encoding='utf-8') as out:
        out.write('window.REPORT_DATA = ' + json.dumps(data) + ';')

    print("\nSuccessfully updated dashboard/data/report.json and dashboard/data/report.js!")
