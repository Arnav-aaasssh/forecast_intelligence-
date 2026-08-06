import os, shutil

def create_standalone():
    with open('dashboard/index.html', 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()

    with open('dashboard/data/report.js', 'r', encoding='utf-8', errors='ignore') as f:
        report_js = f.read()

    with open('dashboard/js/dashboard2_app.js', 'r', encoding='utf-8', errors='ignore') as f:
        app_js = f.read()

    html = html.replace('<script src="data/report.js"></script>', f'<script>\n{report_js}\n</script>')
    html = html.replace('<script src="js/dashboard2_app.js"></script>', f'<script>\n{app_js}\n</script>')

    with open('dashboard_standalone_v2.html', 'w', encoding='utf-8') as f:
        f.write(html)

    shutil.copy('dashboard_standalone_v2.html', 'dashboard/dashboard_standalone_v2.html')
        
    print("Created dashboard_standalone_v2.html successfully in root and dashboard/ directory.")

if __name__ == '__main__':
    create_standalone()

