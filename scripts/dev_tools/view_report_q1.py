import json

with open('dashboard/data/report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

q1_sec = [s for s in report['sections'] if s['business_question_id'] == 'Q1']
if q1_sec:
    print("Q1 Section:")
    print(json.dumps(q1_sec[0], indent=2))
else:
    print("Q1 Section not found")

# Let's also print the leaderboard format
print("\nLeaderboard Format:")
print(json.dumps(report['leaderboard'][:2], indent=2))
