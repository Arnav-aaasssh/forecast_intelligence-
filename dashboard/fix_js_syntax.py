import sys

with open('dashboard/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

target = "const realized_window = series.length > 0 ? ${series[0].week} to  : '';"
replacement = "const realized_window = series.length > 0 ? `${series[0].week} to ${series[series.length-1].week}` : '';"

if target in html:
    with open('dashboard/index.html', 'w', encoding='utf-8') as f:
        f.write(html.replace(target, replacement))
    print('SUCCESS')
else:
    print('TARGET NOT FOUND')
