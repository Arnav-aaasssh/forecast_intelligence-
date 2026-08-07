import pandas as pd

df = pd.read_excel('sample_data/FinalForecast_Imputed.xlsx')
df['Week_Ending'] = pd.to_datetime(df['Week_Ending'])

# Group by Week_Ending and compute WAPEs
weekly = df.groupby('Week_Ending').apply(lambda g: pd.Series({
    'manual_wape': (g['Manual_Forecast'] - g['Actual_Offered']).abs().sum() / g['Actual_Offered'].sum() * 100 if g['Actual_Offered'].sum() > 0 else 0,
    'ml_wape': (g['ML_Forecast'] - g['Actual_Offered']).abs().sum() / g['Actual_Offered'].sum() * 100 if g['Actual_Offered'].sum() > 0 else 0,
})).reset_index()

# Win rate: Manual < ML
manual_wins = (weekly['manual_wape'] < weekly['ml_wape']).sum()
total_weeks = len(weekly)
win_rate = (weekly['manual_wape'] < weekly['ml_wape']).mean() * 100

print(f"Manual Wins: {manual_wins} out of {total_weeks} weeks")
print(f"Calculated Win Rate: {win_rate:.2f}%")
