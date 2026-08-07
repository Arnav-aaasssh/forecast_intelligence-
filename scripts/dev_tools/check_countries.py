import json

with open('dashboard/data/report.json', 'r') as f:
    data = json.load(f)
    level1 = data.get('level1', [])

countries = {}
for row in level1:
    c = row.get('Country', '')
    r = row.get('Region', '')
    if c and c != 'Null' and c != 'N/A':
        if c not in countries:
            countries[c] = r

for c in sorted(countries.keys()):
    print(f"  '{c}' (Region: {countries[c]})")

print(f"\nTotal unique countries: {len(countries)}")
