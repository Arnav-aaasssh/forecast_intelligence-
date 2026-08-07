import json
import statistics

with open('dashboard/data/report.json', 'r') as f:
    data = json.load(f)
    level0 = data.get('level0', [])

queues = {}
for row in level0:
    name = row.get('Forecast_Name')
    if not name: continue
    if name not in queues:
        queues[name] = {'means': [], 'stds': []}
    
    # Check what type of data is in these fields
    mean_val = row.get('Mean (Hist. Contacts) (Last 1 yr.)')
    std_val = row.get('Std Dev (Hist. Contacts)')
    
    if mean_val is not None:
        queues[name]['means'].append(mean_val)
    if std_val is not None:
        queues[name]['stds'].append(std_val)

count_missing = 0
for name, q in queues.items():
    if not q['means'] or not q['stds']:
        count_missing += 1

print(f"Total queues: {len(queues)}")
print(f"Queues missing mean/std data: {count_missing}")
if len(queues) > 0 and len(list(queues.values())[0]['means']) > 0:
    print(f"Sample mean val: {list(queues.values())[0]['means'][0]}")
    print(f"Sample std val: {list(queues.values())[0]['stds'][0]}")

