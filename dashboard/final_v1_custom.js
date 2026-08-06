
const COLORS = { navy:'#101B33', teal:'#2F6F63', amber:'#C98A2C', rust:'#B3452B', gray:'#8A94A3',
  familyColors: {Prophet:'#101B33', ARIMA:'#2F6F63', LR_LA_group:'#C98A2C', XGB_group:'#8A94A3'} };

function chip(level){ return `<span class="chip ${level.toLowerCase()}">${level} Confidence</span>`; }

function countUp(el, end, opts={}){
  const {decimals=0, suffix='', duration=700, prefix=''} = opts;
  const start = 0;
  const startTime = performance.now();
  function tick(now){
    const t = Math.min((now-startTime)/duration, 1);
    const eased = 1 - Math.pow(1-t, 3); // ease-out cubic
    const val = start + (end-start)*eased;
    el.textContent = prefix + val.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g,',') + suffix;
    if(t < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

// ---- Header ----
document.getElementById('dash-title').textContent = DATA.meta.title;
document.getElementById('dash-period').textContent = 'Evaluation Period: ' + DATA.meta.evaluation_period;
document.getElementById('dash-records').textContent = DATA.meta.records_evaluated.toLocaleString();
document.getElementById('dash-models').textContent = DATA.meta.models_evaluated;

// ---- Navigation (left rail + nav-cards) ----
function goToPage(page){
  document.querySelectorAll('.rail-item').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));
  document.querySelector(`.rail-item[data-page="${page}"]`).classList.add('active');
  document.getElementById('page-'+page).classList.add('active');
  window.scrollTo(0,0);
}
document.querySelectorAll('.rail-item').forEach(t=>t.addEventListener('click', ()=>goToPage(t.dataset.page)));
document.querySelectorAll('.nav-card').forEach(c=>c.addEventListener('click', ()=>goToPage(c.dataset.nav)));

// ---- Executive Summary text + nav cards ----
document.getElementById('exec-summary-text').innerHTML =
  `<b>Operational Decision: ${DATA.executive.decision}.</b> Across all four evaluated business questions: `+
  `Manual forecasting outperformed the aggregate ML system with high confidence (Q1); the top-ranked model `+
  `by composite score is <b>${DATA.q2.champion}</b> (${DATA.q2.champion_score}/100), though its lead over the `+
  `runner-up did not clear the policy's confidence threshold (Q2); underlying demand volume was stable, with a `+
  `coefficient of variation of ${DATA.q3.cv}%, well below the 15% high-volatility trigger (Q3); and forecast error `+
  `was only marginally higher during the ${DATA.q4.n_anomalies} detected demand anomalies, with low confidence `+
  `in that association given the small sample (Q4). No deployment change is currently justified by the evidence.`;

document.getElementById('navcard-q1-headline').textContent = DATA.q1.manual_wape+'% vs '+DATA.q1.ml_wape+'%';
document.getElementById('navcard-q1-chip').innerHTML = chip(DATA.q1.confidence);
document.getElementById('navcard-q2-headline').textContent = DATA.q2.champion;
document.getElementById('navcard-q2-chip').innerHTML = chip(DATA.q2.confidence) + ` <span style="font-size:11px;color:var(--text-2);">score ${DATA.q2.champion_score}</span>`;
document.getElementById('navcard-q3-headline').textContent = DATA.q3.cv+'% CV';
document.getElementById('navcard-q3-sub').textContent = DATA.q3.n_anomalies + ' anomalies · stable';
document.getElementById('navcard-q4-headline').textContent = DATA.q4.anomaly_wape+'%';
document.getElementById('navcard-q4-chip').innerHTML = chip(DATA.q4.confidence);

// ---- Executive KPI/evidence block (reuses Q1 numbers) ----
document.getElementById('exec-observation').textContent =
  `Manual WAPE was ${DATA.q1.manual_wape}%. ML WAPE was ${DATA.q1.ml_wape}%. Manual outperformed ML in ${DATA.q1.manual_win_rate}% of 99 evaluated weeks.`;
document.getElementById('exec-ev-manual').textContent = DATA.q1.manual_wape+'%';
document.getElementById('exec-ev-ml').textContent = DATA.q1.ml_wape+'%';
document.getElementById('exec-ev-winrate').textContent = DATA.q1.manual_win_rate+'%';
document.getElementById('exec-ev-p').textContent = DATA.q1.p_value.toExponential(3);
document.getElementById('exec-conclusion').textContent = 'Manual forecasts were more accurate than the aggregate ML system across 99 weeks, with high statistical confidence.';
document.getElementById('exec-rec').textContent = 'Recommendation: Retain the Manual Forecast as the primary production forecasting method.';

