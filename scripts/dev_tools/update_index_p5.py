import sys

def main():
    path = "dashboard/index.html"
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Fix Q4 error chart which was left outside the conditional
    old_q4_chart = """// ---- Q4 error chart ----
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
});"""

    new_q4_chart = """// ---- Q4 error chart ----
if (DATA.q3.n_anomalies > 0 && DATA.q4.series) {
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
}"""
    html = html.replace(old_q4_chart, new_q4_chart)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print("JS array fallbacks fixed!")

if __name__ == "__main__":
    main()
