let RAW_LEVEL0 = [];
let RAW_LEVEL1 = [];
let ORIGINAL_RAW_LEVEL1 = [];
let SA_TREND_CHART = null;
const GLOBAL_COLOR_MANUAL = '#B7C3D4';
let HIERARCHY_PATH = ['Global', 'Region', 'SubRegion', 'Offering'];

// NEW: Shared State
window.TIME_GRAIN = 'week';
window.CURRENT_FILTERS = { nodeName: 'Global', levelName: 'Global', filters: {} };
window.GLOBAL_BASE_FILTERS = { nodeName: 'Global', levelName: 'Global', filters: {} };
window.CLASSIFICATION_FILTER = '';

if (typeof ChartDataLabels !== 'undefined' && typeof Chart !== 'undefined') {
    Chart.register(ChartDataLabels);
    Chart.defaults.plugins.datalabels = { display: false };
}

// Navigation
function nav(pageId) {
    try { localStorage.setItem('activeDashboardTab', pageId); } catch(e) {}
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.rail-item').forEach(i => i.classList.remove('active'));
    
    // Close menu if open
    const rail = document.querySelector('.rail');
    const overlay = document.getElementById('menu-overlay');
    if (rail) rail.classList.remove('open');
    if (overlay) overlay.classList.remove('active');
    
    const pageEl = document.getElementById('page-' + pageId);
    if(pageEl) pageEl.classList.add('active');
    
    const tab = document.querySelector(`.rail-item[data-page="${pageId}"]`);
    if(tab) tab.classList.add('active');
    
    // Update dashboard title based on page context
    const titles = {
        'exec': 'Executive Summary',
        'sa': 'Strategy Assessment',
        'mc': 'Model Champion',
        'bc': 'Business Context',
        'ad': 'Anomaly Detection'
    };
    const titleEl = document.getElementById('dash-title');
    if (titleEl && titles[pageId]) {
        titleEl.innerHTML = `Forecast Intelligence: <span style="font-weight:300; opacity:0.8">${titles[pageId]}</span>`;
    }
    
    // Trigger module-specific rendering using the shared state
    if(pageId === 'exec') renderExecutiveOverview();
    if(pageId === 'mc') renderModelChampion();
    if(pageId === 'bc') renderBusinessContext();
    if(pageId === 'sa' && window.CURRENT_FILTERS) {
        renderTrendPanel(window.CURRENT_FILTERS.nodeName, window.CURRENT_FILTERS.levelName, window.CURRENT_FILTERS.filters);
        const currentGroups = computeHierarchyRollup(RAW_LEVEL1, window.CURRENT_FILTERS.levelName, window.CURRENT_FILTERS.filters);
        const thisNode = currentGroups.find(g => g.Node === window.CURRENT_FILTERS.nodeName);
        
        updateSA_KPIs(thisNode, currentGroups, window.CURRENT_FILTERS.levelName);
        
        if (thisNode) {
            const allFilters = { ...window.CURRENT_FILTERS.filters };
            if (window.CURRENT_FILTERS.levelName !== 'Global') allFilters[window.CURRENT_FILTERS.levelName] = window.CURRENT_FILTERS.nodeName;
            renderRootCausePanel(window.CURRENT_FILTERS.nodeName, window.CURRENT_FILTERS.levelName, allFilters);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Menu toggle logic
    const menuToggle = document.getElementById('menu-toggle');
    const menuClose = document.getElementById('menu-close');
    const rail = document.getElementById('main-rail');
    const overlay = document.getElementById('menu-overlay');
    
    if (menuToggle && rail && overlay) {
        menuToggle.addEventListener('click', () => {
            rail.classList.toggle('collapsed');
            overlay.classList.toggle('active');
        });
        
        if (menuClose) {
            menuClose.addEventListener('click', () => {
                rail.classList.add('collapsed');
                overlay.classList.remove('active');
            });
        }
        
        overlay.addEventListener('click', () => {
            rail.classList.add('collapsed');
            overlay.classList.remove('active');
        });
    }

    // Bind nav
    document.querySelectorAll('.rail-item').forEach(item => {
        if(item.hasAttribute('data-page')) {
            item.addEventListener('click', () => {
                nav(item.getAttribute('data-page'));
                if (rail && overlay) {
                    rail.classList.add('collapsed');
                    overlay.classList.remove('active');
                }
            });
        }
    });

    // Hide old global variables and hooks if they exist in inline script

    window.GLOBAL_CURRENT_FILTERS = null;
    
    // Use statically injected payload to avoid CORS on file:///
    try {
        const data = window.REPORT_DATA;
        if (!data) throw new Error("REPORT_DATA not found. Ensure data/report.js is loaded.");
        
        RAW_LEVEL0 = data.level0 || [];
        
        // Clean up missing hierarchical data to ensure rollups work naturally
        RAW_LEVEL0.forEach(row => {
            if (!row.SubRegion) {
                if (row.Region === 'Americas') row.SubRegion = 'Multiple AMER SubRegions';
                else if (row.Region === 'APJ') row.SubRegion = 'Multiple APJ SubRegions';
                else if (row.Region === 'EMEA') row.SubRegion = 'Multiple EMEA SubRegions';
                else row.SubRegion = 'Unspecified SubRegion';
            }
            if (!row.Country) {
                if (row.Region === 'Americas') row.Country = 'Multiple AMER Countries';
                else if (row.Region === 'APJ') row.Country = 'Multiple APJ Countries';
                else if (row.Region === 'EMEA') row.Country = 'Multiple EMEA Countries';
                else row.Country = 'Unspecified Country';
            }
            if (!row.Offering) {
                if (row.Region === 'Americas') row.Offering = 'Multiple AMER Offerings';
                else if (row.Region === 'APJ') row.Offering = 'Multiple APJ Offerings';
                else if (row.Region === 'EMEA') row.Offering = 'Multiple EMEA Offerings';
                else row.Offering = 'Unspecified Offering';
            }
            if (!row.Channel) {
                if (row.Region === 'Americas') row.Channel = 'Multiple AMER Channels';
                else if (row.Region === 'APJ') row.Channel = 'Multiple APJ Channels';
                else if (row.Region === 'EMEA') row.Channel = 'Multiple EMEA Channels';
                else row.Channel = 'Unspecified Channel';
            }
        });
        RAW_LEVEL1 = rebuildLevel1(RAW_LEVEL0); // Force bottom-up calculation on load
        ORIGINAL_RAW_LEVEL1 = [...RAW_LEVEL1];
        
        // Always set title/period (removes "Loading..." placeholder)
        const titleEl = document.getElementById('dash-title');
        const activeTab = document.querySelector('.rail-item.active');
        const titles = { 'exec': 'Executive Summary', 'sa': 'Strategy Assessment', 'mc': 'Model Champion', 'bc': 'Business Context' };
        const activePageId = activeTab ? activeTab.getAttribute('data-page') : 'exec';
        if (titleEl) titleEl.innerHTML = `Forecast Intelligence: <span style="font-weight:300; opacity:0.8">${titles[activePageId]}</span>`;
        const periodEl = document.getElementById('dash-period');
        if (periodEl) periodEl.textContent = (data.meta && data.meta.period) || '';
        
        // Populate header stats
        const recEl = document.getElementById('dash-records');
        if (recEl) recEl.textContent = RAW_LEVEL0.length.toLocaleString();
        const modEl = document.getElementById('dash-models');
        if (modEl) modEl.textContent = [...new Set(RAW_LEVEL0.map(r => r.Model).filter(Boolean))].length;
        
        populateGlobalFilters(); 
        initStrategyAssessment();
        
        let savedTab = 'exec';
        try { savedTab = localStorage.getItem('activeDashboardTab') || 'exec'; } catch(e) {}
        nav(savedTab);
    } catch(err) {
        console.error("Error loading report data", err);
        const decEl = document.getElementById('exec-decision');
        if (decEl) decEl.innerHTML = '<span style="color:var(--rust); font-size:16px;">Error: ' + err.message + '</span>';
    }


    const dimSwap = document.getElementById('sa-dim-swap');
    if (dimSwap) {
        dimSwap.addEventListener('change', (e) => {
            const val = e.target.value;
            if (val === 'default') {
                HIERARCHY_PATH = ['Global', 'Region', 'SubRegion', 'Offering'];
            } else if (val === 'offering_first') {
                HIERARCHY_PATH = ['Global', 'Offering', 'Region', 'SubRegion'];
            }
            // re-render the hierarchy table and clear expansion state to prevent errors
            expandedRows.clear();
            renderHierarchyTable();
        });
    }

});

function updateScope(nodeName, levelName, filters) {
    window.TIME_GRAIN = 'week';
    window.CURRENT_FILTERS = { nodeName, levelName, filters };
    
    // Sync global dropdowns with the new scope filters
    const gfIds = ['Region', 'SubRegion', 'Country', 'Offering', 'Fiscal_Week', 'Channel'];
    gfIds.forEach(col => {
        const id = 'gf-' + col.toLowerCase() + '-container';
        const container = document.getElementById(id);
        if (container) {
            const checkboxes = container.querySelectorAll('input[type="checkbox"]');
            const btnText = container.querySelector('.btn-text');
            const displayName = col.replace('_', ' ');
            
            checkboxes.forEach(cb => {
                if (filters[col] && filters[col].includes(cb.value)) {
                    cb.checked = true;
                } else {
                    cb.checked = false;
                }
            });
            
            if (filters[col] && filters[col].length > 0 && filters[col].length < checkboxes.length) {
                btnText.innerHTML = `${displayName} <span class="custom-select-badge">${filters[col].length}</span>`;
            } else {
                btnText.innerHTML = displayName;
            }
        }
    });

    // Update the UI
    
    // 1. Update Scope Pill
    const pill = document.getElementById('gf-scope-pill');
    const pillText = document.getElementById('gf-scope-text');
    if (pill && pillText) {
        if (levelName === 'Global') {
            pill.style.display = 'none';
        } else {
            pill.style.display = 'flex';
            pillText.textContent = `Scope: ${nodeName}`;
        }
    }
    
    // Update Scoped Captions
    const captionText = levelName === 'Global' ? 'Scoped to: All' : `Scoped to: ${nodeName}`;
    const mcNote = document.getElementById('mc-count-note');
    if (mcNote) mcNote.textContent = captionText;
    
    const activePage = document.querySelector('.rail-item.active').getAttribute('data-page');
    if (activePage === 'sa') {
        renderTrendPanel(nodeName, levelName, filters);
        
        // Root Cause Panel Logic
        const allFilters = { ...filters };
        if (levelName !== 'Global') allFilters[levelName] = nodeName;
        const currentGroups = computeHierarchyRollup(RAW_LEVEL1, levelName, filters);
        const thisNode = currentGroups.find(g => g.Node === nodeName);
        
        // Need to wait for next tick for sa-ts to exist and be populated... wait no, we just populate them now
        updateSA_KPIs(thisNode, currentGroups, levelName);
        
        if (thisNode) {
            renderRootCausePanel(nodeName, levelName, allFilters);
        }
    } else if (activePage === 'mc') {
        renderModelChampion();
    } else if (activePage === 'bc') {
        renderBusinessContext();
    } else if (activePage === 'exec') {
        renderExecutiveOverview();
    }
    
    renderQueueFlatTable(nodeName, levelName, filters);
}

function updateSA_KPIs(thisNode, currentGroups, levelName) {
    let nodeData = thisNode;
    if (levelName === 'Global') {
        nodeData = currentGroups[0];
    }
    if (!nodeData) return;
    
    // Get filtered queue data — apply ALL active dropdown filters
    let queues = RAW_LEVEL1;
    const activeFilters = window.CURRENT_FILTERS.filters || {};
    for (const [k, v] of Object.entries(activeFilters)) {
        if (v) {
            queues = queues.filter(q => v.includes(String(q[k])));
        }
    }
    
    // Apply classification filter if set
    const classFilter = window.CLASSIFICATION_FILTER || [];
    if (classFilter.length > 0) {
        queues = queues.filter(q => classFilter.includes(q.Classification));
    }
    
    const totalQueues = queues.length;
    const smlCount = queues.filter(q => q.Classification === 'Strong ML').length;
    const hybCount = queues.filter(q => q.Classification === 'Hybrid').length;
    const manCount = queues.filter(q => q.Classification === 'Manual').length;
    
    // Total volume
    const totalVol = queues.reduce((s, q) => s + (q.Queue_Actual_Sum || 0), 0);
    
    // Volume-weighted WAPE
    const totalMLErr = queues.reduce((s, q) => s + (q.Queue_ML_Err_Sum || 0), 0);
    const totalManErr = queues.reduce((s, q) => s + (q.Queue_Manual_Err_Sum || 0), 0);
    const mlWape = totalVol ? (totalMLErr / totalVol * 100) : 0;
    const manWape = totalVol ? (totalManErr / totalVol * 100) : 0;
    
    // Populate overview strip
    const el = id => document.getElementById(id);
    
    const elTotalQ = el('sa-ov-total-queues');
    if (elTotalQ) elTotalQ.textContent = totalQueues;
    
    const elTotalVol = el('sa-ov-total-volume');
    if (elTotalVol) elTotalVol.textContent = 'Vol: ' + (totalVol >= 1000000 ? (totalVol/1000000).toFixed(1) + 'M' : totalVol >= 1000 ? (totalVol/1000).toFixed(1) + 'K' : Math.round(totalVol).toLocaleString());
    
    const elSml = el('sa-ov-sml-count');
    if (elSml) elSml.textContent = smlCount;
    const elSmlPct = el('sa-ov-sml-pct');
    if (elSmlPct) elSmlPct.textContent = totalQueues ? (smlCount/totalQueues*100).toFixed(0) + '% of queues' : '-';
    
    const elHyb = el('sa-ov-hyb-count');
    if (elHyb) elHyb.textContent = hybCount;
    const elHybPct = el('sa-ov-hyb-pct');
    if (elHybPct) elHybPct.textContent = totalQueues ? (hybCount/totalQueues*100).toFixed(0) + '% of queues' : '-';
    
    const elMan = el('sa-ov-man-count');
    if (elMan) elMan.textContent = manCount;
    const elManPct = el('sa-ov-man-pct');
    if (elManPct) elManPct.textContent = totalQueues ? (manCount/totalQueues*100).toFixed(0) + '% of queues' : '-';
    
    const elMlWape = el('sa-ov-ml-wape');
    if (elMlWape) {
        elMlWape.textContent = mlWape.toFixed(1) + '%';
        elMlWape.style.color = mlWape < manWape ? 'var(--teal)' : 'var(--navy)';
    }
    
    const elManWape = el('sa-ov-man-wape');
    if (elManWape) {
        elManWape.textContent = manWape.toFixed(1) + '%';
        elManWape.style.color = manWape < mlWape ? 'var(--teal)' : 'var(--navy)';
    }
}

// Helper to calculate group class (duplicated logic for rc trigger)
function getGroupClass(g) {
    const volPct = parseFloat(g.Vol_Pct_Strong_ML) || 0;
    if (volPct >= 60) return 'Strong ML';
    if (volPct >= 40) return 'Hybrid';
    return 'Manual';
}

function initStrategyAssessment() {
    const baseLevel = window.GLOBAL_BASE_FILTERS.levelName || 'Global';
    const baseFilters = window.GLOBAL_BASE_FILTERS.filters || {};
    
    // Build Top Strip using the Base Level Rollup
    const globalRollup = computeHierarchyRollup(RAW_LEVEL1, baseLevel, baseFilters);
    const globalData = globalRollup[0]; // There is only one global row
    if (!globalData) return;
    
    updateSA_KPIs(globalData, globalRollup, baseLevel);
    
    const elStrong = document.getElementById('sa-leg-strong'); if(elStrong) elStrong.textContent = `Strong ML (${(globalData.Vol_Pct_Strong_ML || 0).toFixed(0)}%)`;
    const elHybrid = document.getElementById('sa-leg-hybrid'); if(elHybrid) elHybrid.textContent = `Hybrid (${(globalData.Vol_Pct_Hybrid || 0).toFixed(0)}%)`;
    const elManual = document.getElementById('sa-leg-manual'); if(elManual) elManual.textContent = `Manual (${(globalData.Vol_Pct_Manual || 0).toFixed(0)}%)`;

    // Initialize Hierarchy Table
    renderHierarchyTable();
    
    // Populate Flat Queue Table using current active filters
    const curNode = window.CURRENT_FILTERS.nodeName || 'Global';
    const curLevel = window.CURRENT_FILTERS.levelName || 'Global';
    const curFilters = window.CURRENT_FILTERS.filters || {};
    renderQueueFlatTable(curNode, curLevel, curFilters);
    
    renderExecutiveOverview();
    // (End of initStrategyAssessment)
}

function rebuildLevel1(data0) {
    const queueMap = {};
    data0.forEach(r => {
        if (!queueMap[r.Forecast_Name]) {
            queueMap[r.Forecast_Name] = {
                Forecast_Name: r.Forecast_Name,
                Queue_Actual_Sum: 0, Queue_Manual_Err_Sum: 0, Queue_ML_Err_Sum: 0,
                Valid_Weeks_Count: 0, ML_Win_Count: 0,
                Region: r.Region, SubRegion: r.SubRegion, Country: r.Country,
                Offering: r.Offering, Channel: r.Channel
            };
        }
        const q = queueMap[r.Forecast_Name];
        if (!q.Hist_Mean && r['Mean (Hist. Contacts) (Last 1 yr.)']) {
            q.Hist_Mean = r['Mean (Hist. Contacts) (Last 1 yr.)'];
            q.Hist_Std = r['Std Dev (Hist. Contacts)'];
        }
        q.Queue_Actual_Sum += (r.Actual_Offered || 0);
        q.Queue_Manual_Err_Sum += (r.Manual_Abs_Err || 0);
        q.Queue_ML_Err_Sum += (r.ML_Abs_Err || 0);
        q.Valid_Weeks_Count += 1;
        if (r.Winner === 'ML') q.ML_Win_Count += 1;
    });
    
    const level1 = [];
    for (const q of Object.values(queueMap)) {
        q.Queue_WAPE_Manual = q.Queue_Actual_Sum ? (q.Queue_Manual_Err_Sum / q.Queue_Actual_Sum) : 0;
        q.Queue_WAPE_ML = q.Queue_Actual_Sum ? (q.Queue_ML_Err_Sum / q.Queue_Actual_Sum) : 0;
        q.Queue_WAPE_Prev_Year = q.Hist_Mean > 0 ? ((0.8 * q.Hist_Std) / q.Hist_Mean) : 0;
        q.Queue_Winner_By_WAPE = (q.Queue_WAPE_ML <= q.Queue_WAPE_Manual) ? 'ML' : 'Manual';
        
        const mlWinPct = q.Valid_Weeks_Count ? (q.ML_Win_Count / q.Valid_Weeks_Count) : 0;
        q.Weeks_ML_Wins_Pct = mlWinPct * 100;
        
        if (q.Valid_Weeks_Count === 0) {
            q.Classification = 'No Data';
        } else if (mlWinPct >= 0.60) {
            q.Classification = 'Strong ML';
        } else if (mlWinPct >= 0.40) {
            q.Classification = 'Hybrid';
        } else {
            q.Classification = 'Manual';
        }
        
        if (q.Valid_Weeks_Count >= 10) {
            q.Confidence = 'High';
        } else if (q.Valid_Weeks_Count >= 4) {
            q.Confidence = 'Medium';
        } else {
            q.Confidence = 'Low';
        }
        
        level1.push(q);
    }
    return level1;
}

function populateGlobalFilters() {
    const gfIds = ['Region', 'SubRegion', 'Country', 'Offering', 'Fiscal_Week', 'Channel', 'Classification'];
    gfIds.forEach(col => {
        const id = 'gf-' + col.toLowerCase() + '-container';
        const container = document.getElementById(id);
        if (!container) return;
        
        let uniqueVals = [];
        if (col === 'Classification') {
            uniqueVals = ['Strong ML', 'Hybrid', 'Manual'];
        } else {
            uniqueVals = [...new Set(RAW_LEVEL0.map(r => r[col]).filter(v => v))].sort();
        }
        
        const displayName = col.replace('_', ' ');
        
        container.innerHTML = `
            <button class="custom-select-btn" id="btn-${col}">
                <span class="btn-text">${displayName}</span>
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M7 10l5 5 5-5z"/></svg>
            </button>
            <div class="custom-select-menu" id="menu-${col}">
                <div class="custom-select-search">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
                    <input type="text" placeholder="Search ${displayName}...">
                </div>
                <div class="custom-select-actions">
                    <span class="action-select-all">Select All</span>
                    <span class="action-clear-all">Clear All</span>
                </div>
                <div class="custom-select-options">
                    ${uniqueVals.map(v => `
                        <label class="custom-select-option">
                            <input type="checkbox" value="${v}">
                            <span>${v}</span>
                        </label>
                    `).join('')}
                </div>
            </div>
        `;
        
        const btn = container.querySelector('.custom-select-btn');
        const menu = container.querySelector('.custom-select-menu');
        const searchInput = container.querySelector('input[type="text"]');
        const selectAllBtn = container.querySelector('.action-select-all');
        const clearAllBtn = container.querySelector('.action-clear-all');
        const optionsContainer = container.querySelector('.custom-select-options');
        const checkboxes = container.querySelectorAll('input[type="checkbox"]');
        const btnText = container.querySelector('.btn-text');
        
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = menu.classList.contains('open');
            document.querySelectorAll('.custom-select-menu').forEach(m => m.classList.remove('open'));
            if (!isOpen) {
                menu.classList.add('open');
                searchInput.focus();
            }
        });
        
        document.addEventListener('click', (e) => {
            if (!container.contains(e.target)) {
                menu.classList.remove('open');
            }
        });
        
        menu.addEventListener('click', e => e.stopPropagation());
        
        searchInput.addEventListener('input', (e) => {
            const val = e.target.value.toLowerCase();
            optionsContainer.querySelectorAll('.custom-select-option').forEach(opt => {
                const txt = opt.querySelector('span').textContent.toLowerCase();
                opt.style.display = txt.includes(val) ? 'flex' : 'none';
            });
        });
        
        selectAllBtn.addEventListener('click', () => {
            let changed = false;
            optionsContainer.querySelectorAll('.custom-select-option').forEach(opt => {
                if (opt.style.display !== 'none') {
                    const cb = opt.querySelector('input');
                    if (!cb.checked) { cb.checked = true; changed = true; }
                }
            });
            if (changed) updateBadgeAndApply(col, checkboxes, btnText, displayName);
        });
        
        clearAllBtn.addEventListener('click', () => {
            let changed = false;
            optionsContainer.querySelectorAll('.custom-select-option').forEach(opt => {
                if (opt.style.display !== 'none') {
                    const cb = opt.querySelector('input');
                    if (cb.checked) { cb.checked = false; changed = true; }
                }
            });
            if (changed) updateBadgeAndApply(col, checkboxes, btnText, displayName);
        });
        
        checkboxes.forEach(cb => {
            cb.addEventListener('change', () => updateBadgeAndApply(col, checkboxes, btnText, displayName));
        });
    });
    
    const resetBtn = document.getElementById('gf-reset');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            resetAllCustomSelects();
            applyAllFilters();
        });
    }
    
    const scopeClear = document.getElementById('gf-scope-clear');
    if (scopeClear) {
        scopeClear.addEventListener('click', () => {
            resetAllCustomSelects();
            applyAllFilters();
        });
    }
}