// ---- Q1: filter-reactive rendering ----
const q1FilterData = DATA.q1_filters;
const q1srSelect = document.getElementById('q1-filter-subregion');
const q1fySelect = document.getElementById('q1-filter-fiscalyear');
const q1qSelect = document.getElementById('q1-filter-quarter');
q1srSelect.innerHTML = '<option value="All">All Sub-Regions</option>' + DATA.filters.subregions.map(s=>`<option value="${s}">${s}</option>`).join('');
q1fySelect.innerHTML = '<option value="All">All Fiscal Years</option>' + DATA.filters.fiscal_years.map(y=>`<option value="${y}">FY${y}</option>`).join('');
q1qSelect.innerHTML = '<option value="All">All Quarters</option>' + DATA.filters.quarters.map(q=>`<option value="${q}">${q}</option>`).join('');

function q1UpdatePills(sr, fy, q){
  const pills = document.getElementById('q1-filter-pills');
  let html = '';
  html += sr==='All' ? '<span class="pill neutral">Sub-Region: All</span>' : `<span class="pill">Sub-Region: ${sr}</span>`;
  html += fy==='All' ? '<span class="pill neutral">Fiscal Year: All</span>' : `<span class="pill">Fiscal Year: FY${fy}</span>`;
  html += q==='All' ? '<span class="pill neutral">Quarter: All</span>' : `<span class="pill">Quarter: ${q}</span>`;
  pills.innerHTML = html;
}

function quantile(sorted, p){
  const idx = (sorted.length-1)*p;
  const lo = Math.floor(idx), hi = Math.ceil(idx);
  if(lo===hi) return sorted[lo];
  return sorted[lo] + (sorted[hi]-sorted[lo])*(idx-lo);
}

let q1MainChart, q1DeltaChart, q1RollingChart, q1DistChart;

