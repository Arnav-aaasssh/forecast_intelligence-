import pandas as pd
import numpy as np
import json
from scipy.stats import wilcoxon

def compute_queue_week_metrics(df):
    """Level 0 - Queue-Week Atomic Table"""
    df_actuals = df[df['Actual_Offered'].notnull() & (df['Actual_Offered'] > 0)].copy()
    df_actuals['Manual_Abs_Err'] = (df_actuals['Manual_Forecast'] - df_actuals['Actual_Offered']).abs()
    df_actuals['ML_Abs_Err'] = (df_actuals['ML_Forecast'] - df_actuals['Actual_Offered']).abs()
    df_actuals['Manual_WAPE'] = df_actuals['Manual_Abs_Err'] / df_actuals['Actual_Offered']
    df_actuals['ML_WAPE'] = df_actuals['ML_Abs_Err'] / df_actuals['Actual_Offered']
    df_actuals['Winner'] = np.where(df_actuals['ML_WAPE'] <= df_actuals['Manual_WAPE'], 'ML', 'Manual')
    df_actuals['Within_Tolerance_ML'] = df_actuals['ML_WAPE'] <= 0.10
    df_actuals['Within_Tolerance_Manual'] = df_actuals['Manual_WAPE'] <= 0.10
    return df_actuals

def compute_queue_rollup(level0_df):
    """Level 1 - Queue Rollup"""
    agg_df = level0_df.groupby('Forecast_Name').agg(
        Queue_Actual_Sum=('Actual_Offered', 'sum'),
        Queue_Manual_Err_Sum=('Manual_Abs_Err', 'sum'),
        Queue_ML_Err_Sum=('ML_Abs_Err', 'sum'),
        Valid_Weeks_Count=('Week_Ending', 'count')
    ).reset_index()
    
    ml_wins = level0_df[level0_df['Winner'] == 'ML'].groupby('Forecast_Name').size().reset_index(name='ML_Win_Count')
    agg_df = pd.merge(agg_df, ml_wins, on='Forecast_Name', how='left')
    agg_df['ML_Win_Count'] = agg_df['ML_Win_Count'].fillna(0)
    
    agg_df['Queue_WAPE_Manual'] = agg_df['Queue_Manual_Err_Sum'] / agg_df['Queue_Actual_Sum']
    agg_df['Queue_WAPE_ML'] = agg_df['Queue_ML_Err_Sum'] / agg_df['Queue_Actual_Sum']
    agg_df['Weeks_ML_Wins_Pct'] = agg_df['ML_Win_Count'] / agg_df['Valid_Weeks_Count']
    
    def classify(pct):
        if pct >= 0.60: return 'Strong ML'
        elif pct >= 0.40: return 'Hybrid'
        else: return 'Manual'
            
    agg_df['Classification'] = agg_df['Weeks_ML_Wins_Pct'].apply(classify)
    
    baseline_cols = ['Forecast_Name', 'Region', 'SubRegion', 'Country', 'Offering', 'Channel']
    available_cols = [c for c in baseline_cols if c in level0_df.columns]
    
    baseline_df = level0_df[available_cols].drop_duplicates(subset=['Forecast_Name'])
    level1_df = pd.merge(agg_df, baseline_df, on='Forecast_Name', how='left')
    return level1_df

