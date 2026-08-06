import sys; sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd, numpy as np, json

df = pd.read_excel('sample_data/FinalForecast_Imputed.xlsx')
df['Actual_Offered']  = pd.to_numeric(df['Actual_Offered'],  errors='coerce').fillna(0)
df['ML_Forecast']     = pd.to_numeric(df['ML_Forecast'],     errors='coerce').fillna(0)
df['Manual_Forecast'] = pd.to_numeric(df['Manual_Forecast'], errors='coerce').fillna(0)
df['Week_Ending']     = pd.to_datetime(df['Week_Ending'])

with open('dashboard/data/report.json', encoding='utf-8') as f:
    rj = json.load(f)
cd = rj['chart_data']

# ── Q3: Why do mean/std mismatch but CV match? ──────────────────────────────
print('=== Q3 ROOT CAUSE ===')
vol_sum  = df.groupby('Week_Ending')['Actual_Offered'].sum()
vol_mean = df.groupby('Week_Ending')['Actual_Offered'].mean()

cv_sum  = vol_sum.std()  / vol_sum.mean()  * 100
cv_mean = vol_mean.std() / vol_mean.mean() * 100

print(f'Weekly volume as SUM  -> mean={vol_sum.mean():,.0f}, std={vol_sum.std():,.0f}, CV={cv_sum:.2f}%')
print(f'Weekly volume as MEAN -> mean={vol_mean.mean():,.0f}, std={vol_mean.std():,.0f}, CV={cv_mean:.2f}%')
print()

json_mean = cd['q3']['weekly_mean']
json_std  = cd['q3']['weekly_std']
json_cv   = cd['q3']['cv']
json_implied_cv = json_std / json_mean * 100

print(f'Dashboard JSON: weekly_mean={json_mean:,}, weekly_std={json_std:,}, cv={json_cv}%')
print(f'  => std/mean check: {json_implied_cv:.2f}% (would need to equal 7.59% to be internally consistent)')
print(f'  => INTERNAL CONSISTENCY: {"OK" if abs(json_implied_cv - json_cv) < 0.1 else "INCONSISTENT - std and mean are from a DIFFERENT run than CV"}')
print()

# ── Q4: Exact replication of generator ──────────────────────────────────────
print('=== Q4 ROOT CAUSE ===')

def weekly_wape_fn(g):
    actual = g['Actual_Offered'].sum()
    if actual == 0:
        return pd.Series({'ml_wape': 0.0})
    return pd.Series({
        'ml_wape': round((g['ML_Forecast'] - g['Actual_Offered']).abs().sum() / actual * 100, 2),
    })

weekly_all = df.groupby('Week_Ending').apply(weekly_wape_fn).reset_index()

vol      = df.groupby('Week_Ending')['Actual_Offered'].sum()
mean_vol = vol.mean()
std_vol  = vol.std()

def get_z(week):
    v = vol.get(week, 0)
    return round((v - mean_vol) / std_vol, 2) if std_vol > 0 else 0

weekly_all['z_score']   = weekly_all['Week_Ending'].apply(get_z)
weekly_all['magnitude'] = weekly_all['z_score'].abs()
weekly_all['is_anomaly']= weekly_all['magnitude'] > 2.5

normal_wape  = weekly_all[~weekly_all['is_anomaly']]['ml_wape'].mean()
anomaly_wape = weekly_all[weekly_all['is_anomaly']]['ml_wape'].mean()

print(f'Generator replication (exact):')
print(f'  Normal WAPE (96 weeks): {normal_wape:.4f}%')
print(f'  Anomaly WAPE (3 weeks): {anomaly_wape:.4f}%')
print(f'  Delta:                  {anomaly_wape - normal_wape:.4f} pp')
print()
print(f'Dashboard JSON stored:  normal={cd["q4"]["normal_wape"]}, anomaly={cd["q4"]["anomaly_wape"]}')
print(f'  => MATCH: {abs(normal_wape - cd["q4"]["normal_wape"]) < 0.5 and abs(anomaly_wape - (cd["q4"]["anomaly_wape"] or 0)) < 0.5}')
print()

# Show 3 anomaly weeks
anomaly_weeks = weekly_all[weekly_all['is_anomaly']][['Week_Ending','ml_wape','z_score']]
print('Anomaly weeks detected:')
for _, row in anomaly_weeks.iterrows():
    print(f'  {row["Week_Ending"].strftime("%Y-%m-%d")}  ml_wape={row["ml_wape"]:.2f}%  z={row["z_score"]:.2f}')
print()

# Show hardcoded values
print('Hardcoded values in generate_dashboard.py (not derived from data):')
keys = ['champion_normal_wape', 'champion_anomaly_wape', 'manual_normal_wape', 'manual_anomaly_wape', 'p_value']
for k in keys:
    print(f'  {k}: {cd["q4"].get(k)}')

print()
print('=== SUMMARY OF DISCREPANCY NATURE ===')
print('Q3: CV is correctly computed. But weekly_mean and weekly_std in JSON')
print('    are internally inconsistent (std/mean != CV shown).')
print('    Root cause: A previous generate run stored different mean/std.')
print()
print('Q4: The dynamic normal_wape/anomaly_wape are derived from data but')
print('    differ slightly from JSON. 5 values (champion WAPEs, manual anomaly')
print('    WAPEs, p_value) are HARDCODED and not data-driven at all.')
