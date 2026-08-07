import pandas as pd

df = pd.read_excel('sample_data/FinalForecast_Imputed.xlsx')
unique_weeks = df[['Fiscal_Year', 'Week_Ending', 'Fiscal_Week', 'Month_Number', 'Week_Number']].drop_duplicates().sort_values('Week_Ending')

# Let's map Week_Number to FQ
# FQ1: 1-13, FQ2: 14-26, FQ3: 27-39, FQ4: 40-52
def get_fq(week_num):
    if 1 <= week_num <= 13: return 'FQ1'
    elif 14 <= week_num <= 26: return 'FQ2'
    elif 27 <= week_num <= 39: return 'FQ3'
    elif 40 <= week_num <= 52: return 'FQ4'
    return 'Unknown'

unique_weeks['Quarter'] = unique_weeks['Week_Number'].apply(get_fq)
print(unique_weeks.groupby(['Quarter'])['Month_Number'].unique())
print(unique_weeks.groupby(['Quarter'])['Week_Number'].agg(['min', 'max', 'count']))
