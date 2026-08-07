import json

with open('dashboard/data/report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

level1 = data.get('level1', [])
amer_queues = [q for q in level1 if q.get('Region') == 'Americas']
print(f"Total Americas queues in level1: {len(amer_queues)}")

subregions = {}
for q in amer_queues:
    sr = str(q.get('SubRegion'))
    subregions[sr] = subregions.get(sr, 0) + 1

print("\nSubRegion counts under Americas:")
for sr, count in sorted(subregions.items()):
    print(f"  - {sr}: {count} queues")

print("\nDetail of all Americas queues:")
for i, q in enumerate(amer_queues, 1):
    print(f"{i:2d}. Name: {q.get('Forecast_Name'):<45} | SubRegion: {str(q.get('SubRegion')):<25} | Country: {q.get('Country')} | Offering: {q.get('Offering')}")
