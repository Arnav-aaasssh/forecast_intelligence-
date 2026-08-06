import re

with open('dashboard/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

lines = html.split('\n')
restored_lines = []
for line in lines:
    if line.startswith('// [AUTO-REMOVED MISSING ID] '):
        line = line.replace('// [AUTO-REMOVED MISSING ID] ', '', 1)
    restored_lines.append(line)

html = '\n'.join(restored_lines)

new_lines = []
for line in restored_lines:
    matches = re.findall(r"getElementById\('([^']+)'\)", line)
    should_comment = False
    for id in matches:
        if f'id="{id}"' not in html and f"id='{id}'" not in html:
            if not line.strip().startswith('//') and 'const ' not in line and 'let ' not in line:
                should_comment = True
    
    if should_comment:
        line = '// [AUTO-REMOVED TRULY MISSING ID] ' + line
    new_lines.append(line)

with open('dashboard/index.html', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
print('SUCCESS')
