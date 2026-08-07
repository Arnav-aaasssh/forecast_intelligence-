import re
import json

with open('dashboard/js/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's extract the slices block
match = re.search(r'"slices":\s*(\{.*?\})', content, re.DOTALL)
if match:
    slices_str = match.group(1)
    # The block might be very large, let's find all keys using regex
    keys = re.findall(r'"([^"]+)"\s*:\s*\{', slices_str)
    print("Number of slice keys:", len(keys))
    print("Sample slice keys:")
    print(keys[:30])
else:
    print("Slices block not found")
