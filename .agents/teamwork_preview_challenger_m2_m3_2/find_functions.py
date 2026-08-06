import re

with open('dashboard/js/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

function_patterns = [
    re.compile(r'function\s+(\w+)\s*\('),
    re.compile(r'(const|let|var)\s+(\w+)\s*=\s*(async\s*)?\([^)]*\)\s*=>'),
    re.compile(r'(\w+)\s*:\s*(async\s*)?function\s*\(')
]

for idx, line in enumerate(lines):
    line_num = idx + 1
    for pattern in function_patterns:
        match = pattern.search(line)
        if match:
            # print matching group
            print(f"Line {line_num}: {line.strip()}")
            break
