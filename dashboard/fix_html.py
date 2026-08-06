import os

with open('dashboard/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

target = """        <thead><tr><th>Week</th><th class="num">Segments Flagged</th><th class="num">Total Segments</th><th class="num">Share %</th><th>Typical Direction</th><th>Notable?</th><th>Passes Stricter Test?</th></tr></thead>
  if(document.getElementById('sa-total-weeks-2')) document.getElementById('sa-total-weeks-2').textContent = sa.n_weeks;"""

replacement = """        <thead><tr><th>Week</th><th class="num">Segments Flagged</th><th class="num">Total Segments</th><th class="num">Share %</th><th>Typical Direction</th><th>Notable?</th><th>Passes Stricter Test?</th></tr></thead>
        <tbody id="ad-body"></tbody>
      </table>
    </div>
  </div>
  <div class="footnote">Deterministic Decision Support Dashboard &middot; Point-in-time snapshot, generated per Current Engine Policy Specification (Parts 1&ndash;8) &middot; Evidence over narrative &middot; Observation before recommendation &middot; Recommendations omitted when confidence does not clear policy threshold.</div>
    </div>
  </div>
</div>

<script>
let GLOBAL_CHART_DATA = {};
let raw_data = {};
let GLOBAL_CURRENT_FILTERS = {
  Region: 'All',
  SubRegion: 'All',
  FiscalYear: 'All',
  Quarter: 'All',
  Channel: 'All'
};
const chartInstances = {};

const REGION_MAP = {
    'APJ': ['ANZ', 'CCC', 'IN', 'JPN', 'KR', 'SA'],
    'Americas': ['Brazil', 'LATAM', 'Multiple AMER SubRegions'],
    'EMEA': ['CER', 'EC', 'NER', 'SER', 'UKI']
};

document.addEventListener('DOMContentLoaded', () => {
  fetch('data/report.json?t=' + Date.now())
    .then(r => r.json())
    .then(payload => {
      raw_data = payload;
      GLOBAL_CHART_DATA = payload.chart_data.global_slices;
      
      const filters = payload.chart_data.filters || {};
      
      const regSelect = document.getElementById('gf-region') || document.getElementById('q1-filter-region');
      if (regSelect && filters.regions) {
         regSelect.innerHTML = '<option value="All">All Regions</option>' + 
           filters.regions.map(r => `<option value="${r}">${r}</option>`).join('');
         regSelect.addEventListener('change', (e) => {
             const region = e.target.value;
             GLOBAL_CURRENT_FILTERS.Region = region;
             
             const srSelect = document.getElementById('gf-subregion') || document.getElementById('q1-filter-subregion');
             if(srSelect) {
                 srSelect.innerHTML = '<option value="All">All Sub-Regions</option>';
                 const allowed = region === 'All' 
                     ? (filters.sub_regions || Object.values(REGION_MAP).flat())
                     : REGION_MAP[region] || [];
                 allowed.sort().forEach(sr => {
                     srSelect.innerHTML += `<option value="${sr}">${sr}</option>`;
                 });
             }
             GLOBAL_CURRENT_FILTERS.SubRegion = 'All';
             updateDashboardFromFilters();
         });
      }

      const srSelect = document.getElementById('gf-subregion') || document.getElementById('q1-filter-subregion');
      if (srSelect) {
         const srList = filters.sub_regions || Object.values(REGION_MAP).flat();
         srSelect.innerHTML = '<option value="All">All Sub-Regions</option>' + 
           srList.sort().map(r => `<option value="${r}">${r}</option>`).join('');
         srSelect.addEventListener('change', (e) => {
             const sr = e.target.value;
             GLOBAL_CURRENT_FILTERS.SubRegion = sr;
             
             if(sr !== 'All') {
                 // Auto-set region
                 for(const [reg, srs] of Object.entries(REGION_MAP)) {
                     if(srs.includes(sr)) {
                         GLOBAL_CURRENT_FILTERS.Region = reg;
                         if (regSelect) regSelect.value = reg;
                         break;
                     }
                 }
             }
             updateDashboardFromFilters();
         });
      }

      const fySelect = document.getElementById('gf-fiscalyear') || document.getElementById('q1-filter-fiscalyear');
      if(fySelect && filters.fiscal_years){
         fySelect.innerHTML = '<option value="All">All Years</option>' + filters.fiscal_years.map(y=>`<option value="${y}">${y}</option>`).join('');
         fySelect.addEventListener('change', e => { GLOBAL_CURRENT_FILTERS.FiscalYear = e.target.value; updateDashboardFromFilters(); });
      }

      const qSelect = document.getElementById('gf-quarter') || document.getElementById('q1-filter-quarter');
      if(qSelect && filters.quarters){
         qSelect.innerHTML = '<option value="All">All Quarters</option>' + filters.quarters.map(q=>`<option value="${q}">${q}</option>`).join('');
         qSelect.addEventListener('change', e => { GLOBAL_CURRENT_FILTERS.Quarter = e.target.value; updateDashboardFromFilters(); });
      }
      
      const chSelect = document.getElementById('gf-channel');
      if(chSelect && filters.channels){
         chSelect.innerHTML = '<option value="All">All Channels</option>' + filters.channels.map(q=>`<option value="${q}">${q}</option>`).join('');
         chSelect.addEventListener('change', e => { GLOBAL_CURRENT_FILTERS.Channel = e.target.value; updateDashboardFromFilters(); });
      }

      const resetBtn = document.getElementById('gf-reset') || document.getElementById('q1-filter-reset');
      if(resetBtn){
         resetBtn.addEventListener('click', () => {
             GLOBAL_CURRENT_FILTERS = { Region: 'All', SubRegion: 'All', FiscalYear: 'All', Quarter: 'All', Channel: 'All' };
             if(regSelect) regSelect.value = 'All';
             if(srSelect) {
                 const srList = filters.sub_regions || Object.values(REGION_MAP).flat();
                 srSelect.innerHTML = '<option value="All">All Sub-Regions</option>' + srList.sort().map(r => `<option value="${r}">${r}</option>`).join('');
                 srSelect.value = 'All';
             }
             if(fySelect) fySelect.value = 'All';
             if(qSelect) qSelect.value = 'All';
             if(chSelect) chSelect.value = 'All';
             updateDashboardFromFilters();
         });
      }

      updateDashboardFromFilters();
    });

  // Nav logic
  document.querySelectorAll('.rail-item').forEach(el => {
    el.addEventListener('click', () => {
      document.querySelectorAll('.rail-item').forEach(i => i.classList.remove('active'));
      document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
      el.classList.add('active');
      const pageId = 'page-' + el.getAttribute('data-page');
      const pageEl = document.getElementById(pageId);
      if(pageEl) pageEl.classList.add('active');
    });
  });

  document.querySelectorAll('.nav-card').forEach(el => {
    el.addEventListener('click', () => {
      const target = el.getAttribute('data-nav');
      const navItem = document.querySelector(`.rail-item[data-page="${target}"]`);
      if(navItem) navItem.click();
    });
  });
});

function getSliceKey(f) {
  return `${f.Region}|${f.SubRegion}|${f.FiscalYear}|${f.Quarter}|${f.Channel}`;
}

function updateDashboardFromFilters() {
  const key = getSliceKey(GLOBAL_CURRENT_FILTERS);
  const slice_data = GLOBAL_CHART_DATA[key];
  if(!slice_data) {
     console.warn("No data for slice", key);
     return;
  }
  
  // Update pills
  const pillsEl = document.getElementById('gf-pills') || document.getElementById('q1-filter-pills');
  if(pillsEl) {
     let htmlText = '';
     if(GLOBAL_CURRENT_FILTERS.Region !== 'All') htmlText += `<div class="pill">Region: ${GLOBAL_CURRENT_FILTERS.Region}</div>`;
     if(GLOBAL_CURRENT_FILTERS.SubRegion !== 'All') htmlText += `<div class="pill">SubRegion: ${GLOBAL_CURRENT_FILTERS.SubRegion}</div>`;
     if(GLOBAL_CURRENT_FILTERS.FiscalYear !== 'All') htmlText += `<div class="pill">FY: ${GLOBAL_CURRENT_FILTERS.FiscalYear}</div>`;
     if(GLOBAL_CURRENT_FILTERS.Quarter !== 'All') htmlText += `<div class="pill">Q: ${GLOBAL_CURRENT_FILTERS.Quarter}</div>`;
     if(GLOBAL_CURRENT_FILTERS.Channel !== 'All') htmlText += `<div class="pill">Channel: ${GLOBAL_CURRENT_FILTERS.Channel}</div>`;
     if(htmlText === '') htmlText = `<div class="pill neutral">Global (All Data)</div>`;
     pillsEl.innerHTML = htmlText;
  }
  
  initDashboard(slice_data);
}

function initDashboard(payload) {
const COLORS = { navy:'#101B33', teal:'#2F6F63', amber:'#C98A2C', rust:'#B3452B', gray:'#8A94A3',
  familyColors: {Prophet:'#101B33', ARIMA:'#2F6F63', LR_LA_group:'#C98A2C', XGB_group:'#8A94A3'} };

function chip(level){ 
  if (!level) return `<span class="chip low">Low Confidence</span>`; 
  if (level === 'INCONCLUSIVE') return `<span class="chip" style="background:#4A5568; color:white;">Inconclusive</span>`;
  return `<span class="chip ${level.toLowerCase()}">${level} Confidence</span>`; 
}

  let DATA = payload;
  DATA.meta = raw_data.metadata || {};
  
  const e = raw_data.sections && raw_data.sections.length > 0 ? raw_data.sections[0] : {};
  DATA.executive = {
    decision: (e.operational_decision || {}).decision || '',
    reasoning: (e.operational_decision || {}).reasoning || '',
    evidence: e.key_evidence || []
  };

  const getM = (arr, id) => {
      const f = (arr||[]).find(x => x.metric_id === id);
      return f ? f.value.replace('%', '') : '0';
  };
  
  const sec1 = payload.q1 || {};
  const sec2 = payload.q2 || {};
  const sec3 = payload.q3 || {};
  const sec4 = payload.q4 || {};
  
  const sa = payload.q1 ? payload.q1.stats : {};
  
  if(document.getElementById('sa-total-weeks-2')) document.getElementById('sa-total-weeks-2').textContent = sa.n_weeks;"""

if target in html:
    new_html = html.replace(target, replacement)
    with open('dashboard/index.html', 'w', encoding='utf-8') as f:
        f.write(new_html)
    print("Replacement successful!")
else:
    print("Target not found. Doing fallback match...")
    target_start = '        <thead><tr><th>Week</th><th class="num">Segments Flagged</th><th class="num">Total Segments</th><th class="num">Share %</th><th>Typical Direction</th><th>Notable?</th><th>Passes Stricter Test?</th></tr></thead>'
    if target_start in html:
        prefix = html.split(target_start)[0] + target_start
        suffix = "  if(document.getElementById('sa-total-weeks-2')) document.getElementById('sa-total-weeks-2').textContent = sa.n_weeks;" + html.split("  if(document.getElementById('sa-total-weeks-2')) document.getElementById('sa-total-weeks-2').textContent = sa.n_weeks;")[1]
        
        replacement_middle = replacement.replace(target_start, "").replace("  if(document.getElementById('sa-total-weeks-2')) document.getElementById('sa-total-weeks-2').textContent = sa.n_weeks;", "")
        with open('dashboard/index.html', 'w', encoding='utf-8') as f:
             f.write(prefix + replacement_middle + suffix)
        print("Fallback replacement successful!")
    else:
        print("Target start NOT found.")