function renderQ1(sr, fy, q){
  const key = `${sr}|${fy}|${q}`;
  const slice = q1FilterData[key];
  q1UpdatePills(sr, fy, q);
  if(!slice || !slice.series || slice.series.length===0){
    document.getElementById('q1-observation').textContent = 'No data available for this filter combination.';
    return;
  }
  const s = slice.series;
  const labels = s.map(d=>d.week);

  // KPIs
  countUp(document.getElementById('q1-kpi-manual'), slice.manual_wape, {decimals:2, suffix:'%'});
  countUp(document.getElementById('q1-kpi-ml'), slice.ml_wape, {decimals:2, suffix:'%'});
  countUp(document.getElementById('q1-kpi-winrate'), slice.manual_win_rate, {decimals:1, suffix:'%'});
  document.getElementById('q1-kpi-conf').innerHTML = chip(slice.confidence);

  // Evidence blocks
  const absImprovement = (slice.ml_wape - slice.manual_wape).toFixed(2);
  const relImprovement = (((slice.ml_wape - slice.manual_wape)/slice.manual_wape)*100).toFixed(1);
  document.getElementById('q1-observation').textContent =
    `Manual WAPE was ${slice.manual_wape}%. ML WAPE was ${slice.ml_wape}%. Manual outperformed ML in ${slice.manual_win_rate}% of ${slice.n_weeks} evaluated weeks.`;
  document.getElementById('q1-primary').innerHTML = `
    <tr><td>Manual WAPE</td><td>${slice.manual_wape}%</td></tr>
    <tr><td>ML WAPE</td><td>${slice.ml_wape}%</td></tr>
    <tr><td>Absolute Improvement (ML vs Manual)</td><td>${absImprovement}pp</td></tr>`;
  document.getElementById('q1-supporting').innerHTML = `
    <tr><td>Weekly Win Rate (Manual)</td><td>${slice.manual_win_rate}%</td></tr>
    <tr><td>Statistical Significance (Wilcoxon, p)</td><td>${slice.p_value===null?'n/a (too few weeks)':slice.p_value.toExponential(3)}</td></tr>
    <tr><td>Effect Size</td><td>${slice.effect_size}</td></tr>
    <tr><td>Sample Size</td><td>${slice.n_weeks} weeks</td></tr>`;

  const manualBetter = slice.manual_wape <= slice.ml_wape;
  document.getElementById('q1-conclusion').textContent = manualBetter
    ? `Manual forecasts were more accurate than the aggregate ML system in this slice, at ${slice.confidence.toLowerCase()} confidence.`
    : `The aggregate ML system was more accurate than Manual forecasts in this slice, at ${slice.confidence.toLowerCase()} confidence.`;
  document.getElementById('q1-decision-support').textContent =
    'Relative accuracy in this slice should be considered alongside its confidence tier and sample size before drawing operational conclusions.';

  const recEl = document.getElementById('q1-rec');
  if(slice.confidence === 'Low'){
    recEl.className = 'rec-suppressed';
    recEl.textContent = `Recommendation omitted: confidence is Low (p=${slice.p_value===null?'n/a':slice.p_value}, effect size ${slice.effect_size}, n=${slice.n_weeks} weeks) — insufficient evidence to justify any operational change for this slice.`;
  } else if(manualBetter){
    recEl.className = 'rec-box';
    recEl.innerHTML = chip(slice.confidence) + ' &nbsp;Retain the Manual Forecast as the primary method for this slice.';
  } else {
    const meetsRegional = slice.effect_size >= 0.010;
    recEl.className = 'rec-box';
    recEl.innerHTML = meetsRegional
      ? chip(slice.confidence) + ` &nbsp;ML meets the Regional improvement threshold (≥1.0pp) for this slice — consider a scoped ML pilot here.`
      : chip(slice.confidence) + ` &nbsp;ML outperforms Manual here, but the margin (${Math.abs(absImprovement)}pp) does not clear the Regional improvement threshold (1.0pp).`;
  }

  // Main line chart
  if(q1MainChart) q1MainChart.destroy();
  q1MainChart = lineChart('chart-q1', labels, [
    {label:'Manual WAPE %', data: s.map(d=>d.manual_wape), borderColor:COLORS.navy, backgroundColor:COLORS.navy+'15', borderWidth:2, pointRadius:0, tension:.25},
    {label:'ML WAPE %', data: s.map(d=>d.ml_wape), borderColor:COLORS.rust, backgroundColor:COLORS.rust+'15', borderWidth:2, pointRadius:0, tension:.25}
  ]);

  // Delta bar chart (Manual advantage per week)
  const deltas = s.map(d=>Math.round((d.ml_wape-d.manual_wape)*100)/100); // positive = Manual better
  if(q1DeltaChart) q1DeltaChart.destroy();
  q1DeltaChart = new Chart(document.getElementById('chart-q1-delta'), {
    type:'bar',
    data:{labels, datasets:[{label:'Manual advantage (pp)', data:deltas,
      backgroundColor: deltas.map(v=>v>=0?COLORS.teal:COLORS.rust)}]},
    options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}},
      scales:{x:{ticks:{maxTicksLimit:10}, grid:{display:false}}, y:{grid:{color:'#EEF1F4'}, title:{display:true,text:'pp',font:{size:10}}}}}
  });

  // Weekly winner heatmap
  const hm = document.getElementById('q1-heatmap');
  hm.innerHTML = '';
  let tooltipEl = document.querySelector('.hm-tooltip');
  if(!tooltipEl){ tooltipEl = document.createElement('div'); tooltipEl.className='hm-tooltip'; tooltipEl.style.display='none'; document.body.appendChild(tooltipEl); }
  s.forEach(d=>{
    const cell = document.createElement('div');
    const win = d.manual_wape < d.ml_wape;
    cell.className = 'hm-cell ' + (win?'manual':'ml');
    cell.addEventListener('mousemove', (e)=>{
      tooltipEl.style.display='block';
      tooltipEl.style.left = (e.clientX+14)+'px';
      tooltipEl.style.top = (e.clientY+14)+'px';
      tooltipEl.textContent = `${d.week} — Manual ${d.manual_wape}% · ML ${d.ml_wape}%`;
    });
    cell.addEventListener('mouseleave', ()=>{ tooltipEl.style.display='none'; });
    hm.appendChild(cell);
  });

  // Rolling 8-week Manual win rate
  const winFlags = s.map(d=>d.manual_wape < d.ml_wape ? 1 : 0);
  const rollingWin = winFlags.map((_,i)=>{
    const start = Math.max(0,i-7);
    const window = winFlags.slice(start,i+1);
    return Math.round(window.reduce((a,b)=>a+b,0)/window.length*1000)/10;
  });
  if(q1RollingChart) q1RollingChart.destroy();
  q1RollingChart = new Chart(document.getElementById('chart-q1-rolling'), {
    type:'line',
    data:{labels, datasets:[{label:'Rolling 8-wk Manual win rate %', data:rollingWin, borderColor:COLORS.navy, backgroundColor:COLORS.navy+'12', borderWidth:2, pointRadius:0, tension:.3, fill:true}]},
    options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{position:'top',labels:{boxWidth:10}}},
      scales:{x:{ticks:{maxTicksLimit:10}, grid:{display:false}}, y:{min:0,max:100, grid:{color:'#EEF1F4'}, title:{display:true,text:'%',font:{size:10}}}}}
  });

  // Weekly WAPE distribution (box-plot style, Manual vs ML)
  function boxStats(arr){
    const sorted = arr.slice().sort((a,b)=>a-b);
    return {min:sorted[0], q1:quantile(sorted,.25), median:quantile(sorted,.5), q3:quantile(sorted,.75), max:sorted[sorted.length-1]};
  }
  const manualStats = boxStats(s.map(d=>d.manual_wape));
  const mlStats = boxStats(s.map(d=>d.ml_wape));
  if(q1DistChart) q1DistChart.destroy();
  q1DistChart = new Chart(document.getElementById('chart-q1-dist'), {
    type:'bar',
    data:{labels:['Manual','ML'],
      datasets:[
        {label:'IQR (Q1–Q3)', data:[[manualStats.q1,manualStats.q3],[mlStats.q1,mlStats.q3]], backgroundColor:[COLORS.navy+'55',COLORS.rust+'55'], borderColor:[COLORS.navy,COLORS.rust], borderWidth:1.5, borderSkipped:false},
        {label:'Median', data:[[manualStats.median-0.3,manualStats.median+0.3],[mlStats.median-0.3,mlStats.median+0.3]], backgroundColor:[COLORS.navy,COLORS.rust]}
      ]},
    options:{responsive:true, maintainAspectRatio:false, indexAxis:'y',
      plugins:{legend:{position:'bottom',labels:{boxWidth:10}}, tooltip:{callbacks:{label:(ctx)=>{
        const st = ctx.dataIndex===0?manualStats:mlStats;
        return ctx.datasetIndex===0 ? `Q1: ${st.q1}%  Q3: ${st.q3}%  (min ${st.min}%, max ${st.max}%)` : `Median: ${st.median}%`;
      }}}},
      scales:{x:{title:{display:true,text:'WAPE %',font:{size:10}}, grid:{color:'#EEF1F4'}}, y:{grid:{display:false}}}}
  });
}

