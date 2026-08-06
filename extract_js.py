import re
import sys

with open('Forecast_Decision_Intelligence_Dashboard _1.html', 'r', encoding='utf-8') as f:
    html = f.read()

script_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
if script_match:
    script = script_match.group(1).strip()
    
    # Extract original DATA block
    data_match = re.search(r'const DATA = \{.*?\};', script, re.DOTALL)
    if data_match:
        original_data_block = data_match.group(0)
        
        # Change to let DATA
        new_data_block = original_data_block.replace('const DATA', 'let DATA', 1)
        
        fetch_logic = """
// --- Dynamic Data Fetching & Override ---
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('data/report.json');
        const reportData = await response.json();
        
        // Override metrics from report.json
        DATA.meta.title = reportData.metadata.title;
        DATA.meta.evaluation_period = reportData.metadata.evaluation_period;
        DATA.meta.generated_on = reportData.metadata.generated_at.split('T')[0];
        DATA.meta.records_evaluated = reportData.metadata.records_evaluated;
        DATA.meta.models_evaluated = reportData.metadata.models_evaluated;
        
        const execSection = reportData.sections.find(s => s.business_question_id === 'EXECUTIVE');
        const q1Section = reportData.sections.find(s => s.business_question_id === 'Q1');
        const q2Section = reportData.sections.find(s => s.business_question_id === 'Q2');
        const q3Section = reportData.sections.find(s => s.business_question_id === 'Q3');
        const q4Section = reportData.sections.find(s => s.business_question_id === 'Q4');
        
        DATA.executive.decision = execSection.decision_support;
        DATA.executive.confidence_q1 = q1Section.confidence === 'HIGH' ? 'High' : 'Low';
        DATA.executive.confidence_q2 = q2Section.confidence === 'HIGH' ? 'High' : 'Low';
        DATA.executive.champion_model = reportData.leaderboard[0].model;
        DATA.executive.champion_score = reportData.leaderboard[0].score;
        DATA.executive.manual_wape = parseFloat(q1Section.primary_evidence.find(e => e.metric_id === 'manual_wape').value);
        DATA.executive.ml_wape = parseFloat(q1Section.primary_evidence.find(e => e.metric_id === 'ml_wape').value);
        DATA.executive.manual_win_rate = parseFloat(q1Section.supporting_evidence.find(e => e.metric_id === 'manual_win_rate').value);
        DATA.executive.cv = parseFloat(q3Section.primary_evidence.find(e => e.metric_id === 'cv').value);
        
        DATA.q1.manual_wape = parseFloat(q1Section.primary_evidence.find(e => e.metric_id === 'manual_wape').value);
        DATA.q1.ml_wape = parseFloat(q1Section.primary_evidence.find(e => e.metric_id === 'ml_wape').value);
        DATA.q1.abs_improvement = parseFloat(q1Section.primary_evidence.find(e => e.metric_id === 'abs_improvement').value);
        DATA.q1.manual_win_rate = parseFloat(q1Section.supporting_evidence.find(e => e.metric_id === 'manual_win_rate').value);
        DATA.q1.p_value = parseFloat(q1Section.supporting_evidence.find(e => e.metric_id === 'p_value').value);
        DATA.q1.effect_size = parseFloat(q1Section.supporting_evidence.find(e => e.metric_id === 'effect_size').value);
        DATA.q1.confidence = q1Section.confidence === 'HIGH' ? 'High' : 'Low';
        
        DATA.q2.champion = q2Section.primary_evidence.find(e => e.metric_id === 'champion').value;
        DATA.q2.champion_score = parseFloat(q2Section.primary_evidence.find(e => e.metric_id === 'score').value);
        DATA.q2.runner_up = q2Section.primary_evidence.find(e => e.metric_id === 'runner_up').value;
        DATA.q2.confidence = q2Section.confidence === 'HIGH' ? 'High' : 'Low';
        DATA.q2.p_value = parseFloat(q2Section.supporting_evidence.find(e => e.metric_id === 'p_value').value);
        
        DATA.q3.cv = parseFloat(q3Section.primary_evidence.find(e => e.metric_id === 'cv').value);
        DATA.q3.n_anomalies = parseInt(q3Section.primary_evidence.find(e => e.metric_id === 'anomalies').value);
        DATA.q3.weekly_mean = parseFloat(q3Section.supporting_evidence.find(e => e.metric_id === 'mean_vol').value.replace(/,/g, ''));
        DATA.q3.weekly_std = parseFloat(q3Section.supporting_evidence.find(e => e.metric_id === 'std_dev').value.replace(/,/g, ''));
        
        DATA.q4.normal_wape = parseFloat(q4Section.primary_evidence.find(e => e.metric_id === 'normal_wape').value);
        DATA.q4.anomaly_wape = parseFloat(q4Section.primary_evidence.find(e => e.metric_id === 'anomaly_wape').value);
        DATA.q4.confidence = q4Section.confidence === 'HIGH' ? 'High' : 'Low';
        DATA.q4.n_anomalies = parseInt(q4Section.supporting_evidence.find(e => e.metric_id === 'anomaly_count').value);
        
        const setText = (id, html) => {
            const el = document.getElementById(id);
            if(el) el.innerHTML = html;
        };
        
        setText('exec-summary-text', reportData.metadata.executive_summary);
        setText('q1-observation', q1Section.observation);
        setText('q1-conclusion', q1Section.conclusion);
        setText('q1-decision-support', q1Section.decision_support);
        setText('q1-rec', q1Section.recommendation);
        
        setText('q2-observation', q2Section.observation);
        setText('q2-conclusion', q2Section.conclusion);
        setText('q2-decision-support', q2Section.decision_support);
        if(q2Section.recommendation_suppressed) {
            setText('q2-rec-suppressed', q2Section.recommendation);
        }
        
        setText('q3-observation', q3Section.observation);
        setText('q3-conclusion', q3Section.conclusion);
        setText('q3-decision-support', q3Section.decision_support);
        
        setText('q4-observation', q4Section.observation);
        setText('q4-conclusion', q4Section.conclusion);
        setText('q4-decision-support', q4Section.decision_support);
        
    } catch (err) {
        console.error('Failed to load dynamic data, falling back to original static data', err);
    }
    
    // Render functions from original script
    try {
        renderNav();
        updateExec();
        updateQ1();
        updateQ2();
        updateQ3();
        updateQ4();
        document.getElementById('dash-title').textContent = DATA.meta.title;
        document.getElementById('dash-period').textContent = DATA.meta.evaluation_period;
        document.getElementById('dash-date').textContent = DATA.meta.generated_on;
        document.getElementById('dash-records').textContent = DATA.meta.records_evaluated.toLocaleString();
        document.getElementById('dash-models').textContent = DATA.meta.models_evaluated;
        document.getElementById('rail-title').textContent = DATA.meta.title;
    } catch (err) {
        console.error("Error during rendering:", err);
    }
});
"""

        new_script = script.replace(original_data_block, new_data_block)
        
        # We need to remove the initialization calls from the bottom of the script
        lines = new_script.split('\n')
        # Filter out the initializations at the bottom since we moved them to the fetch block
        filtered_lines = [line for line in lines if not line.startswith('update') and not line.startswith('renderNav') and not line.startswith("document.getElementById('dash") and not line.startswith("document.getElementById('rail")]
        
        with open('dashboard/js/app.js', 'w', encoding='utf-8') as f:
            f.write(fetch_logic)
            f.write('\n'.join(filtered_lines))
        print('JS successfully rewritten to use fallback DATA object.')
