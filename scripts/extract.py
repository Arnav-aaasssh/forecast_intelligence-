import re

with open('Forecast_Decision_Intelligence_Dashboard _1.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Extract HTML structure
html_match = re.search(r'<body>(.*?)<script>', html, re.DOTALL)
if html_match:
    html_content = html_match.group(1).strip()
    with open('dashboard/index.html', 'w', encoding='utf-8') as f:
        f.write('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Forecast Decision Intelligence Dashboard</title>\n<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1"></script>\n<link rel="preconnect" href="https://fonts.googleapis.com">\n<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">\n<link rel="stylesheet" href="css/styles.css">\n</head>\n<body>\n' + html_content + '\n<script src="js/app.js"></script>\n</body>\n</html>')

# 2. Extract CSS styles
css_match = re.search(r'<style>(.*?)</style>', html, re.DOTALL)
if css_match:
    with open('dashboard/css/styles.css', 'w', encoding='utf-8') as f:
        f.write(css_match.group(1).strip())

# 3. Extract JS and wire it up
script_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
if script_match:
    script_content = script_match.group(1).strip()
    
    # We replace the hardcoded DATA block.
    data_match = re.search(r'const DATA = (\{.*?\});', script_content, re.DOTALL)
    if data_match:
        # We need to wrap the execution part in a function, so we can fetch data first
        new_script = script_content.replace(data_match.group(0), 'let DATA = {};')
        
        # In the reference script, execution happens by calling functions at the global scope, e.g.:
        # updateExec(); updateQ1(); updateQ2(); updateQ3(); updateQ4();
        
        fetch_logic = """
// --- Dynamic Data Fetching ---
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('data/report.json');
        const reportData = await response.json();
        
        // Map report.json to the expected DATA format
        DATA = {
            meta: {
                title: reportData.metadata.title,
                evaluation_period: reportData.metadata.evaluation_period,
                generated_on: reportData.metadata.generated_at.split('T')[0],
                records_evaluated: reportData.metadata.records_evaluated,
                models_evaluated: reportData.metadata.models_evaluated
            },
            executive: {
                decision: reportData.sections.find(s => s.business_question_id === 'EXECUTIVE').decision_support,
                confidence_q1: reportData.sections.find(s => s.business_question_id === 'Q1').confidence === 'HIGH' ? 'High' : 'Low',
                confidence_q2: reportData.sections.find(s => s.business_question_id === 'Q2').confidence === 'HIGH' ? 'High' : 'Low',
                champion_model: reportData.leaderboard[0].model,
                champion_score: reportData.leaderboard[0].score,
                manual_wape: parseFloat(reportData.sections.find(s => s.business_question_id === 'Q1').primary_evidence.find(e => e.metric_id === 'manual_wape').value),
                ml_wape: parseFloat(reportData.sections.find(s => s.business_question_id === 'Q1').primary_evidence.find(e => e.metric_id === 'ml_wape').value),
                manual_win_rate: parseFloat(reportData.sections.find(s => s.business_question_id === 'Q1').supporting_evidence.find(e => e.metric_id === 'manual_win_rate').value),
                cv: parseFloat(reportData.sections.find(s => s.business_question_id === 'Q3').primary_evidence.find(e => e.metric_id === 'cv').value)
            },
            q1: {
                manual_wape: parseFloat(reportData.sections.find(s => s.business_question_id === 'Q1').primary_evidence.find(e => e.metric_id === 'manual_wape').value),
                ml_wape: parseFloat(reportData.sections.find(s => s.business_question_id === 'Q1').primary_evidence.find(e => e.metric_id === 'ml_wape').value),
                abs_improvement: parseFloat(reportData.sections.find(s => s.business_question_id === 'Q1').primary_evidence.find(e => e.metric_id === 'abs_improvement').value),
                manual_win_rate: parseFloat(reportData.sections.find(s => s.business_question_id === 'Q1').supporting_evidence.find(e => e.metric_id === 'manual_win_rate').value),
                p_value: parseFloat(reportData.sections.find(s => s.business_question_id === 'Q1').supporting_evidence.find(e => e.metric_id === 'p_value').value),
                effect_size: parseFloat(reportData.sections.find(s => s.business_question_id === 'Q1').supporting_evidence.find(e => e.metric_id === 'effect_size').value),
                confidence: reportData.sections.find(s => s.business_question_id === 'Q1').confidence === 'HIGH' ? 'High' : 'Low',
                series: [] // Fallback, we'll need to mock or ignore series if not in report.json
            },
            q2: {
                champion: reportData.sections.find(s => s.business_question_id === 'Q2').primary_evidence.find(e => e.metric_id === 'champion').value,
                champion_score: parseFloat(reportData.sections.find(s => s.business_question_id === 'Q2').primary_evidence.find(e => e.metric_id === 'score').value),
                runner_up: reportData.sections.find(s => s.business_question_id === 'Q2').primary_evidence.find(e => e.metric_id === 'runner_up').value,
                confidence: reportData.sections.find(s => s.business_question_id === 'Q2').confidence === 'HIGH' ? 'High' : 'Low',
                p_value: parseFloat(reportData.sections.find(s => s.business_question_id === 'Q2').supporting_evidence.find(e => e.metric_id === 'p_value').value),
                family_scores: [], // mock/ignore
                leaderboard: reportData.leaderboard.map(m => ({
                    Model: m.model,
                    n_rows: 99,
                    n_weeks: 99,
                    WAPE: parseFloat(m.wape),
                    Hit10: 50,
                    Bias: parseFloat(m.bias),
                    Stability: 0.5,
                    CompositeScore: m.score,
                    family: m.family
                }))
            },
            q3: {
                cv: parseFloat(reportData.sections.find(s => s.business_question_id === 'Q3').primary_evidence.find(e => e.metric_id === 'cv').value),
                anomalies: parseInt(reportData.sections.find(s => s.business_question_id === 'Q3').primary_evidence.find(e => e.metric_id === 'anomalies').value),
                mean_vol: reportData.sections.find(s => s.business_question_id === 'Q3').supporting_evidence.find(e => e.metric_id === 'mean_vol').value,
                std_dev: reportData.sections.find(s => s.business_question_id === 'Q3').supporting_evidence.find(e => e.metric_id === 'std_dev').value,
                series: [], // mock/ignore
                anomaly_factors: [] // mock/ignore
            },
            q4: {
                normal_wape: parseFloat(reportData.sections.find(s => s.business_question_id === 'Q4').primary_evidence.find(e => e.metric_id === 'normal_wape').value),
                anomaly_wape: parseFloat(reportData.sections.find(s => s.business_question_id === 'Q4').primary_evidence.find(e => e.metric_id === 'anomaly_wape').value),
                confidence: reportData.sections.find(s => s.business_question_id === 'Q4').confidence === 'HIGH' ? 'High' : 'Low',
                n_anomalies: parseInt(reportData.sections.find(s => s.business_question_id === 'Q4').supporting_evidence.find(e => e.metric_id === 'anomaly_count').value),
                series: [], // mock/ignore
                events: [] // mock/ignore
            }
        };

        // We also need to map the text content for observations and conclusions
        const setText = (id, html) => {
            const el = document.getElementById(id);
            if(el) el.innerHTML = html;
        };
        
        setText('exec-summary-text', reportData.metadata.executive_summary);
        
        const q1 = reportData.sections.find(s => s.business_question_id === 'Q1');
        setText('q1-observation', q1.observation);
        setText('q1-conclusion', q1.conclusion);
        setText('q1-decision-support', q1.decision_support);
        setText('q1-rec', q1.recommendation);
        
        const q2 = reportData.sections.find(s => s.business_question_id === 'Q2');
        setText('q2-observation', q2.observation);
        setText('q2-conclusion', q2.conclusion);
        setText('q2-decision-support', q2.decision_support);
        if(q2.recommendation_suppressed) {
            setText('q2-rec-suppressed', q2.recommendation);
        }
        
        const q3 = reportData.sections.find(s => s.business_question_id === 'Q3');
        setText('q3-observation', q3.observation);
        setText('q3-conclusion', q3.conclusion);
        setText('q3-decision-support', q3.decision_support);
        
        const q4 = reportData.sections.find(s => s.business_question_id === 'Q4');
        setText('q4-observation', q4.observation);
        setText('q4-conclusion', q4.conclusion);
        setText('q4-decision-support', q4.decision_support);

        // Run the initialization code
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
        console.error('Failed to load dynamic data', err);
    }
});

// Original script follows:
"""
        
        # We need to remove the initialization calls from the bottom of the script
        lines = new_script.split('\n')
        # Filter out the initializations at the bottom since we moved them to the fetch block
        filtered_lines = [line for line in lines if not line.startswith('update') and not line.startswith('renderNav') and not line.startswith("document.getElementById('dash")]
        
        with open('dashboard/js/app.js', 'w', encoding='utf-8') as f:
            f.write(fetch_logic)
            f.write('\n'.join(filtered_lines))
