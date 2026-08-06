with open('dashboard/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

replacement = '''
  // EXEC DASHBOARD CHARTS
  const execVolEl = document.getElementById('chart-exec-volume');
  if (execVolEl && typeof bc !== 'undefined' && bc && bc.series) {
    const realSeries = bc.series.filter(d => d.realized_volume !== null);
    const nRealized = realSeries.length;
    chartInstances['exec-volume'] = new Chart(execVolEl, {
      type:'line',
      data:{ labels: bc.series.map(d=>d.week), datasets:[
        { label:'Planned Volume', data: bc.series.map(d=>d.planned_volume), borderColor:COLORS.gray, borderDash:[5,4], borderWidth:1.5, pointRadius:0, tension:.15 },
        { label:'Realized Volume', data: realSeries.map(d=>d.realized_volume).concat(Array(bc.series.length-nRealized).fill(null)), borderColor:COLORS.navy, backgroundColor:COLORS.navy+'12', borderWidth:2.5, pointRadius:2, tension:.15, fill:true }
      ]},
      options:{ interaction: { mode: 'index', intersect: false }, responsive:true, maintainAspectRatio:false, plugins:{ legend:{position:'top',labels:{boxWidth:10}} }, scales:{ x:{grid:{display:false}}, y:{grid:{color:'#EEF1F4'}} } }
    });
  }

  const execBiasEl = document.getElementById('chart-exec-bias');
  if (execBiasEl && typeof bd !== 'undefined' && bd && bd.length) {
    chartInstances['exec-bias'] = new Chart(execBiasEl, {
      type:'line',
      data:{ labels: bd.map(d=>d.week), datasets:[
        {label:'ML Tracking Signal', data: bd.map(d=>d.ml_tracking), borderColor:COLORS.teal, backgroundColor:COLORS.teal+'10', borderWidth:2, pointRadius:3, tension:.3, fill:true}
      ]},
      options:{ responsive:true, maintainAspectRatio:false, plugins:{legend:{position:'top',labels:{boxWidth:10}}}, scales:{ x:{grid:{display:false}}, y:{grid:{color:'#EEF1F4'}} } }
    });
  }
'''

target = "if (document.getElementById('exec-new-records')) document.getElementById('exec-new-records').textContent = (meta.records_evaluated || 0).toLocaleString();"

if target in html:
    with open('dashboard/index.html', 'w', encoding='utf-8') as f:
        f.write(html.replace(target, target + '\n' + replacement))
    print('SUCCESS')
else:
    print('Target not found')
