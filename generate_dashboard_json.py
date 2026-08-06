import pandas as pd
import json
import numpy as np

def generate_chart_data(df):
    chart_data = {"q1": {}, "q2": {}, "q3": {}, "q4": {}}
    
    # Pre-process
    df['Week_Ending'] = pd.to_datetime(df['Week_Ending'])
    
    # Q1 Series: Weekly WAPE
    # Group by Week_Ending
    weekly = df.groupby('Week_Ending').apply(lambda g: pd.Series({
        'manual_wape': (g['Manual_Forecast'] - g['Actual_Offered']).abs().sum() / g['Actual_Offered'].sum() * 100 if g['Actual_Offered'].sum() > 0 else 0,
        'ml_wape': (g['ML_Forecast'] - g['Actual_Offered']).abs().sum() / g['Actual_Offered'].sum() * 100 if g['Actual_Offered'].sum() > 0 else 0,
    })).reset_index()
    weekly['week'] = weekly['Week_Ending'].dt.strftime('%Y-%m-%d')
    chart_data['q1']['series'] = weekly[['week', 'manual_wape', 'ml_wape']].to_dict('records')
    
    # Q2 Scatter & Boxplot
    # Group by Model and Family
    model_stats = df.groupby(['Model', 'Family']).apply(lambda g: pd.Series({
        'WAPE': (g['ML_Forecast'] - g['Actual_Offered']).abs().sum() / g['Actual_Offered'].sum() * 100 if g['Actual_Offered'].sum() > 0 else 0,
        'Hit10': (g['ML_±10%'] == True).mean() * 100,
        'CompositeScore': 0 # Mock or recalculate if needed, we'll just mock for now
    })).reset_index()
    chart_data['q2']['scatter'] = model_stats.to_dict('records')
    
    boxplot = []
    for family, g in model_stats.groupby('Family'):
        wapes = g['WAPE'].dropna()
        if len(wapes) > 0:
            boxplot.append({
                'family': family,
                'min': wapes.min(),
                'q1': wapes.quantile(0.25),
                'median': wapes.median(),
                'q3': wapes.quantile(0.75),
                'max': wapes.max(),
                'n': len(wapes)
            })
    chart_data['q2']['boxplot'] = boxplot
    
    # Q3 Series & Anomalies (Volume trends)
    vol_weekly = df.groupby('Week_Ending').apply(lambda g: pd.Series({
        'volume': g['Actual_Offered'].sum(),
        'is_anomaly': False # Mock
    })).reset_index()
    vol_weekly['week'] = vol_weekly['Week_Ending'].dt.strftime('%Y-%m-%d')
    chart_data['q3']['series'] = vol_weekly[['week', 'volume', 'is_anomaly']].to_dict('records')
    chart_data['q3']['anomaly_cards'] = []
    
    # Q4 Series (Normal vs Anomaly WAPE)
    # We will just reuse Q1 ML WAPE but named wape
    q4_series = weekly[['week', 'ml_wape']].rename(columns={'ml_wape': 'wape'})
    q4_series['is_anomaly'] = False
    chart_data['q4']['series'] = q4_series.to_dict('records')
    
    return chart_data

if __name__ == '__main__':
    df = pd.read_excel('sample_data/FinalForecast_Imputed.xlsx')
    cdata = generate_chart_data(df)
    with open('dashboard/data/chart_data_test.json', 'w') as f:
        json.dump(cdata, f, indent=2)
    print("Done generating chart data.")
