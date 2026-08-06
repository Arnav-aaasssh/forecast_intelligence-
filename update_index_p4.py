import sys

def main():
    path = "dashboard/index.html"
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Update fetch to prevent caching
    html = html.replace("fetch('data/report.json')", "fetch('data/report.json?t=' + Date.now())")

    # 2. Update the Executive Summary UI
    old_exec_ui = """      <ul id="exec-summary-list" style="margin-top: 1rem; line-height: 1.6; padding-left: 1.5rem;">
        <li id="exec-part1">Loading...</li>
        <li id="exec-part2"></li>
        <li id="exec-part3"></li>
        <li id="exec-part4"></li>
      </ul>"""
    new_exec_ui = """      <div id="exec-summary-list" style="margin-top: 1rem; display: flex; flex-direction: column; gap: 12px;">
        <div class="exec-point" style="background: rgba(47, 111, 99, 0.05); border-left: 3px solid var(--teal); padding: 10px 14px; border-radius: 0 6px 6px 0; font-size: 13.5px;">
          <div style="font-weight: 600; color: var(--navy); margin-bottom: 4px; display: flex; align-items: center; gap: 6px;"><div class="kpi-icon" style="width:18px;height:18px;font-size:10px;color:white;background:var(--teal)">01</div> Strategy Assessment</div>
          <div id="exec-part1" style="color: var(--text-2);">Loading...</div>
        </div>
        <div class="exec-point" style="background: rgba(47, 111, 99, 0.05); border-left: 3px solid var(--teal); padding: 10px 14px; border-radius: 0 6px 6px 0; font-size: 13.5px;">
          <div style="font-weight: 600; color: var(--navy); margin-bottom: 4px; display: flex; align-items: center; gap: 6px;"><div class="kpi-icon" style="width:18px;height:18px;font-size:10px;color:white;background:var(--teal)">02</div> Model Champion</div>
          <div id="exec-part2" style="color: var(--text-2);"></div>
        </div>
        <div class="exec-point" style="background: rgba(184, 91, 55, 0.05); border-left: 3px solid var(--rust); padding: 10px 14px; border-radius: 0 6px 6px 0; font-size: 13.5px;">
          <div style="font-weight: 600; color: var(--navy); margin-bottom: 4px; display: flex; align-items: center; gap: 6px;"><div class="kpi-icon" style="width:18px;height:18px;font-size:10px;color:white;background:var(--rust)">03</div> Demand Stability</div>
          <div id="exec-part3" style="color: var(--text-2);"></div>
        </div>
        <div class="exec-point" style="background: rgba(74, 85, 104, 0.05); border-left: 3px solid #4A5568; padding: 10px 14px; border-radius: 0 6px 6px 0; font-size: 13.5px;">
          <div style="font-weight: 600; color: var(--navy); margin-bottom: 4px; display: flex; align-items: center; gap: 6px;"><div class="kpi-icon" style="width:18px;height:18px;font-size:10px;color:white;background:#4A5568">04</div> Anomaly Behavior</div>
          <div id="exec-part4" style="color: var(--text-2);"></div>
        </div>
      </div>"""
    html = html.replace(old_exec_ui, new_exec_ui)

    # 3. Update the Javascript rendering to match
    old_exec_js = """document.getElementById('exec-part1').innerHTML = `<b>Strategy Assessment:</b> Manual WAPE is ${DATA.q1.manual_wape}% vs ML WAPE at ${DATA.q1.ml_wape}%.`;
document.getElementById('exec-part2').innerHTML = `<b>Model Champion:</b> The top performing model is ${DATA.q2.champion} (Score: ${DATA.q2.champion_score}).`;
document.getElementById('exec-part3').innerHTML = `<b>Demand Stability:</b> Volume CV is ${DATA.q3.cv}%. ${DATA.q3.below_hist}% of segments are below historical baseline.`;
document.getElementById('exec-part4').innerHTML = `<b>Anomaly Behavior:</b> ${DATA.q3.n_anomalies > 0 ? DATA.q3.n_anomalies + ' anomalies detected.' : 'No anomalies detected.'}`;"""

    new_exec_js = """document.getElementById('exec-part1').innerHTML = `Manual WAPE is <b>${DATA.q1.manual_wape}%</b> vs ML WAPE at <b>${DATA.q1.ml_wape}%</b>.`;
document.getElementById('exec-part2').innerHTML = `The top performing model is <b>${DATA.q2.champion}</b> (Score: ${DATA.q2.champion_score}).`;
document.getElementById('exec-part3').innerHTML = `Volume CV is <b>${DATA.q3.cv}%</b>. <b>${DATA.q3.below_hist}%</b> of segments are below historical baseline.`;
document.getElementById('exec-part4').innerHTML = `${DATA.q3.n_anomalies > 0 ? DATA.q3.n_anomalies + ' anomalies detected.' : 'No anomalies detected.'}`;"""
    html = html.replace(old_exec_js, new_exec_js)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print("UI update complete")

if __name__ == "__main__":
    main()
