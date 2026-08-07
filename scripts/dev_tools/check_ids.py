import re

with open('dashboard/index.html', encoding='utf-8') as f:
    content = f.read()

ids = re.findall(r'id="(gf-[^"]+)"', content)
print('All gf- element IDs in index.html:')
for i in ids:
    print(' ', i)

print()
# Check what the JS expects
js_ids = ['gf-region-container', 'gf-subregion-container', 'gf-country-container',
          'gf-offering-container', 'gf-fiscal_week-container', 'gf-channel-container',
          'gf-classification-container']
print('JS expected IDs:')
for i in js_ids:
    found = i in content
    print(f'  {i}: {"FOUND" if found else "MISSING!"}')