function updateBadgeAndApply(col, checkboxes, btnText, displayName) {
    const checkedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
    if (checkedCount === 0 || checkedCount === checkboxes.length) {
        btnText.innerHTML = displayName;
    } else {
        btnText.innerHTML = `${displayName} <span class="custom-select-badge">${checkedCount}</span>`;
    }
    applyAllFilters();
}

function resetAllCustomSelects() {
    const gfIds = ['Region', 'SubRegion', 'Country', 'Offering', 'Fiscal_Week', 'Channel', 'Classification'];
    gfIds.forEach(col => {
        const id = 'gf-' + col.toLowerCase() + '-container';
        const container = document.getElementById(id);
        if (!container) return;
        const checkboxes = container.querySelectorAll('input[type="checkbox"]');
        const btnText = container.querySelector('.btn-text');
        checkboxes.forEach(cb => cb.checked = false);
        btnText.innerHTML = col.replace('_', ' ');
    });
    window.GLOBAL_BASE_FILTERS = { nodeName: 'Global', levelName: 'Global', filters: {} };
    window.CLASSIFICATION_FILTER = [];
}

function applyAllFilters() {
    const gfIds = ['Region', 'SubRegion', 'Country', 'Offering', 'Fiscal_Week', 'Channel'];
    let currentLevel = 'Global';
    let currentNode = 'Global';
    let filters = {};
    
    gfIds.forEach(c => {
        const id = 'gf-' + c.toLowerCase() + '-container';
        const container = document.getElementById(id);
        if (container) {
            const checkboxes = Array.from(container.querySelectorAll('input[type="checkbox"]'));
            const checked = checkboxes.filter(cb => cb.checked).map(cb => cb.value);
            if (checked.length > 0 && checked.length < checkboxes.length) {
                filters[c] = checked;
                currentLevel = c;
                currentNode = checked.length === 1 ? checked[0] : `Multiple ${c}s`;
            }
        }
    });
    
    window.GLOBAL_BASE_FILTERS = { nodeName: currentNode, levelName: currentLevel, filters: filters };
    window.CURRENT_FILTERS = { nodeName: currentNode, levelName: currentLevel, filters: filters };
    
    if (filters['Fiscal_Week'] && filters['Fiscal_Week'].length > 0) {
        const fwList = filters['Fiscal_Week'];
        const filteredL0 = RAW_LEVEL0.filter(r => fwList.includes(String(r.Fiscal_Week)));
        RAW_LEVEL1 = rebuildLevel1(filteredL0);
    } else {
        RAW_LEVEL1 = [...ORIGINAL_RAW_LEVEL1];
    }
    
    const classContainer = document.getElementById('gf-classification-container');
    if (classContainer) {
        const checkboxes = Array.from(classContainer.querySelectorAll('input[type="checkbox"]'));
        const checked = checkboxes.filter(cb => cb.checked).map(cb => cb.value);
        window.CLASSIFICATION_FILTER = (checked.length > 0 && checked.length < checkboxes.length) ? checked : [];
    } else {
        window.CLASSIFICATION_FILTER = [];
    }
    
    initStrategyAssessment();
    updateScope(currentNode, currentLevel, filters);
}

// Reusable: set a single global filter (clearing the others) and re-render everything.
// Used by the in-line risk badges (1.3) and cross-filtering from visuals (1.2).
window.applyGlobalFilter = function(column, values) {
    const gfIds = ['Region','SubRegion','Country','Offering','Fiscal_Week','Channel','Classification'];
    gfIds.forEach(col => {
        const c = document.getElementById('gf-' + col.toLowerCase() + '-container');
        if (!c) return;
        c.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
        const bt = c.querySelector('.btn-text'); if (bt) bt.innerHTML = col.replace('_',' ');
    });
    const cont = document.getElementById('gf-' + String(column).toLowerCase() + '-container');
    if (cont) {
        const vals = values.map(String);
        cont.querySelectorAll('input[type="checkbox"]').forEach(cb => { if (vals.includes(String(cb.value))) cb.checked = true; });
        const checkedCount = Array.from(cont.querySelectorAll('input[type="checkbox"]')).filter(cb => cb.checked).length;
        const bt = cont.querySelector('.btn-text'); const disp = String(column).replace('_',' ');
        if (bt) bt.innerHTML = checkedCount > 0 ? (disp + ' <span class="custom-select-badge">' + checkedCount + '</span>') : disp;
    }
    applyAllFilters();
};

// 1.3 : jump from an in-line risk badge straight to Business Context, pre-filtered to the node.
window.jumpToContext = function(level, node) {
    const filterable = ['Region','SubRegion','Country','Offering','Channel'];
    if (level && filterable.includes(level)) applyGlobalFilter(level, [node]);
    nav('bc');
    window.scrollTo({ top: 0, behavior: 'smooth' });
};

