import re
html = open('dashboard/index.html', encoding='utf-8').read()
js = re.search(r'<script>(.*?)</script>', html, re.DOTALL).group(1)
ids = re.findall(r"getElementById\('([^']+)'\)", js)
for id in ids:
    parts = html.split(f'id="{id}"')
    if len(parts) > 1:
        before = parts[0]
        if before.rfind('<!--') > before.rfind('-->'):
            print(f'{id} is COMMENTED OUT in HTML!')
