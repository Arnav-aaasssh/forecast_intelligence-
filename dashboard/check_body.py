html_body = open('dashboard/index.html', encoding='utf-8').read().split('<script>')[0]
print('id="chart-sa"' in html_body)