q1srSelect.addEventListener('change', ()=>renderQ1(q1srSelect.value, q1fySelect.value, q1qSelect.value));
q1fySelect.addEventListener('change', ()=>renderQ1(q1srSelect.value, q1fySelect.value, q1qSelect.value));
q1qSelect.addEventListener('change', ()=>renderQ1(q1srSelect.value, q1fySelect.value, q1qSelect.value));
document.getElementById('q1-filter-reset').addEventListener('click', ()=>{
  q1srSelect.value='All'; q1fySelect.value='All'; q1qSelect.value='All'; renderQ1('All','All','All');
});

// ---- Q3 static text ----
document.getElementById('q3-cv').textContent = '';
countUp(document.getElementById('q3-cv'), DATA.q3.cv, {decimals:2, suffix:'%'});
document.getElementById('q3-anomalies').textContent = '';
countUp(document.getElementById('q3-anomalies'), DATA.q3.n_anomalies, {decimals:0});
document.getElementById('q3-mean').textContent = '';
countUp(document.getElementById('q3-mean'), DATA.q3.weekly_mean, {decimals:0, duration:900});
document.getElementById('q3-std').textContent = '';
countUp(document.getElementById('q3-std'), DATA.q3.weekly_std, {decimals:0, duration:900});
document.getElementById('q3-observation').textContent = `Weekly actual volume had a coefficient of variation of ${DATA.q3.cv}% across 99 weeks, below the policy's 15% high-volatility trigger. ${DATA.q3.n_anomalies} weeks were flagged as statistical anomalies (|z| > 2.5).`;
document.getElementById('q3-conclusion').textContent = 'Weekly demand volume was stable and below the high-volatility policy trigger, with three holiday-associated anomalies out of 99 weeks.';
document.getElementById('q3-decision-support').textContent = 'Low overall volatility should be considered when interpreting forecast accuracy results. Context only — no recommendations, per policy.';

function divergingBarsHTML(deltas){
  const maxAbs = Math.max(...deltas.map(d=>Math.abs(d.delta_pct)), 1);
  return deltas.map(d=>{
    const pct = Math.abs(d.delta_pct)/maxAbs*50; // half-track max since diverging from center
    const side = d.delta_pct < 0 ? 'left' : 'right';
    return `<div class="divbar-row">
      <div class="divbar-label">${d.category}</div>
      <div class="divbar-track"><span class="zero-line"></span><div class="divbar-fill ${side}" style="width:${pct}%"></div></div>
      <div class="divbar-val">${d.delta_pct>0?'+':''}${d.delta_pct}%</div>
    </div>`;
  }).join('');
}

document.getElementById('anomaly-cards-container').innerHTML = DATA.q3.anomaly_cards.map((a,i) => `
  <div class="anomaly-card stagger" style="animation-delay:${i*0.08}s">
    <div class="anomaly-head">
      <div class="anomaly-head-left">
        <span class="anomaly-date">${a.week}</span>
        <span class="severity-badge ${a.severity}">${a.severity}</span>
      </div>
      <div class="anomaly-meta">
        <span>Volume <b>${a.volume.toLocaleString()}</b></span>
        <span>Z-Score <b>${a.z_score}</b></span>
        <span>Deviation <b>${a.deviation_pct}%</b></span>
        <span>Holiday Count <b>${a.holiday_count}</b></span>
      </div>
    </div>
    <div class="rc-cols">
      <div>
        <div class="rc-col-title">By Region — deviation vs. own baseline</div>
        ${divergingBarsHTML(a.region_deltas)}
      </div>
      <div>
        <div class="rc-col-title">By Channel — deviation vs. own baseline</div>
        ${divergingBarsHTML(a.channel_deltas)}
      </div>
    </div>
  </div>
`).join('');

