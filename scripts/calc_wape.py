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
        queues[name] = {'vol': 0, 'ml_err': 0, 'man_err': 0}
    queues[name]['vol'] += row.get('Actual_Offered', 0)
    queues[name]['ml_err'] += row.get('ML_Abs_Err', 0)
    queues[name]['man_err'] += row.get('Manual_Abs_Err', 0)

ml_wapes_won = []
man_wapes_won = []
for name, q in queues.items():
    if q['vol'] > 0:
        ml_wape = (q['ml_err'] / q['vol']) * 100
        man_wape = (q['man_err'] / q['vol']) * 100
        if ml_wape <= man_wape:
            ml_wapes_won.append(ml_wape)
        else:
            man_wapes_won.append(man_wape)

print(f"Mean ML WAPE (where ML won): {statistics.mean(ml_wapes_won):.2f}%")
print(f"Mean Manual WAPE (where Manual won): {statistics.mean(man_wapes_won):.2f}%")
