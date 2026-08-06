import re
def get_ids(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        html = f.read()
    init_func = html.split('function initDashboard')[1]
    ids = re.findall(r"getElementById\('([^']+)'\)", init_func)
    return set(ids)

chk_ids = get_ids('dashboard/index_checkpoint.html')
cur_ids = get_ids('dashboard/index.html')

missing = chk_ids - cur_ids
if missing:
    print('MISSING IDs:', missing)
else:
    print('No IDs missing!')