// ---- Q4 static text ----
countUp(document.getElementById('q4-normal'), DATA.q4.normal_wape, {decimals:2, suffix:'%'});
countUp(document.getElementById('q4-anomaly'), DATA.q4.anomaly_wape, {decimals:2, suffix:'%'});
document.getElementById('q4-conf').innerHTML = chip(DATA.q4.confidence);
countUp(document.getElementById('q4-n'), DATA.q4.n_anomalies, {decimals:0});
document.getElementById('q4-observation').textContent = `Mean weekly ML WAPE was ${DATA.q4.normal_wape}% in normal weeks and ${DATA.q4.anomaly_wape}% in anomaly weeks (n=${DATA.q4.n_anomalies}).`;
document.getElementById('q4-conclusion').textContent = 'Forecast error was marginally higher during anomaly weeks, but the small anomaly sample (n=3) limits confidence in this association.';
document.getElementById('q4-decision-support').textContent = 'Observational only — no causal mechanism is asserted, and no recommendations are produced for this question, per policy.';

// ---- Q4 deeper signal: Manual vs Champion, Normal vs Anomaly ----
new Chart(document.getElementById('chart-q4-compare'), {
  type: 'bar',
  data: {
    labels: ['Normal Weeks', 'Anomaly Weeks'],
    datasets: [
      { label: 'Manual', data: [DATA.q4.manual_normal_wape, DATA.q4.manual_anomaly_wape], backgroundColor: COLORS.navy },
      { label: 'Champion (V2_9_Prophet)', data: [DATA.q4.champion_normal_wape, DATA.q4.champion_anomaly_wape], backgroundColor: COLORS.teal }
    ]
  },
  options: { responsive:true, maintainAspectRatio:false, plugins:{legend:{position:'bottom',labels:{boxWidth:10}}},
    scales:{ y:{title:{display:true,text:'WAPE %',font:{size:10}}, grid:{color:'#EEF1F4'}}, x:{grid:{display:false}} } }
});

const degLabels = DATA.q4.degradation_detail.map(d=>d.week);
const degVals = DATA.q4.degradation_detail.map(d=>d.delta_pp);
new Chart(document.getElementById('chart-q4-degbar'), {
  type: 'bar',
  data: { labels: degLabels, datasets: [{ label: 'Δ vs. baseline (pp)', data: degVals,
    backgroundColor: degVals.map(v => v > 0 ? COLORS.rust : COLORS.teal) }] },
  options: { responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}},
    scales:{ y:{title:{display:true,text:'pp',font:{size:10}}, grid:{color:'#EEF1F4'}}, x:{grid:{display:false}} } }
});

const manualDelta = (DATA.q4.manual_anomaly_wape - DATA.q4.manual_normal_wape).toFixed(2);
const champDelta = (DATA.q4.champion_anomaly_wape - DATA.q4.champion_normal_wape).toFixed(2);
document.getElementById('q4-insight-callout').innerHTML =
  `<b>Observed split:</b> during anomaly weeks, Manual WAPE moved ${manualDelta>0?'+':''}${manualDelta}pp `+
  `(${DATA.q4.manual_normal_wape}% → ${DATA.q4.manual_anomaly_wape}%), while the champion model moved `+
  `${champDelta>0?'+':''}${champDelta}pp (${DATA.q4.champion_normal_wape}% → ${DATA.q4.champion_anomaly_wape}%). `+
  `The aggregate ML view alone would not have surfaced this split — it blends the champion together with weaker models. `+
  `This is an observed association at n=3 anomaly weeks, not a causal claim, and does not meet the confidence bar for a recommendation.`;

document.getElementById('q4-stat-p').textContent = DATA.q4.p_value;
document.getElementById('q4-stat-conf').innerHTML = chip(DATA.q4.confidence);

document.getElementById('q4-degradation-body').innerHTML = DATA.q4.degradation_detail.map((d,i) => `
  <tr class="stagger" style="animation-delay:${i*0.08}s">
    <td>${d.week}</td>
    <td class="num">${d.anomaly_wape}%</td>
    <td class="num">${d.baseline_wape}%</td>
    <td class="num">${d.delta_pp > 0 ? '+' : ''}${d.delta_pp}pp</td>
    <td><span class="${d.event_type==='Degradation'?'badge-deg':'badge-res'}">${d.event_type}</span></td>
  </tr>`).join('');

// ============ CHARTS ============
Chart.defaults.font.family = "'IBM Plex Sans', sans-serif";
Chart.defaults.font.size = 11;
Chart.defaults.color = '#5B6472';

function lineChart(canvasId, labels, datasets, opts={}){
  return new Chart(document.getElementById(canvasId), {
    type:'line', data:{labels, datasets},
    options: Object.assign({ responsive:true, maintainAspectRatio:false, interaction:{mode:'index', intersect:false},
      plugins:{legend:{position:'top', labels:{boxWidth:10}}},
      scales:{ x:{ticks:{maxTicksLimit:12}, grid:{display:false}}, y:{grid:{color:'#EEF1F4'}} } }, opts)
  });
}

