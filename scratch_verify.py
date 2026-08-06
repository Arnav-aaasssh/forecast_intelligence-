import pandas as pd
import numpy as np

def verify_dashboard_metrics(excel_path):
    print("Loading data...")
    df = pd.read_excel(excel_path)
    
    print("Filtering realized weeks (Actual_Offered > 0)...")
    df_actuals = df[df['Actual_Offered'].notnull() & (df['Actual_Offered'] > 0)].copy()
    
    # Calculate Weekly Errors
    df_actuals['Manual_Abs_Err'] = (df_actuals['Manual_Forecast'] - df_actuals['Actual_Offered']).abs()
    df_actuals['ML_Abs_Err'] = (df_actuals['ML_Forecast'] - df_actuals['Actual_Offered']).abs()
    
    # Determine winner per week
    # Note: Using absolute error directly is mathematically identical to WAPE since denominators are the same
    df_actuals['Winner'] = np.where(df_actuals['ML_Abs_Err'] <= df_actuals['Manual_Abs_Err'], 'ML', 'Manual')
    
    # Aggregate by Queue (Forecast_Name)
    print("Aggregating by Queue...")
    queue_agg = df_actuals.groupby('Forecast_Name').agg(
        Valid_Weeks_Count=('Week_Ending', 'count')
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
    
    # Calculate global counts and percentages
    total_queues = len(queue_agg)
    counts = queue_agg['Classification'].value_counts()
    
    print(f"\n--- GLOBAL QUEUE CLASSIFICATION ---")
    print(f"Total Queues: {total_queues}")
    
    for cls in ['Strong ML', 'Hybrid', 'Manual']:
        count = counts.get(cls, 0)
        pct = (count / total_queues) * 100
        print(f"{cls}: {count} queues ({pct:.1f}%)")
        
    print("\n--- SAMPLE QUEUE DATA (First 5) ---")
    print(queue_agg.head().to_string())

if __name__ == '__main__':
    verify_dashboard_metrics('sample_data/Final_data.xlsx')