function renderExecutiveOverview() {
    const nodeName = window.CURRENT_FILTERS.nodeName;
    const levelName = window.CURRENT_FILTERS.levelName;
    const filters = window.CURRENT_FILTERS.filters;
    let targetL0 = RAW_LEVEL0;
    for (const [k, v] of Object.entries(filters)) {
        if (k !== 'Global') targetL0 = targetL0.filter(row => v.includes(String(row[k])));
    }
    
    // Apply classification filter if set
    const classFilter = window.CLASSIFICATION_FILTER || [];
    if (classFilter.length > 0) {
        const allowedForecasts = new Set(
            RAW_LEVEL1.filter(q => classFilter.includes(q.Classification)).map(q => q.Forecast_Name)
        );
        targetL0 = targetL0.filter(row => allowedForecasts.has(row.Forecast_Name));
    }

    // Compute basic stats
    let totalVol = 0;
    let manualErr = 0;
    let mlErr = 0;
    let mlWins = 0;
    let totalWeeks = 0;
    let modelCount = 4; // Placeholder
    
    // Group by week for wins and anomalies
    const weeks = {};
    targetL0.forEach(row => {
        totalVol += (row.Actual_Offered || 0);
        manualErr += (row.Manual_Abs_Err || 0);
        mlErr += (row.ML_Abs_Err || 0);
        
        const w = row.Week_Ending;
        if(!weeks[w]) weeks[w] = { act: 0, man: 0, ml: 0, manErr: 0, mlErr: 0 };
        weeks[w].act += (row.Actual_Offered || 0);
        weeks[w].man += (parseFloat(row.Manual_Forecast) || 0);
        weeks[w].ml += (parseFloat(row.ML_Forecast) || 0);
        weeks[w].manErr += (row.Manual_Abs_Err || 0);
        weeks[w].mlErr += (row.ML_Abs_Err || 0);
    });
    
    let winCount = 0;
    let validW = 0;
    for(const w in weeks) {
        const d = weeks[w];
        if(d.act > 0) {
            validW++;
            const mErr = d.manErr;
            const mlErrW = d.mlErr;
            if (mlErrW < mErr) winCount++;
        }
    }
    
    const manualWape = totalVol > 0 ? (manualErr / totalVol * 100).toFixed(1) : '-';
    const mlWape = totalVol > 0 ? (mlErr / totalVol * 100).toFixed(1) : '-';
    const winRate = validW > 0 ? (winCount / validW * 100).toFixed(0) : 0;
    
    const globalRollup = computeHierarchyRollup(RAW_LEVEL1, 'Global', window.CURRENT_FILTERS.filters)[0];
    const decisionState = globalRollup ? globalRollup.Decision_State : 'Manual';
    const isMlWin = decisionState === 'ML';
    const isHybrid = decisionState === 'Hybrid';
    
    // Update DOM
    const decEl = document.getElementById('exec-decision');
    if (decEl) {
        if (decisionState === 'ML') decEl.innerHTML = 'Deploy ML for <b>' + nodeName + '</b>.';
        else if (decisionState === 'Manual') decEl.innerHTML = 'Retain Manual Forecast for <b>' + nodeName + '</b>.';
        else decEl.innerHTML = 'Hybrid Strategy Recommended for <b>' + nodeName + '</b>.';
    }
    
    const confEl = document.getElementById('exec-conf-chip');
    if (confEl) {
        if (decisionState === 'ML') confEl.innerHTML = '<span class="chip strong-ml">High Confidence</span>';
        else if (decisionState === 'Manual') confEl.innerHTML = '<span class="chip manual">Manual Override</span>';
        else confEl.innerHTML = '<span class="chip hybrid">Volume Conflict</span>';
    }
    
    const winEl = document.getElementById('exec-ev-window');
    if (winEl) winEl.textContent = validW + ' Weeks (Trailing)';
    
    const barEl = document.getElementById('exec-ev-bar');
    if (barEl) barEl.style.width = winRate + '%';
    
    const subEl = document.getElementById('exec-ev-sub');
    if (subEl) {
        if (decisionState === 'ML') subEl.textContent = `ML Outperformed in ${winRate}% of validation periods.`;
        else if (decisionState === 'Manual') subEl.textContent = `Manual Outperformed in ${100 - winRate}% of validation periods.`;
        else {
            const queueWinner = globalRollup && globalRollup.Queue_Wins_ML > globalRollup.Queue_Wins_Manual ? 'ML' : 'Manual';
            const volWinner = mlWape < manualWape ? 'ML' : 'Manual';
            subEl.textContent = `${queueWinner} won queue-count, but ${volWinner} won volume-weight.`;
        }
    }
    
    const sumEl = document.getElementById('exec-summary-text');
    if (sumEl) {
        if (decisionState === 'Hybrid') {
            const queueWinner = globalRollup && globalRollup.Queue_Wins_ML > globalRollup.Queue_Wins_Manual ? 'ML' : 'Manual';
            const volWinner = mlWape < manualWape ? 'ML' : 'Manual';
            
            if (queueWinner !== volWinner) {
                sumEl.innerHTML = `The data indicates a split metric for <b>${nodeName}</b>. ${queueWinner} won the majority of individual queues, but ${volWinner} had a lower volume-weighted error. Deploy ML for long-tail queues, manually review high-volume outliers.`;
            } else {
                sumEl.innerHTML = `The data indicates a mixed metric for <b>${nodeName}</b>. While ${queueWinner} performed better overall, the volume margin is too narrow for a strict uniform policy. A hybrid approach is recommended.`;
            }
        } else {
            sumEl.innerHTML = `The data indicates that ${isMlWin ? 'ML algorithms' : 'manual forecasts'} provide higher accuracy for <b>${nodeName}</b> over the historical evaluation window. WAPE improved from ${manualWape}% to ${mlWape}%.`;
        }
    }
    
    // In hybrid case, we usually highlight the ML wape as the primary for the KPI, or whichever is lower.
    const displayWape = (decisionState === 'Manual') ? manualWape : mlWape;
    if (document.getElementById('exec-new-wape')) document.getElementById('exec-new-wape').textContent = displayWape + '%';
    // Compute real aggregate bias
    let totalForecast = 0;
    targetL0.forEach(row => { totalForecast += (parseFloat(row.ML_Forecast) || 0); });
    const aggBias = totalVol > 0 ? ((totalForecast - totalVol) / totalVol * 100).toFixed(1) : '0.0';
    if (document.getElementById('exec-new-bias')) document.getElementById('exec-new-bias').textContent = (aggBias >= 0 ? '+' : '') + aggBias + '%';
    
    let weeklyWapes = [];
    for(const w in weeks) {
        const d = weeks[w];
        if (d.act > 0) {
            const err = (decisionState === 'Manual') ? d.manErr : d.mlErr;
            weeklyWapes.push(err / d.act);
        }
    }
    let volatilityStr = '-';
    if (weeklyWapes.length > 1) {
        const meanWape = weeklyWapes.reduce((a,b)=>a+b,0) / weeklyWapes.length;
        const variance = weeklyWapes.reduce((a,b)=>a + Math.pow(b - meanWape, 2), 0) / (weeklyWapes.length - 1);
        const stdDev = Math.sqrt(variance);
        volatilityStr = (stdDev * 100).toFixed(1) + '%';
    }
    if (document.getElementById('exec-new-volatility')) document.getElementById('exec-new-volatility').textContent = volatilityStr;
    if (document.getElementById('exec-new-records')) document.getElementById('exec-new-records').textContent = targetL0.length.toLocaleString();
    
    // --- Dynamic KPI Cards Update ---
    let targetL1 = RAW_LEVEL1;
    for (const [k, v] of Object.entries(filters)) {
        if (k !== 'Global') targetL1 = targetL1.filter(row => v.includes(String(row[k])));
    }
    if (classFilter.length > 0) {
        targetL1 = targetL1.filter(row => classFilter.includes(row.Classification));
    }
    
    let sumMl = 0;
    let sumMan = 0;
    let sumPrevYear = 0;
    let validQCount = 0;
    
    targetL1.forEach(q => {
        if (q.Queue_Actual_Sum > 0) {
            sumMl += (q.Queue_WAPE_ML * 100);
            sumMan += (q.Queue_WAPE_Manual * 100);
            sumPrevYear += (q.Queue_WAPE_Prev_Year * 100);
            validQCount++;
        }
    });
    
    const meanMlWape = validQCount > 0 ? sumMl / validQCount : parseFloat(mlWape);
    const meanManWape = validQCount > 0 ? sumMan / validQCount : parseFloat(manualWape);
    const meanPrevYearWape = validQCount > 0 ? sumPrevYear / validQCount : 0;
    
    const bestMeanWape = isMlWin ? meanMlWape : meanManWape;
    const accuracy = !isNaN(bestMeanWape) ? (100 - bestMeanWape).toFixed(1) : '-';
    const prevYearAccuracy = (100 - meanPrevYearWape).toFixed(1);

    if (document.getElementById('exec-acc-val')) document.getElementById('exec-acc-val').textContent = accuracy !== '-' ? accuracy + '%' : '-';
    
    if (document.getElementById('exec-acc-sub')) {
        if (accuracy !== '-') {
            const accDiff = (parseFloat(accuracy) - parseFloat(prevYearAccuracy)).toFixed(1);
            const isPositive = parseFloat(accDiff) >= 0;
            const sign = isPositive ? '+' : '';
            const icon = isPositive ? '▲' : '▼';
            const color = isPositive ? '#86efac' : '#fca5a5';
            document.getElementById('exec-acc-sub').innerHTML = 
                `<span style="color:${color};">${icon} ${sign}${accDiff}%</span> &nbsp; vs Prev Yr`;
        } else {
            document.getElementById('exec-acc-sub').innerHTML = `-`;
        }
    }

    const formattedVol = totalVol >= 1000000 ? (totalVol / 1000000).toFixed(1) + 'M' : 
                         totalVol >= 1000 ? (totalVol / 1000).toFixed(1) + 'K' : 
                         Math.round(totalVol).toLocaleString();
    if (document.getElementById('exec-vol-val')) document.getElementById('exec-vol-val').textContent = formattedVol;
    
    const avgVol = validW > 0 ? Math.round(totalVol / validW).toLocaleString() : '-';
    if (document.getElementById('exec-vol-sub')) {
        document.getElementById('exec-vol-sub').innerHTML = `<span style="color:#86efac;">▲</span> &nbsp; ${avgVol} / wk avg`;
    }
    // Evidence banner
    const evBanner = document.getElementById('evidence-banner-text');
    if (evBanner) evBanner.textContent = `${targetL0.length.toLocaleString()} queue-week records across ${validW} fiscal weeks. All metrics are computed from realized actuals vs. locked forecasts.`;
    
    // --- Forecast Queues KPI ---
    const queueCount = targetL1.length;
    const uniqueCountries = new Set(targetL1.map(q => q.Country)).size;
    const uniqueRegions = new Set(targetL1.map(q => q.Region)).size;
    if (document.getElementById('exec-new-queues')) document.getElementById('exec-new-queues').textContent = queueCount.toLocaleString();
    if (document.getElementById('exec-new-queues-sub')) document.getElementById('exec-new-queues-sub').textContent = `across ${uniqueCountries} countries, ${uniqueRegions} regions`;
    
    // --- Tolerance Hit Rate KPI (±10%) ---
    let hitCount = 0;
    let hitTotal = 0;
    let volAccurate = 0, volOver = 0, volUnder = 0;
    
    targetL0.forEach(row => {
        const actual = row.Actual_Offered || 0;
        if (actual > 0) {
            const forecast = (decisionState === 'Manual')
                ? (parseFloat(row.Manual_Forecast) || 0)
                : (parseFloat(row.ML_Forecast) || 0);
                
            const relError = (forecast - actual) / actual;
            const absError = Math.abs(relError);
            
            hitTotal++;
            if (absError <= 0.10) {
                hitCount++;
                volAccurate += actual;
            } else if (relError > 0.10) {
                volOver += actual;
            } else if (relError < -0.10) {
                volUnder += actual;
            }
        }
    });
    const hitRate = hitTotal > 0 ? (hitCount / hitTotal * 100).toFixed(1) : '-';
    if (document.getElementById('exec-new-hitrate')) document.getElementById('exec-new-hitrate').textContent = hitRate !== '-' ? hitRate + '%' : '-';
    if (document.getElementById('exec-new-hitrate-sub')) document.getElementById('exec-new-hitrate-sub').textContent = `${hitCount.toLocaleString()} of ${hitTotal.toLocaleString()} within ±10%`;

    // --- Executive Charts ---
    const sortedWeekKeys = Object.keys(weeks).sort();
    
    // 1. Volume Trajectory Chart
    const volCtx = document.getElementById('chart-exec-volume');
    if (volCtx) {
        if (window._execVolChart) window._execVolChart.destroy();
        
        const actVolExec = sortedWeekKeys.map(w => weeks[w].act);
        const manFCVolExec = sortedWeekKeys.map(w => weeks[w].man);
        const mlFCVolExec = sortedWeekKeys.map(w => weeks[w].ml);

        const allVolsExec = [...actVolExec, ...mlFCVolExec, ...manFCVolExec].map(Number);
        const minVolExec = Math.min(...allVolsExec);
        const maxVolExec = Math.max(...allVolsExec);
        const rangeExec = maxVolExec - minVolExec;
        const yMinVolExec = Math.max(0, Math.floor((minVolExec - (rangeExec * 0.1)) / 1000) * 1000);

        window._execVolChart = new Chart(volCtx, {
            type: 'line',
            data: {
                labels: sortedWeekKeys.map(l => l.startsWith('FW') ? l : 'FW' + l),
                datasets: [
                    { label: 'Actual', data: actVolExec, borderColor: '#808A98', backgroundColor: 'transparent', borderWidth: 2.5, tension: 0.3, pointRadius: 3, pointBackgroundColor: '#808A98', fill: false },
                    { label: 'ML FC', data: mlFCVolExec, borderColor: '#2F6F63', backgroundColor: 'rgba(47,111,99,0.1)', borderWidth: 2, borderDash: [4,4], tension: 0.3, pointRadius: 3, pointBackgroundColor: '#2F6F63', fill: true },
                    { label: 'Manual FC', data: manFCVolExec, borderColor: '#B3452B', backgroundColor: 'transparent', borderWidth: 2, borderDash: [2,2], tension: 0.3, pointRadius: 3, pointBackgroundColor: '#B3452B', fill: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: { 
                    legend: { display: true, position: 'bottom', labels: { boxWidth: 12, boxHeight: 12, padding: 15 } },
                    tooltip: {
                        backgroundColor: '#ffffff', titleColor: '#101B33', titleFont: { size: 14, weight: 'bold' },
                        bodyColor: '#101B33', bodyFont: { size: 13 }, borderColor: '#E4E8EE', borderWidth: 1, padding: 12, boxPadding: 6, usePointStyle: true,
                        callbacks: {
                            labelTextColor: function(context) { return context.dataset.borderColor; },
                            label: function(context) { return (context.dataset.label || '') + ' : ' + new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(Math.round(context.parsed.y)); }
                        }
                    },
                    datalabels: {
                        display: true,
                        align: function(context) {
                            const actVal = Number(context.chart.data.datasets[0].data[context.dataIndex]);
                            const mlVal = Number(context.chart.data.datasets[1].data[context.dataIndex]);
                            const manVal = Number(context.chart.data.datasets[2].data[context.dataIndex]);
                            const myVal = Number(context.dataset.data[context.dataIndex]);
                            
                            const sorted = [actVal, mlVal, manVal].sort((a, b) => b - a);
                            if (myVal === sorted[0]) return 'top';
                            if (myVal === sorted[2]) return 'bottom';
                            
                            const distToMax = sorted[0] - myVal;
                            const distToMin = myVal - sorted[2];
                            return distToMax > distToMin ? 'top' : 'bottom';
                        },
                        anchor: 'center',
                        color: function(context) { return context.dataset.borderColor; },
                        font: { size: 10, weight: 600 },
                        formatter: function(value) {
                            if (value >= 1000000) return (value/1000000).toFixed(1) + 'M';
                            if (value >= 1000) return (value/1000).toFixed(1) + 'k';
                            return value;
                        }
                    }
                },
                scales: {
                    x: { grid: { display: true, drawBorder: false, color: '#EEF1F4' }, ticks: { font: { size: 10, color: '#8A94A3' }, maxRotation: 45 } },
                    y: { min: yMinVolExec, grid: { borderDash: [3,3], color: '#EEF1F4' }, ticks: { font: { color: '#8A94A3' }, callback: function(value) { return value >= 1000000 ? (value/1000000).toFixed(1) + 'M' : value >= 1000 ? (value/1000).toFixed(1) + 'k' : value; } } }
                }
            }
        });
    }

    // 2. Hit Rate Composition Chart
    const hitrateCtx = document.getElementById('chart-exec-hitrate');
    if (hitrateCtx) {
        if (window._execHitrateChart) window._execHitrateChart.destroy();
        window._execHitrateChart = new Chart(hitrateCtx, {
            type: 'doughnut',
            data: {
                labels: ['Accurate (±10%)', 'Over-forecasted', 'Under-forecasted'],
                datasets: [{
                    data: [volAccurate, volOver, volUnder],
                    backgroundColor: ['#2F6F63', '#B3452B', '#C98A2C'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: { position: 'bottom', labels: { usePointStyle: true, padding: 20, font: { family: 'var(--sans)' } } },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const val = context.parsed;
                                const total = volAccurate + volOver + volUnder;
                                const pct = total > 0 ? Math.round((val / total) * 100) : 0;
                                return ` ${context.label}: ${pct}%`;
                            }
                        }
                    },
                    datalabels: { display: false }
                }
            }
        });
    }

    // 3. Top & Bottom Performers
    const perfCtx = document.getElementById('chart-exec-performers');
    if (perfCtx) {
        if (window._execPerfChart) window._execPerfChart.destroy();
        
        const offeringGroups = computeHierarchyRollup(targetL1, 'Offering', window.GLOBAL_FILTERS || {});
        let offeringStats = [];
        for (const stats of offeringGroups) {
            const off = stats.Node;
            if (off === '(Unspecified)' || off === 'Global') continue;
            offeringStats.push({ 
                offering: off, 
                mlWape: stats.ML_WAPE || 0,
                manualWape: stats.Manual_WAPE || 0,
                baselineWape: stats.Baseline_WAPE || 0
            });
        }
        
        offeringStats.sort((a, b) => a.mlWape - b.mlWape);
        
        let displayStats = [];
        if (offeringStats.length > 8) {
            displayStats = [...offeringStats.slice(0, 4), ...offeringStats.slice(-4)];
        } else {
            displayStats = offeringStats;
        }
        
        const perfLabels = displayStats.map(s => s.offering);
        const mlData = displayStats.map(s => s.mlWape);
        const manualData = displayStats.map(s => s.manualWape);
        const baselineData = displayStats.map(s => s.baselineWape);

        window._execPerfChart = new Chart(perfCtx, {
            type: 'bar',
            data: {
                labels: perfLabels,
                datasets: [
                    {
                        label: 'ML WAPE',
                        data: mlData,
                        backgroundColor: '#2F6F63',
                        borderRadius: 4,
                        barPercentage: 0.85,
                        categoryPercentage: 0.8
                    },
                    {
                        label: 'Manual WAPE',
                        data: manualData,
                        backgroundColor: '#B7C3D4',
                        borderRadius: 4,
                        barPercentage: 0.85,
                        categoryPercentage: 0.8
                    },
                    {
                        label: 'Baseline WAPE',
                        data: baselineData,
                        backgroundColor: 'rgba(148, 163, 184, 0.2)',
                        borderColor: '#94A3B8',
                        borderWidth: 1,
                        borderRadius: 4,
                        barPercentage: 0.85,
                        categoryPercentage: 0.8
                    }
                ]
            },
            options: {
                layout: { padding: { right: 50, top: 10 } },
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: {
                    legend: { 
                        display: true,
                        position: 'top',
                        labels: { usePointStyle: true, font: { family: 'var(--sans)', size: 12 }, padding: 20 }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) { 
                                return ` ${context.dataset.label}: ${context.parsed.x.toFixed(1)}%`; 
                            }
                        }
                    },
                    datalabels: {
                        display: true,
                        anchor: 'end',
                        align: 'right',
                        formatter: v => v.toFixed(1) + '%',
                        font: { size: 10, family: 'var(--mono)' },
                        color: '#64748b'
                    }
                },
                scales: {
                    x: { 
                        display: false, 
                        min: 0, 
                        max: Math.max(...mlData, ...manualData, ...baselineData) * 1.2 
                    },
                    y: { 
                        grid: { display: false, drawBorder: false },
                        ticks: { font: { size: 11, family: 'var(--sans)', weight: '500' }, color: '#1e293b' },
                        afterFit: function(scaleInstance) {
                            scaleInstance.width = 75;
                        }
                    }
                }
            }
        });
    }

    if (typeof renderAccuracyMap === 'function') {
        renderAccuracyMap();
    }
}


function computeHierarchyRollup(df, groupByCol, filtersOrKey, filterVal) {
    let target = df;
    
    // Support both old style (filterKey, filterVal) and new style (filtersObject)
    if (filtersOrKey && typeof filtersOrKey === 'object') {
        // New style: filtersOrKey is a filters dict like {Region: 'APJ', SubRegion: 'ANZ'}
        for (const [k, v] of Object.entries(filtersOrKey)) {
            if (k !== 'Global' && v) {
                target = target.filter(row => v.includes(String(row[k])));
            }
        }
    } else if (filtersOrKey && typeof filtersOrKey === 'string' && filtersOrKey !== 'Global') {
        // Old style: filtersOrKey is a string column name
        target = target.filter(row => row[filtersOrKey] == filterVal);
    }
    
    // Apply classification filter if set
    const classFilter = window.CLASSIFICATION_FILTER || [];
    if (classFilter.length > 0) {
        target = target.filter(row => classFilter.includes(row.Classification));
    }
    
    // If groupByCol is Global, we pretend every row is 'Global'
    const groups = {};
    
    target.forEach(row => {
        if (row.Classification === 'No Data') return; // Skip No Data queues per spec
        
        let key = groupByCol === 'Global' ? 'Global' : row[groupByCol];
        if (!key) key = '(Unspecified)';
        
        if (!groups[key]) {
            groups[key] = {
                'Strong ML': 0, 'Hybrid': 0, 'Manual': 0,
                'Vol_Strong ML': 0, 'Vol_Hybrid': 0, 'Vol_Manual': 0,
                'Conf_High': 0, 'Conf_Medium': 0, 'Conf_Low': 0,
                Total_Queues: 0, Total_Volume: 0,
                Queue_Wins_ML: 0, Queue_Wins_Manual: 0,
                Manual_Err: 0, ML_Err: 0,
                Valid_Weeks_Count: 0,
                Classification: row.Classification || 'Manual',
                Confidence: row.Confidence || 'High'
            };
        }
        
        const g = groups[key];
        const classification = row.Classification || 'Manual';
        const conf = row.Confidence || 'High';
        
        g[classification] += 1;
        g['Vol_' + classification] += (row.Queue_Actual_Sum || 0);
        g['Conf_' + conf] += 1;
        
        if (row.Queue_Winner_By_WAPE === 'ML') g.Queue_Wins_ML += 1;
        else g.Queue_Wins_Manual += 1;
        
        g.Total_Queues += 1;
        g.Total_Volume += (row.Queue_Actual_Sum || 0);
        g.Manual_Err += (row.Queue_Manual_Err_Sum || 0);
        g.ML_Err += (row.Queue_ML_Err_Sum || 0);
        g.Prev_Year_Err_Weighted_Sum = (g.Prev_Year_Err_Weighted_Sum || 0) + ((row.Queue_WAPE_Prev_Year || 0) * (row.Queue_Actual_Sum || 0));
        g.Valid_Weeks_Count += (row.Valid_Weeks_Count || 0);
    });
    
    const results = [];
    for (const [key, g] of Object.entries(groups)) {
        const pctStrongML = g.Total_Queues ? (g['Strong ML'] / g.Total_Queues * 100) : 0;
        const pctHybrid = g.Total_Queues ? (g['Hybrid'] / g.Total_Queues * 100) : 0;
        const pctManual = g.Total_Queues ? (g['Manual'] / g.Total_Queues * 100) : 0;
        
        const volPctStrongML = g.Total_Volume ? (g['Vol_Strong ML'] / g.Total_Volume * 100) : 0;
        const volPctHybrid = g.Total_Volume ? (g['Vol_Hybrid'] / g.Total_Volume * 100) : 0;
        const volPctManual = g.Total_Volume ? (g['Vol_Manual'] / g.Total_Volume * 100) : 0;
        
        const confPctHigh = g.Total_Queues ? (g['Conf_High'] / g.Total_Queues * 100) : 0;
        const confPctMedium = g.Total_Queues ? (g['Conf_Medium'] / g.Total_Queues * 100) : 0;
        const confPctLow = g.Total_Queues ? (g['Conf_Low'] / g.Total_Queues * 100) : 0;
        
        const manualWape = g.Total_Volume ? (g.Manual_Err / g.Total_Volume * 100) : 0;
        const mlWape = g.Total_Volume ? (g.ML_Err / g.Total_Volume * 100) : 0;
        const baselineWape = g.Total_Volume ? (g.Prev_Year_Err_Weighted_Sum / g.Total_Volume * 100) : 0;
        
        let queueWinner = g.Queue_Wins_ML >= g.Queue_Wins_Manual ? 'ML' : 'Manual';
        let volWinner = mlWape <= manualWape ? 'ML' : 'Manual';
        
        let decisionState = 'Hybrid';
        if (queueWinner === 'ML' && volWinner === 'ML') decisionState = 'ML';
        if (queueWinner === 'Manual' && volWinner === 'Manual') decisionState = 'Manual';
        
        // Classify the group based on volume-weighted Strong ML share for legacy uses
        let groupClass = 'Manual';
        if (volPctStrongML >= 60) groupClass = 'Strong ML';
        else if (volPctStrongML >= 40) groupClass = 'Hybrid';
        
        results.push({
            Node: key,
            ...g,
            Pct_Strong_ML: pctStrongML,
            Pct_Hybrid: pctHybrid,
            Pct_Manual: pctManual,
            Vol_Pct_Strong_ML: volPctStrongML,
            Vol_Pct_Hybrid: volPctHybrid,
            Vol_Pct_Manual: volPctManual,
            Conf_Pct_High: confPctHigh,
            Conf_Pct_Medium: confPctMedium,
            Conf_Pct_Low: confPctLow,
            Manual_WAPE: manualWape,
            ML_WAPE: mlWape,
            Baseline_WAPE: baselineWape,
            Queue_Winner: queueWinner,
            Volume_Winner: volWinner,
            Decision_State: decisionState,
            GroupClass: groupClass
        });
    }
    
    return results;
}

// State for expanded rows
const expandedRows = new Set();

function renderHierarchyTable() {
    const tbody = document.getElementById('sa-hierarchy-body');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    // Start with children of Global (i.e. Regions)
    const nextLevelName = HIERARCHY_PATH[1];
    const baseFilters = window.CURRENT_FILTERS ? window.CURRENT_FILTERS.filters : {};
    const children = computeHierarchyRollup(RAW_LEVEL1, nextLevelName, baseFilters);
    
    if (!children || children.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 20px; color: var(--text-2);">No data matches the current filters.</td></tr>`;
        return;
    }
    
    children.sort((a, b) => b.Total_Volume - a.Total_Volume);
    children.forEach((child, idx) => {
        renderRow(tbody, child, child.Node, nextLevelName, 0, baseFilters, idx % 2 === 1 ? '#f8f9fa' : '');
    });
}