const q1labels = DATA.q1.series.map(d=>d.week);
const q1deltas = DATA.q1.series.map(d => Math.round((d.ml_wape - d.manual_wape)*100)/100); // positive = Manual better
new Chart(document.getElementById('chart-exec-main'), {
  type: 'bar',
  data: { labels: q1labels, datasets: [{
    label: 'Manual advantage (pp)', data: q1deltas,
    backgroundColor: q1deltas.map(v => v >= 0 ? COLORS.teal : COLORS.rust)
  }]},
  options: { responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}},
    scales:{ x:{ticks:{maxTicksLimit:10}, grid:{display:false}}, y:{grid:{color:'#EEF1F4'}, title:{display:true,text:'pp',font:{size:10}}} } }
});
renderQ1('All','All','All');

// ---- Q3 volume chart ----
const q3labels = DATA.q3.series.map(d=>d.week);
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
});

// ---- Q4 error chart ----
const q4wape = DATA.q4.series.map(d=>d.wape);
const q4anomPoints = DATA.q4.series.map(d=>d.is_anomaly ? d.wape : null);
new Chart(document.getElementById('chart-q4'), {
  type:'line',
  data:{labels:q3labels, datasets:[
    {label:'Weekly ML WAPE %', data:q4wape, borderColor:COLORS.teal, backgroundColor:COLORS.teal+'10', borderWidth:2, pointRadius:0, tension:.2, fill:true},
    {label:'Anomaly Week', data:q4anomPoints, borderColor:COLORS.rust, backgroundColor:COLORS.rust, pointRadius:5, pointStyle:'circle', showLine:false}
  ]},
  options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{position:'top',labels:{boxWidth:10}}},
    scales:{x:{ticks:{maxTicksLimit:12}, grid:{display:false}}, y:{grid:{color:'#EEF1F4'}}}}
});

// ============ Q2: FILTERS + REACTIVE CHARTS/TABLE ============
const filterData = DATA.filters;
const srSelect = document.getElementById('filter-subregion');
const fySelect = document.getElementById('filter-fiscalyear');
const qSelect = document.getElementById('filter-quarter');
srSelect.innerHTML = '<option value="All">All Sub-Regions</option>' + filterData.subregions.map(s=>`<option value="${s}">${s}</option>`).join('');
fySelect.innerHTML = '<option value="All">All Fiscal Years</option>' + filterData.fiscal_years.map(y=>`<option value="${y}">FY${y}</option>`).join('');
qSelect.innerHTML = '<option value="All">All Quarters</option>' + filterData.quarters.map(q=>`<option value="${q}">${q}</option>`).join('');

let contribChart, familyChart, histChart, scatterChart, boxChart;

function normalizeAbs(v, best, worst){
  const lo = Math.min(best,worst), hi = Math.max(best,worst);
  const c = Math.min(Math.max(v,lo),hi);
  return best < worst ? (worst-c)/(worst-best) : (c-worst)/(best-worst);
}
function contribPoints(row){
  const s_w = normalizeAbs(row.WAPE/100, 0.05, 0.40);
  const s_b = normalizeAbs(row.Bias/100, 0.00, 0.20);
  const s_s = normalizeAbs(row.Stability, 0.00, 0.30);
  const s_h = normalizeAbs(row.Hit10/100, 0.90, 0.30);
  return [35*s_w, 25*s_h, 20*s_b, 20*s_s];
}

let lbSort = {key:'CompositeScore', asc:false};
let currentLeaderboard = [];

function renderLeaderboard(filter=''){
  let rows = currentLeaderboard.slice();
  if(filter) rows = rows.filter(r=>r.Model.toLowerCase().includes(filter.toLowerCase()));
  rows.sort((a,b)=>{
    let av=a[lbSort.key], bv=b[lbSort.key];
    if(typeof av === 'string') return lbSort.asc ? av.localeCompare(bv) : bv.localeCompare(av);
    return lbSort.asc ? av-bv : bv-av;
  });
  document.querySelectorAll('#leaderboard-table th').forEach(th=>{
    th.classList.toggle('sorted', th.dataset.k===lbSort.key);
    th.classList.toggle('asc', th.dataset.k===lbSort.key && lbSort.asc);
  });
  const body = document.getElementById('lb-body');
  body.innerHTML = rows.map((r,i)=>{
    const rank = currentLeaderboard.indexOf(r)+1;
    let badgeCls = rank===1 ? 'top1' : rank===2 ? 'top2' : rank===3 ? 'top3' : '';
    const barPct = Math.max(2, Math.min(100, r.CompositeScore));
    return `<tr style="animation-delay:${Math.min(i*0.012,0.3)}s">
      <td><span class="rank-badge ${badgeCls}">${rank}</span></td>
      <td>${r.Model}</td>
      <td class="num"><div class="score-cell"><span>${r.CompositeScore.toFixed(2)}</span><div class="score-bar-track"><div class="score-bar-fill" style="width:${barPct}%"></div></div></div></td>
      <td class="num">${r.WAPE.toFixed(2)}</td>
      <td class="num">${r.Hit10.toFixed(2)}</td>
      <td class="num">${r.Bias.toFixed(2)}</td>
      <td class="num">${r.Stability.toFixed(3)}</td>
      <td class="num">${r.n_rows}</td>
    </tr>`;
  }).join('');
}
document.querySelectorAll('#leaderboard-table th').forEach(th=>{
  th.addEventListener('click', ()=>{
    const k = th.dataset.k;
    if(k==='rank') return;
    if(lbSort.key===k) lbSort.asc=!lbSort.asc; else {lbSort.key=k; lbSort.asc=false;}
    renderLeaderboard(document.getElementById('lb-search').value);
  });
});
document.getElementById('lb-search').addEventListener('input', e=>renderLeaderboard(e.target.value));

