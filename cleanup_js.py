"""
Clean up dashboard2_app.js by removing duplicate/leftover filter function code.
After the new applyAllFilters() closes at line ~729 (ending with '}'),
everything until 'window.applyGlobalFilter' is dead code that needs removal.
"""

with open('dashboard/js/dashboard2_app.js', encoding='utf-8') as f:
    content = f.read()

# Find the end of the new applyAllFilters (line 729 area: "    updateScope...")
# Find the start of window.applyGlobalFilter
MARKER_START = '\n// Reusable: set a single global filter (clearing the others) and re-render everything.'
MARKER_BEFORE = '    updateScope(currentNode, currentLevel, filters);\n}\n'

idx_end_new_apply = content.find(MARKER_BEFORE)
idx_start_reusable = content.find(MARKER_START)

if idx_end_new_apply == -1:
    print('ERROR: Could not find end of new applyAllFilters')
elif idx_start_reusable == -1:
    print('ERROR: Could not find window.applyGlobalFilter marker')
else:
    # The dead code is between end of new applyAllFilters and start of applyGlobalFilter comment
    dead_start = idx_end_new_apply + len(MARKER_BEFORE)
    dead_end = idx_start_reusable
    
    dead_code = content[dead_start:dead_end]
    print(f'Dead code block ({dead_end - dead_start} chars):')
    print(repr(dead_code[:200]))
    print('...')
    print(repr(dead_code[-200:]))
    print()
    
    # Remove the dead code
    new_content = content[:dead_start] + '\n' + content[dead_end:]
    
    with open('dashboard/js/dashboard2_app.js', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f'Removed {dead_end - dead_start} chars of dead code.')
    print(f'New file size: {len(new_content)} chars')