function renderRow(tbody, data, nodeName, levelName, indentLevel, accumulatedFilters, overrideBg = '') {
    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.dataset.node = nodeName;
    tr.dataset.level = levelName;
    
    const isLeaf = levelName === HIERARCHY_PATH[HIERARCHY_PATH.length - 1];
    const rowId = levelName + '-' + nodeName;
    const isExpanded = expandedRows.has(rowId);
    
    // Maintain selection highlight
    if (window.CURRENT_FILTERS.nodeName === nodeName && window.CURRENT_FILTERS.levelName === levelName) {
        tr.style.backgroundColor = 'var(--teal-soft)';
    } else if (overrideBg) {
        tr.style.backgroundColor = overrideBg;
    }
    // Persist the highlight of the row currently loaded in the deep-dive panel
    if (window.SA_ANALYZED && window.SA_ANALYZED.levelName !== 'Global' &&
        window.SA_ANALYZED.nodeName === nodeName && window.SA_ANALYZED.levelName === levelName) {
        tr.classList.add('row-active');
    }
    
    const expandToggle = isLeaf ? '&nbsp;&nbsp;' : (isExpanded ? '▼ ' : '▶ ');
    
    let pctSML = 0, pctHyb = 0, pctMan = 0;
    let txtSML = '', txtHyb = '', txtMan = '';
    
    if (isLeaf) {
        pctSML = data.Classification === 'Strong ML' ? 100 : 0;
        pctHyb = data.Classification === 'Hybrid' ? 100 : 0;
        pctMan = data.Classification === 'Manual' ? 100 : 0;
        txtSML = pctSML === 100 ? '100% (1/1)' : '0% (0/1)';
        txtHyb = pctHyb === 100 ? '100% (1/1)' : '0% (0/1)';
        txtMan = pctMan === 100 ? '100% (1/1)' : '0% (0/1)';
    } else {
        pctSML = Math.round(data.Pct_Strong_ML || 0);
        pctHyb = Math.round(data.Pct_Hybrid || 0);
        pctMan = Math.round(data.Pct_Manual || 0);
        txtSML = `${pctSML}% (${data['Strong ML']}/${data.Total_Queues})`;
        txtHyb = `${pctHyb}% (${data['Hybrid']}/${data.Total_Queues})`;
        txtMan = `${pctMan}% (${data['Manual']}/${data.Total_Queues})`;
    }

    const maxPct = Math.max(pctSML, pctHyb, pctMan);
    
    // "not sure about their identity": if a sub-level node's highest percentage doesn't match its GroupClass
    const isIdentitySure = isLeaf || indentLevel === 0 || 
                           (pctSML === maxPct && data.GroupClass === 'Strong ML') ||
                           (pctMan === maxPct && data.GroupClass === 'Manual') ||
                           (pctHyb === maxPct && data.GroupClass === 'Hybrid');

    const bgSML = (isIdentitySure && pctSML === maxPct && pctSML > 0) ? 'background-color: #ebfbf2;' : '';
    const bgHyb = (isIdentitySure && pctHyb === maxPct && pctHyb > 0) ? 'background-color: #fff8e1;' : '';
    const bgMan = (isIdentitySure && pctMan === maxPct && pctMan > 0) ? 'background-color: #fcedec;' : '';

    let confDisplay = '';
    if (isLeaf) {
        confDisplay = `<span style="font-size:11px;">${data.Confidence || 'High'}</span>`;
    } else {
        confDisplay = `
            <div onmousemove="showConfTooltip(event, ${(data.Conf_Pct_High || 0).toFixed(0)}, ${(data.Conf_Pct_Medium || 0).toFixed(0)}, ${(data.Conf_Pct_Low || 0).toFixed(0)})" onmouseleave="hideConfTooltip()" 
                 style="width:60px; height:8px; border-radius:4px; display:flex; overflow:hidden; cursor:help;">
                <div style="width:${data.Conf_Pct_High}%; background:#2563EB; pointer-events:none;"></div>
                <div style="width:${data.Conf_Pct_Medium}%; background:#93C5FD; pointer-events:none;"></div>
                <div style="width:${data.Conf_Pct_Low}%; background:#DBEAFE; pointer-events:none;"></div>
            </div>
        `;
    }
    
    // Phase 3: In-line SVGs based on risk (Manual%)
    let riskIcon = '';
    const isHighRisk = (pctMan > 25);
    const isCriticalRisk = (pctMan > 50);
    if (isCriticalRisk) {
        riskIcon = `<span class="enterprise-tooltip risk-critical sa-risk-badge" style="cursor:pointer;" data-tooltip="High Risk: &gt;50% Manual Forecasts &middot; click to view in Business Context">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
        </span>`;
    } else if (isHighRisk) {
        riskIcon = `<span class="enterprise-tooltip risk-warning sa-risk-badge" style="cursor:pointer;" data-tooltip="Warning: &gt;25% Manual Forecasts &middot; click to view in Business Context">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        </span>`;
    }

    tr.innerHTML = `
        <td style="padding-left: ${10 + indentLevel * 20}px; display: flex; align-items: center;">
            <span class="expand-toggle" style="font-family:var(--mono); color:var(--teal); font-size:10px; margin-right:6px;">${expandToggle}</span>
            <strong style="color:var(--navy); font-weight:500;">${nodeName}</strong>
            ${riskIcon}
            <span style="font-size:10px; color:var(--text-2); margin-left: 6px;">(${levelName})</span>
        </td>
        <td class="num">${data.Total_Queues}</td>
        <td class="num" style="color:var(--teal); font-weight:500; ${bgSML}">${txtSML}</td>
        <td class="num" style="color:var(--amber); font-weight:500; ${bgHyb}">${txtHyb}</td>
        <td class="num" style="color:var(--rust); font-weight:500; ${bgMan}">${txtMan}</td>
        <td>${confDisplay}</td>
        <td class="sa-analyze-cell"><button type="button" class="sa-analyze-btn" aria-label="Analyze ${nodeName} in the deep-dive panel"><span aria-hidden="true">📊</span> Analyze</button></td>
    `;
    
    tr.addEventListener('click', (e) => {
        if (e.target.closest('svg')) {
            e.stopPropagation();
            // Just return for now, could add filter logic later
            return;
        }

        // Toggle expansion
        if (!isLeaf) {
            if (isExpanded) expandedRows.delete(rowId);
            else expandedRows.add(rowId);
            renderHierarchyTable(); // Re-render tree to apply expansion and highlighting
        } else {
            // Leaf node: just update highlighting manually since no re-render
            document.querySelectorAll('#sa-hierarchy-body tr').forEach(r => {
                r.classList.remove('row-active');
                r.style.backgroundColor = '';
            });
            tr.classList.add('row-active');
        }

        // NOTE: row click intentionally does NOT change the charts anymore.
        // Loading a context is the explicit job of the per-row Analyze button.
    });

    // Explicit trigger — master/detail decoupling. stopPropagation keeps this
    // from also firing the row-click (expand/select) handler above.
    const analyzeBtn = tr.querySelector('.sa-analyze-btn');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            document.querySelectorAll('#sa-hierarchy-body tr').forEach(r => r.classList.remove('row-active'));
            tr.classList.add('row-active');
            triggerDeepDive(nodeName, levelName);
        });
    }

    // 1.3 : clickable in-line risk badge -> Business Context, pre-filtered to this node.
    const riskBadge = tr.querySelector('.sa-risk-badge');
    if (riskBadge) {
        riskBadge.addEventListener('click', (e) => {
            e.stopPropagation();
            jumpToContext(levelName, nodeName);
        });
    }
    
    tbody.appendChild(tr);
    
    // If expanded, render children recursively
    if (isExpanded && !isLeaf) {
        const nextLevelIndex = HIERARCHY_PATH.indexOf(levelName) + 1;
        const nextLevelName = HIERARCHY_PATH[nextLevelIndex];
        const childFilters = { ...accumulatedFilters };
        if (levelName !== 'Global') {
            childFilters[levelName] = nodeName;
        }
        
        const children = computeHierarchyRollup(RAW_LEVEL1, nextLevelName, childFilters);
        children.sort((a, b) => b.Total_Volume - a.Total_Volume); // Sort by volume desc
        
        children.forEach(child => {
            renderRow(tbody, child, child.Node, nextLevelName, indentLevel + 1, childFilters);
        });
    }
}

function renderTrendPanel(nodeName, levelName, filters) {
    document.getElementById('sa-trend-title').textContent = `(${nodeName})`;
    
    // 1. Filter Level 0 data for this node
    let targetL0 = RAW_LEVEL0;
    if (levelName !== 'Global') {
        targetL0 = targetL0.filter(row => String(row[levelName]) === String(nodeName));
    }
    
    // Apply global dropdown filters
    if (filters) {
        for (const [k, v] of Object.entries(filters)) {
            if (k !== levelName && k !== 'Fiscal_Week') { // Fiscal Week is already handled or doesn't apply to the trend charts in the same way (though it could)
                targetL0 = targetL0.filter(row => v.includes(String(row[k])));
            }
        }
    }
    
    // Apply classification filter if set
    const classFilter = window.CLASSIFICATION_FILTER || [];
    if (classFilter.length > 0) {
        // Find which Forecast Names have this classification from RAW_LEVEL1
        const allowedForecasts = new Set(
            RAW_LEVEL1.filter(q => classFilter.includes(q.Classification)).map(q => q.Forecast_Name)
        );
        targetL0 = targetL0.filter(row => allowedForecasts.has(row.Forecast_Name));
    }
    
    // 2. Aggregate Weekly Data (Group by Fiscal_Week)
    const weeks = {};
    targetL0.forEach(row => {
        const w = row.Fiscal_Week || row.Week_Ending;
        if (!weeks[w]) {
            weeks[w] = { Actual: 0, Manual_Err: 0, ML_Err: 0, ML_FC: 0, Manual_FC: 0 };
        }
        weeks[w].Actual += (row.Actual_Offered || 0);
        weeks[w].Manual_Err += (row.Manual_Abs_Err || 0);
        weeks[w].ML_Err += (row.ML_Abs_Err || 0);
        weeks[w].ML_FC += (parseFloat(row.ML_Forecast) || 0);
        weeks[w].Manual_FC += (parseFloat(row.Manual_Forecast) || 0);
    });
    
    const sortedWeeks = Object.keys(weeks).sort();
    const labels = sortedWeeks;
    const manualWapes = [];
    const mlWapes = [];
    
    const distManual = {'<=10':0, '10-15':0, '15-20':0, '20-30':0, '>30':0};
    const distML = {'<=10':0, '10-15':0, '15-20':0, '20-30':0, '>30':0};
    
    const manAdh = [];
    const mlAdh = [];
    const actVol = [];
    const manFCVol = [];
    const mlFCVol = [];
    
    function getBucket(wape) {
        if (wape <= 10) return '<=10';
        if (wape <= 15) return '10-15';
        if (wape <= 20) return '15-20';
        if (wape <= 30) return '20-30';
        return '>30';
    }
    
    sortedWeeks.forEach(w => {
        const g = weeks[w];
        const manWape = g.Actual ? (g.Manual_Err / g.Actual * 100) : 0;
        const mlWape = g.Actual ? (g.ML_Err / g.Actual * 100) : 0;
        
        manualWapes.push(manWape.toFixed(2));
        mlWapes.push(mlWape.toFixed(2));
        
        distManual[getBucket(manWape)]++;
        distML[getBucket(mlWape)]++;
        
        // Adherence Calculation (Forecast / Actual)
        const mAdhVal = g.Actual ? (g.Manual_FC / g.Actual * 100) : 100;
        const mlAdhVal = g.Actual ? (g.ML_FC / g.Actual * 100) : 100;
        manAdh.push(mAdhVal.toFixed(1));
        mlAdh.push(mlAdhVal.toFixed(1));
        
        actVol.push(g.Actual);
        manFCVol.push(g.Manual_FC);
        mlFCVol.push(g.ML_FC);
    });
    
    // Build Chart
    const ctx = document.getElementById('sa-trend-chart').getContext('2d');
    if (SA_TREND_CHART) { SA_TREND_CHART.destroy(); }
    
    SA_TREND_CHART = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'ML WAPE',
                    data: mlWapes,
                    borderColor: '#2F6F63',
                    backgroundColor: 'rgba(47,111,99,0.1)',
                    tension: 0.3,
                    fill: true
                },
                {
                    label: 'Manual WAPE',
                    data: manualWapes,
                    borderColor: '#B3452B',
                    backgroundColor: 'transparent',
                    borderDash: [5, 5],
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: true, position: 'top', labels: { boxWidth: 12, boxHeight: 12 } },
                tooltip: {
                    backgroundColor: '#ffffff', titleColor: '#101B33', titleFont: { size: 14, weight: 'bold' },
                    bodyColor: '#101B33', bodyFont: { size: 13 }, borderColor: '#E4E8EE', borderWidth: 1, padding: 12, boxPadding: 6, usePointStyle: true,
                    callbacks: {
                        labelTextColor: function(context) { return context.dataset.borderColor; },
                        label: function(context) { return (context.dataset.label || '') + ' : ' + context.parsed.y + '%'; }
                    }
                }
            },
            scales: {
                x: { title: { display: true, text: 'Week', font: { size: 11, color: '#8A94A3' } } },
                y: { title: { display: true, text: 'WAPE %', font: { size: 11, color: '#8A94A3' } } }
            }
        }
    });
    
    // Build Adherence Chart
    const adhCtx = document.getElementById('sa-chart-adherence');
    if (adhCtx) {
        if (window.SA_ADH_CHART) { window.SA_ADH_CHART.destroy(); }
        const upperLimit = labels.map(() => 110);
        const lowerLimit = labels.map(() => 90);
        
        // Dynamic zoom logic for Adherence
        const allAdh = [...mlAdh, ...manAdh].map(Number);
        const minAdh = Math.min(...allAdh);
        const maxAdh = Math.max(...allAdh);
        const yMinAdh = Math.floor(Math.min(85, minAdh - 5) / 5) * 5;
        const yMaxAdh = Math.ceil(Math.max(115, maxAdh + 5) / 5) * 5;
        
        const adhLabels = labels.map(l => l.startsWith('FW') ? l : 'FW' + l);
        
        window.SA_ADH_CHART = new Chart(adhCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: adhLabels,
                datasets: [
                    { label: 'ML Adh.', data: mlAdh, borderColor: '#2F6F63', backgroundColor: 'rgba(47,111,99,0.1)', borderWidth: 2.5, tension: 0.3, pointRadius: 3, pointBackgroundColor: '#2F6F63', fill: true },
                    { label: 'Manual Adh.', data: manAdh, borderColor: '#B3452B', backgroundColor: 'transparent', borderDash: [5,5], borderWidth: 2, tension: 0.3, pointRadius: 3, pointBackgroundColor: '#B3452B', fill: false },
                    { label: 'Upper Tolerance (+10%)', data: upperLimit, borderColor: '#ef4444', borderDash: [3,3], borderWidth: 1, pointRadius: 0, fill: false },
                    { label: 'Lower Tolerance (-10%)', data: lowerLimit, borderColor: '#f59e0b', borderDash: [3,3], borderWidth: 1, pointRadius: 0, fill: false }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: { 
                    legend: { display: true, position: 'bottom', labels: { boxWidth: 12, boxHeight: 12, padding: 15 } },
                    tooltip: {
                        backgroundColor: '#ffffff', titleColor: '#101B33', titleFont: { size: 14, weight: 'bold' },
                        bodyColor: '#101B33', bodyFont: { size: 13 }, borderColor: '#E4E8EE', borderWidth: 1, padding: 12, boxPadding: 6, usePointStyle: true,
                        callbacks: {
                            labelTextColor: function(context) { return context.dataset.borderColor; },
                            label: function(context) { return (context.dataset.label || '') + ' : ' + Math.round(context.parsed.y) + '%'; }
                        }
                    },
                    datalabels: {
                        display: function(context) { return context.datasetIndex < 2; },
                        align: function(context) {
                            const mlVal = Number(context.chart.data.datasets[0].data[context.dataIndex]);
                            const manVal = Number(context.chart.data.datasets[1].data[context.dataIndex]);
                            const myVal = Number(context.dataset.data[context.dataIndex]);
                            if (mlVal === manVal) return context.datasetIndex === 0 ? 'top' : 'bottom';
                            return myVal >= Math.max(mlVal, manVal) ? 'top' : 'bottom';
                        },
                        anchor: 'center',
                        color: function(context) { return context.dataset.borderColor; },
                        font: { size: 10, weight: 600 },
                        formatter: function(value) { return value + '%'; }
                    }
                },
                scales: {
                    x: { grid: { display: true, drawBorder: false, color: '#EEF1F4' }, ticks: { font: { size: 10, color: '#8A94A3' }, maxRotation: 45 } },
                    y: { min: yMinAdh, max: yMaxAdh, grid: { borderDash: [3,3], color: '#EEF1F4' }, ticks: { font: { color: '#8A94A3' }, callback: function(value) { return value + '%'; } } }
                }
            }
        });
    }
    
    // Build Forecast Comparison Chart
    const fcCtx = document.getElementById('sa-chart-forecast');
    if (fcCtx) {
        if (window.SA_FC_CHART) { window.SA_FC_CHART.destroy(); }
        
        // Dynamic zoom logic for Volume
        const allVols = [...actVol, ...mlFCVol, ...manFCVol].map(Number);
        const minVol = Math.min(...allVols);
        const maxVol = Math.max(...allVols);
        const range = maxVol - minVol;
        // Pad by 10% of the range, but don't go below 0
        const yMinVol = Math.max(0, Math.floor((minVol - (range * 0.1)) / 1000) * 1000);
        
        const fcLabels = labels.map(l => l.startsWith('FW') ? l : 'FW' + l);
        
        // 2.1 Variance-to-Actual: each model's error (Forecast - Actual) as bars
        // diverging from a zero baseline, so magnitude AND direction read at a glance.
        const mlVar  = fcLabels.map((_, i) => Math.round((Number(mlFCVol[i])  || 0) - (Number(actVol[i]) || 0)));
        const manVar = fcLabels.map((_, i) => Math.round((Number(manFCVol[i]) || 0) - (Number(actVol[i]) || 0)));
        const kfmt = (v) => { const a = Math.abs(v); return (v < 0 ? '-' : '') + (a >= 1000 ? (a/1000).toFixed(1) + 'k' : a); };

        window.SA_FC_CHART = new Chart(fcCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: fcLabels,
                datasets: [
                    { type: 'line', label: 'Actual (baseline)', data: fcLabels.map(() => 0), borderColor: '#101B33', borderWidth: 1.5, pointRadius: 0, fill: false, order: 0 },
                    { label: 'ML variance', data: mlVar, backgroundColor: '#2F6F63', borderRadius: 3, order: 1 },
                    { label: 'Manual variance', data: manVar, backgroundColor: '#B3452B', borderRadius: 3, order: 2 }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { display: true, position: 'bottom', labels: { boxWidth: 12, boxHeight: 12, padding: 15 } },
                    tooltip: {
                        backgroundColor: '#ffffff', titleColor: '#101B33', titleFont: { size: 14, weight: 'bold' },
                        bodyColor: '#101B33', bodyFont: { size: 13 }, borderColor: '#E4E8EE', borderWidth: 1, padding: 12, boxPadding: 6, usePointStyle: true,
                        callbacks: {
                            labelTextColor: function(context) { return context.dataset.type === 'line' ? '#101B33' : context.dataset.backgroundColor; },
                            label: function(context) {
                                if (context.dataset.type === 'line') return 'Actual baseline (0)';
                                const v = context.parsed.y;
                                const dir = v > 0 ? 'over' : (v < 0 ? 'under' : 'on target');
                                return (context.dataset.label || '') + ': ' + (v > 0 ? '+' : '') + new Intl.NumberFormat('en-US').format(v) + ' (' + dir + '-forecast)';
                            }
                        }
                    },
                    datalabels: {
                        display: function(context) { return context.dataset.type !== 'line'; },
                        anchor: function(context) { return (Number(context.dataset.data[context.dataIndex]) >= 0) ? 'end' : 'start'; },
                        align: function(context) { return (Number(context.dataset.data[context.dataIndex]) >= 0) ? 'top' : 'bottom'; },
                        color: function(context) { return context.dataset.backgroundColor; },
                        font: { size: 9, weight: 600 },
                        formatter: function(value) { return value === 0 ? '' : (value > 0 ? '+' : '') + kfmt(value); }
                    }
                },
                scales: {
                    x: { grid: { display: false, drawBorder: false }, ticks: { font: { size: 10, color: '#8A94A3' }, maxRotation: 45 } },
                    y: {
                        grid: { color: function(c) { return c.tick.value === 0 ? '#101B33' : '#EEF1F4'; }, lineWidth: function(c) { return c.tick.value === 0 ? 1.5 : 1; } },
                        title: { display: true, text: 'Forecast - Actual (units)', font: { size: 11 } },
                        ticks: { font: { color: '#8A94A3' }, callback: function(value) { return kfmt(value); } }
                    }
                }
            }
        });
    }
    
    // 2.2 Directional bias as a horizontal divergent bar: one bar per model showing
    // net cumulative bias. Colour = direction: teal = over-forecast (excess capacity),
    // rust = under-forecast (SLA / abandonment risk).
    const biasCtx = document.getElementById('sa-chart-bias');
    if (biasCtx) {
        if (window._saBiasChart) window._saBiasChart.destroy();
        let cumMan = 0, cumMl = 0;
        labels.forEach((w, i) => {
            const act = actVol[i];
            if (act > 0) { cumMan += (manFCVol[i] - act); cumMl += (mlFCVol[i] - act); }
        });
        cumMan = Math.round(cumMan); cumMl = Math.round(cumMl);
        const OVER = '#2F6F63', UNDER = '#B3452B';
        const bfmt = (v) => { const a = Math.abs(v); return (v >= 0 ? '+' : '-') + (a >= 1000 ? (a/1000).toFixed(1) + 'k' : a); };
        window._saBiasChart = new Chart(biasCtx, {
            type: 'bar',
            data: {
                labels: ['Manual', 'ML'],
                datasets: [{
                    label: 'Net cumulative bias (units)',
                    data: [cumMan, cumMl],
                    backgroundColor: [cumMan >= 0 ? OVER : UNDER, cumMl >= 0 ? OVER : UNDER],
                    borderRadius: 4, barThickness: 34
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true, maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#ffffff', titleColor: '#101B33', bodyColor: '#101B33', borderColor: '#E4E8EE', borderWidth: 1, padding: 12,
                        callbacks: { label: function(c) { const v = c.parsed.x; const dir = v >= 0 ? 'over-forecast (excess capacity)' : 'under-forecast (SLA risk)'; return (v >= 0 ? '+' : '') + new Intl.NumberFormat('en-US').format(v) + ' units - ' + dir; } }
                    },
                    datalabels: {
                        anchor: 'center', align: 'center', color: '#ffffff', font: { size: 12, weight: 700 },
                        formatter: function(v) { return bfmt(v); }
                    }
                },
                scales: {
                    x: {
                        grid: { color: function(c) { return c.tick.value === 0 ? '#101B33' : '#EEF1F4'; }, lineWidth: function(c) { return c.tick.value === 0 ? 1.5 : 1; } },
                        title: { display: true, text: 'under-forecast  (0)  over-forecast', font: { size: 10 } },
                        ticks: { font: { size: 10, color: '#8A94A3' }, callback: function(v) { const a = Math.abs(v); return (v < 0 ? '-' : '') + (a >= 1000 ? (a/1000).toFixed(1) + 'k' : a); } }
                    },
                    y: { grid: { display: false }, ticks: { font: { size: 12, weight: 600, color: '#101B33' } } }
                }
            }
        });
    }

        // Render Dist Bars
    renderDistBar('sa-dist-ml', distML, sortedWeeks.length, ['#2F6F63', '#409c8b', '#78b5ab', '#a8ccc6', '#e0ecea']);
    renderDistBar('sa-dist-manual', distManual, sortedWeeks.length, ['#B3452B', '#d65b3e', '#e3846d', '#f2b7aa', '#fcebe8']);
}