function updateFilterPills(sr, fy, q){
  const pills = document.getElementById('filter-pills');
  let html = '';
  html += sr==='All' ? '<span class="pill neutral">Sub-Region: All</span>' : `<span class="pill">Sub-Region: ${sr}</span>`;
  html += fy==='All' ? '<span class="pill neutral">Fiscal Year: All</span>' : `<span class="pill">Fiscal Year: FY${fy}</span>`;
  html += q==='All' ? '<span class="pill neutral">Quarter: All</span>' : `<span class="pill">Quarter: ${q}</span>`;
  pills.innerHTML = html;
}

function renderQ2(sr, fy, q){
  const key = `${sr}|${fy}|${q}`;
  const slice = filterData.slices[key];
  updateFilterPills(sr, fy, q);
  if(!slice){
    document.getElementById('q2-champ').textContent = 'No qualifying models';
    document.getElementById('q2-champ-score').textContent = '—';
    document.getElementById('q2-runner').textContent = '—';
    document.getElementById('q2-conf').innerHTML = chip('Low');
    document.getElementById('lb-count-note').textContent = '(this filter combination has fewer than 30 rows for every model — insufficient data to score)';
    document.getElementById('q2-observation').textContent = 'No model met the minimum 30-row eligibility threshold for this filter combination.';
    document.getElementById('q2-conclusion').textContent = 'Insufficient data to identify a champion for this slice.';
    document.getElementById('q2-decision-support').textContent = 'Consider broadening the Sub-Region, Fiscal Year, or Quarter filter to increase the evaluated sample size.';
    document.getElementById('q2-rec-suppressed').textContent = 'Recommendation omitted: no eligible candidates in this slice.';
    currentLeaderboard = [];
    renderLeaderboard(document.getElementById('lb-search').value);
    if(contribChart){ contribChart.destroy(); contribChart = null; }
    return;
  }
  currentLeaderboard = slice.leaderboard;
  const champRow = slice.leaderboard[0];
  const runnerRow = slice.leaderboard[1] || slice.leaderboard[0];

  document.getElementById('q2-champ').textContent = champRow.Model;
  const scoreEl = document.getElementById('q2-champ-score');
  scoreEl.textContent = '';
  countUp(scoreEl, champRow.CompositeScore, {decimals:2});
  document.getElementById('q2-runner').textContent = runnerRow.Model;
  document.getElementById('lb-count-note').textContent = `(${slice.n_models} eligible models, ≥30 rows, ${slice.n_rows.toLocaleString()} total rows in slice)`;

  // confidence: only computed precisely for the GLOBAL (All|All|All) slice; for filtered slices,
  // display Low by default (sub-sample significance testing not pre-computed per slice)
  const conf = (sr==='All' && fy==='All' && q==='All') ? DATA.q2.confidence : 'Low';
  document.getElementById('q2-conf').innerHTML = chip(conf);
  document.getElementById('q2-observation').textContent =
    `${champRow.Model} ranked first among ${slice.n_models} eligible models with a Composite Score of ${champRow.CompositeScore.toFixed(2)}. ${runnerRow.Model} ranked second at ${runnerRow.CompositeScore.toFixed(2)}.`;
  document.getElementById('q2-conclusion').textContent = `${champRow.Model} scored highest in this slice, but per-slice statistical testing was not pre-computed for filtered views — treat as a ranking, not a proven champion.`;
  document.getElementById('q2-decision-support').textContent = `Composite score gap: ${(champRow.CompositeScore-runnerRow.CompositeScore).toFixed(2)} points. This should be considered alongside the global (unfiltered) significance test shown when no filters are applied.`;
  document.getElementById('q2-rec-suppressed').textContent = 'Recommendation omitted: confidence for filtered slices is treated conservatively as Low pending dedicated significance testing.';

  renderLeaderboard(document.getElementById('lb-search').value);

  // contribution chart
  const champPts = contribPoints(champRow), runnerPts = contribPoints(runnerRow);
  if(contribChart) contribChart.destroy();
  contribChart = new Chart(document.getElementById('chart-q2-contrib'), {
    type:'bar',
    data:{ labels:[champRow.Model, runnerRow.Model],
      datasets:[
        {label:'WAPE (35%)', data:[champPts[0], runnerPts[0]], backgroundColor:COLORS.navy},
        {label:'Hit10 (25%)', data:[champPts[1], runnerPts[1]], backgroundColor:COLORS.teal},
        {label:'Bias (20%)', data:[champPts[2], runnerPts[2]], backgroundColor:COLORS.amber},
        {label:'Stability (20%)', data:[champPts[3], runnerPts[3]], backgroundColor:COLORS.gray},
      ]},
    options:{responsive:true, maintainAspectRatio:false, indexAxis:'y',
      plugins:{legend:{position:'bottom', labels:{boxWidth:10}}},
      scales:{x:{stacked:true, max:100, grid:{color:'#EEF1F4'}}, y:{stacked:true, grid:{display:false}}}}
  });
}

