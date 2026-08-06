import json
with open('dashboard/data/report.js', encoding='utf-8') as f:
    js_content = f.read()

start = js_content.find('{')
end = js_content.rfind('}') + 1
data = json.loads(js_content[start:end])
RAW_LEVEL0 = data['level0']
print('RAW_LEVEL0 length:', len(RAW_LEVEL0))

cols = ['Region', 'SubRegion', 'Country', 'Offering', 'Fiscal_Week', 'Channel']
for col in cols:
    uniqueVals = sorted(set(r.get(col) for r in RAW_LEVEL0 if r.get(col)))
    val_types = set(type(v).__name__ for v in uniqueVals)
    print(f'{col}: {len(uniqueVals)} values, types: {val_types}, sample: {uniqueVals[:3]}')

# Fiscal_Week specifically
fw_vals = [r.get('Fiscal_Week') for r in RAW_LEVEL0[:5]]
print('Fiscal_Week raw values:', fw_vals)
print('Fiscal_Week types:', [type(v).__name__ for v in fw_vals])

# When JS does `.sort()` on Fiscal_Week integers, they sort as numbers
# But in template literal: `value="${v}"` converts int to string -> "202706"
# In validVals: String(r.Fiscal_Week) -> "202706"
# So they should match. Unless Fiscal_Week is stored as float?
print()
print('Fiscal_Week uniqueVals (sorted):')
fw_unique = sorted(set(r.get('Fiscal_Week') for r in RAW_LEVEL0 if r.get('Fiscal_Week')))
print(fw_unique)
