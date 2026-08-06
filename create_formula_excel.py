import pandas as pd
import xlsxwriter
from datetime import datetime

def generate_formula_validation():
    print("Reading data...")
    raw_df = pd.read_excel('sample_data/Final_data.xlsx')
    
    # We need to extract unique weeks where Actual_Offered is present
    df_actuals = raw_df[raw_df['Actual_Offered'].notnull() & (raw_df['Actual_Offered'] > 0)]
    weeks = sorted(df_actuals['Week_Ending'].dt.strftime('%Y-%m-%d').unique().tolist())
    
    writer = pd.ExcelWriter('Validation_Formulas.xlsx', engine='xlsxwriter')
    
    # Write Raw Data sheet
    print("Writing Raw Data...")
    raw_df['Week_Ending'] = raw_df['Week_Ending'].dt.strftime('%Y-%m-%d')
    raw_df.to_excel(writer, sheet_name='Raw_Data', index=False)
    
    workbook = writer.book
    
    # Formatting
    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
    pct_fmt = workbook.add_format({'num_format': '0.00%'})
    num_fmt = workbook.add_format({'num_format': '#,##0'})
    dec_fmt = workbook.add_format({'num_format': '0.00'})
    bold_fmt = workbook.add_format({'bold': True})
    
    # ---------------------------------------------------------
    # Create ANZ_Validation Sheet
    # ---------------------------------------------------------
    print("Writing ANZ Validation formulas...")
    worksheet = workbook.add_worksheet('ANZ_Validation')
    
    # Set column widths
    worksheet.set_column('A:A', 12)
    worksheet.set_column('B:H', 15)
    worksheet.set_column('I:L', 18)
    worksheet.set_column('M:R', 18)
    
    # Build Top Summary KPIs
    worksheet.write('B1', 'Dashboard Top-Level KPIs Validation (ANZ)', bold_fmt)
    
    summary_labels = [
        "Total Actual Volume", "Total ML Abs Error", "Total Manual Abs Error",
        "ML Overall WAPE", "Manual Overall WAPE", 
        "Total Weeks Evaluated", "Manual Won Weeks", "Pragmatic ML Won Weeks",
        "Manual Win Rate", "Pragmatic ML Win Rate"
    ]
    
    for idx, label in enumerate(summary_labels):
        worksheet.write(idx+2, 1, label, bold_fmt)
        
    n_weeks = len(weeks)
    last_row = 7 + n_weeks
    
    # Summary Formulas
    worksheet.write_formula('C3', f'=SUM(B8:B{last_row})', num_fmt)
    worksheet.write_formula('C4', f'=SUM(G8:G{last_row})', num_fmt)
    worksheet.write_formula('C5', f'=SUM(H8:H{last_row})', num_fmt)
    worksheet.write_formula('C6', f'=C4/C3', pct_fmt)
    worksheet.write_formula('C7', f'=C5/C3', pct_fmt)
    worksheet.write_formula('C8', f'=COUNT(A8:A{last_row})', num_fmt)
    worksheet.write_formula('C9', f'=SUM(K8:K{last_row})', num_fmt)
    worksheet.write_formula('C10', f'=SUM(L8:L{last_row})', num_fmt)
    worksheet.write_formula('C11', f'=C9/C8', pct_fmt)
    worksheet.write_formula('C12', f'=C10/C8', pct_fmt)
    
    # Weekly Data Headers
    headers = [
        "Week_Ending", "Actual Volume", "ML Forecast", "Manual Forecast",
        "ML Error (Bias)", "Manual Error (Bias)", "ML Abs Error", "Manual Abs Error",
        "ML Weekly WAPE", "Manual Weekly WAPE", "Manual Won?", "Pragmatic ML Won?",
        "Cum ML Bias", "Cum Manual Bias", "Cum ML MAD", "Cum Manual MAD",
        "ML Tracking Signal", "Manual Tracking Signal"
    ]
    
    for col, head in enumerate(headers):
        worksheet.write(6, col, head, header_fmt)
        
    # Write Weekly Rows with Formulas
    for idx, week in enumerate(weeks):
        row = idx + 7 # 0-indexed, starts at row 8 (index 7)
        xl_row = row + 1 # Excel row number (1-indexed)
        
        # Week Ending
        worksheet.write(row, 0, week)
        
        # SUMIFS
        worksheet.write_formula(row, 1, f'=SUMIFS(Raw_Data!$AP:$AP, Raw_Data!$E:$E, $A{xl_row}, Raw_Data!$K:$K, "ANZ")', num_fmt)
        worksheet.write_formula(row, 2, f'=SUMIFS(Raw_Data!$AS:$AS, Raw_Data!$E:$E, $A{xl_row}, Raw_Data!$K:$K, "ANZ")', num_fmt)
        worksheet.write_formula(row, 3, f'=SUMIFS(Raw_Data!$AQ:$AQ, Raw_Data!$E:$E, $A{xl_row}, Raw_Data!$K:$K, "ANZ")', num_fmt)
        
        # Errors
        worksheet.write_formula(row, 4, f'=C{xl_row} - B{xl_row}', num_fmt)
        worksheet.write_formula(row, 5, f'=D{xl_row} - B{xl_row}', num_fmt)
        worksheet.write_formula(row, 6, f'=ABS(E{xl_row})', num_fmt)
        worksheet.write_formula(row, 7, f'=ABS(F{xl_row})', num_fmt)
        
        # WAPEs
        worksheet.write_formula(row, 8, f'=IF(B{xl_row}>0, G{xl_row}/B{xl_row}, 0)', pct_fmt)
        worksheet.write_formula(row, 9, f'=IF(B{xl_row}>0, H{xl_row}/B{xl_row}, 0)', pct_fmt)
        
        # Wins
        worksheet.write_formula(row, 10, f'=IF(H{xl_row}<=G{xl_row}, 1, 0)')
        worksheet.write_formula(row, 11, f'=IF(OR(I{xl_row}<=J{xl_row}, AND(I{xl_row}<=0.1, J{xl_row}>0.1)), 1, 0)')
        
        # Cumulative
        worksheet.write_formula(row, 12, f'=SUM($E$8:$E{xl_row})', num_fmt)
        worksheet.write_formula(row, 13, f'=SUM($F$8:$F{xl_row})', num_fmt)
        worksheet.write_formula(row, 14, f'=AVERAGE($G$8:$G{xl_row})', dec_fmt)
        worksheet.write_formula(row, 15, f'=AVERAGE($H$8:$H{xl_row})', dec_fmt)
        
        # Tracking Signals
        worksheet.write_formula(row, 16, f'=IF(O{xl_row}>0, M{xl_row}/O{xl_row}, 0)', dec_fmt)
        worksheet.write_formula(row, 17, f'=IF(P{xl_row}>0, N{xl_row}/P{xl_row}, 0)', dec_fmt)

    writer.close()
    print("Exported Validation_Formulas.xlsx successfully.")

if __name__ == "__main__":
    generate_formula_validation()
