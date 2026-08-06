import json

with open('dashboard/data/report.json', 'r') as f:
    data = json.load(f)
    level0 = data.get('level0', [])

if level0:
    print(level0[0].keys())
