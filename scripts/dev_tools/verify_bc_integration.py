"""
Verify that dashboard_standalone_v2.html contains all 4 Tier-1 Business Context components and no duplicate tags.
"""
import re

with open('dashboard_standalone_v2.html', encoding='utf-8') as f:
    content = f.read()

components = [
    'bc-exceptions-banner',
    'bc-exceptions-list',
    'bc-kpi-strip',
    'bc-tier1-actual-val',
    'bc-tier1-baseline-val',
    'bc-heatmap-container',
    'chart-bc-waterfall'
]

print("Checking component IDs in standalone HTML:")
for comp in components:
    found = comp in content
    print(f"  {comp}: {'FOUND' if found else 'MISSING!'}")

print()
print("Checking for duplicate script declarations:")
for item in ['let RAW_LEVEL0', 'window.REPORT_DATA =', 'function renderBC_Tier1Exceptions']:
    count = content.count(item)
    print(f"  {item}: {count}x")

print()
print("File size:", len(content), "bytes")