def compute_hierarchy_rollup(level1_df, group_by_col):
    """
    Level 2+ Hierarchy Rollup
    Computes count-based and volume-weighted rollups for any given hierarchy node/level.
    """
    if group_by_col == 'Global':
        df_target = level1_df.copy()
        df_target['Global'] = 'Global'
    elif group_by_col in level1_df.columns:
        df_target = level1_df
    else:
        return None
        
    count_rollup = df_target.groupby([group_by_col, 'Classification']).size().unstack(fill_value=0)
    for col in ['Strong ML', 'Hybrid', 'Manual']:
        if col not in count_rollup.columns: count_rollup[col] = 0
            
    count_rollup['Total_Queues'] = count_rollup[['Strong ML', 'Hybrid', 'Manual']].sum(axis=1)
    count_rollup['Pct_Strong_ML'] = (count_rollup['Strong ML'] / count_rollup['Total_Queues'] * 100).round(1)
    count_rollup['Pct_Hybrid'] = (count_rollup['Hybrid'] / count_rollup['Total_Queues'] * 100).round(1)
    count_rollup['Pct_Manual'] = (count_rollup['Manual'] / count_rollup['Total_Queues'] * 100).round(1)
    
    vol_rollup = df_target.groupby([group_by_col, 'Classification'])['Queue_Actual_Sum'].sum().unstack(fill_value=0)
    for col in ['Strong ML', 'Hybrid', 'Manual']:
        if col not in vol_rollup.columns: vol_rollup[col] = 0
            
    vol_rollup['Total_Volume'] = vol_rollup[['Strong ML', 'Hybrid', 'Manual']].sum(axis=1)
    vol_rollup['Vol_Pct_Strong_ML'] = (vol_rollup['Strong ML'] / vol_rollup['Total_Volume'] * 100).round(1)
    vol_rollup['Vol_Pct_Hybrid'] = (vol_rollup['Hybrid'] / vol_rollup['Total_Volume'] * 100).round(1)
    vol_rollup['Vol_Pct_Manual'] = (vol_rollup['Manual'] / vol_rollup['Total_Volume'] * 100).round(1)
    
    err_rollup = df_target.groupby(group_by_col).agg(
        Total_Volume_Err=('Queue_Actual_Sum', 'sum'),
        Manual_Err=('Queue_Manual_Err_Sum', 'sum'),
        ML_Err=('Queue_ML_Err_Sum', 'sum')
    )
    err_rollup['Manual_WAPE'] = (err_rollup['Manual_Err'] / err_rollup['Total_Volume_Err'] * 100).round(2)
    err_rollup['ML_WAPE'] = (err_rollup['ML_Err'] / err_rollup['Total_Volume_Err'] * 100).round(2)
    err_rollup['Volume_Winner'] = np.where(err_rollup['ML_WAPE'] <= err_rollup['Manual_WAPE'], 'ML', 'Manual')
    
    result = count_rollup.join(vol_rollup.drop(columns=['Strong ML', 'Hybrid', 'Manual']), rsuffix='_Vol')
    result = result.join(err_rollup.drop(columns=['Total_Volume_Err']))
    
    return result.reset_index()

def generate_dashboard_data(df, output_path='dashboard/data/report.json'):
    # Pre-process
    df = df.copy()
    df['Week_Ending'] = pd.to_datetime(df['Week_Ending'])
    df['Actual_Offered'] = pd.to_numeric(df['Actual_Offered'], errors='coerce')
    df['Manual_Forecast'] = pd.to_numeric(df['Manual_Forecast'], errors='coerce').fillna(0)
    df['ML_Forecast'] = pd.to_numeric(df['ML_Forecast'], errors='coerce').fillna(0)
    
    # cols_to_drop = [c for c in df.columns if c.startswith('Final_Y')]
    # df = df.drop(columns=cols_to_drop)

    print("Computing Level 0...")
    level0 = compute_queue_week_metrics(df)
    
    print("Computing Level 1...")
    level1 = compute_queue_rollup(level0)

    level0_json = level0.copy()
    if 'Week_Ending' in level0_json.columns:
        level0_json['Week_Ending'] = level0_json['Week_Ending'].dt.strftime('%Y-%m-%d')
        
    data = {
        'level0': level0_json.to_dict(orient='records'),
        'level1': level1.to_dict(orient='records')
    }

    import re
    import json
    with open(output_path, 'w', encoding='utf-8') as f:
        json_str = json.dumps(data, indent=2, default=str)
        json_str = re.sub(r':\s*NaN', ': null', json_str)
        f.write(json_str)
        
    print(f"Chart data successfully updated in {output_path} with new architecture payload.")

if __name__ == "__main__":
    df = pd.read_excel('sample_data/Final_data.xlsx')
    generate_dashboard_data(df)
