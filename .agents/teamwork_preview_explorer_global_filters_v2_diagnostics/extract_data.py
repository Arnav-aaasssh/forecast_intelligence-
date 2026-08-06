import json

def main():
    with open('dashboard/js/app.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    start = content.find('let DATA =') + len('let DATA =')
    count = 0
    json_str = ''
    for c in content[start:]:
        json_str += c
        if c == '{':
            count += 1
        elif c == '}':
            count -= 1
            if count == 0:
                break
                
    d = json.loads(json_str)
    q2 = d.get('q2', {})
    print("DATA.q2 keys:", list(q2.keys()))
    print("scatter length:", len(q2.get('scatter', [])))
    if q2.get('scatter'):
        print("scatter sample:", q2['scatter'][0])
    print("boxplot length:", len(q2.get('boxplot', [])))
    if q2.get('boxplot'):
        print("boxplot sample:", q2['boxplot'][0])
    print("histogram length:", len(q2.get('histogram', [])))
    if q2.get('histogram'):
        print("histogram sample:", q2['histogram'][0])
        
    print("\nDATA.filters keys:", list(d.get('filters', {}).keys()))
    print("slices count:", len(d.get('filters', {}).get('slices', {})))

if __name__ == '__main__':
    main()
