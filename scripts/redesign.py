import re

def run():
    with open('dashboard/index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Replace the entire <style> block with OLED Dark Minimalist CSS
    new_style = """<style>
:root {
  --bg: #0B1120;
  --card: #111827;
  --line: #1F2937;
  --text: #F3F4F6;
  --text-2: #9CA3AF;
  --teal: #2DD4BF;
  --teal-soft: rgba(45,212,191,0.15);
  --navy: #60A5FA;
  --navy-soft: rgba(96,165,250,0.15);
  --amber: #FBBF24;
  --amber-soft: rgba(251,191,36,0.15);
  --rust: #F87171;
  --rust-soft: rgba(248,113,113,0.15);
  --gray-chip: #94A3B8;
  --gray-chip-soft: rgba(148,163,184,0.15);
  --sans: 'Fira Sans', sans-serif;
  --mono: 'Fira Code', monospace;
  --serif: 'Fira Sans', sans-serif;
  --radius: 12px;
}
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Fira+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap');

body { font-family: var(--sans); background: var(--bg); color: var(--text); margin: 0; line-height: 1.5; -webkit-font-smoothing: antialiased; }
* { box-sizing: border-box; }
.app { display: flex; min-height: 100vh; }
.rail { width: 260px; background: #080C17; border-right: 1px solid var(--line); display: flex; flex-direction: column; padding: 24px 20px; position: sticky; top: 0; height: 100vh; flex-shrink: 0; }
.rail-brand { margin-bottom: 40px; }
.rail-mark { font-size: 24px; color: var(--teal); margin-bottom: 8px; text-shadow: 0 0 10px var(--teal-soft); }
.rail-wordmark { font-family: var(--sans); font-size: 18px; font-weight: 600; color: #fff; letter-spacing: -0.5px; }
.rail-eyebrow { font-family: var(--mono); font-size: 10px; color: var(--text-2); text-transform: uppercase; margin-top: 4px; letter-spacing: 0.5px; }
.rail-nav { display: flex; flex-direction: column; gap: 6px; flex-grow: 1; }
.rail-item { text-decoration: none; font-size: 14px; font-weight: 500; color: var(--text-2); padding: 10px 14px; border-radius: 8px; transition: all 0.2s ease; display: flex; align-items: center; gap: 10px; cursor: pointer; border: 1px solid transparent; }
.rail-icon { font-size: 10px; opacity: 0; transition: opacity 0.2s; color: var(--teal); }
.rail-item:hover { background: rgba(255,255,255,0.03); color: var(--text); }
.rail-item.active { background: var(--card); color: #fff; border-color: var(--line); box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
.rail-item.active .rail-icon { opacity: 1; text-shadow: 0 0 8px var(--teal); }
.rail-foot { font-size: 11px; color: #4B5563; line-height: 1.4; border-top: 1px solid var(--line); padding-top: 16px; margin-top: 20px; }
.main { flex-grow: 1; max-width: 1200px; padding: 40px 60px; }
.page { display: none; animation: fadeIn 0.4s ease both; }
.page.active { display: block; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.hdr { margin-bottom: 40px; border-bottom: 1px solid var(--line); padding-bottom: 24px; }
.hdr-inner { display: flex; justify-content: space-between; align-items: flex-end; }
.hdr-eyebrow { font-family: var(--mono); font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: var(--teal); margin-bottom: 8px; }
h1 { font-family: var(--sans); font-size: 32px; font-weight: 600; margin: 0 0 8px; color: #fff; letter-spacing: -1px; }
.sub { font-size: 14px; color: var(--text-2); }
.hdr-meta { font-family: var(--mono); font-size: 12px; color: #6B7280; text-align: right; }

.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.kpi { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); padding: 20px; transition: transform 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
.kpi:hover { transform: translateY(-2px); border-color: #374151; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); }
.kpi-top { display: flex; justify-content: space-between; margin-bottom: 12px; }
.kpi-label { font-family: var(--mono); font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-2); }
.kpi-icon { width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; background: var(--teal-soft); color: var(--teal); font-size: 14px; }
.kpi-icon.amber { background: var(--amber-soft); color: var(--amber); }
.kpi-icon.rust { background: var(--rust-soft); color: var(--rust); }
.kpi-icon.gray { background: var(--gray-chip-soft); color: var(--gray-chip); }
.kpi-value { font-family: var(--sans); font-size: 28px; font-weight: 600; color: #fff; margin-bottom: 4px; }
.kpi-sub { font-size: 12px; color: var(--text-2); }

.chip { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 100px; font-family: var(--mono); font-size: 11px; font-weight: 500; }
.chip::before { content: ''; width: 6px; height: 6px; border-radius: 50%; }
.chip.high { background: var(--teal-soft); color: var(--teal); } .chip.high::before { background: var(--teal); box-shadow: 0 0 6px var(--teal); }
.chip.medium { background: var(--amber-soft); color: var(--amber); } .chip.medium::before { background: var(--amber); box-shadow: 0 0 6px var(--amber); }
.chip.low { background: var(--gray-chip-soft); color: var(--gray-chip); } .chip.low::before { background: var(--gray-chip); }

.grid-2 { display: grid; grid-template-columns: 1.3fr 1fr; gap: 20px; margin-bottom: 20px; }
.grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 20px; }
.grid-1 { display: grid; grid-template-columns: 1fr; gap: 20px; margin-bottom: 20px; }
@media(max-width:1000px){ .grid-2, .grid-3 { grid-template-columns: 1fr; } }

.card { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); padding: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
.card h3 { font-family: var(--sans); font-size: 18px; font-weight: 500; margin: 0 0 6px; color: #fff; }
.card h4 { font-family: var(--sans); font-size: 15px; font-weight: 500; margin: 0 0 10px; color: #E5E7EB; }
.card .bq { font-size: 13px; color: var(--text-2); margin-bottom: 16px; font-style: italic; }
.card canvas { max-height: 270px; }

.evtable { width: 100%; border-collapse: collapse; font-size: 13px; }
.evtable td { padding: 10px 8px; border-bottom: 1px solid var(--line); color: var(--text-2); }
.evtable td:last-child { text-align: right; font-family: var(--mono); color: #fff; font-weight: 500; }

.observation { background: #0F172A; border-left: 3px solid var(--navy); padding: 14px 16px; font-size: 13.5px; margin-bottom: 16px; border-radius: 0 6px 6px 0; }
.conclusion { font-size: 14.5px; font-weight: 500; margin: 16px 0 8px; color: #fff; }
.decision-support { font-size: 13px; color: var(--text-2); }
.rec-box { margin-top: 16px; padding: 14px 16px; background: var(--teal-soft); border-radius: 8px; font-size: 13.5px; color: var(--teal); border: 1px solid rgba(45,212,191,0.2); text-shadow: 0 0 10px rgba(45,212,191,0.1); }
.rec-suppressed { margin-top: 16px; padding: 14px 16px; background: var(--gray-chip-soft); border-radius: 8px; font-size: 13px; color: var(--text-2); font-style: italic; border: 1px solid var(--line); }

/* Filters */
.filter-bar { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); padding: 16px 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
.filter-group { display: flex; align-items: center; gap: 10px; }
.filter-group label { font-family: var(--mono); font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-2); }
.filter-group select { padding: 8px 32px 8px 12px; border: 1px solid var(--line); border-radius: 6px; font-family: var(--sans); font-size: 13px; background: #1F2937 url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="10" height="6"><path d="M0 0l5 6 5-6z" fill="%239CA3AF"/></svg>') no-repeat right 12px center; color: #F3F4F6; appearance: none; cursor: pointer; transition: all 0.15s; }
.filter-group select:hover, .filter-group select:focus { border-color: var(--teal); outline: none; }
.filter-pills { display: flex; gap: 8px; flex-wrap: wrap; margin-left: auto; }
.pill { background: var(--teal-soft); color: var(--teal); font-family: var(--mono); font-size: 11px; padding: 6px 12px; border-radius: 100px; }
.pill.neutral { background: var(--line); color: var(--text-2); }
.reset-btn { font-family: var(--mono); font-size: 11px; color: var(--text-2); cursor: pointer; background: transparent; border: 1px solid var(--line); border-radius: 100px; padding: 6px 14px; transition: all 0.15s; }
.reset-btn:hover { border-color: var(--rust); color: var(--rust); background: var(--rust-soft); }

/* Leaderboard */
.table-wrap { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); padding: 16px 24px 24px; overflow-x: auto; }
table.lb { width: 100%; border-collapse: collapse; font-size: 13px; min-width: 800px; }
table.lb th { text-align: left; padding: 12px; font-family: var(--mono); font-size: 11px; text-transform: uppercase; color: var(--text-2); border-bottom: 2px solid var(--line); cursor: pointer; transition: color 0.15s; }
table.lb th:hover { color: var(--teal); }
table.lb th.sorted { color: #fff; }
table.lb td { padding: 10px 12px; border-bottom: 1px solid var(--line); color: var(--text); }
table.lb tbody tr:hover { background: rgba(255,255,255,0.02); }
table.lb td.num, table.lb th.num { text-align: right; font-family: var(--mono); }
.rank-badge { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 50%; background: var(--line); color: var(--text-2); font-family: var(--mono); font-size: 11px; }
.rank-badge.top1 { background: var(--teal); color: #000; font-weight: 600; box-shadow: 0 0 8px var(--teal); }
.rank-badge.top2 { background: var(--teal-soft); color: var(--teal); }
.rank-badge.top3 { background: var(--amber-soft); color: var(--amber); }
.score-cell { display: flex; align-items: center; gap: 10px; justify-content: flex-end; }
.score-bar-track { width: 60px; height: 4px; background: var(--line); border-radius: 2px; overflow: hidden; }
.score-bar-fill { height: 100%; background: var(--teal); box-shadow: 0 0 6px var(--teal); transition: width 0.4s ease; }
.search-box { margin: 12px 0 8px; padding: 10px 16px; border: 1px solid var(--line); border-radius: 8px; font-size: 13px; width: 300px; background: #0B1120; color: #fff; }
.search-box:focus { outline: none; border-color: var(--teal); }

/* Heatmap & Bars */
.heatmap-strip { display: flex; flex-wrap: wrap; gap: 4px; }
.hm-cell { width: 18px; height: 18px; border-radius: 4px; cursor: pointer; transition: transform 0.15s; }
.hm-cell:hover { transform: scale(1.4); z-index: 2; box-shadow: 0 4px 12px rgba(0,0,0,0.5); }
.hm-cell.manual { background: var(--teal); box-shadow: 0 0 4px var(--teal-soft); }
.hm-cell.ml { background: var(--rust); box-shadow: 0 0 4px var(--rust-soft); }
.hm-tooltip { position: fixed; background: #fff; color: #000; font-family: var(--mono); font-size: 11px; padding: 8px 12px; border-radius: 6px; pointer-events: none; z-index: 50; white-space: nowrap; font-weight: 500; }

.exec-summary-card { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); padding: 28px; position: relative; margin-bottom: 20px; }
.exec-summary-card::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--teal); box-shadow: 0 0 10px var(--teal); }
.nav-cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 20px; }
.nav-card { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); padding: 24px; cursor: pointer; transition: all 0.2s; position: relative; }
.nav-card:hover { border-color: var(--teal); transform: translateY(-2px); box-shadow: 0 8px 16px rgba(0,0,0,0.4); }
.nav-card .qtag { font-family: var(--mono); font-size: 11px; color: var(--teal); text-transform: uppercase; margin-bottom: 12px; letter-spacing: 0.5px; }
.nav-card h4 { font-size: 15px; color: var(--text-2); font-weight: 400; margin: 0 0 8px; }
.nav-card .headline { font-size: 24px; font-weight: 600; color: #fff; margin-bottom: 12px; }
.nav-card .arrow { color: var(--text-2); font-size: 18px; transition: transform 0.2s; }
.nav-card:hover .arrow { transform: translateX(6px); color: var(--teal); }

.anomaly-head-left { display: flex; align-items: center; gap: 12px; }
.severity-badge { font-family: var(--mono); font-size: 10px; font-weight: 600; padding: 4px 11px; border-radius: 100px; text-transform: uppercase; }
.severity-badge.Severe { background: var(--rust-soft); color: var(--rust); }
.anomaly-meta { display: flex; gap: 18px; font-size: 12px; color: var(--text-2); flex-wrap: wrap; }
.anomaly-meta b { color: var(--teal); font-family: var(--mono); }
.anomaly-card { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 22px 24px; margin-bottom: 16px; }
.rc-col-title { font-family: var(--mono); font-size: 10.5px; text-transform: uppercase; color: var(--text-2); margin-bottom: 10px; }
.divbar-row { display: grid; grid-template-columns: 76px 1fr 52px; align-items: center; gap: 10px; margin-bottom: 9px; }
.divbar-label { font-size: 12px; color: var(--text); font-weight: 500; }
.divbar-track { position: relative; height: 20px; background: #1F2937; border-radius: 5px; overflow: hidden; }
.divbar-fill { position: absolute; top: 2px; bottom: 2px; border-radius: 4px; background: var(--rust); box-shadow: 0 0 8px rgba(248,113,113,0.4); animation: growBar .6s cubic-bezier(.22,.61,.36,1) both; }
@keyframes growBar{from{transform:scaleX(0);}to{transform:scaleX(1);}}
.divbar-fill.right{right:50%;transform-origin:right;left:auto;}
.divbar-fill.left{left:50%;transform-origin:left;}
.divbar-track .zero-line{position:absolute;left:50%;top:0;bottom:0;width:1px;background:#374151;}
.divbar-val{font-family:var(--mono);font-size:11.5px;font-weight:600;color:var(--rust);text-align:right;}

.evidence-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.evidence-table th { text-align: left; padding: 11px 10px; font-family: var(--mono); font-size: 10px; text-transform: uppercase; color: var(--text-2); border-bottom: 2px solid var(--line); }
.evidence-table th.num, .evidence-table td.num { text-align: right; font-family: var(--mono); }
.evidence-table td { padding: 11px 10px; border-bottom: 1px solid var(--line); }
.evidence-table tr:hover { background: rgba(255,255,255,0.02); }
.badge-deg { background: var(--rust-soft); color: var(--rust); font-family: var(--mono); font-size: 10.5px; padding: 4px 10px; border-radius: 100px; font-weight: 600; }
.badge-res { background: var(--teal-soft); color: var(--teal); font-family: var(--mono); font-size: 10.5px; padding: 4px 10px; border-radius: 100px; font-weight: 600; }

.footnote { font-family: var(--mono); font-size: 11px; color: #4B5563; border-top: 1px solid var(--line); padding-top: 16px; margin-top: 32px; }
</style>"""

    # Replace <style> block
    html = re.sub(r'<style>.*?</style>', new_style, html, flags=re.DOTALL)

    # 2. Replace COLORS constant
    new_colors = """const COLORS = { navy:'#60A5FA', teal:'#2DD4BF', amber:'#FBBF24', rust:'#F87171', gray:'#94A3B8',
  familyColors: {Prophet:'#60A5FA', ARIMA:'#2DD4BF', LR_LA_group:'#FBBF24', XGB_group:'#94A3B8'} };"""
    html = re.sub(r'const COLORS = \{.*?\};', new_colors, html, flags=re.DOTALL)

    # 3. Inject default filter logic in Q1 and Q2
    q1_filters_target = "q1qSelect.innerHTML = '<option value=\"All\">All Quarters</option>' + DATA.filters.quarters.map(q=>`<option value=\"${q}\">${q}</option>`).join('');"
    q1_filters_injection = """
const latestFY = DATA.filters.fiscal_years[DATA.filters.fiscal_years.length - 1];
const latestQ = DATA.filters.quarters[DATA.filters.quarters.length - 1];
q1fySelect.value = latestFY;
q1qSelect.value = latestQ;
"""
    html = html.replace(q1_filters_target, q1_filters_target + q1_filters_injection)
    
    html = html.replace("renderQ1('All','All','All');", "renderQ1('All', latestFY, latestQ);")

    q2_filters_target = "qSelect.innerHTML = '<option value=\"All\">All Quarters</option>' + filterData.quarters.map(q=>`<option value=\"${q}\">${q}</option>`).join('');"
    q2_filters_injection = """
fySelect.value = latestFY;
qSelect.value = latestQ;
"""
    html = html.replace(q2_filters_target, q2_filters_target + q2_filters_injection)
    html = html.replace("renderQ2('All','All','All');", "renderQ2('All', latestFY, latestQ);")
    
    # 4. Make charts adapt to dark mode (grids and ticks)
    html = html.replace("grid:{color:'#EEF1F4'}", "grid:{color:'#1F2937'}")
    
    # 5. Fix chart styling
    # Line 856: q1MainChart = lineChart('chart-q1', labels, [
    # Area chart updates
    html = html.replace("borderWidth:2, pointRadius:0, tension:.25", "borderWidth:2, pointRadius:0, tension:.25, fill: true")
    
    with open('dashboard/index.html', 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == '__main__':
    run()
