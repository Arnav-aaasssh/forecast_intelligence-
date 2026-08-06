import pandas as pd
import numpy as np
from scipy.stats import wilcoxon

def generate_validation_sheet():
    df = pd.read_excel('sample_data/Final_data.xlsx')
    
    # Pre-process same as dashboard
    df['Week_Ending'] = pd.to_datetime(df['Week_Ending'])
    df['Actual_Offered'] = pd.to_numeric(df['Actual_Offered'], errors='coerce')
    df['Manual_Forecast'] = pd.to_numeric(df['Manual_Forecast'], errors='coerce').fillna(0)
    df['ML_Forecast'] = pd.to_numeric(df['ML_Forecast'], errors='coerce').fillna(0)
    
    df_actuals = df[df['Actual_Offered'].notnull() & (df['Actual_Offered'] > 0)].copy()
    
    sub_regions = sorted(df['SubRegion'].dropna().unique().tolist())
    channels = sorted(df['Channel'].dropna().unique().tolist()) if 'Channel' in df.columns else []
    
    combinations = [('All', 'All')]
    for sr in sub_regions:
        combinations.append((sr, 'All'))
        for ch in channels:
            combinations.append((sr, ch))
            
    summary_data = []
    weekly_data = []
    
    for sr, ch in combinations:
        sub_df = df_actuals
        if sr != 'All': 
            sub_df = sub_df[sub_df['SubRegion'] == sr]
        if ch != 'All': 
            sub_df = sub_df[sub_df['Channel'] == ch]
            
        if len(sub_df) == 0:
            continue
            
        actual = sub_df['Actual_Offered'].sum()
        if actual == 0:
            continue
            
        # Overall WAPE calculations
        man_wape = round((sub_df['Manual_Forecast'] - sub_df['Actual_Offered']).abs().sum() / actual * 100, 2)
        ml_wape = round((sub_df['ML_Forecast'] - sub_df['Actual_Offered']).abs().sum() / actual * 100, 2)
        
        # Weekly Errors for Win Rate and Wilcoxon
        weekly_err = sub_df.groupby('Week_Ending').apply(lambda g: pd.Series({
            'man_err': (g['Manual_Forecast'] - g['Actual_Offered']).abs().sum(),
            'ml_err': (g['ML_Forecast'] - g['Actual_Offered']).abs().sum(),
            'actual': g['Actual_Offered'].sum()
        })).reset_index()
        weekly_err['man_wape'] = (weekly_err['man_err'] / weekly_err['actual'] * 100).fillna(0)
        weekly_err['ml_wape'] = (weekly_err['ml_err'] / weekly_err['actual'] * 100).fillna(0)
        weekly_err['ml_acceptable'] = (weekly_err['ml_wape'] <= weekly_err['man_wape']) | ((weekly_err['ml_wape'] <= 10) & (weekly_err['man_wape'] > 10))

        man_wins = (weekly_err['man_err'] <= weekly_err['ml_err']).sum()
        pragmatic_ml_wins = weekly_err['ml_acceptable'].sum()
        n_weeks = len(weekly_err)
        win_rate = round(man_wins / n_weeks * 100, 1) if n_weeks > 0 else 0
        pragmatic_ml_win_rate = round(pragmatic_ml_wins / n_weeks * 100, 1) if n_weeks > 0 else 0
        
        # Wilcoxon test
        try:
            diffs = weekly_err['man_err'] - weekly_err['ml_err']
            diffs = diffs[diffs != 0]
            if len(diffs) >= 3:
                stat, p = wilcoxon(weekly_err['man_err'], weekly_err['ml_err'])
                conf = "High" if p < 0.05 else ("Medium" if p < 0.10 else "Low")
            else:
                conf = "Inconclusive"
        except Exception:
            conf = "Inconclusive"
            
        summary_data.append({
            'SubRegion': sr,
            'Channel': ch,
            'Total_Actual': actual,
            'ML_Error': (sub_df['ML_Forecast'] - sub_df['Actual_Offered']).abs().sum(),
            'Manual_Error': (sub_df['Manual_Forecast'] - sub_df['Actual_Offered']).abs().sum(),
            'ML_WAPE': ml_wape,
            'Manual_WAPE': man_wape,
            'Delta_WAPE (ML - Man)': ml_wape - man_wape,
            'ML_Pragmatic_Win_Rate': pragmatic_ml_win_rate,
            'Manual_Win_Rate': win_rate,
            'Evaluated_Weeks': n_weeks,
            'Wilcoxon_Confidence': conf
        })
        
        # Bias Drift Details
        weekly_bias = sub_df.groupby('Week_Ending').apply(lambda g: pd.Series({
            'Actual_Vol': g['Actual_Offered'].sum(),
            'ML_Forecast_Vol': g['ML_Forecast'].sum(),
            'Manual_Forecast_Vol': g['Manual_Forecast'].sum(),
            'ML_Bias': (g['ML_Forecast'] - g['Actual_Offered']).sum(),
            'Manual_Bias': (g['Manual_Forecast'] - g['Actual_Offered']).sum(),
            'ML_Abs_Error': (g['ML_Forecast'] - g['Actual_Offered']).abs().sum(),
            'Manual_Abs_Error': (g['Manual_Forecast'] - g['Actual_Offered']).abs().sum(),
        })).reset_index().sort_values('Week_Ending')
        
        weekly_bias['Cum_ML_Bias'] = weekly_bias['ML_Bias'].cumsum()
        weekly_bias['Cum_Manual_Bias'] = weekly_bias['Manual_Bias'].cumsum()
        weekly_bias['Cum_ML_MAD'] = weekly_bias['ML_Abs_Error'].expanding().mean()
        weekly_bias['Cum_Manual_MAD'] = weekly_bias['Manual_Abs_Error'].expanding().mean()
        
        weekly_bias['ML_Tracking_Signal'] = np.where(weekly_bias['Cum_ML_MAD'] > 0, 
                                              weekly_bias['Cum_ML_Bias'] / weekly_bias['Cum_ML_MAD'], 
                                              0.0).round(3)
        weekly_bias['Manual_Tracking_Signal'] = np.where(weekly_bias['Cum_Manual_MAD'] > 0, 
                                                  weekly_bias['Cum_Manual_Bias'] / weekly_bias['Cum_Manual_MAD'], 
                                                  0.0).round(3)
                                                  
        weekly_bias['SubRegion'] = sr
        weekly_bias['Channel'] = ch
        
        # Reorder columns for neatness
        cols = ['SubRegion', 'Channel', 'Week_Ending', 'Actual_Vol', 'ML_Forecast_Vol', 'Manual_Forecast_Vol', 
                'ML_Bias', 'Manual_Bias', 'ML_Abs_Error', 'Manual_Abs_Error', 
                'Cum_ML_Bias', 'Cum_Manual_Bias', 'Cum_ML_MAD', 'Cum_Manual_MAD', 
                'ML_Tracking_Signal', 'Manual_Tracking_Signal']
        weekly_data.extend(weekly_bias[cols].to_dict('records'))
        
    df_sum = pd.DataFrame(summary_data)
    df_week = pd.DataFrame(weekly_data)
    
    with pd.ExcelWriter('ML_vs_Manual_Validation.xlsx', engine='openpyxl') as writer:
        df_sum.to_excel(writer, sheet_name='Summary_KPIs', index=False)
        df_week.to_excel(writer, sheet_name='Weekly_Data', index=False)
        
    print("Exported validation data to ML_vs_Manual_Validation.xlsx successfully.")

if __name__ == '__main__':
    generate_validation_sheet()
