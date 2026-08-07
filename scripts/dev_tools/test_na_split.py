import json

with open('dashboard/data/report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

level1 = data.get('level1', [])

# Check SubRegions before and after
amer_before = [q for q in level1 if q.get('Region') == 'Americas']
print(f"Total Americas queues: {len(amer_before)}")

# Apply NA mapping
na_count = 0
multi_count = 0
for q in level1:
    if q.get('Region') == 'Americas':
        sr = q.get('SubRegion')
        if sr is None or sr == 'None' or sr == '' or sr == 'Multiple AMER SubRegions':
            if q.get('Forecast_Name') == 'Social Media QuickSilver':
                q['SubRegion'] = 'Multiple AMER SubRegions'
                multi_count += 1
            else:
                q['SubRegion'] = 'NA'
                na_count += 1

print(f"\nAfter remapping:")
print(f"  - NA Queues: {na_count}")
print(f"  - Multiple AMER SubRegions Queues: {multi_count}")

# Verify subregion counts under Americas
subregions = {}
for q in level1:
    if q.get('Region') == 'Americas':
        sr = q.get('SubRegion')
        subregions[sr] = subregions.get(sr, 0) + 1

for sr, count in sorted(subregions.items()):
    print(f"  - SubRegion '{sr}': {count} queues")
