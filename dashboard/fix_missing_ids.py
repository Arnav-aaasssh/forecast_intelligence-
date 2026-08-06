import re

with open('dashboard/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

html_body = html.split('<script>')[0]
lines = html.split('\n')
new_lines = []
modified = False

for line in lines:
    matches = re.findall(r"getElementById\('([^']+)'\)", line)
    should_comment = False
    for id in matches:
        if f'id="{id}"' not in html_body and f"id='{id}'" not in html_body:
            if not line.strip().startswith('//') and 'const ' not in line and 'let ' not in line:
                should_comment = True
    
    if should_comment:
        line = '// [AUTO-REMOVED MISSING ID] ' + line
        modified = True
    new_lines.append(line)

with open('dashboard/index.html', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
print('SUCCESS' if modified else 'NO CHANGES')
