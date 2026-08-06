import sys

def main():
    path = "dashboard/index.html"
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Update Q3 KPI HTML
    old_q3_kpi = """      <div class="kpi"><div class="kpi-top"><div class="kpi-label">Weekly Mean Volume</div><div class="kpi-icon gray">µ</div></div><div class="kpi-value" id="q3-mean"></div></div>"""
    new_q3_kpi = """      <div class="kpi"><div class="kpi-top"><div class="kpi-label">Below Hist. Baseline</div><div class="kpi-icon gray">📉</div></div><div class="kpi-value" id="q3-below-hist"></div></div>"""
    html = html.replace(old_q3_kpi, new_q3_kpi)
    # in case of different encoding or spacing, let's use a simpler replace
    html = html.replace('id="q3-mean"', 'id="q3-below-hist"')
    html = html.replace('Weekly Mean Volume', 'Below Hist. Baseline')
    html = html.replace('µ', '📉')

    # 2. Update Q3 KPI JS
    old_q3_mean_js = """document.getElementById('q3-mean').textContent = '';
countUp(document.getElementById('q3-mean'), DATA.q3.weekly_mean, {decimals:0, duration:900});"""
    new_q3_mean_js = """document.getElementById('q3-below-hist').textContent = '';
countUp(document.getElementById('q3-below-hist'), DATA.q3.below_hist, {decimals:1, suffix:'%'});"""
    html = html.replace(old_q3_mean_js, new_q3_mean_js)

    # 3. Update Q3 Chart
    old_q3_chart = """const q3labels = DATA.q3.series.map(d=>d.week);
const q3vol = DATA.q3.series.map(d=>d.volume);
const q3anomPoints = DATA.q3.series.map(d=>d.is_anomaly ? d.volume : null);
new Chart(document.getElementById('chart-q3'), {
  type:'line',
  data:{labels:q3labels, datasets:[
    {label:'Weekly Actual Volume', data:q3vol, borderColor:COLORS.navy, backgroundColor:COLORS.navy+'10', borderWidth:2, pointRadius:0, tension:.2, fill:true},
    {label:'Anomaly (|z|>2.5)', data:q3anomPoints, borderColor:COLORS.rust, backgroundColor:COLORS.rust, pointRadius:5, pointStyle:'circle', showLine:false}
  ]},
  options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{position:'top',labels:{boxWidth:10}}},
    scales:{x:{ticks:{maxTicksLimit:12}, grid:{display:false}}, y:{grid:{color:'#EEF1F4'}}}}
});"""
    new_q3_chart = """const q3labels = DATA.q3.series.map(d=>d.week);
const q3Realized = DATA.q3.series.map(d=>d.realized_volume);
const q3Planned = DATA.q3.series.map(d=>d.planned_volume);
const q3HistMean = DATA.q3.series.map(d=>d.historical_mean);
const q3HistUpper = DATA.q3.series.map(d=>(d.historical_mean||0) + (d.historical_std||0));
const q3HistLower = DATA.q3.series.map(d=>Math.max(0, (d.historical_mean||0) - (d.historical_std||0)));

new Chart(document.getElementById('chart-q3'), {
  type:'line',
  data:{labels:q3labels, datasets:[
    {label:'Historical +1σ', data:q3HistUpper, borderColor:'transparent', backgroundColor:COLORS.gray+'20', fill: '+1', pointRadius:0, tension:0, order: 4},
    {label:'Historical -1σ', data:q3HistLower, borderColor:'transparent', backgroundColor:COLORS.gray+'20', fill: false, pointRadius:0, tension:0, order: 5},
    {label:'Historical Mean', data:q3HistMean, borderColor:COLORS.gray, borderDash:[5,5], borderWidth:2, pointRadius:0, tension:0, fill:false, order: 3},
    {label:'Planned Volume', data:q3Planned, borderColor:COLORS.teal, borderDash:[2,2], borderWidth:2, pointRadius:0, tension:0, fill:false, order: 2},
    {label:'Realized Volume', data:q3Realized, borderColor:COLORS.navy, borderWidth:3, pointRadius:3, tension:0, fill:false, order: 1}
  ]},
  options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{position:'top',labels:{boxWidth:10, usePointStyle:true}}},
    scales:{x:{ticks:{maxTicksLimit:12}, grid:{display:false}}, y:{grid:{color:'#EEF1F4'}}}}
});"""
    html = html.replace(old_q3_chart, new_q3_chart)

    # 4. Handle Q4 empty state
    # We will inject some JS at the top of // ---- Q4 static text ----
    q4_marker = "// ---- Q4 static text ----"
    q4_empty_logic = """// ---- Q4 static text ----
if (DATA.q3.n_anomalies === 0) {
  document.getElementById('page-q4').innerHTML = `
    <div class="exec-summary-card" style="margin-top:20px; text-align:center; padding: 40px;">
      <h3 style="margin-bottom: 10px; color: var(--navy);">No Anomalies Detected</h3>
      <p style="color: var(--text-2); font-size: 14px;">
        During the 13-week realized evaluation period, zero demand anomalies were triggered.
        <br>Consequently, there is no anomaly-specific error degradation to report.
      </p>
    </div>
  `;
} else {
"""
    # Now we need to close this else block. But where? We can just close it at the end of the file or just return if n_anomalies === 0 instead of else block. Wait! The JS is all in a single scope inside `initDashboard`. If we return early, it won't render the rest!
    # So instead of `else`, let's just do:
    # if (DATA.q3.n_anomalies === 0) { ... } 
    # And then we wrap the rest of Q4 logic in `if (DATA.q3.n_anomalies > 0) { ... }`
    
    # Actually, simpler:
    q4_empty_logic = """// ---- Q4 static text ----
if (DATA.q3.n_anomalies === 0) {
  document.getElementById('page-q4').innerHTML = `
    <div class="exec-summary-card" style="margin-top:20px; text-align:center; padding: 40px;">
      <h3 style="margin-bottom: 10px; color: var(--navy);">No Anomalies Detected</h3>
      <p style="color: var(--text-2); font-size: 14px;">
        During the 13-week realized evaluation period, zero demand anomalies were triggered.
        <br>Consequently, there is no anomaly-specific error degradation to report.
      </p>
    </div>
  `;
}
if (DATA.q3.n_anomalies > 0) {
"""
    html = html.replace(q4_marker, q4_empty_logic)
    
    # find the end of Q4 logic to close the if statement.
    # Q4 logic ends right before `// ============ CHARTS ============`
    q4_end_marker = "// ============ CHARTS ============"
    html = html.replace(q4_end_marker, "}\n" + q4_end_marker)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print("Q3 and Q4 updated successfully")

if __name__ == "__main__":
    main()
