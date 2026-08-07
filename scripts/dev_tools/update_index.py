import re
import sys

def main():
    path = "dashboard/index.html"
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Update Executive Summary HTML
    old_exec = """    <div class="exec-summary-card">
      <h3>Executive Summary — All Four Business Questions</h3>
      <p id="exec-summary-text">Loading…</p>
    </div>"""
    new_exec = """    <div class="exec-summary-card">
      <h3>Executive Summary</h3>
      <ul id="exec-summary-list" style="margin-top: 1rem; line-height: 1.6; padding-left: 1.5rem;">
        <li id="exec-part1">Loading...</li>
        <li id="exec-part2"></li>
        <li id="exec-part3"></li>
        <li id="exec-part4"></li>
      </ul>
    </div>"""
    html = html.replace(old_exec, new_exec)

    # 2. Update Nav Cards HTML (Remove Q1-Q4, add sparklines)
    # Nav Card 1
    old_nav1 = """<div class="card-top"><div class="qtag">Strategy Assessment</div><div class="nav-icon">01</div></div>"""
    new_nav1 = """<div class="card-top"><div class="qtag">Strategy Assessment</div></div>"""
    html = html.replace(old_nav1, new_nav1)
    
    html = html.replace("""<div class="headline" id="navcard-q1-headline">—</div>""",
                        """<div class="headline" id="navcard-q1-headline">—</div>\n        <canvas id="spark-q1" width="200" height="40" style="margin-top: 10px; width: 100%;"></canvas>""")

    # Nav Card 2
    old_nav2_real = """<div class="card-top"><div class="qtag">Model Champion</div><div class="nav-icon">02</div></div>"""
    new_nav2_real = """<div class="card-top"><div class="qtag">Model Champion</div></div>"""
    html = html.replace(old_nav2_real, new_nav2_real)

    html = html.replace("""<div class="headline" id="navcard-q2-headline">—</div>""",
                        """<div class="headline" id="navcard-q2-headline">—</div>\n        <canvas id="spark-q2" width="200" height="40" style="margin-top: 10px; width: 100%;"></canvas>""")

    # Nav Card 3
    old_nav3 = """<div class="card-top"><div class="qtag">Business Context</div><div class="nav-icon">03</div></div>"""
    new_nav3 = """<div class="card-top"><div class="qtag">Business Context</div></div>"""
    html = html.replace(old_nav3, new_nav3)

    html = html.replace("""<div class="headline" id="navcard-q3-headline">—</div>""",
                        """<div class="headline" id="navcard-q3-headline">—</div>\n        <canvas id="spark-q3" width="200" height="40" style="margin-top: 10px; width: 100%;"></canvas>""")

    # Nav Card 4
    old_nav4 = """<div class="card-top"><div class="qtag">Anomaly Behaviour</div><div class="nav-icon">04</div></div>"""
    new_nav4 = """<div class="card-top"><div class="qtag">Anomaly Behaviour</div></div>"""
    html = html.replace(old_nav4, new_nav4)

    html = html.replace("""<div class="headline" id="navcard-q4-headline">—</div>""",
                        """<div class="headline" id="navcard-q4-headline">—</div>\n        <canvas id="spark-q4" width="200" height="40" style="margin-top: 10px; width: 100%;"></canvas>""")

    # 3. Update DATA extraction logic
    old_data_extract = """      DATA.q1 = DATA.q1 || {};
      DATA.q1.manual_wape = getM(sec1.primary_evidence, 'manual_wape');
      DATA.q1.ml_wape = getM(sec1.primary_evidence, 'ml_wape');
      DATA.q1.confidence = sec1.confidence || 'LOW';
      DATA.q1.manual_win_rate = DATA.q1.manual_win_rate || 79.8;
      DATA.q1.p_value = DATA.q1.p_value || 0.00004998;
      
      DATA.q2 = DATA.q2 || {};
      DATA.q2.champion = getM(sec2.primary_evidence, 'champion');
      if (DATA.q2.champion === '0') DATA.q2.champion = getM(e.primary_evidence, 'champion_model') || 'N/A';
      DATA.q2.champion_score = getM(sec2.primary_evidence, 'score');
      if (DATA.q2.champion_score === '0') DATA.q2.champion_score = getM(e.primary_evidence, 'champion_score') || '0';
      DATA.q2.confidence = sec2.confidence || 'LOW';
      
      DATA.q3 = DATA.q3 || {};
      DATA.q3.cv = getM(sec3.primary_evidence, 'cv');
      DATA.q3.n_anomalies = getM(sec3.primary_evidence, 'anomalies');
      
      DATA.q4 = DATA.q4 || {};
      DATA.q4.anomaly_wape = getM(sec4.primary_evidence, 'anomaly_wape');
      DATA.q4.confidence = sec4.confidence || 'LOW';"""

    new_data_extract = """      // Phase 2: Derive DATA from chart_data instead of hardcoded sections
      let allq1 = payload.chart_data.q1_filters["All|All|All"] || {};
      DATA.q1 = DATA.q1 || {};
      DATA.q1.manual_wape = allq1.manual_wape || 0;
      DATA.q1.ml_wape = allq1.ml_wape || 0;
      DATA.q1.confidence = allq1.confidence || 'HIGH';
      DATA.q1.manual_win_rate = allq1.manual_win_rate || 0;
      DATA.q1.p_value = allq1.p_value || 0.0001;
      
      let allq2 = payload.chart_data.filters.slices["All|All|All"] || {leaderboard:[]};
      let champ = allq2.leaderboard[0] || {Model: "N/A", CompositeScore: 0};
      DATA.q2 = DATA.q2 || {};
      DATA.q2.champion = champ.Model;
      DATA.q2.champion_score = champ.CompositeScore;
      // Evaluate Q2 Confidence based on threshold (e.g. if diff to runner up > 5 then High else Inconclusive)
      let runner_up = allq2.leaderboard[1] || {CompositeScore: 0};
      DATA.q2.confidence = (champ.CompositeScore - runner_up.CompositeScore > 5) ? 'HIGH' : 'INCONCLUSIVE';
      
      DATA.q3 = DATA.q3 || {};
      DATA.q3.cv = payload.chart_data.q3.cv || 0;
      DATA.q3.n_anomalies = payload.chart_data.q3.n_anomalies || 0;
      DATA.q3.below_hist = payload.chart_data.q3.segments_below_historical_pct || 0;
      
      DATA.q4 = DATA.q4 || {};
      DATA.q4.normal_wape = payload.chart_data.q4.normal_wape || 0;
      DATA.q4.anomaly_wape = payload.chart_data.q4.anomaly_wape || 0;
      DATA.q4.confidence = (DATA.q4.anomaly_wape > 0) ? 'LOW' : 'INCONCLUSIVE';"""
    html = html.replace(old_data_extract, new_data_extract)

    # 4. Update the chip() function for INCONCLUSIVE
    old_chip = """function chip(level){ if (!level) return `<span class="chip low">Low Confidence</span>`; return `<span class="chip ${level.toLowerCase()}">${level} Confidence</span>`; }"""
    new_chip = """function chip(level){ 
  if (!level) return `<span class="chip low">Low Confidence</span>`; 
  if (level === 'INCONCLUSIVE') return `<span class="chip" style="background:#4A5568; color:white;">Inconclusive</span>`;
  return `<span class="chip ${level.toLowerCase()}">${level} Confidence</span>`; 
}"""
    html = html.replace(old_chip, new_chip)

    # 5. Update the Executive Summary rendering
    old_exec_render = """// ---- Executive Summary text + nav cards ----
document.getElementById('exec-summary-text').innerHTML =
  `<b>Operational Decision: ${DATA.executive.decision}.</b> Across all four evaluated business questions: `+
  `Manual forecasting outperformed the aggregate ML system with high confidence (Q1); the top-ranked model `+
  `by composite score is <b>${DATA.q2.champion}</b> (${DATA.q2.champion_score}/100), though its lead over the `+
  `runner-up did not clear the policy's confidence threshold (Q2); underlying demand volume was stable, with a `+
  `coefficient of variation of ${DATA.q3.cv}%, well below the 15% high-volatility trigger (Q3); and forecast error `+
  `was only marginally higher during the ${DATA.q4.n_anomalies} detected demand anomalies, with low confidence `+
  `in that association given the small sample (Q4). No deployment change is currently justified by the evidence.`;"""

    new_exec_render = """// ---- Executive Summary text + nav cards ----
document.getElementById('exec-part1').innerHTML = `<b>Strategy Assessment:</b> Manual WAPE is ${DATA.q1.manual_wape}% vs ML WAPE at ${DATA.q1.ml_wape}%.`;
document.getElementById('exec-part2').innerHTML = `<b>Model Champion:</b> The top performing model is ${DATA.q2.champion} (Score: ${DATA.q2.champion_score}).`;
document.getElementById('exec-part3').innerHTML = `<b>Demand Stability:</b> Volume CV is ${DATA.q3.cv}%. ${DATA.q3.below_hist}% of segments are below historical baseline.`;
document.getElementById('exec-part4').innerHTML = `<b>Anomaly Behavior:</b> ${DATA.q3.n_anomalies > 0 ? DATA.q3.n_anomalies + ' anomalies detected.' : 'No anomalies detected.'}`;"""
    html = html.replace(old_exec_render, new_exec_render)

    # Add sparkline logic to end of initDashboard
    sparkline_logic = """
  // Render Sparklines
  function drawSparkline(id, data, color) {
    const canvas = document.getElementById(id);
    if(!canvas || !data || data.length === 0) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0,0,canvas.width,canvas.height);
    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;
    const w = canvas.width;
    const h = canvas.height - 10;
    
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    data.forEach((val, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((val - min) / range) * h + 5;
      if (i===0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }
  
  if (payload.chart_data.q1 && payload.chart_data.q1.bias_drift) {
    const q1Data = payload.chart_data.q1.bias_drift.map(d => d.manual_tracking).filter(v => v !== null && !isNaN(v));
    drawSparkline('spark-q1', q1Data, COLORS.teal);
  }
  if (payload.chart_data.q3 && payload.chart_data.q3.series) {
    const q3Data = payload.chart_data.q3.series.map(d => d.realized_volume).filter(x => x != null);
    drawSparkline('spark-q3', q3Data, COLORS.amber);
  }
"""
    old_end = "renderQ1('All', 'All', 'All');\n  renderQ2('All', 'All', 'All');\n  renderQ3();\n  renderQ4();\n}"
    new_end = "renderQ1('All', 'All', 'All');\n  renderQ2('All', 'All', 'All');\n  renderQ3();\n  renderQ4();\n" + sparkline_logic + "\n}"
    html = html.replace(old_end, new_end)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print("Dashboard index.html updated successfully!")

if __name__ == "__main__":
    main()