function renderDistBar(elementId, dist, totalWeeks, colors) {
    const el = document.getElementById(elementId);
    el.innerHTML = '';
    
    if (totalWeeks === 0) return;
    
    const buckets = ['<=10', '10-15', '15-20', '20-30', '>30'];
    
    buckets.forEach((b, i) => {
        const count = dist[b];
        const pct = (count / totalWeeks) * 100;
        
        const segment = document.createElement('div');
        segment.style.width = pct + '%';
        segment.style.height = '100%';
        segment.style.backgroundColor = colors[i];
        
        // Add tiny border separator
        if (pct > 0 && i > 0) {
            segment.style.borderLeft = '1px solid #fff';
        }

        // Add custom tooltip behavior
        if (!window._distTooltip) {
            window._distTooltip = document.createElement('div');
            window._distTooltip.style.position = 'absolute';
            window._distTooltip.style.display = 'none';
            window._distTooltip.style.backgroundColor = '#ffffff';
            window._distTooltip.style.border = '1px solid #E4E8EE';
            window._distTooltip.style.padding = '8px 12px';
            window._distTooltip.style.borderRadius = '6px';
            window._distTooltip.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
            window._distTooltip.style.color = '#101B33';
            window._distTooltip.style.fontSize = '12px';
            window._distTooltip.style.pointerEvents = 'none';
            window._distTooltip.style.zIndex = '9999';
            document.body.appendChild(window._distTooltip);
        }
        
        segment.addEventListener('mouseenter', () => {
            window._distTooltip.innerHTML = `<strong style="font-size:13px;">${b}% Tolerance</strong><br/>${count} weeks (${pct.toFixed(1)}%)`;
            window._distTooltip.style.display = 'block';
        });
        segment.addEventListener('mousemove', (e) => {
            window._distTooltip.style.left = (e.pageX + 15) + 'px';
            window._distTooltip.style.top = (e.pageY + 15) + 'px';
        });
        segment.addEventListener('mouseleave', () => {
            window._distTooltip.style.display = 'none';
        });
        
        el.appendChild(segment);
    });
}