srSelect.addEventListener('change', ()=>renderQ2(srSelect.value, fySelect.value, qSelect.value));
fySelect.addEventListener('change', ()=>renderQ2(srSelect.value, fySelect.value, qSelect.value));
qSelect.addEventListener('change', ()=>renderQ2(srSelect.value, fySelect.value, qSelect.value));
document.getElementById('filter-reset').addEventListener('click', ()=>{
  srSelect.value='All'; fySelect.value='All'; qSelect.value='All'; renderQ2('All','All','All');
});

renderQ2('All','All','All');

// family chart (static, global)
new Chart(document.getElementById('chart-q2-family'), {
  type:'bar',
  data:{ labels: DATA.q2.family_scores.map(f=>f.Family),
    datasets:[{label:'Composite Score', data: DATA.q2.family_scores.map(f=>f.CompositeScore),
      backgroundColor:[COLORS.navy,COLORS.teal,COLORS.amber,COLORS.gray]}] },
  options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}},
    scales:{y:{max:100, grid:{color:'#EEF1F4'}}, x:{grid:{display:false}}}}
});

// histogram (static, global population)
new Chart(document.getElementById('chart-q2-hist'), {
  type:'bar',
  data:{ labels: DATA.q2.histogram.map(h=>h.bin),
    datasets:[{label:'# Models', data: DATA.q2.histogram.map(h=>h.count), backgroundColor: COLORS.navy}] },
  options:{responsive:true, maintainAspectRatio:false, plugins:{legend:{display:false}},
    scales:{y:{grid:{color:'#EEF1F4'}, title:{display:true,text:'# Models',font:{size:10}}}, x:{grid:{display:false}, title:{display:true,text:'Composite Score Range',font:{size:10}}}}}
});

// scatter (static, global)
const scatterByFamily = {};
DATA.q2.scatter.forEach(r=>{
  if(!scatterByFamily[r.Family]) scatterByFamily[r.Family] = [];
  scatterByFamily[r.Family].push({x:r.WAPE, y:r.Hit10, model:r.Model});
});
new Chart(document.getElementById('chart-q2-scatter'), {
  type:'scatter',
  data:{ datasets: Object.keys(scatterByFamily).map(fam=>({
    label:fam, data:scatterByFamily[fam], backgroundColor:(COLORS.familyColors[fam]||COLORS.gray)+'CC', pointRadius:4
  }))},
  options:{responsive:true, maintainAspectRatio:false,
    plugins:{legend:{position:'bottom',labels:{boxWidth:10}}, tooltip:{callbacks:{label:(ctx)=>`${ctx.raw.model}: WAPE ${ctx.raw.x}%, Hit10 ${ctx.raw.y}%`}}},
    scales:{x:{title:{display:true,text:'WAPE %',font:{size:10}}, grid:{color:'#EEF1F4'}}, y:{title:{display:true,text:'Hit10 %',font:{size:10}}, grid:{color:'#EEF1F4'}}}}
});

// boxplot approximation: floating bar q1-q3 + median marker (static, global)
const boxLabels = DATA.q2.boxplot.map(b=>b.family);
new Chart(document.getElementById('chart-q2-box'), {
  type:'bar',
  data:{ labels: boxLabels,
    datasets:[
      {label:'IQR (Q1–Q3)', data: DATA.q2.boxplot.map(b=>[b.q1,b.q3]), backgroundColor: COLORS.teal+'55', borderColor: COLORS.teal, borderWidth:1.5, borderSkipped:false},
      {label:'Median', data: DATA.q2.boxplot.map(b=>[b.median-0.4,b.median+0.4]), backgroundColor: COLORS.navy, type:'bar'}
    ]},
  options:{responsive:true, maintainAspectRatio:false,
    plugins:{legend:{position:'bottom',labels:{boxWidth:10}}, tooltip:{callbacks:{label:(ctx)=>{
      const b = DATA.q2.boxplot[ctx.dataIndex];
      return ctx.datasetIndex===0 ? `Q1: ${b.q1}%  Q3: ${b.q3}%  (min ${b.min}%, max ${b.max}%, n=${b.n})` : `Median: ${b.median}%`;
    }}}},
    scales:{y:{title:{display:true,text:'WAPE %',font:{size:10}}, grid:{color:'#EEF1F4'}}, x:{grid:{display:false}}}}
});

