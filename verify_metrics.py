import pandas as pd

def main():
    print("Loading data...")
    df = pd.read_excel('sample_data/FinalForecast_Imputed.xlsx')
    
    print("Calculating volume anomalies (Q3/Q4)...")
    # For volume, since Actual_Offered is duplicated across models per week, we just take the mean to get the true volume for that week.
    vol_weekly = df.groupby('Week_Ending')['Actual_Offered'].mean().reset_index()
    vol_weekly.rename(columns={'Actual_Offered': 'Weekly_Volume'}, inplace=True)
    
    mean_vol = vol_weekly['Weekly_Volume'].mean()
    std_vol = vol_weekly['Weekly_Volume'].std()
    
    vol_weekly['Vol_Z_Score'] = (vol_weekly['Weekly_Volume'] - mean_vol) / std_vol
    vol_weekly['Is_Anomaly_Week'] = vol_weekly['Vol_Z_Score'].abs() > 2.5
    
    df = df.merge(vol_weekly[['Week_Ending', 'Weekly_Volume', 'Vol_Z_Score', 'Is_Anomaly_Week']], on='Week_Ending', how='left')
    
    print("Calculating absolute errors...")
    df['Manual_Abs_Error'] = (df['Manual_Forecast'] - df['Actual_Offered']).abs()
    df['ML_Abs_Error'] = (df['ML_Forecast'] - df['Actual_Offered']).abs()
    
    print("Calculating weekly win rate (Q1)...")
    weekly_err = df.groupby('Week_Ending').apply(lambda g: pd.Series({
        'man_err': g['Manual_Abs_Error'].sum(),
        'ml_err': g['ML_Abs_Error'].sum()
    })).reset_index()
    weekly_err['Manual_Wins_Week'] = weekly_err['man_err'] <= weekly_err['ml_err']
    
    df = df.merge(weekly_err[['Week_Ending', 'Manual_Wins_Week']], on='Week_Ending', how='left')
    
    print("Saving to Verification_Data.xlsx...")
    df.to_excel('Verification_Data.xlsx', index=False)
    print("Done! The verification file is ready.")

if __name__ == '__main__':
    main()
