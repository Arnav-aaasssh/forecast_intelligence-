import sys; sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np
import json

print("=== VERIFICATION OF NEW 13-WEEK LOGIC ===")

# 1. Load the raw data
df = pd.read_excel('sample_data/Final_data.xlsx')
df['Actual_Offered']    = pd.to_numeric(df['Actual_Offered'],    errors='coerce').fillna(0)
df['Manual_Forecast']   = pd.to_numeric(df['Manual_Forecast'],   errors='coerce').fillna(0)
df['ML_Forecast']       = pd.to_numeric(df['ML_Forecast'],       errors='coerce').fillna(0)
df['Week_Ending']       = pd.to_datetime(df['Week_Ending'])

# Filter only the 13 realized weeks
df_realized = df[df['Actual_Offered'] > 0].copy()
total_actual = df_realized['Actual_Offered'].sum()

print(f"Total realized weeks: {df_realized['Week_Ending'].nunique()}")
print(f"Total actual volume: {total_actual:,.0f}")
print()

# 2. Load the dashboard JSON payload
with open('dashboard/data/report.json', 'r', encoding='utf-8') as f:
    dashboard_data = json.load(f)

# ── Q1 ──────────────────────────────────────────────────────────────────────
man_wape = df_realized['Manual_Forecast'].sub(df_realized['Actual_Offered']).abs().sum() / total_actual * 100
ml_wape  = df_realized['ML_Forecast'].sub(df_realized['Actual_Offered']).abs().sum()    / total_actual * 100

weekly_err = df_realized.groupby('Week_Ending').apply(lambda g: pd.Series({
    'man_err': g['Manual_Forecast'].sub(g['Actual_Offered']).abs().sum(),
    'ml_err':  g['ML_Forecast'].sub(g['Actual_Offered']).abs().sum()
}))
man_wins = (weekly_err['man_err'] <= weekly_err['ml_err']).sum()
n_weeks  = len(weekly_err)
win_rate = man_wins / n_weeks * 100

q1_dash = dashboard_data['chart_data']['q1_filters']['All|All|All']

print("=== Q1 STRATEGY ASSESSMENT ===")
print(f"  Manual WAPE:      {man_wape:.2f}%   | dashboard: {q1_dash['manual_wape']}%")
print(f"  ML WAPE:          {ml_wape:.2f}%   | dashboard: {q1_dash['ml_wape']}%")
print(f"  Manual Win Rate:  {win_rate:.1f}%     | dashboard: {q1_dash['manual_win_rate']}%")
print(f"  Sample Size:      {n_weeks} weeks   | dashboard: {q1_dash['n_weeks']}")
print()

# ── Q3 ──────────────────────────────────────────────────────────────────────
vol_weekly = df_realized.groupby('Week_Ending')['Actual_Offered'].sum()
mean_vol   = vol_weekly.mean()
std_vol    = vol_weekly.std()
cv         = std_vol / mean_vol * 100

q3_dash = dashboard_data['chart_data']['q3']
print("=== Q3 BUSINESS CONTEXT ===")
print(f"  Realized CV%:     {cv:.2f}%     | dashboard: {q3_dash['cv']}%")
print(f"  Anomaly Weeks:    0          | dashboard: {q3_dash['n_anomalies']}")
print()

# ── Q2 ──────────────────────────────────────────────────────────────────────
def compute_group(g):
    actual_sum = g['Actual_Offered'].sum()
    if actual_sum == 0:
        return None
    wape  = g['ML_Forecast'].sub(g['Actual_Offered']).abs().sum() / actual_sum * 100
    bias  = abs(g['ML_Forecast'].sub(g['Actual_Offered']).sum()   / actual_sum) * 100
    weekly_actuals = g.groupby('Week_Ending')['Actual_Offered'].sum()
    weekly_ml = g.groupby('Week_Ending')['ML_Forecast'].sum()
    weekly_err = (weekly_ml - weekly_actuals).abs() / weekly_actuals.replace(0, np.nan) * 100
    max_err = weekly_err.max() if not weekly_err.empty else 0.0
    if pd.isna(max_err): max_err = 0.0
    hit10 = (g['ML_Forecast'].sub(g['Actual_Offered']).div(g['Actual_Offered'].replace(0, np.nan)).abs() <= 0.10).mean() * 100
    return pd.Series({'WAPE': round(wape,2), 'Bias': round(bias,2),
                      'MaxErr': max_err, 'Hit10': round(hit10,2), 'n_weeks': g['Week_Ending'].nunique()})

model_stats = df_realized.groupby(['Model','Family']).apply(compute_group).dropna().reset_index()
# New Rule: Must have predictions in at least 8 of the 13 realized weeks
model_stats = model_stats[model_stats['n_weeks'] >= 8]

def norm(s, best, worst):
    if best < worst:
        return (worst - s.clip(best, worst)) / (worst - best)
    else:
        return (s.clip(worst, best) - worst) / (best - worst)

model_stats['s_wape']  = norm(model_stats['WAPE'],  5.0,  40.0)
model_stats['s_hit10'] = norm(model_stats['Hit10'], 90.0, 30.0)
model_stats['s_bias']  = norm(model_stats['Bias'],  0.0,  20.0)

# MaxErr normalization: best is 0, worst is 50.0 (per dashboard rules)
model_stats['s_stab']  = norm(model_stats['MaxErr'], 0.0, 50.0)

model_stats['Score']   = (0.35*model_stats['s_wape'] + 0.25*model_stats['s_hit10'] +
                          0.20*model_stats['s_bias']  + 0.20*model_stats['s_stab']) * 100

champion    = model_stats.loc[model_stats['Score'].idxmax()]
champ_name  = champion['Model']
champ_score = champion['Score']

q2_dash = dashboard_data['chart_data']['filters']['slices']['All|All|All']['leaderboard'][0]

print("=== Q2 MODEL CHAMPION ===")
print(f"  Eligible Models:  {len(model_stats)}        ")
print(f"  Champion Model:   {champ_name}  | dashboard: {q2_dash['Model']}")
print(f"  Champion Score:   {champ_score:.2f}        | dashboard: {q2_dash['CompositeScore']}")
print()
