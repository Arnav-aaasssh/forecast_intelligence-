with open('dashboard/index.html', encoding='utf-8') as f:
    content = f.read()

# find the gf-region-container definition - what's inside it?
idx = content.find('gf-region-container')
print('gf-region-container HTML:')
print(content[idx-20:idx+300])
print()

# find gf-subregion-container
idx2 = content.find('gf-subregion-container')
print('gf-subregion-container HTML:')
print(content[idx2-20:idx2+200])
