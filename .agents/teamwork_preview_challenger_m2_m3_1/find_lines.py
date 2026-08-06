import re
import sys

# Configure output to be utf-8 to avoid encoding errors on windows
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/js/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
for i, line in enumerate(lines):
    stripped = line.strip()
    if len(stripped) < 200 and len(stripped) > 0:
        print(f"{i+1}: {stripped}")
