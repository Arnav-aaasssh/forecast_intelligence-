import re

def run():
    with open('dashboard/index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Update Heatmap CSS
    html = html.replace('.hm-cell.manual{background:var(--teal);}', '.hm-cell.manual{background:var(--rust);}')
    html = html.replace('.hm-cell.ml{background:var(--rust);}', '.hm-cell.ml{background:var(--teal);}')

    # 2. Update Heatmap Legend
    legend_old = '<div class="heatmap-legend"><span class="hm-swatch teal"></span> Manual more accurate <span class="hm-swatch rust" style="margin-left:14px;"></span> ML more accurate</div>'
    legend_new = '<div class="heatmap-legend"><span class="hm-swatch rust"></span> Manual more accurate <span class="hm-swatch teal" style="margin-left:14px;"></span> ML more accurate</div>'
    html = html.replace(legend_old, legend_new)

    # 3. Update Manual WAPE Chart
    html = html.replace(
        "label:'Manual WAPE %', data: s.map(d=>d.manual_wape), borderColor:COLORS.navy, backgroundColor:COLORS.navy+'15'",
        "label:'Manual WAPE %', data: s.map(d=>d.manual_wape), borderColor:COLORS.rust, backgroundColor:COLORS.rust+'15'"
    )

    # 4. Update ML WAPE Chart
    html = html.replace(
        "label:'ML WAPE %', data: s.map(d=>d.ml_wape), borderColor:COLORS.rust, backgroundColor:COLORS.rust+'15'",
        "label:'ML WAPE %', data: s.map(d=>d.ml_wape), borderColor:COLORS.teal, backgroundColor:COLORS.teal+'15'"
    )

    # 5. Update Rolling Win Rate
    html = html.replace(
        "label:'Rolling 8-wk Manual win rate %', data:rollingWin, borderColor:COLORS.navy, backgroundColor:COLORS.navy+'12'",
        "label:'Rolling 8-wk Manual win rate %', data:rollingWin, borderColor:COLORS.rust, backgroundColor:COLORS.rust+'12'"
    )

    # 6. Update Boxplot IQR
    html = html.replace(
        "backgroundColor:[COLORS.navy+'55',COLORS.rust+'55'], borderColor:[COLORS.navy,COLORS.rust]",
        "backgroundColor:[COLORS.rust+'55',COLORS.teal+'55'], borderColor:[COLORS.rust,COLORS.teal]"
    )

    # 7. Update Boxplot Median
    html = html.replace(
        "backgroundColor:[COLORS.navy,COLORS.rust]",
        "backgroundColor:[COLORS.rust,COLORS.teal]"
    )

    # 8. Update Q4 Manual Bars
    html = html.replace(
        "{ label: 'Manual', data: [DATA.q4.manual_normal_wape, DATA.q4.manual_anomaly_wape], backgroundColor: COLORS.navy }",
        "{ label: 'Manual', data: [DATA.q4.manual_normal_wape, DATA.q4.manual_anomaly_wape], backgroundColor: COLORS.rust }"
    )

    # Note: Q4 ML bars are already Teal, so no need to change.
    
    with open('dashboard/index.html', 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == '__main__':
    run()
