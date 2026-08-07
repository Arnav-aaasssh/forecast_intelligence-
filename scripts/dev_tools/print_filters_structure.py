import json
import re

with open('dashboard/js/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'let DATA\s*=\s*(\{.*?\});', content, re.DOTALL)
if match:
    data_str = match.group(1)
    data = json.loads(data_str)
    filters = data.get('filters', {})
    for k, v in filters.items():
        if isinstance(v, list):
            print(f"filters.{k}: list of length {len(v)}, sample: {v[:5]}")
        elif isinstance(v, dict):
            print(f"filters.{k}: dict with keys {list(v.keys())[:5]}, sample keys length {len(v)}")
        else:
            print(f"filters.{k}: {type(v)}")
else:
    print("DATA not found")
