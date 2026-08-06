import re
html = open('dashboard/index.html', encoding='utf-8').read()
js = ''.join(re.findall(r'<script>(.*?)</script>', html, re.DOTALL))
ids = re.findall(r"getElementById\('([^']+)'\)", js)
missing = []
for id in ids:
    if f'id="{id}"' not in html and f"id='{id}'" not in html:
        missing.append(id)
print('MISSING IDs:', set(missing))
