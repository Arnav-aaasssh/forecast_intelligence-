const fs = require('fs');

const raw = JSON.parse(fs.readFileSync('dashboard/data/report.json', 'utf8'));
const RAW_LEVEL0 = raw.level0;

function rebuildLevel1(data0) {
    const queueMap = {};
    data0.forEach(r => {
        if (!queueMap[r.Forecast_Name]) {
            queueMap[r.Forecast_Name] = {
                Forecast_Name: r.Forecast_Name,
                Queue_Actual_Sum: 0, Queue_Manual_Err_Sum: 0, Queue_ML_Err_Sum: 0,
                Valid_Weeks_Count: 0, ML_Win_Count: 0,
                Classification: 'Manual'
            };
        }
        const q = queueMap[r.Forecast_Name];
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
        
        const mlWinPct = q.Valid_Weeks_Count ? (q.ML_Win_Count / q.Valid_Weeks_Count) : 0;
        if (q.Valid_Weeks_Count === 0) {
            q.Classification = 'No Data';
        } else if (mlWinPct >= 0.60) {
            q.Classification = 'Strong ML';
        } else if (mlWinPct >= 0.40) {
            q.Classification = 'Hybrid';
        } else {
            q.Classification = 'Manual';
        }
        level1.push(q);
    }
    return level1;
}

const RAW_LEVEL1 = rebuildLevel1(RAW_LEVEL0);

function getWape(filterClass) {
    let sumMl = 0;
    let sumMan = 0;
    let validQCount = 0;

    RAW_LEVEL1.forEach(q => {
        if (q.Queue_Actual_Sum > 0 && (!filterClass || q.Classification === filterClass)) {
            sumMl += (q.Queue_WAPE_ML * 100);
            sumMan += (q.Queue_WAPE_Manual * 100);
            validQCount++;
        }
    });

    console.log(filterClass || 'All');
    console.log("meanMlWape:", sumMl / validQCount);
    console.log("meanManWape:", sumMan / validQCount);
}

getWape();
getWape('Strong ML');
getWape('Hybrid');
getWape('Manual');
