        const stdDev = Math.sqrt(variance);
        volatilityStr = (stdDev * 100).toFixed(1) + '%';
    }
    if (document.getElementById('exec-new-volatility')) document.getElementById('exec-new-volatility').textContent = volatilityStr;
    if (document.getElementById('exec-new-records')) document.getElementById('exec-new-records').textContent = targetL0.length.toLocaleString();
    
    // --- Dynamic KPI Cards Update ---
    let targetL1 = RAW_LEVEL1;
    for (const [k, v] of Object.entries(filters)) {
        if (k !== 'Global') targetL1 = targetL1.filter(row => String(row[k]) === String(v));
    }
    if (classFilter) {
        targetL1 = targetL1.filter(row => row.Classification === classFilter);
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
    targetL0.forEach(row => {
        const actual = row.Actual_Offered || 0;
        if (actual > 0) {
            const forecast = (decisionState === 'Manual')
                ? (parseFloat(row.Manual_Forecast) || 0)
                : (parseFloat(row.ML_Forecast) || 0);
            const relError = Math.abs(actual - forecast) / actual;
            hitTotal++;
            if (relError <= 0.10) hitCount++;
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
        window._execVolChart = new Chart(volCtx, {
            type: 'line',
            data: {
                labels: sortedWeekKeys,
                datasets: [
                    { label: 'Actual Volume', data: sortedWeekKeys.map(w => weeks[w].act), borderColor: '#2F6F63', backgroundColor: 'rgba(47,111,99,0.08)', borderWidth: 2.5, tension: 0.3, fill: true, pointRadius: 3, pointBackgroundColor: '#2F6F63' },
                    { label: 'Manual Forecast', data: sortedWeekKeys.map(w => weeks[w].man), borderColor: '#B3452B', borderDash: [5,5], borderWidth: 1.5, tension: 0.3, pointRadius: 0, fill: false },
                    { label: 'ML Forecast', data: sortedWeekKeys.map(w => weeks[w].ml), borderColor: '#808A98', borderDash: [3,3], borderWidth: 1.5, tension: 0.3, pointRadius: 0, fill: false }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: true, position: 'bottom', labels: { boxWidth: 12, padding: 14, font: { size: 11 } } } }, scales: { y: { beginAtZero: false, grid: { color: '#EEF1F4' } }, x: { grid: { display: false }, ticks: { maxRotation: 45, font: { size: 10 } } } } }
        });
    }
    
    // 2. Cumulative Bias Drift Chart
    const biasCtx = document.getElementById('chart-exec-bias');
    if (biasCtx) {
        if (window._execBiasChart) window._execBiasChart.destroy();
        let cumManBias = 0, cumMlBias = 0;
        const manBiasData = [];
        const mlBiasData = [];
        sortedWeekKeys.forEach(w => {
            const d = weeks[w];
            if (d.act > 0) {
                cumManBias += (d.man - d.act);
                cumMlBias += (d.ml - d.act);
            }
            manBiasData.push(cumManBias);
            mlBiasData.push(cumMlBias);
        });
        window._execBiasChart = new Chart(biasCtx, {
            type: 'line',
            data: {
                labels: sortedWeekKeys,
                datasets: [
                    { label: 'Manual Cumulative Bias', data: manBiasData, borderColor: '#B3452B', backgroundColor: 'rgba(179,69,43,0.06)', borderWidth: 2, tension: 0.3, fill: true, pointRadius: 2 },
                    { label: 'ML Cumulative Bias', data: mlBiasData, borderColor: '#808A98', backgroundColor: 'rgba(128,138,152,0.06)', borderWidth: 2, tension: 0.3, fill: true, pointRadius: 2 }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: true, position: 'bottom', labels: { boxWidth: 12, padding: 14, font: { size: 11 } } }, annotation: {} }, scales: { y: { grid: { color: '#EEF1F4' }, title: { display: true, text: 'Cumulative Error', font: { size: 11 } } }, x: { grid: { display: false }, ticks: { maxRotation: 45, font: { size: 10 } } } } }
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
                target = target.filter(row => row[k] == v);
            }
        }
    } else if (filtersOrKey && typeof filtersOrKey === 'string' && filtersOrKey !== 'Global') {
        // Old style: filtersOrKey is a string column name
        target = target.filter(row => row[filtersOrKey] == filterVal);
    }
    
    // Apply classification filter if set
    const classFilter = window.CLASSIFICATION_FILTER || '';
    if (classFilter) {
        target = target.filter(row => row.Classification === classFilter);
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
    const children = computeHierarchyRollup(RAW_LEVEL1, nextLevelName, {});
    
    if (!children || children.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 20px; color: var(--text-2);">No data matches the current filters.</td></tr>`;
        return;
    }
    
    children.sort((a, b) => b.Total_Volume - a.Total_Volume);
    children.forEach((child, idx) => {
        renderRow(tbody, child, child.Node, nextLevelName, 0, {}, idx % 2 === 1 ? '#f8f9fa' : '');
    });
}

function renderRow(tbody, data, nodeName, levelName, indentLevel, accumulatedFilters, overrideBg = '') {
    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    
    const isLeaf = levelName === 'Forecast_Name';
    const rowId = levelName + '-' + nodeName;
    const isExpanded = expandedRows.has(rowId);
    
    // Maintain selection highlight
    if (window.CURRENT_FILTERS.nodeName === nodeName && window.CURRENT_FILTERS.levelName === levelName) {
        tr.style.backgroundColor = 'var(--teal-soft)';
    } else if (overrideBg) {
        tr.style.backgroundColor = overrideBg;
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
    
    tr.innerHTML = `
        <td style="padding-left: ${10 + indentLevel * 20}px;">
            <span class="expand-toggle" style="font-family:var(--mono); color:var(--teal); font-size:10px; margin-right:6px;">${expandToggle}</span>
            <strong style="color:var(--navy); font-weight:500;">${nodeName}</strong>
            <span style="font-size:10px; color:var(--text-2); margin-left: 6px;">(${levelName})</span>
        </td>
        <td class="num">${isLeaf ? '1' : data.Total_Queues}</td>
        <td class="num" style="color:var(--teal); font-weight:500; ${bgSML}">${txtSML}</td>
        <td class="num" style="color:var(--amber); font-weight:500; ${bgHyb}">${txtHyb}</td>
        <td class="num" style="color:var(--rust); font-weight:500; ${bgMan}">${txtMan}</td>
        <td>${confDisplay}</td>
    `;
    
    tr.addEventListener('click', (e) => {
        // Toggle expansion
        if (!isLeaf) {
            if (isExpanded) expandedRows.delete(rowId);
            else expandedRows.add(rowId);
            renderHierarchyTable(); // Re-render tree to apply expansion and highlighting
        } else {
            // Leaf node: just update highlighting manually since no re-render
            document.querySelectorAll('#sa-hierarchy-body tr').forEach(r => r.style.backgroundColor = '');
            tr.style.backgroundColor = 'var(--teal-soft)';
        }
    });
    
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
                targetL0 = targetL0.filter(row => String(row[k]) === String(v));
            }
        }
    }
    
    // Apply classification filter if set
    const classFilter = window.CLASSIFICATION_FILTER || '';
    if (classFilter) {
        // Find which Forecast Names have this classification from RAW_LEVEL1
        const allowedForecasts = new Set(
            RAW_LEVEL1.filter(q => q.Classification === classFilter).map(q => q.Forecast_Name)
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
        
        window.SA_FC_CHART = new Chart(fcCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: fcLabels,
                datasets: [
                    { label: 'Actual', data: actVol, borderColor: '#808A98', backgroundColor: 'transparent', borderWidth: 2.5, tension: 0.3, pointRadius: 3, pointBackgroundColor: '#808A98', fill: false },
                    { label: 'ML FC', data: mlFCVol, borderColor: '#2F6F63', backgroundColor: 'rgba(47,111,99,0.1)', borderWidth: 2, borderDash: [4,4], tension: 0.3, pointRadius: 3, pointBackgroundColor: '#2F6F63', fill: true },
                    { label: 'Manual FC', data: manFCVol, borderColor: '#B3452B', backgroundColor: 'transparent', borderWidth: 2, borderDash: [2,2], tension: 0.3, pointRadius: 3, pointBackgroundColor: '#B3452B', fill: false }
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
                            
                            // It's the middle value. Push it away from whichever extreme it's closest to.
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
                    y: { min: yMinVol, grid: { borderDash: [3,3], color: '#EEF1F4' }, ticks: { font: { color: '#8A94A3' }, callback: function(value) { return value >= 1000000 ? (value/1000000).toFixed(1) + 'M' : value >= 1000 ? (value/1000).toFixed(1) + 'k' : value; } } }
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