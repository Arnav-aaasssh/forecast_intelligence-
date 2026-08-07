with open('dashboard/js/dashboard2_app.js', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
for i in range(150, 185):
    if i < len(lines):
        line = lines[i].encode('ascii', errors='replace').decode('ascii')
        print(f'{i+1}: {line}')
