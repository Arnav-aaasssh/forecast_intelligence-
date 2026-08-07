import pandas as pd

df = pd.read_excel('sample_data/FinalForecast_Imputed.xlsx')
# Select unique combinations
unique_weeks = df[['Fiscal_Year', 'Week_Ending', 'Fiscal_Week', 'Month_Number', 'Week_Number']].drop_duplicates().sort_values('Week_Ending')

print("First 20 rows:")
print(unique_weeks.head(20))

print("\nLast 20 rows:")
print(unique_weeks.tail(20))

# Group by Month_Number and see which Fiscal_Weeks or Fiscal_Years it maps to
print("\nMonth to Fiscal Year mapping:")
print(df.groupby('Month_Number')['Fiscal_Year'].unique())

print("\nMonth_Number unique values:")
print(sorted(df['Month_Number'].unique()))
