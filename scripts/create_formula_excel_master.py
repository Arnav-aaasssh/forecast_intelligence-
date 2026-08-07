import pandas as pd
import xlsxwriter
from datetime import datetime

def generate_formula_validation_master():
    print("Reading data...")
    raw_df = pd.read_excel('sample_data/Final_data.xlsx')
    
    raw_df['Week_Ending'] = pd.to_datetime(raw_df['Week_Ending'])
    raw_df['Actual_Offered'] = pd.to_numeric(raw_df['Actual_Offered'], errors='coerce').fillna(0)
    raw_df['ML_Forecast'] = pd.to_numeric(raw_df['ML_Forecast'], errors='coerce').fillna(0)
    raw_df['Manual_Forecast'] = pd.to_numeric(raw_df['Manual_Forecast'], errors='coerce').fillna(0)
    
    # Calculate row-level absolute errors to allow Bottom-Up WAPE calculation in SUMIFS
    raw_df['ML_Abs_Error_Row'] = (raw_df['ML_Forecast'] - raw_df['Actual_Offered']).abs()
    raw_df['Manual_Abs_Error_Row'] = (raw_df['Manual_Forecast'] - raw_df['Actual_Offered']).abs()

    # Extract actual weeks
    df_actuals = raw_df[raw_df['Actual_Offered'] > 0]
    weeks = sorted(df_actuals['Week_Ending'].unique())
    weeks = [pd.to_datetime(w).to_pydatetime() for w in weeks]
    
    sub_regions = sorted(raw_df['SubRegion'].dropna().unique().tolist())
    regions = sorted(raw_df['Region'].dropna().unique().tolist()) if 'Region' in raw_df.columns else []
    channels = sorted(raw_df['Channel'].dropna().unique().tolist()) if 'Channel' in raw_df.columns else []
    
    offerings = sorted(raw_df['Offering'].dropna().unique().tolist()) if 'Offering' in raw_df.columns else []
    
    # Build combinations (Dashboard Slices)
    # Format: (level, name, channel, offering)
    combinations = [('Global', 'Global', 'All', 'All')]
    for r in regions:
        combinations.append(('Region', r, 'All', 'All'))
        for ch in channels:
            combinations.append(('Region', r, ch, 'All'))
    for sr in sub_regions:
        combinations.append(('SubRegion', sr, 'All', 'All'))
        for ch in channels:
            combinations.append(('SubRegion', sr, ch, 'All'))
            for off in offerings:
                combinations.append(('Offering', sr, ch, off))
            
    writer = pd.ExcelWriter('Validation_Formulas_Master_v2.xlsx', engine='xlsxwriter', datetime_format='yyyy-mm-dd')
    
    # Write Raw Data sheet
    print("Writing Raw Data...")
    raw_df.to_excel(writer, sheet_name='Raw_Data', index=False)
    
    workbook = writer.book
    
    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
    pct_fmt = workbook.add_format({'num_format': '0.00%'})
    num_fmt = workbook.add_format({'num_format': '#,##0'})
    dec_fmt = workbook.add_format({'num_format': '0.00'})
    date_fmt = workbook.add_format({'num_format': 'yyyy-mm-dd'})
    
    # ---------------------------------------------------------
    # Create Master Validation Sheet
    # ---------------------------------------------------------
    print("Writing Master Validation formulas...")
    worksheet = workbook.add_worksheet('Master_Weekly_Validation')
    
    # Set column widths
    worksheet.set_column('A:A', 25) # Dashboard Slice
    worksheet.set_column('B:B', 12) # Week
    worksheet.set_column('C:I', 15)
    worksheet.set_column('J:K', 18)
    
    headers = [
        "Dashboard_Slice", "Week_Ending", 
        "Actual Volume", "ML Forecast", "Manual Forecast",
        "ML Error (Bias)", "Manual Error (Bias)", "ML Abs Error", "Manual Abs Error",
        "ML Weekly WAPE", "Manual Weekly WAPE", "Manual Won Week?", "ML Won Week?"
    ]
    
    for col, head in enumerate(headers):
        worksheet.write(0, col, head, header_fmt)
        
    current_row = 1
    
    for level, name, ch, off in combinations:
        if level == 'Offering':
            slice_name = f"Offering: {name} - {ch} - {off}"
        elif ch == 'All':
            slice_name = f"{level}: {name} - All Channels" if level != 'Global' else f"{name} - All Channels"
        else:
            slice_name = f"{level}: {name} - {ch}"
        
        for week in weeks:
            xl_row = current_row + 1 # 1-indexed for formulas
            
            # Build SUMIFS condition string dynamically for each row
            cond = f', Raw_Data!$E:$E, $B{xl_row}'
            if level == 'Region':
                cond += f', Raw_Data!$J:$J, "{name}"'
            elif level == 'SubRegion':
                cond += f', Raw_Data!$K:$K, "{name}"'
            elif level == 'Offering':
                cond += f', Raw_Data!$K:$K, "{name}"'
                
            if ch != 'All':
                cond += f', Raw_Data!$M:$M, "{ch}"'
            
            if off != 'All':
                cond += f', Raw_Data!$L:$L, "{off}"'
            
            worksheet.write(current_row, 0, slice_name)
            # Write datetime natively so SUMIFS matching works perfectly
            worksheet.write_datetime(current_row, 1, week, date_fmt)
            
            # Volumes
            worksheet.write_formula(current_row, 2, f'=SUMIFS(Raw_Data!$AP:$AP{cond})', num_fmt)
            worksheet.write_formula(current_row, 3, f'=SUMIFS(Raw_Data!$AS:$AS{cond})', num_fmt)
            worksheet.write_formula(current_row, 4, f'=SUMIFS(Raw_Data!$AQ:$AQ{cond})', num_fmt)
            
            # Errors
            worksheet.write_formula(current_row, 5, f'=D{xl_row} - C{xl_row}', num_fmt) # ML Bias
            worksheet.write_formula(current_row, 6, f'=E{xl_row} - C{xl_row}', num_fmt) # Manual Bias
            worksheet.write_formula(current_row, 7, f'=SUMIFS(Raw_Data!$AT:$AT{cond})', num_fmt) # ML Bottom-Up Abs Error
            worksheet.write_formula(current_row, 8, f'=SUMIFS(Raw_Data!$AU:$AU{cond})', num_fmt) # Manual Bottom-Up Abs Error
            
            # WAPEs
            worksheet.write_formula(current_row, 9, f'=IF(C{xl_row}>0, H{xl_row}/C{xl_row}, 0)', pct_fmt)
            worksheet.write_formula(current_row, 10, f'=IF(C{xl_row}>0, I{xl_row}/C{xl_row}, 0)', pct_fmt)
            
            # Wins — strict inequality: ML must strictly beat Manual; ties go to Manual
            worksheet.write_formula(current_row, 11, f'=IF(I{xl_row}<=H{xl_row}, 1, 0)')  # Manual Won Week (Manual err <= ML err)
            worksheet.write_formula(current_row, 12, f'=IF(H{xl_row}<I{xl_row}, 1, 0)')   # ML Won Week (ML err strictly < Manual err)
            
            current_row += 1

    # Add auto-filter
    worksheet.autofilter(0, 0, current_row, len(headers) - 1)

    writer.close()
    print("Exported Validation_Formulas_Master_v2.xlsx successfully.")

if __name__ == "__main__":
    generate_formula_validation_master()
