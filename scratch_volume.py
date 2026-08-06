import pandas as pd
import numpy as np

def verify_volume_metrics(excel_path):
    df = pd.read_excel(excel_path)
    df_actuals = df[df['Actual_Offered'].notnull() & (df['Actual_Offered'] > 0)].copy()
    
    df_actuals['Manual_Abs_Err'] = (df_actuals['Manual_Forecast'] - df_actuals['Actual_Offered']).abs()
    df_actuals['ML_Abs_Err'] = (df_actuals['ML_Forecast'] - df_actuals['Actual_Offered']).abs()
    df_actuals['Winner'] = np.where(df_actuals['ML_Abs_Err'] <= df_actuals['Manual_Abs_Err'], 'ML', 'Manual')
    
    # 1. Overall WAPE (Pooling everything into one bucket)
    total_actual = df_actuals['Actual_Offered'].sum()
    total_manual_err = df_actuals['Manual_Abs_Err'].sum()
    total_ml_err = df_actuals['ML_Abs_Err'].sum()
    
    global_manual_wape = total_manual_err / total_actual * 100
    global_ml_wape = total_ml_err / total_actual * 100
    
    print("--- 1. GLOBAL POOLED WAPE (Volume Weighted) ---")
    print(f"Global Manual WAPE: {global_manual_wape:.2f}%")
    print(f"Global ML WAPE:     {global_ml_wape:.2f}%")
    print(f"Winner by Volume:   {'ML' if global_ml_wape <= global_manual_wape else 'Manual'}\n")
    
    # 2. Volume breakdown by Classification
    queue_agg = df_actuals.groupby('Forecast_Name').agg(
        Valid_Weeks_Count=('Week_Ending', 'count'),
        Total_Queue_Volume=('Actual_Offered', 'sum')
    ).reset_index()
    
    ml_wins = df_actuals[df_actuals['Winner'] == 'ML'].groupby('Forecast_Name').size().reset_index(name='ML_Win_Count')
    queue_agg = pd.merge(queue_agg, ml_wins, on='Forecast_Name', how='left')
    queue_agg['ML_Win_Count'] = queue_agg['ML_Win_Count'].fillna(0)
    queue_agg['Weeks_ML_Wins_Pct'] = queue_agg['ML_Win_Count'] / queue_agg['Valid_Weeks_Count']
    
    def classify(pct):
        if pct >= 0.60: return 'Strong ML'
        elif pct >= 0.40: return 'Hybrid'
        else: return 'Manual'
            
    queue_agg['Classification'] = queue_agg['Weeks_ML_Wins_Pct'].apply(classify)
    
    vol_by_class = queue_agg.groupby('Classification')['Total_Queue_Volume'].sum()
    total_vol = vol_by_class.sum()
    
    print("--- 2. VOLUME BY CLASSIFICATION ---")
    for cls in ['Strong ML', 'Hybrid', 'Manual']:
        vol = vol_by_class.get(cls, 0)
        pct = (vol / total_vol) * 100
        print(f"{cls}: {vol:,.0f} contacts ({pct:.1f}%)")

if __name__ == '__main__':
    verify_volume_metrics('sample_data/Final_data.xlsx')
