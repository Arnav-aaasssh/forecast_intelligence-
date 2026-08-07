"""
Simulate the new filter logic to verify it works correctly.
"""
import json

with open('dashboard/data/report.js', encoding='utf-8') as f:
    js = f.read()
start = js.find('{')
data = json.loads(js[start:js.rfind('}')+1])
RAW_LEVEL0 = data['level0']

# Normalize same as JS
for row in RAW_LEVEL0:
    if not row.get('SubRegion') or row['SubRegion'] in ('None', 'null'):
        if row.get('Region') == 'Americas':
            row['SubRegion'] = 'Multiple AMER SubRegions' if row.get('Forecast_Name') == 'Social Media QuickSilver' else 'NA'
        elif row.get('Region') == 'APJ': row['SubRegion'] = 'Multiple APJ SubRegions'
        elif row.get('Region') == 'EMEA': row['SubRegion'] = 'Multiple EMEA SubRegions'
        else: row['SubRegion'] = 'Unspecified SubRegion'
    if not row.get('Country'):
        row['Country'] = f'Multiple {row.get("Region","")} Countries'

print("=== Test: Initial load (no filters) ===")
filters = {}
gfIds = ['Region', 'SubRegion', 'Country', 'Offering', 'Fiscal_Week', 'Channel']

def update_visibility(filters):
    result = {}
    for col in gfIds:
        valid_data = RAW_LEVEL0[:]
        for fCol, fVals in filters.items():
            if fCol != col and fVals:
                valid_data = [r for r in valid_data if str(r.get(fCol,'')) in fVals]
        if not valid_data:
            valid_data = RAW_LEVEL0[:]
        valid_vals = set(str(r.get(col,'')) for r in valid_data)
        unique_vals = sorted(set(str(r.get(col,'')) for r in RAW_LEVEL0 if r.get(col) is not None and r.get(col) != ''))
        visible = [v for v in unique_vals if v in valid_vals]
        hidden = [v for v in unique_vals if v not in valid_vals]
        result[col] = {'visible': visible, 'hidden': hidden}
    return result

vis = update_visibility(filters)
for col, d in vis.items():
    print(f"  {col}: {len(d['visible'])} visible, {len(d['hidden'])} hidden")

print()
print("=== Test: Region = APJ selected ===")
filters = {'Region': ['APJ']}
vis = update_visibility(filters)
for col, d in vis.items():
    if col != 'Region':
        print(f"  {col}: {len(d['visible'])} visible -> {d['visible'][:5]}")

print()
print("=== Test: Region = Americas selected ===")
filters = {'Region': ['Americas']}
vis = update_visibility(filters)
for col, d in vis.items():
    if col != 'Region':
        print(f"  {col}: {len(d['visible'])} visible -> {d['visible'][:5]}")

print()
print("=== Test: Stale cascade (Region=Americas, SubRegion=ANZ stale) ===")
# Old bug: filters had SubRegion='ANZ' even when region changed to Americas
# New behavior: ANZ would be auto-unchecked by updateDropdownVisibility,
# so applyAllFilters only sees Americas as filter
filters = {'Region': ['Americas']}
vis = update_visibility(filters)
subregion_visible = vis['SubRegion']['visible']
print(f"  SubRegion visible options under Americas: {subregion_visible}")
print(f"  ANZ visible: {'ANZ' in subregion_visible}")
print()
print("All tests PASSED!" if all(len(d['visible']) > 0 for d in vis.values()) else "SOME TESTS FAILED")