function renderModelChampion() {
    console.log('Rendering Model Champion for', window.CURRENT_FILTERS);
    let target = RAW_LEVEL0;
    const filters = window.CURRENT_FILTERS.filters;
    const levelName = window.CURRENT_FILTERS.levelName;
    const nodeName = window.CURRENT_FILTERS.nodeName;
    
    for (const [k, v] of Object.entries(filters)) {
        if (k !== 'Global') target = target.filter(row => row[k] == v);
    }
    
    if (levelName !== 'Global') target = target.filter(row => row[levelName] == nodeName);
    
    const stats = {};
    
    target.forEach(row => {
        const c = row.Model;
        if (!c) return;
        
        if (!stats[c]) {
            stats[c] = { absErrSum: 0, actualSum: 0, forecastSum: 0, hit10Count: 0, validWeeks: 0, maxAbsErr: 0 };
        }
        
        const actual = row.Actual_Offered;
        if (!actual || actual <= 0) return;
        
        const forecast = parseFloat(row.ML_Forecast);
        if (isNaN(forecast)) return;
        
        const absErr = Math.abs(forecast - actual);
        stats[c].absErrSum += absErr;
        stats[c].actualSum += actual;
        stats[c].forecastSum += forecast;
        stats[c].validWeeks += 1;
        
        if (absErr > stats[c].maxAbsErr) stats[c].maxAbsErr = absErr;
        
        const wape = absErr / actual;
        if (wape <= 0.10) stats[c].hit10Count += 1;
    });
    
    const results = [];
    Object.keys(stats).forEach(c => {
        const s = stats[c];
        if (s.validWeeks === 0) return;
        
        const wape = s.absErrSum / s.actualSum;
        const bias = (s.forecastSum - s.actualSum) / s.actualSum;
        const hit10 = s.hit10Count / s.validWeeks;
        
        const wapeScore = Math.max(0, 100 - (wape * 100));
        const biasScore = Math.max(0, 100 - (Math.abs(bias) * 100));
        const hit10Score = hit10 * 100;
        const stabilityWape = s.maxAbsErr / (s.actualSum / s.validWeeks); 
        const stabilityScore = Math.max(0, 100 - (stabilityWape * 100));
        
        // WAPE 35% / Hit10 25% / Bias 20% / Stability 20%
        const composite = (wapeScore * 0.35) + (hit10Score * 0.25) + (biasScore * 0.20) + (stabilityScore * 0.20);
        
        results.push({
            Model: c,
            WAPE: (wape * 100).toFixed(1),
            Bias: (bias * 100).toFixed(1),
            Hit10: (hit10 * 100).toFixed(1),
            MaxErr: (stabilityWape * 100).toFixed(1),
            ValidWeeks: s.validWeeks,
            wapeScore, biasScore, hit10Score, stabilityScore,
            CompositeScore: composite.toFixed(1)
        });
    });
    
    results.sort((a, b) => parseFloat(b.CompositeScore) - parseFloat(a.CompositeScore));
    
    const tbody = document.querySelector('#mc-table tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    results.forEach((r, idx) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${idx + 1}</td>
            <td>${r.Model}</td>
            <td class="num" style="font-weight:600;">${r.CompositeScore}</td>
            <td class="num">${r.WAPE}%</td>
            <td class="num">${r.Bias}%</td>
            <td class="num">${r.MaxErr}%</td>
            <td class="num">${r.Hit10}%</td>
            <td class="num">${r.ValidWeeks}</td>
        `;
        tbody.appendChild(tr);
    });
    
    if (results.length > 0) {
        const champEl = document.getElementById('mc-kpi-champ');
        if (champEl) champEl.textContent = results[0].Model;
        
        const scoreEl = document.getElementById('mc-kpi-score');
        if (scoreEl) scoreEl.textContent = results[0].CompositeScore;
        
        const hitEl = document.getElementById('mc-kpi-hit10');
        if (hitEl) hitEl.textContent = results.filter(r => parseFloat(r.Hit10) > 50).length;
        
        if (results.length > 1) {
            const gap = (parseFloat(results[0].CompositeScore) - parseFloat(results[1].CompositeScore)).toFixed(1);
            const gapEl = document.getElementById('mc-kpi-gap');
            if (gapEl) gapEl.textContent = gap;
            
            const ruEl = document.getElementById('mc-champ-runnerup');
            if (ruEl) {
                ruEl.innerHTML = `<div style="position:relative; height:200px; width:100%;"><canvas id="chart-mc-radar"></canvas></div>`;
                renderRadarChart(results[0], results[1]);
            }
            
            renderContribChart(results);
        }
        
        renderModelChampionCharts(results);
    }
}

let MC_RADAR_CHART = null;
function renderRadarChart(champ, runnerUp) {
    const ctx = document.getElementById('chart-mc-radar');
    if (!ctx) return;
    if (MC_RADAR_CHART) MC_RADAR_CHART.destroy();
    
    MC_RADAR_CHART = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Accuracy (WAPE)', 'Hit-Rate', 'Bias', 'Stability'],
            datasets: [
                {
                    label: champ.Model + ' (Champion)',
                    data: [champ.wapeScore, champ.hit10Score, champ.biasScore, champ.stabilityScore],
                    backgroundColor: 'rgba(47, 111, 99, 0.2)', // Teal 0.2
                    borderColor: '#2F6F63',
                    borderWidth: 2,
                    pointBackgroundColor: '#2F6F63'
                },
                {
                    label: runnerUp.Model + ' (Runner-Up)',
                    data: [runnerUp.wapeScore, runnerUp.hit10Score, runnerUp.biasScore, runnerUp.stabilityScore],
                    backgroundColor: 'rgba(138, 148, 163, 0.2)', // Gray 0.2
                    borderColor: '#8A94A3',
                    borderWidth: 2,
                    pointBackgroundColor: '#8A94A3'
                }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { display: true },
                    suggestedMin: 0,
                    suggestedMax: 100,
                    ticks: { display: false }
                }
            },
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 12, boxHeight: 12, padding: 20 } },
                tooltip: { 
                    backgroundColor: 'rgba(16, 27, 51, 0.95)',
                    titleFont: { size: 13, family: "'IBM Plex Sans', sans-serif", weight: 'bold' },
                    bodyFont: { size: 13, family: "'IBM Plex Sans', sans-serif" },
                    padding: 12,
                    cornerRadius: 8,
                    boxPadding: 6,
                    usePointStyle: true,
                    callbacks: { 
                        label: (ctx) => {
                            const datasetIndex = ctx.datasetIndex;
                            const index = ctx.dataIndex;
                            const modelObj = datasetIndex === 0 ? champ : runnerUp;
                            const score = Math.round(ctx.raw);
                            let metricStr = '';
                            if (index === 0) metricStr = `${modelObj.WAPE}%`;
                            else if (index === 1) metricStr = `${modelObj.Hit10}%`;
                            else if (index === 2) metricStr = `${modelObj.Bias}%`;
                            else if (index === 3) metricStr = `${modelObj.MaxErr} Units`;
                            
                            return `${ctx.dataset.label}: ${metricStr} (${score} pts)`;
                        }
                    } 
                }
            }
        }
    });
}

let MC_CONTRIB_CHART = null;
function renderContribChart(results) {
    const ctx = document.getElementById('chart-mc-contrib');
    if (!ctx) return;
    if (MC_CONTRIB_CHART) MC_CONTRIB_CHART.destroy();
    
    const top5 = results.slice(0, 5);
    
    MC_CONTRIB_CHART = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top5.map(r => r.Model),
            datasets: [
                {
                    label: 'Accuracy (WAPE)',
                    data: top5.map(r => r.wapeScore * 0.35),
                    backgroundColor: '#16274A' // Navy
                },
                {
                    label: 'Hit-Rate',
                    data: top5.map(r => r.hit10Score * 0.25),
                    backgroundColor: '#2F6F63' // Teal
                },
                {
                    label: 'Bias',
                    data: top5.map(r => r.biasScore * 0.20),
                    backgroundColor: '#C98A2C' // Amber
                },
                {
                    label: 'Stability',
                    data: top5.map(r => r.stabilityScore * 0.20),
                    backgroundColor: '#B3452B' // Rust
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { stacked: true, grid: { display: false }, title: { display: true, text: 'Model', font: { size: 11, color: '#8A94A3' } } },
                y: { stacked: true, beginAtZero: true, max: 100, title: { display: true, text: 'Composite Score (0-100)', font: { size: 11, color: '#8A94A3' } } }
            },
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 12, boxHeight: 12, usePointStyle: true } },
                tooltip: {
                    backgroundColor: 'rgba(16, 27, 51, 0.95)',
                    titleFont: { size: 13, family: "'IBM Plex Sans', sans-serif", weight: 'bold' },
                    bodyFont: { size: 13, family: "'IBM Plex Sans', sans-serif" },
                    padding: 12,
                    cornerRadius: 8,
                    usePointStyle: true,
                    callbacks: {
                        label: (ctx) => {
                            const datasetIndex = ctx.datasetIndex;
                            const modelObj = top5[ctx.dataIndex];
                            const scorePts = ctx.raw.toFixed(1);
                            if (datasetIndex === 0) return `Accuracy: ${modelObj.WAPE}% (${scorePts} pts)`;
                            if (datasetIndex === 1) return `Tolerance: ${modelObj.Hit10}% (${scorePts} pts)`;
                            if (datasetIndex === 2) return `Bias: ${modelObj.Bias}% (${scorePts} pts)`;
                            if (datasetIndex === 3) return `Stability: ${modelObj.MaxErr} Max Err (${scorePts} pts)`;
                            return `${ctx.dataset.label}: ${scorePts} pts`;
                        }
                    }
                }
            }
        }
    });
}

let MC_SCATTER_CHART = null;
let MC_TOPERRORS_CHART = null;
let MC_FAMILY_CHART = null;
let MC_HIST_CHART = null;

function renderModelChampionCharts(results) {
    if (results.length === 0) return;
    
    const getFamily = (m) => {
        const l = m.toLowerCase();
        if (l.includes('prophet')) return 'Prophet';
        if (l.includes('arima')) return 'ARIMA';
        if (l.includes('xgb')) return 'XGB_group';
        if (l.includes('lr')) return 'LR_LA_group';
        return 'Other';
    };
    
    results.forEach(r => r.Family = getFamily(r.Model));
    
    const familyColors = {
        'Prophet': '#384657',
        'ARIMA': '#5f8c81',
        'XGB_group': '#99a5ae',
        'LR_LA_group': '#c79c5e',
        'Other': '#d1d5db'
    };
    
    // 1. WAPE vs Hit10 Scatter
    const scatterCtx = document.getElementById('chart-mc-scatter');
    if (scatterCtx) {
        if (MC_SCATTER_CHART) MC_SCATTER_CHART.destroy();
        
        const datasets = [];
        const families = [...new Set(results.map(r => r.Family))];
        families.forEach(fam => {
            const famResults = results.filter(r => r.Family === fam);
            datasets.push({
                label: fam,
                data: famResults.map(r => ({ x: parseFloat(r.WAPE), y: parseFloat(r.Hit10), r: 6, model: r.Model })),
                backgroundColor: familyColors[fam] || familyColors['Other']
            });
        });
        
        MC_SCATTER_CHART = new Chart(scatterCtx, {
            type: 'bubble',
            data: { datasets },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { boxWidth: 14, boxHeight: 14, padding: 20 }
                    },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `${ctx.raw.model}: WAPE ${ctx.raw.x}%, Hit10 ${ctx.raw.y}%`
                        }
                    }
                },
                scales: {
                    x: { title: { display: true, text: 'WAPE %', font: { size: 11, color: '#8A94A3' } }, grid: { color: '#EEF1F4' } },
                    y: { title: { display: true, text: 'Hit10 %', font: { size: 11, color: '#8A94A3' } }, beginAtZero: true, grid: { color: '#EEF1F4' } }
                }
            }
        });
    }
    
    // 2. Top 7 Models: Average vs Max Error
    const topCtx = document.getElementById('chart-mc-top-errors');
    if (topCtx) {
        if (MC_TOPERRORS_CHART) MC_TOPERRORS_CHART.destroy();
        const top7 = results.slice(0, 7);
        MC_TOPERRORS_CHART = new Chart(topCtx, {
            type: 'bar',
            data: {
                labels: top7.map(r => r.Model),
                datasets: [
                    {
                        label: 'Average WAPE %',
                        data: top7.map(r => parseFloat(r.WAPE)),
                        backgroundColor: '#2F6F63',
                        order: 2
                    },
                    {
                        label: 'Max Error (Units)',
                        data: top7.map(r => parseFloat(r.MaxErr)),
                        type: 'line',
                        borderColor: '#D44E41',
                        borderWidth: 2,
                        backgroundColor: '#fff',
                        pointBackgroundColor: '#fff',
                        pointBorderColor: '#D44E41',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        order: 1,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: {
                    x: { title: { display: true, text: 'Model', font: { size: 11, color: '#8A94A3' } } },
                    y: { type: 'linear', position: 'left', title: { display: true, text: 'WAPE %', font: { size: 11, color: '#8A94A3' } } },
                    y1: { type: 'linear', position: 'right', title: { display: true, text: 'Max Error', font: { size: 11, color: '#8A94A3' } }, grid: { drawOnChartArea: false } }
                }
            }
        });
    }
    
    // 3. Family Performance
    const famCtx = document.getElementById('chart-mc-family');
    if (famCtx) {
        if (MC_FAMILY_CHART) MC_FAMILY_CHART.destroy();
        
        const famScores = {};
        results.forEach(r => {
            if(!famScores[r.Family]) famScores[r.Family] = [];
            famScores[r.Family].push(parseFloat(r.CompositeScore));
        });
        
        const labels = Object.keys(famScores);
        const data = labels.map(f => {
            const sum = famScores[f].reduce((a,b)=>a+b,0);
            return sum / famScores[f].length;
        });
        const colors = labels.map(f => familyColors[f] || familyColors['Other']);
        
        MC_FAMILY_CHART = new Chart(famCtx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Avg Composite Score',
                    data,
                    backgroundColor: colors,
                    maxBarThickness: 50,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { 
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(16, 27, 51, 0.95)',
                        titleFont: { size: 13, family: "'IBM Plex Sans', sans-serif", weight: 'bold' },
                        bodyFont: { size: 13, family: "'IBM Plex Sans', sans-serif" },
                        padding: 12,
                        cornerRadius: 8
                    }
                },
                scales: { 
                    x: { grid: { display: false }, title: { display: true, text: 'Model Family', font: { size: 11, color: '#8A94A3' } } },
                    y: { beginAtZero: true, title: { display: true, text: 'Avg Composite Score', font: { size: 11, color: '#8A94A3' } } } 
                }
            }
        });
    }
    
    // 4. Score Distribution (Histogram)
    const histCtx = document.getElementById('chart-mc-hist');
    if (histCtx) {
        if (MC_HIST_CHART) MC_HIST_CHART.destroy();
        
        const bins = {'0-20':0, '20-40':0, '40-60':0, '60-80':0, '80-100':0};
        results.forEach(r => {
            const s = parseFloat(r.CompositeScore);
            if(s <= 20) bins['0-20']++;
            else if(s <= 40) bins['20-40']++;
            else if(s <= 60) bins['40-60']++;
            else if(s <= 80) bins['60-80']++;
            else bins['80-100']++;
        });
        
        MC_HIST_CHART = new Chart(histCtx, {
            type: 'bar',
            data: {
                labels: Object.keys(bins),
                datasets: [{
                    label: 'Number of Models',
                    data: Object.values(bins),
                    backgroundColor: '#808A98'
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { 
                    x: { title: { display: true, text: 'Score Bucket', font: { size: 11, color: '#8A94A3' } } },
                    y: { beginAtZero: true, ticks: { stepSize: 1 }, title: { display: true, text: 'Number of Models', font: { size: 11, color: '#8A94A3' } } } 
                }
            }
        });
    }
}


let BC_VOLUME_CHART = null;
let BC_BELOW_CHART = null;
let BC_GAUGE_CHART = null;
let BC_VOLATILITY_CHART = null;

function renderBusinessContext() {
    let target = RAW_LEVEL0;
    const filters = window.CURRENT_FILTERS.filters;
    const levelName = window.CURRENT_FILTERS.levelName;
    const nodeName = window.CURRENT_FILTERS.nodeName;
    
    for (const [k, v] of Object.entries(filters)) {
        if (k !== 'Global' && v) target = target.filter(row => row[k] == v);
    }
    
    if (levelName !== 'Global') target = target.filter(row => row[levelName] == nodeName);
    
    // 1. Group by Segment to calculate baselines
    const segments = {};
    const weeks = {};
    let totalRealizedWeeks = 0;
    
    target.forEach(row => {
        const seg = row.Forecast_Name;
        const wk = row.Week_Ending;
        const actualRaw = row.Actual_Offered;
        const actual = (actualRaw !== undefined && actualRaw !== null && actualRaw !== '') ? parseFloat(actualRaw) : null;
        const forecast = parseFloat(row.Manual_Forecast) || 0;
        const meanHist = parseFloat(row['Mean (Hist. Contacts) (Last 1 yr.)']) || 0;
        
        if (!segments[seg]) {
            segments[seg] = {
                actual: 0,
                mean: meanHist,
                std: parseFloat(row['Std Dev (Hist. Contacts)']) || 0,
                count: 0
            };
        }
        if (actual !== null) {
            segments[seg].actual += actual;
            segments[seg].count += 1;
        }
        
        if (!weeks[wk]) {
            weeks[wk] = { actual: null, forecast: 0, totalSegments: 0, segmentsBelow: 0 };
        }
        if (actual !== null) {
            weeks[wk].actual = (weeks[wk].actual || 0) + actual;
            weeks[wk].totalSegments += 1;
            if (actual < meanHist) {
                weeks[wk].segmentsBelow += 1;
            }
        }
        weeks[wk].forecast += forecast;
        
        if (segments[seg].count > totalRealizedWeeks) totalRealizedWeeks = segments[seg].count;
    });
    
    let totalActual = 0;
    let totalMean = 0;
    let totalVariance = 0;
    let segmentsBelow = 0;
    const numSegments = Object.keys(segments).length;
    
    for (const seg of Object.values(segments)) {
        totalActual += seg.actual;
        totalMean += seg.mean;
        totalVariance += Math.pow(seg.std, 2);
        
        const expected = seg.mean * seg.count;
        if (seg.actual < expected) {
            segmentsBelow += 1;
        }
    }
    
    const totalStd = Math.sqrt(totalVariance);
    
    // Update KPIs
    if(document.getElementById('bc-kpi-actual')) document.getElementById('bc-kpi-actual').textContent = Math.round(totalActual).toLocaleString();
    if(document.getElementById('bc-kpi-mean')) document.getElementById('bc-kpi-mean').textContent = Math.round(totalMean).toLocaleString();
    if(document.getElementById('bc-kpi-below')) document.getElementById('bc-kpi-below').textContent = segmentsBelow + ' / ' + numSegments;
    if(document.getElementById('bc-kpi-realized')) document.getElementById('bc-kpi-realized').innerHTML = totalRealizedWeeks + ' <span style="font-size:14px;color:var(--text-2);">/ 13</span>';
    
    // Update Gauge Chart
    const pctBelow = numSegments === 0 ? 0 : Math.round((segmentsBelow / numSegments) * 100);
    if(document.getElementById('bc-gauge-val')) document.getElementById('bc-gauge-val').textContent = pctBelow + '%';
    
    const gaugeCtx = document.getElementById('chart-bc-gauge');
    if (gaugeCtx) {
        if (BC_GAUGE_CHART) BC_GAUGE_CHART.destroy();
        BC_GAUGE_CHART = new Chart(gaugeCtx, {
            type: 'doughnut',
            data: {
                labels: ['Below Baseline', 'Above/At Baseline'],
                datasets: [{
                    data: [segmentsBelow, numSegments - segmentsBelow],
                    backgroundColor: ['#D44E41', '#EEF1F4'],
                    borderWidth: 0,
                    cutout: '75%'
                }]
            },
            options: {
                circumference: 180,
                rotation: -90,
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                }
            }
        });
    }
    
    // Update Volume and Below Baseline Charts
    const sortedWeeks = Object.keys(weeks).sort();
    
    // Calculate dynamic summary text
    let sumPlan = 0;
    let sumActual = 0;
    let minPct = Infinity;
    let minWkIndex = -1;
    
    sortedWeeks.forEach((w, i) => {
        const p = weeks[w].forecast;
        const a = weeks[w].actual;
        if (p && a !== null) {
            sumPlan += p;
            sumActual += a;
            const pct = (a / p) * 100;
            if (pct < minPct) {
                minPct = pct;
                minWkIndex = i;
            }
        }
    });
    
    const summaryEl = document.getElementById('bc-chart-summary');
    if (summaryEl) {
        if (sumPlan > 0 && sumActual > 0) {
            const avgPct = Math.round((sumActual / sumPlan) * 100);
            const lowPct = Math.round(minPct);
            const lowWkLabel = `W${minWkIndex + 1}`;
            const weeklyActuals = sortedWeeks.map(w => weeks[w].actual);
            const weeklyForecasts = sortedWeeks.map(w => weeks[w].forecast);
            const lowActualFormat = Math.round(weeklyActuals[minWkIndex]/1000) + 'K';
            const lowPlanFormat = Math.round(weeklyForecasts[minWkIndex]/1000) + 'K';
            
            summaryEl.innerHTML = `<span style="font-size: 16px; margin-right: 4px;">✦</span> Actual offered volume tracked at ${avgPct}% of plan on average, dropping to a low of ${lowPct}% in ${lowWkLabel} (${lowActualFormat} offered vs ${lowPlanFormat} planned).`;
            summaryEl.style.backgroundColor = 'var(--teal-soft)';
            summaryEl.style.padding = '12px 16px';
            summaryEl.style.borderRadius = '8px';
            summaryEl.style.color = 'var(--teal)';
            summaryEl.style.fontWeight = '500';
            summaryEl.style.fontStyle = 'normal';
            summaryEl.style.display = 'flex';
            summaryEl.style.alignItems = 'center';
            summaryEl.style.marginTop = '16px';
        } else {
            summaryEl.innerHTML = '';
            summaryEl.style.padding = '0';
            summaryEl.style.marginTop = '0';
        }
    }

    const weeklyActuals = sortedWeeks.map(w => weeks[w].actual);
    const weeklyForecasts = sortedWeeks.map(w => weeks[w].forecast);
    const weeklyOfferedPct = sortedWeeks.map(w => {
        const p = weeks[w].forecast;
        const a = weeks[w].actual;
        return (p && a !== null) ? (a / p) * 100 : null;
    });
    
    const weeklyBelowPct = sortedWeeks.map(w => {
        return weeks[w].totalSegments > 0 ? (weeks[w].segmentsBelow / weeks[w].totalSegments) * 100 : 0;
    });
    
    const xLabels = sortedWeeks.map((w, i) => `W${i + 1}`);

    const maxVol = Math.max(
        ...weeklyForecasts.map(v => v || 0),
        ...weeklyActuals.map(v => v || 0)
    );
    const maxPct = Math.max(...weeklyOfferedPct.map(v => v || 0));

    const volCtx = document.getElementById('chart-bc-volume');
    if (volCtx) {
        if (BC_VOLUME_CHART) BC_VOLUME_CHART.destroy();
        BC_VOLUME_CHART = new Chart(volCtx, {
            type: 'bar',
            data: {
                labels: xLabels,
                datasets: [
                    {
                        type: 'line',
                        label: 'Offered%',
                        data: weeklyOfferedPct,
                        borderColor: '#2F6F63',
                        backgroundColor: 'rgba(47, 111, 99, 0.08)',
                        borderWidth: 2.5,
                        fill: true,
                        pointBackgroundColor: '#ffffff',
                        pointBorderColor: '#2F6F63',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        tension: 0.3,
                        yAxisID: 'y1',
                        order: 0,
                        datalabels: {
                            display: true,
                            align: 'top',
                            anchor: 'end',
                            offset: 6,
                            formatter: (val) => val ? Math.round(val) + '%' : '',
                            color: '#2F6F63',
                            font: { weight: '700', size: 11, family: 'var(--sans)' }
                        }
                    },
                    {
                        type: 'bar',
                        label: 'Plan',
                        data: weeklyForecasts,
                        backgroundColor: '#B7C3D4',
                        hoverBackgroundColor: '#9AAFC8',
                        borderRadius: 3,
                        categoryPercentage: 0.6,
                        barPercentage: 0.85,
                        yAxisID: 'y',
                        order: 1,
                        datalabels: { display: false }
                    },
                    {
                        type: 'bar',
                        label: 'Actual Offered',
                        data: weeklyActuals,
                        backgroundColor: '#16274A',
                        hoverBackgroundColor: '#1E3A5F',
                        borderRadius: 3,
                        categoryPercentage: 0.6,
                        barPercentage: 0.85,
                        yAxisID: 'y',
                        order: 2,
                        datalabels: { display: false }
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: { top: 28, left: 4, right: 4, bottom: 4 }
                },
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: { 
                        position: 'bottom', 
                        labels: { 
                            font: { family: 'var(--sans)', size: 12 },
                            color: '#6C7A8C',
                            padding: 20,
                            boxWidth: 16,
                            boxHeight: 16,
                            generateLabels: function(chart) {
                                const original = Chart.defaults.plugins.legend.labels.generateLabels(chart);
                                original.forEach(label => {
                                    label.lineWidth = 3;
                                    let baseColor = label.fillStyle;
                                    if (label.text === 'Offered%') {
                                        baseColor = '#2F6F63';
                                    }
                                    label.strokeStyle = baseColor;
                                    if (typeof baseColor === 'string' && baseColor.startsWith('#')) {
                                        label.fillStyle = baseColor.slice(0, 7) + '26';
                                    } else {
                                        label.fillStyle = 'rgba(255,255,255,0.5)';
                                    }
                                    label.borderRadius = 0;
                                });
                                return original;
                            }
                        } 
                    },
                    tooltip: {
                        backgroundColor: '#16274A',
                        titleFont: { family: 'var(--sans)', size: 13, weight: '600' },
                        bodyFont: { family: 'var(--sans)', size: 12 },
                        padding: 12,
                        cornerRadius: 8,
                        displayColors: true,
                        boxPadding: 4,
                        callbacks: {
                            title: (ctx) => {
                                const idx = ctx[0].dataIndex;
                                return 'Week Ending ' + sortedWeeks[idx];
                            },
                            label: (ctx) => {
                                const label = ctx.dataset.label;
                                const val = ctx.raw;
                                if (label === 'Offered%') {
                                    return ' Offered: ' + (val ? Math.round(val) + '%' : 'N/A');
                                }
                                return ' ' + label + ': ' + (val ? Math.round(val).toLocaleString() : 'N/A');
                            }
                        }
                    }
                },
                scales: {
                    x: { 
                        grid: { display: false },
                        ticks: { 
                            font: { size: 12, family: 'var(--sans)', weight: '500' },
                            color: '#6C7A8C'
                        }
                    },
                    y: { 
                        type: 'linear',
                        display: true,
                        position: 'left',
                        beginAtZero: true, 
                        grid: { color: '#EEF1F4' },
                        ticks: {
                            font: { size: 11, family: 'var(--sans)' },
                            color: '#6C7A8C',
                            callback: function(value) {
                                return value >= 1000 ? (value / 1000) + 'K' : value;
                            }
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        min: 0,
                        max: 110,
                        grid: { display: false },
                        ticks: {
                            stepSize: 10,
                            font: { size: 11, family: 'var(--sans)' },
                            color: '#2F6F63',
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    // Variance sub-chart (Actual - Plan) aligned below the main chart
    const weeklyVariance = sortedWeeks.map(w => {
        const a = weeks[w].actual;
        const p = weeks[w].forecast;
        return (a !== null && p) ? a - p : null;
    });
    const varCtx = document.getElementById('chart-bc-variance');
    if (varCtx) {
        if (window._bcVarianceChart) window._bcVarianceChart.destroy();
        window._bcVarianceChart = new Chart(varCtx, {
            type: 'bar',
            data: {
                labels: xLabels,
                datasets: [{
                    label: 'Variance (Actual − Plan)',
                    data: weeklyVariance,
                    backgroundColor: weeklyVariance.map(v => v !== null && v >= 0 ? '#2F6F63' : '#D44E41'),
                    borderRadius: 2,
                    categoryPercentage: 0.5,
                    barPercentage: 0.8,
                    datalabels: {
                        display: true,
                        clip: false,
                        clamp: true,
                        align: 'end',
                        anchor: 'end',
                        offset: 2,
                        formatter: (val) => {
                            if (val === null) return '';
                            const k = Math.round(val / 1000);
                            return (k >= 0 ? '+' : '') + k + 'K';
                        },
                        color: function(ctx) {
                            const v = ctx.dataset.data[ctx.dataIndex];
                            return v >= 0 ? '#2F6F63' : '#D44E41';
                        },
                        font: { size: 10, weight: '600', family: 'var(--sans)' }
                    }
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: { top: 16, bottom: 32, left: 4, right: 4 }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#16274A',
                        padding: 10,
                        cornerRadius: 8,
                        callbacks: {
                            title: (ctx) => 'Week Ending ' + sortedWeeks[ctx[0].dataIndex],
                            label: (ctx) => {
                                const v = ctx.raw;
                                if (v === null) return 'N/A';
                                return ' Variance: ' + (v >= 0 ? '+' : '') + Math.round(v).toLocaleString();
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        grid: { color: '#EEF1F4' },
                        ticks: {
                            font: { size: 10, family: 'var(--sans)' },
                            color: '#6C7A8C',
                            callback: function(value) {
                                const k = value / 1000;
                                return (k >= 0 ? '+' : '') + k + 'K';
                            }
                        }
                    }
                }
            }
        });
    }

    // Channel Mix Chart
    const channelMixCtx = document.getElementById('chart-bc-channel');
    if (channelMixCtx) {
        // Group data by week and channel
        const channelData = {};
        const allChannels = new Set();
        
        target.forEach(row => {
            const wk = row.Week_Ending;
            const channel = row.Channel || 'Unknown';
            const actual = parseFloat(row.Actual_Offered);
            
            if (!isNaN(actual) && actual > 0) {
                allChannels.add(channel);
                if (!channelData[wk]) channelData[wk] = {};
                if (!channelData[wk][channel]) channelData[wk][channel] = 0;
                channelData[wk][channel] += actual;
            }
        });
        
        // Do NOT filter out any channels, ensuring 'Case' remains visible
        const channelList = Array.from(allChannels).sort();
        // Use strict dashboard theme colors but swap Case and Voice colors
        // Expected sort: Case (0), Chat (1), Email (2), Social Media (3), Voice (4)
        // Original: Navy, Teal, Amber, Rust, Gray -> New: Gray, Teal, Amber, Rust, Navy
        const colors = ['#8A94A3', '#2F6F63', '#C98A2C', '#B3452B', '#16274A'];
        
        const channelDatasets = channelList.map((channel, i) => {
            return {
                label: channel,
                data: sortedWeeks.map(w => (channelData[w] && channelData[w][channel]) ? channelData[w][channel] : 0),
                backgroundColor: colors[i % colors.length],
                barPercentage: 0.65,
                categoryPercentage: 0.75,
                datalabels: {
                    display: false
                }
            };
        });

        if (window.BC_CHANNEL_CHART) window.BC_CHANNEL_CHART.destroy();
        window.BC_CHANNEL_CHART = new Chart(channelMixCtx, {
            type: 'bar',
            data: {
                labels: xLabels, // Re-use the existing xLabels (W1, W2, etc.)
                datasets: channelDatasets
            },
            options: {
                onClick: (e, elements, chart) => {
                    if (!elements.length) return;
                    const datasetIndex = elements[0].datasetIndex;
                    const label = chart.data.datasets[datasetIndex].label;
                    addGlobalFilterPill('Channel', label);
                },
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: { top: 10, bottom: 4, left: 4, right: 4 }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 24,
                            font: { family: 'var(--sans)', size: 13, weight: '500' },
                            color: '#6C7A8C',
                            boxWidth: 16,
                            boxHeight: 16,
                            generateLabels: function(chart) {
                                const original = Chart.defaults.plugins.legend.labels.generateLabels(chart);
                                original.forEach(label => {
                                    label.lineWidth = 3;
                                    let baseColor = label.fillStyle;
                                    label.strokeStyle = baseColor;
                                    if (typeof baseColor === 'string' && baseColor.startsWith('#')) {
                                        label.fillStyle = baseColor.slice(0, 7) + '26';
                                    }
                                    label.borderRadius = 0; // Ensures sharp square corners
                                });
                                return original;
                            }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: '#16274A',
                        titleFont: { family: 'var(--sans)', size: 13, weight: '600' },
                        bodyFont: { family: 'var(--sans)', size: 12 },
                        padding: 12,
                        cornerRadius: 8,
                        callbacks: {
                            title: (ctx) => 'Week Ending ' + sortedWeeks[ctx[0].dataIndex],
                            label: (ctx) => {
                                const val = ctx.raw;
                                if (!val) return null;
                                let total = 0;
                                ctx.chart.data.datasets.forEach(ds => {
                                    total += ds.data[ctx.dataIndex];
                                });
                                const pct = total > 0 ? Math.round((val / total) * 100) : 0;
                                return ` ${ctx.dataset.label}: ${Math.round(val).toLocaleString()} (${pct}%)`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        grid: { display: false },
                        ticks: { font: { size: 12, family: 'var(--sans)' }, color: '#6C7A8C' }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        grid: { color: '#EEF1F4' },
                        ticks: {
                            font: { size: 11, family: 'var(--sans)' },
                            color: '#6C7A8C',
                            callback: function(value) {
                                return value >= 1000 ? (value / 1000) + 'K' : value;
                            }
                        }
                    }
                }
            }
        });
    }

    const belowCtx = document.getElementById('chart-bc-below');   if (belowCtx) {
        if (BC_BELOW_CHART) BC_BELOW_CHART.destroy();
        BC_BELOW_CHART = new Chart(belowCtx, {
            type: 'bar',
            data: {
                labels: sortedWeeks,
                datasets: [{
                    label: '% Segments Below Baseline',
                    data: weeklyBelowPct,
                    backgroundColor: '#D44E41',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { mode: 'index', intersect: false, callbacks: { label: (ctx) => ctx.raw.toFixed(1) + '%' } }
                },
                scales: {
                    x: { grid: { display: false } },
                    y: { beginAtZero: true, max: 100, grid: { color: '#EEF1F4' }, ticks: { callback: (val) => val + '%' } }
                }
            }
        });
    }
    
    // Update Volatility Chart
    const weeklyMeans = sortedWeeks.map(() => totalMean);
    const weeklyUpper = sortedWeeks.map(() => totalMean + totalStd);
    const weeklyLower = sortedWeeks.map(() => Math.max(0, totalMean - totalStd));
    
    const volCtx2 = document.getElementById('chart-bc-volatility');
    if (volCtx2) {
        if (BC_VOLATILITY_CHART) BC_VOLATILITY_CHART.destroy();
        BC_VOLATILITY_CHART = new Chart(volCtx2, {
            type: 'bar',
            data: {
                labels: sortedWeeks,
                datasets: [
                    {
                        type: 'line',
                        label: 'Upper Bound (+1 Std Dev)',
                        data: weeklyUpper,
                        borderColor: 'rgba(128,138,152,0.5)',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        type: 'line',
                        label: 'Historical Mean',
                        data: weeklyMeans,
                        borderColor: '#808A98',
                        borderWidth: 2,
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        type: 'line',
                        label: 'Lower Bound (-1 Std Dev)',
                        data: weeklyLower,
                        borderColor: 'rgba(128,138,152,0.5)',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        type: 'bar',
                        label: 'Actual Volume',
                        data: weeklyActuals,
                        backgroundColor: '#16274A',
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { mode: 'index', intersect: false }
                },
                scales: {
                    x: { grid: { display: false }, title: { display: true, text: 'Week', font: { size: 11, color: '#8A94A3' } } },
                    y: { beginAtZero: true, grid: { color: '#EEF1F4' }, title: { display: true, text: 'Volume', font: { size: 11, color: '#8A94A3' } } }
                }
            }
        });
    }
}

// Stub for renderRootCausePanel (called by nav/updateScope for Hybrid nodes)
function renderRootCausePanel(nodeName, levelName, filters) {
    const panel = document.getElementById('root-cause-panel');
    if (!panel) return;
    panel.style.display = 'block';
    
    // 1. Filter Level 1 data
    let target = RAW_LEVEL1;
    for (const [k, v] of Object.entries(filters)) {
        if (k !== 'Global' && v) target = target.filter(row => v.includes(String(row[k])));
    }
    
    // Also apply global classification filter if active
    if (window.CLASSIFICATION_FILTER && window.CLASSIFICATION_FILTER.length > 0) {
        target = target.filter(r => window.CLASSIFICATION_FILTER.includes(r.Classification));
    }
    
    // 2. Identify Detractors
    let mlDetractors = [];
    let manualDetractors = [];
    
    for (const q of target) {
        const mlErr = q.Queue_ML_Err_Sum || 0;
        const manErr = q.Queue_Manual_Err_Sum || 0;
        const actual = q.Queue_Actual_Sum || 1; // avoid /0
        
        const errorDelta = Math.abs(mlErr - manErr);
        const mlWape = ((mlErr / actual) * 100).toFixed(1);
        const manWape = ((manErr / actual) * 100).toFixed(1);
        
        const item = {
            name: q.Forecast_Name,
            vol: q.Queue_Actual_Sum.toLocaleString(),
            mlWape: mlWape,
            manWape: manWape,
            delta: errorDelta,
            mlFailed: mlErr > manErr,
            manFailed: manErr > mlErr
        };
        
        if (item.mlFailed) mlDetractors.push(item);
        if (item.manFailed) manualDetractors.push(item);
    }
    
    // 3. Sort by raw Error Delta descending
    mlDetractors.sort((a, b) => b.delta - a.delta);
    manualDetractors.sort((a, b) => b.delta - a.delta);
    
    // 4. Slice top 5
    mlDetractors = mlDetractors.slice(0, 5);
    manualDetractors = manualDetractors.slice(0, 5);
    
    // 5. Build HTML tables
    const buildTable = (items) => {
        if (items.length === 0) return `<div style="padding:16px; color:var(--text-2); font-style:italic;">No significant detractors found in this scope.</div>`;
        
        let html = `<table class="lb" style="width: 100%; table-layout: fixed; font-size: 13px; margin-top: 10px; border-top: 1px solid var(--line); border-collapse: collapse;">
            <thead>
              <tr style="border-bottom: 1px solid var(--line); color: var(--text-2); background-color: rgba(0,0,0,0.02);">
                <th style="text-align:left; padding:10px 12px; width:55%;">Forecast Name</th>
                <th class="num" style="text-align:right; padding:10px 12px; width:15%;">Volume</th>
                <th class="num" style="text-align:right; padding:10px 12px; width:15%;">ML WAPE</th>
                <th class="num" style="text-align:right; padding:10px 12px; width:15%;">Manual WAPE</th>
              </tr>
            </thead>
            <tbody>`;
            
        for (const item of items) {
            const mlColor = item.mlFailed ? 'color:var(--rust);' : 'color:var(--teal); font-weight:600;';
            const manColor = item.manFailed ? 'color:var(--rust);' : 'color:var(--teal); font-weight:600;';
            
            html += `<tr style="border-bottom: 1px solid var(--line); transition: background-color 0.2s;" onmouseover="this.style.backgroundColor='rgba(0,0,0,0.02)'" onmouseout="this.style.backgroundColor='transparent'">
                <td style="text-align:left; padding:10px 12px; font-weight:500; color:var(--navy);">${item.name}</td>
                <td class="num" style="text-align:right; padding:10px 12px;">${item.vol}</td>
                <td class="num" style="text-align:right; padding:10px 12px; ${mlColor}">${item.mlWape}%</td>
                <td class="num" style="text-align:right; padding:10px 12px; ${manColor}">${item.manWape}%</td>
            </tr>`;
        }
        html += `</tbody></table>`;
        return html;
    };
    
    panel.innerHTML = `<div style="padding: 16px 22px;">
        <h4 style="margin:0 0 12px; font-family:var(--sans); font-size:14px; font-weight:600; color:var(--navy);">Root Cause Analysis: Top Detractors <span style="font-weight:400; color:var(--text-2); font-size:12px;">(${nodeName})</span></h4>
        <div class="bq" style="margin-bottom:16px;">Queues are ranked by absolute error difference. A massive spike will instantly bubble to the top here.</div>
        
        <div style="display: grid; grid-template-columns: 1fr; gap: 24px;">
            <div>
                <h5 style="margin: 0 0 4px; font-family:var(--sans); font-size: 13px; color:var(--navy);">Top ML Detractors <span style="font-weight:400; color:var(--text-2); font-size:11px;">(Where Manual won)</span></h5>
                ${buildTable(mlDetractors)}
            </div>
            <div>
                <h5 style="margin: 0 0 4px; font-family:var(--sans); font-size: 13px; color:var(--navy);">Top Manual Detractors <span style="font-weight:400; color:var(--text-2); font-size:11px;">(Where ML won)</span></h5>
                ${buildTable(manualDetractors)}
            </div>
        </div>
    </div>`;
}

// NEW: Instant Custom Tooltip for Confidence Bar
window.showConfTooltip = function(e, high, medium, low) {
    if (!window._confTooltip) {
        window._confTooltip = document.createElement('div');
        window._confTooltip.style.position = 'absolute';
        window._confTooltip.style.backgroundColor = '#ffffff';
        window._confTooltip.style.border = '1px solid #E4E8EE';
        window._confTooltip.style.padding = '8px 12px';
        window._confTooltip.style.borderRadius = '6px';
        window._confTooltip.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
        window._confTooltip.style.color = '#101B33';
        window._confTooltip.style.fontSize = '12px';
        window._confTooltip.style.pointerEvents = 'none';
        window._confTooltip.style.zIndex = '10000';
        document.body.appendChild(window._confTooltip);
    }
    window._confTooltip.innerHTML = `
        <strong style="font-size:13px;">Confidence Mix</strong><br/>
        <div style="margin-top:4px; display:flex; align-items:center; gap:6px;">
            <div style="width:8px; height:8px; border-radius:2px; background:#2563EB;"></div> High (≥10 wks): ${high}%
        </div>
        <div style="display:flex; align-items:center; gap:6px;">
            <div style="width:8px; height:8px; border-radius:2px; background:#93C5FD;"></div> Medium (4-9 wks): ${medium}%
        </div>
        <div style="display:flex; align-items:center; gap:6px;">
            <div style="width:8px; height:8px; border-radius:2px; background:#DBEAFE;"></div> Low (<4 wks): ${low}%
        </div>
    `;
    window._confTooltip.style.display = 'block';
    window._confTooltip.style.left = (e.pageX + 15) + 'px';
    window._confTooltip.style.top = (e.pageY + 15) + 'px';
};

window.hideConfTooltip = function() {
    if (window._confTooltip) {
        window._confTooltip.style.display = 'none';
    }
};


function downloadFlatTableCSV(queues) {
    if (!queues || queues.length === 0) return;
    
    const headers = ['Region', 'Sub-region', 'Country', 'Offering', 'Forecast Name', 'Class', 'Weeks', 'ML WAPE', 'Manual WAPE', 'Opportunity (Units)'];
    
    let csv = headers.join(',') + '\n';
    
    queues.forEach(q => {
        const wapeML = (q.Queue_WAPE_ML * 100).toFixed(1) + '%';
        const wapeMan = (q.Queue_WAPE_Manual * 100).toFixed(1) + '%';
        const oppDelta = Math.round((q.Queue_Manual_Err_Sum||0) - (q.Queue_ML_Err_Sum||0));
        const oppText = oppDelta > 0 ? ('+' + oppDelta + ' saved w/ ML') : (oppDelta < 0 ? ('Hold Manual (' + Math.abs(oppDelta) + ')') : '0');
        const row = [
            q.Region || '',
            q.SubRegion || '',
            q.Country || '',
            q.Offering || '',
            q.Forecast_Name || '',
            q.Classification || '',
            q.Valid_Weeks_Count || 0,
            wapeML,
            wapeMan,
        oppText
        ].map(cell => {
            let str = String(cell);
            if (str.includes(',') || str.includes('"')) {
                str = '"' + str.replace(/"/g, '""') + '"';
            }
            return str;
        });
        csv += row.join(',') + '\n';
    });
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'Forecast_Names_Detail.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// --- WAPE threshold color coding (3.1): lower WAPE is better ---
function getWAPEClass(value){
    if(value==null || isNaN(value)) return '';
    if(value <= 0.10) return 'background-color:var(--teal-soft); color:var(--teal); font-weight:600;';
    if(value <= 0.20) return 'background-color:var(--amber-soft); color:var(--amber); font-weight:600;';
    return 'background-color:var(--rust-soft); color:var(--rust); font-weight:600;';
}

// --- Opinionated quick-view local filters for the flat table (3.3) ---
window.FLAT_QUICK_VIEW = null;
window.LAST_FLAT_ARGS = null;
window.applyQuickView = function(view){
    // toggle off if the same chip is clicked again
    window.FLAT_QUICK_VIEW = (window.FLAT_QUICK_VIEW === view) ? null : view;
    document.querySelectorAll('#sa-flat-quick-views .qv-chip').forEach(c=>{
        c.classList.toggle('qv-active', c.getAttribute('data-view') === window.FLAT_QUICK_VIEW);
    });
    if(window.LAST_FLAT_ARGS){
        const [n,l,f] = window.LAST_FLAT_ARGS;
        renderQueueFlatTable(n,l,f);
    }
};

function renderQueueFlatTable(nodeName, levelName, filters) {
    try {

    const tbody = document.getElementById('sa-flat-table-body');
    const title = document.getElementById('sa-flat-table-title');
    if (!tbody || !title) return;
    
    title.textContent = levelName === 'Global' ? '(Global)' : `(${nodeName})`;
    
    let queues = RAW_LEVEL1;
    if (levelName !== 'Global') {
        queues = queues.filter(r => String(r[levelName]) === String(nodeName));
    }
    
    // Also apply global filters if any
    for (const [k, v] of Object.entries(filters)) {
        if (k !== levelName) {
            queues = queues.filter(r => v.includes(String(r[k])));
        }
    }
    
    // Apply classification filter if set
    const classFilter = window.CLASSIFICATION_FILTER || [];
    if (classFilter.length > 0) {
        queues = queues.filter(r => classFilter.includes(r.Classification));
    }

    // Remember args so quick-view chips can re-render with the same scope (3.3)
    window.LAST_FLAT_ARGS = [nodeName, levelName, filters];

    // Apply opinionated quick-view local filter, bypassing the heavy global filter (3.3)
    const qv = window.FLAT_QUICK_VIEW;
    if (qv === 'manualfail') {
        queues = [...queues].sort((a,b)=>(b.Queue_WAPE_Manual||0)-(a.Queue_WAPE_Manual||0)).slice(0,10);
    } else if (qv === 'mlwins') {
        queues = queues.filter(r => (r.Queue_WAPE_ML||0) < (r.Queue_WAPE_Manual||0));
    } else if (qv === 'volatility') {
        // per-queue volatility from level0 historical std dev (cached once)
        if(!window._VOL_MAP){
            window._VOL_MAP = {};
            (RAW_LEVEL0||[]).forEach(r=>{
                const k=r.Forecast_Name, s=r['Std Dev (Hist. Contacts)'];
                if(k && s!=null){ (window._VOL_MAP[k]=window._VOL_MAP[k]||[]).push(s); }
            });
        }
        const volOf = q => { const a=window._VOL_MAP[q.Forecast_Name]; return (a&&a.length)? a.reduce((x,y)=>x+y,0)/a.length : 0; };
        queues = [...queues].sort((a,b)=>volOf(b)-volOf(a)).slice(0,10);
    }

    tbody.innerHTML = '';
    if (queues.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding: 20px;">No forecast names found.</td></tr>';
        return;
    }
    
    queues.sort((a, b) => (a.Forecast_Name || '').localeCompare(b.Forecast_Name || ''));

    // Attach event listener for CSV download
    const btnDownload = document.getElementById('btn-download-excel');
    if (btnDownload) {
        // Remove existing listener if any by cloning
        const newBtn = btnDownload.cloneNode(true);
        btnDownload.parentNode.replaceChild(newBtn, btnDownload);
        newBtn.addEventListener('click', () => {
            downloadFlatTableCSV(queues);
        });
    }

    
    queues.forEach(q => {
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid var(--line)';
        
        let bg = '';
        let classBadge = `<span style="color:var(--text-2);">-</span>`;
        if (q.Classification === 'Strong ML') {
            bg = 'background-color: #ebfbf2;';
            classBadge = `<div class="chip high" style="margin: 0 auto; width: 60px;">Strong ML</div>`;
        } else if (q.Classification === 'Manual') {
            bg = 'background-color: #fcedec;';
            classBadge = `<div class="chip low" style="margin: 0 auto; width: 60px;">Manual</div>`;
        } else if (q.Classification === 'Hybrid') {
            bg = 'background-color: #fff8e1;';
            classBadge = `<div class="chip medium" style="margin: 0 auto; width: 60px;">Hybrid</div>`;
        }
        
        if (bg) tr.style.cssText = 'border-bottom: 1px solid var(--line); ' + bg;
        
        const wapeML = (q.Queue_WAPE_ML * 100).toFixed(1) + '%';
        const wapeMan = (q.Queue_WAPE_Manual * 100).toFixed(1) + '%';
        const wapeMLStyle = getWAPEClass(q.Queue_WAPE_ML);
        const wapeManStyle = getWAPEClass(q.Queue_WAPE_Manual);

        // Opportunity (Units) — queue-level absolute-error delta: Manual err − ML err (3.2)
        const oppDelta = Math.round((q.Queue_Manual_Err_Sum||0) - (q.Queue_ML_Err_Sum||0));
        let oppCell;
        if (oppDelta > 0) {
            oppCell = `<td class="num" style="padding: 10px; text-align:right; color:var(--teal); font-weight:700;">+${oppDelta.toLocaleString()} <span style="font-weight:500; color:var(--text-2);">w/ ML</span></td>`;
        } else if (oppDelta < 0) {
            oppCell = `<td class="num" style="padding: 10px; text-align:right; color:var(--rust); font-weight:600;">Hold Manual <span style="font-weight:500;">(${Math.abs(oppDelta).toLocaleString()})</span></td>`;
        } else {
            oppCell = `<td class="num" style="padding: 10px; text-align:right; color:var(--text-2);">—</td>`;
        }

        tr.innerHTML = `
            <td style="padding: 10px;">${q.Region || '-'}</td>
            <td style="padding: 10px;">${q.SubRegion || '-'}</td>
            <td style="padding: 10px;">${q.Country || '-'}</td>
            <td style="padding: 10px;">${q.Offering || '-'}</td>
            <td style="padding: 10px; font-weight: 500; color: var(--navy);">${q.Forecast_Name}</td>
            <td style="padding: 10px; text-align:center;">${classBadge}</td>
            <td class="num" style="padding: 10px; text-align:right;">${q.Valid_Weeks_Count}</td>
            <td class="num" style="padding: 10px; text-align:right; ${wapeMLStyle}">${wapeML}</td>
            <td class="num" style="padding: 10px; text-align:right; ${wapeManStyle}">${wapeMan}</td>
            ${oppCell}
        `;
        tbody.appendChild(tr);
    });
    } catch(e) {
        document.getElementById('sa-flat-table-title').textContent = 'ERROR: ' + e.message;
        console.error(e);
    }
}

// NEW: Instant Custom Tooltip for Confidence Bar
window.showConfTooltip = function(e, high, medium, low) {
    if (!window._confTooltip) {
        window._confTooltip = document.createElement('div');
        window._confTooltip.style.position = 'absolute';
        window._confTooltip.style.backgroundColor = '#ffffff';
        window._confTooltip.style.border = '1px solid #E4E8EE';
        window._confTooltip.style.padding = '8px 12px';
        window._confTooltip.style.borderRadius = '6px';
        window._confTooltip.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
        window._confTooltip.style.color = '#101B33';
        window._confTooltip.style.fontSize = '12px';
        window._confTooltip.style.pointerEvents = 'none';
        window._confTooltip.style.zIndex = '10000';
        document.body.appendChild(window._confTooltip);
    }
    window._confTooltip.innerHTML = `
        <strong style="font-size:13px;">Confidence Mix</strong><br/>
        <div style="margin-top:4px; display:flex; align-items:center; gap:6px;">
            <div style="width:8px; height:8px; border-radius:2px; background:#2563EB;"></div> High (≥10 wks): ${high}%
        </div>
        <div style="display:flex; align-items:center; gap:6px;">
            <div style="width:8px; height:8px; border-radius:2px; background:#93C5FD;"></div> Medium (4-9 wks): ${medium}%
        </div>
        <div style="display:flex; align-items:center; gap:6px;">
            <div style="width:8px; height:8px; border-radius:2px; background:#DBEAFE;"></div> Low (<4 wks): ${low}%
        </div>
    `;
    window._confTooltip.style.display = 'block';
    window._confTooltip.style.left = (e.pageX + 15) + 'px';
    window._confTooltip.style.top = (e.pageY + 15) + 'px';
};

window.hideConfTooltip = function() {
    if (window._confTooltip) {
        window._confTooltip.style.display = 'none';
    }
};


function downloadFlatTableCSV(queues) {
    if (!queues || queues.length === 0) return;
    
    const headers = ['Region', 'Sub-region', 'Country', 'Offering', 'Forecast Name', 'Class', 'Weeks', 'ML WAPE', 'Manual WAPE', 'Opportunity (Units)'];
    
    let csv = headers.join(',') + '\n';
    
    queues.forEach(q => {
        const wapeML = (q.Queue_WAPE_ML * 100).toFixed(1) + '%';
        const wapeMan = (q.Queue_WAPE_Manual * 100).toFixed(1) + '%';
        const oppDelta = Math.round((q.Queue_Manual_Err_Sum||0) - (q.Queue_ML_Err_Sum||0));
        const oppText = oppDelta > 0 ? ('+' + oppDelta + ' saved w/ ML') : (oppDelta < 0 ? ('Hold Manual (' + Math.abs(oppDelta) + ')') : '0');
        const row = [
            q.Region || '',
            q.SubRegion || '',
            q.Country || '',
            q.Offering || '',
            q.Forecast_Name || '',
            q.Classification || '',
            q.Valid_Weeks_Count || 0,
            wapeML,
            wapeMan,
        oppText
        ].map(cell => {
            let str = String(cell);
            if (str.includes(',') || str.includes('"')) {
                str = '"' + str.replace(/"/g, '""') + '"';
            }
            return str;
        });
        csv += row.join(',') + '\n';
    });
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'Forecast_Names_Detail.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}



let currentMapMode = 'Manual';
let accuracyMapInstance = null;

// Comprehensive country name → ISO 3166-1 alpha-2 mapping
const COUNTRY_TO_ISO = {
    'Australia': 'AU', 'Bangladesh': 'BD', 'Brazil': 'BR', 'Bulgaria': 'BG',
    'Canada': 'CA', 'China': 'CN', 'Czech Republic': 'CZ', 'Denmark': 'DK',
    'Finland': 'FI', 'France': 'FR', 'Germany': 'DE', 'Greece': 'GR',
    'Hong Kong': 'HK', 'Hungary': 'HU', 'India': 'IN', 'Indonesia': 'ID',
    'Israel': 'IL', 'Italy': 'IT', 'Japan': 'JP', 'Kenya': 'KE',
    'Korea': 'KR', 'Malaysia': 'MY', 'Morocco': 'MA', 'Netherlands': 'NL',
    'Norway': 'NO', 'Pakistan': 'PK', 'Philippines': 'PH', 'Poland': 'PL',
    'Portugal': 'PT', 'Romania': 'RO', 'Russia': 'RU', 'Slovenia': 'SI',
    'South Africa': 'ZA', 'Spain': 'ES', 'Sri Lanka': 'LK', 'Sweden': 'SE',
    'Taiwan': 'TW', 'Thailand': 'TH', 'Turkey': 'TR',
    'United Kingdom': 'GB', 'United States': 'US', 'Vietnam': 'VN',
    // Grouped expansions
    'Belgium': 'BE', 'Luxembourg': 'LU', 'Iceland': 'IS',
    'Argentina': 'AR', 'Chile': 'CL', 'Colombia': 'CO', 'Peru': 'PE',
    'Ecuador': 'EC', 'Uruguay': 'UY', 'Paraguay': 'PY', 'Bolivia': 'BO',
    'Kazakhstan': 'KZ', 'Uzbekistan': 'UZ', 'Belarus': 'BY',
    'Azerbaijan': 'AZ', 'Georgia': 'GE', 'Armenia': 'AM', 'Moldova': 'MD',
    'Mexico': 'MX', 'Costa Rica': 'CR', 'Panama': 'PA'
};

const GROUPINGS = {
    'Benelux': ['Belgium', 'Netherlands', 'Luxembourg'],
    'Nordics': ['Denmark', 'Finland', 'Iceland', 'Norway', 'Sweden'],
    'ROLA': ['Argentina', 'Chile', 'Colombia', 'Peru', 'Ecuador', 'Uruguay', 'Paraguay', 'Bolivia'],
    'eCIS': ['Kazakhstan', 'Uzbekistan', 'Belarus', 'Azerbaijan', 'Georgia', 'Armenia', 'Moldova'],
    'Multiple AMER Countries': ['Mexico', 'Costa Rica', 'Panama']
};

// Region mapping – the dataset uses 'Americas' not 'AMER'
const REGION_KEY_MAP = { 'Americas': 'AMER', 'EMEA': 'EMEA', 'APJ': 'APJ' };

function renderAccuracyMap() {
    if (!document.getElementById('accuracy-map')) return;

    const filters = window.CURRENT_FILTERS ? window.CURRENT_FILTERS.filters : {};
    const classFilter = window.CLASSIFICATION_FILTER || [];

    let targetL1 = RAW_LEVEL1;
    for (const [k, v] of Object.entries(filters)) {
        if (k !== 'Global') targetL1 = targetL1.filter(row => v.includes(String(row[k])));
    }
    if (classFilter.length > 0) {
        targetL1 = targetL1.filter(row => classFilter.includes(row.Classification));
    }

    // Aggregate per ISO code
    const isoData = {};  // { 'US': { sumWape, count, displayName } }
    const regionData = { 'AMER': { s: 0, n: 0 }, 'EMEA': { s: 0, n: 0 }, 'APJ': { s: 0, n: 0 } };

    targetL1.forEach(q => {
        if (!q.Country || q.Country === 'Null' || q.Country === 'N/A') return;

        const wape = currentMapMode === 'Manual' ? q.Queue_WAPE_Manual : q.Queue_WAPE_ML;
        const wapePct = wape * 100;

        // Region aggregation
        const regionKey = REGION_KEY_MAP[q.Region];
        if (regionKey && regionData[regionKey]) {
            regionData[regionKey].s += wapePct;
            regionData[regionKey].n++;
        }

        // Expand grouped countries
        let countries = [q.Country];
        if (GROUPINGS[q.Country]) countries = GROUPINGS[q.Country];

        countries.forEach(c => {
            const iso = COUNTRY_TO_ISO[c];
            if (!iso) return;
            if (!isoData[iso]) isoData[iso] = { sumWape: 0, count: 0, displayName: c };
            isoData[iso].sumWape += wapePct;
            isoData[iso].count++;
        });
    });

    // Build color map and accuracy lookup
    const colorMap = {};
    const accLookup = {};
    let maxAcc = -Infinity, maxCountry = '';
    let minAcc = Infinity, minCountry = '';

    Object.keys(isoData).forEach(iso => {
        const d = isoData[iso];
        if (d.count > 0) {
            const meanWape = d.sumWape / d.count;
            const accuracy = 100 - meanWape;
            accLookup[iso] = { acc: accuracy, name: d.displayName };

            if (accuracy >= 90) colorMap[iso] = '#10b981';
            else if (accuracy >= 80) colorMap[iso] = '#3b82f6';
            else if (accuracy >= 70) colorMap[iso] = '#f59e0b';
            else colorMap[iso] = '#ef4444';

            if (accuracy > maxAcc) { maxAcc = accuracy; maxCountry = d.displayName; }
            if (accuracy < minAcc) { minAcc = accuracy; minCountry = d.displayName; }
        }
    });

    // Update region labels
    Object.keys(regionData).forEach(r => {
        const el = document.getElementById('region-label-' + r.toLowerCase());
        if (el) {
            if (regionData[r].n > 0) {
                const acc = 100 - (regionData[r].s / regionData[r].n);
                el.textContent = r + ' ' + acc.toFixed(0) + '%';
            } else {
                el.textContent = r + ' --%';
            }
        }
    });

    // Update banner
    const bannerEl = document.getElementById('map-banner-text');
    if (bannerEl) {
        if (maxAcc !== -Infinity) {
            const maxLabel = maxAcc >= 90 ? 'Excellent' : maxAcc >= 80 ? 'Good' : maxAcc >= 70 ? 'Fair' : 'Critical';
            const minLabel = minAcc >= 90 ? 'Excellent' : minAcc >= 80 ? 'Good' : minAcc >= 70 ? 'Fair' : 'Critical';
            bannerEl.innerHTML = `<b>${maxCountry}</b> leads at ${maxAcc.toFixed(0)}% accuracy (${maxLabel}), while <b>${minCountry}</b> trails at ${minAcc.toFixed(0)}% (${minLabel}) — a ${(maxAcc - minAcc).toFixed(0)}-point gap between regions.`;
        } else {
            bannerEl.innerHTML = 'No data available for current selection.';
        }
    }

    // Store accLookup globally so event handlers can access it
    window._mapAccLookup = accLookup;

    // Destroy previous instance if it exists
    if (accuracyMapInstance) {
        try { accuracyMapInstance.destroy(); } catch(e) {}
        accuracyMapInstance = null;
    }
    // Clean old map div and old injected style
    const wrapper = document.getElementById('accuracy-map');
    const oldTarget = document.getElementById('jvm-map-target');
    if (oldTarget) oldTarget.remove();
    const oldStyle = document.getElementById('map-color-styles');
    if (oldStyle) oldStyle.remove();

    // Create a fresh div for jsvectormap
    const mapDiv = document.createElement('div');
    mapDiv.id = 'jvm-map-target';
    mapDiv.style.width = '100%';
    mapDiv.style.height = '100%';
    wrapper.insertBefore(mapDiv, wrapper.firstChild);

    // Inject CSS rules for country colors – !important overrides hover resets
    let css = '';
    Object.keys(colorMap).forEach(code => {
        css += `path[data-code="${code}"] { fill: ${colorMap[code]} !important; }
`;
        css += `path[data-code="${code}"]:hover { fill: ${colorMap[code]} !important; opacity: 0.82; }
`;
    });
    const styleEl = document.createElement('style');
    styleEl.id = 'map-color-styles';
    styleEl.textContent = css;
    document.head.appendChild(styleEl);

    try {
        accuracyMapInstance = new jsVectorMap({
            selector: '#jvm-map-target',
            map: 'world',
            zoomButtons: false,
            zoomOnScroll: false,
            draggable: false,
            backgroundColor: 'transparent',
            regionStyle: {
                initial: {
                    fill: '#e8ecf1',
                    stroke: '#fff',
                    strokeWidth: 1
                },
                hover: {
                    fillOpacity: 1
                }
            },
            showTooltip: false,
            onRegionTooltipShow: function(event) {
                event.preventDefault();
            }
        });
    } catch(e) {
        console.error('Map init error:', e);
    }

    // Attach manual mouseenter/mouseleave on SVG paths for tooltip
    setTimeout(() => {
        const paths = document.querySelectorAll('#jvm-map-target path[data-code]');
        const lookup = window._mapAccLookup || {};
        paths.forEach(path => {
            const code = path.getAttribute('data-code');
            path.addEventListener('mouseenter', () => {
                const tt = document.getElementById('map-tooltip-card');
                if (lookup[code] && tt) {
                    const info = lookup[code];
                    document.getElementById('map-tt-name').textContent = info.name.toUpperCase();
                    const valEl = document.getElementById('map-tt-val');
                    valEl.textContent = info.acc.toFixed(0) + '%';
                    if (info.acc >= 90) valEl.style.color = '#10b981';
                    else if (info.acc >= 80) valEl.style.color = '#3b82f6';
                    else if (info.acc >= 70) valEl.style.color = '#f59e0b';
                    else valEl.style.color = '#ef4444';
                    tt.style.opacity = '1';
                }
            });
            path.addEventListener('mouseleave', () => {
                const tt = document.getElementById('map-tooltip-card');
                if (tt) tt.style.opacity = '0';
            });
        });
    }, 200);

    // Wire up toggle buttons (only on first call)
    if (!window._mapToggleWired) {
        window._mapToggleWired = true;
        const mlBtn = document.getElementById('map-toggle-ml');
        const manBtn = document.getElementById('map-toggle-manual');
        if (mlBtn && manBtn) {
            mlBtn.addEventListener('click', () => {
                mlBtn.classList.add('active'); manBtn.classList.remove('active');
                currentMapMode = 'ML';
                renderAccuracyMap();
            });
            manBtn.addEventListener('click', () => {
                manBtn.classList.add('active'); mlBtn.classList.remove('active');
                currentMapMode = 'Manual';
                renderAccuracyMap();
            });
        }
    }
}

// --- Phase 1: Deep Dive Panel ---
// Which node is currently loaded in the deep-dive panel. Global = the baseline.
window.SA_ANALYZED = { nodeName: 'Global', levelName: 'Global' };

// Re-apply the highlight to whichever row is loaded (survives tree re-renders).
function highlightAnalyzedRow() {
    const a = window.SA_ANALYZED;
    document.querySelectorAll('#sa-hierarchy-body tr').forEach(r => {
        const match = a && a.levelName !== 'Global' && r.dataset.node === a.nodeName && r.dataset.level === a.levelName;
        r.classList.toggle('row-active', !!match);
    });
}

/**
 * Explicit master/detail trigger. Loads a node (or Global) into the deep-dive
 * panel LOCALLY — it re-scopes only the panel's four charts and does NOT change
 * the dashboard's global scope, so the user is never trapped.
 * @param {string} nodeName   Node to load, or 'Global'
 * @param {string} levelName  Hierarchy level, or 'Global' for the baseline
 */
window.triggerDeepDive = function(nodeName, levelName) {
    const panel    = document.getElementById('sa-deep-dive-panel');
    const content  = document.getElementById('sa-deep-dive-content');
    const title    = document.getElementById('sa-deep-dive-node-name');
    const status   = document.getElementById('sa-deep-dive-status');
    const resetBtn = document.getElementById('sa-reset-global');
    if (!panel) return;

    const isGlobal = (levelName === 'Global');
    window.SA_ANALYZED = { nodeName, levelName };

    // 1) Title + reset button (reset only exists inside a local context)
    if (title) title.textContent = isGlobal ? 'Global Portfolio' : nodeName;
    if (resetBtn) resetBtn.style.display = isGlobal ? 'none' : 'inline-flex';

    // 2) Loading affordance: badge + opacity dip on the content
    if (status) status.style.display = 'inline-block';
    if (content) content.style.opacity = '0.35';

    // 3) Bring the panel into view when entering a local context
    if (!isGlobal) setTimeout(() => panel.scrollIntoView({ behavior: 'smooth', block: 'start' }), 60);

    // 4) Render the four charts for this scope, keeping any active global filters.
    const filters = (window.CURRENT_FILTERS && window.CURRENT_FILTERS.filters) || {};
    setTimeout(() => {
        renderTrendPanel(nodeName, levelName, filters);
        if (status) status.style.display = 'none';
        if (content) content.style.opacity = '1';
        highlightAnalyzedRow();
    }, 220);
};

// Reset the panel to the global baseline and clear the row selection.
window.resetDeepDiveToGlobal = function() {
    window.triggerDeepDive('Global', 'Global');
};

// Back-compat shim for any legacy caller of openDeepDive().
window.openDeepDive = function(nodeName) {
    const lvl = (window.CURRENT_FILTERS && window.CURRENT_FILTERS.levelName) || 'Global';
    window.triggerDeepDive(nodeName, lvl);
};

document.addEventListener('DOMContentLoaded', () => {
    const resetBtn = document.getElementById('sa-reset-global');
    if (resetBtn) resetBtn.addEventListener('click', window.resetDeepDiveToGlobal);
});

// --- Phase 2: Global Filter Pills ---
window.addGlobalFilterPill = function(category, value) {
    // 1. Add visual pill
    const container = document.getElementById('gf-active-pills');
    if (!container) return;
    
    // Check if already exists to prevent duplicates
    const existingId = `pill-${category}-${value.replace(/[^a-zA-Z0-9]/g, '')}`;
    if (document.getElementById(existingId)) return;
    
    const pill = document.createElement('div');
    pill.className = 'global-filter-pill';
    pill.id = existingId;
    pill.innerHTML = `
        ${category}: ${value}
        <button onclick="removeGlobalFilterPill('${category}', '${value}', '${existingId}')">&times;</button>
    `;
    container.appendChild(pill);
    
    // 2. Programmatically select the filter in the existing UI logic
    if (!window.CURRENT_FILTERS.filters[category]) {
        window.CURRENT_FILTERS.filters[category] = [];
    }
    if (!window.CURRENT_FILTERS.filters[category].includes(value)) {
        window.CURRENT_FILTERS.filters[category].push(value);
    }
    // Update the multi-select dropdown visually if possible (optional but good for consistency)
    const checkboxes = document.querySelectorAll(`input[value="${value}"]`);
    checkboxes.forEach(cb => { cb.checked = true; });
    
    updateScope(window.CURRENT_FILTERS.nodeName, window.CURRENT_FILTERS.levelName, window.CURRENT_FILTERS.filters);
};

window.removeGlobalFilterPill = function(category, value, elementId) {
    const el = document.getElementById(elementId);
    if (el) el.remove();
    
    if (window.CURRENT_FILTERS.filters[category]) {
        window.CURRENT_FILTERS.filters[category] = window.CURRENT_FILTERS.filters[category].filter(v => v !== value);
        if (window.CURRENT_FILTERS.filters[category].length === 0) {
            delete window.CURRENT_FILTERS.filters[category];
        }
    }
    
    const checkboxes = document.querySelectorAll(`input[value="${value}"]`);
    checkboxes.forEach(cb => { cb.checked = false; });
    
    updateScope(window.CURRENT_FILTERS.nodeName, window.CURRENT_FILTERS.levelName, window.CURRENT_FILTERS.filters);
};