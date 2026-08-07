import pandas as pd
import numpy as np
from scipy.stats import wilcoxon

df = pd.read_excel('sample_data/FinalForecast_Imputed.xlsx')
df['Week_Ending'] = pd.to_datetime(df['Week_Ending'])

# 1. Let's compute weekly WAPE series
weekly = df.groupby('Week_Ending').apply(lambda g: pd.Series({
    'manual_wape': (g['Manual_Forecast'] - g['Actual_Offered']).abs().sum() / g['Actual_Offered'].sum() * 100 if g['Actual_Offered'].sum() > 0 else 0,
    'ml_wape': (g['ML_Forecast'] - g['Actual_Offered']).abs().sum() / g['Actual_Offered'].sum() * 100 if g['Actual_Offered'].sum() > 0 else 0,
})).reset_index().sort_values('Week_Ending')

# Let's test Wilcoxon on weekly series:
# Option A: Wilcoxon two-sided on weekly WAPE series
try:
    res_2s = wilcoxon(weekly['ml_wape'], weekly['manual_wape'], alternative='two-sided')
    print("Wilcoxon two-sided on weekly WAPE:", res_2s.pvalue)
except Exception as e:
    print("Option A failed:", e)

# Option B: Wilcoxon greater on weekly WAPE series
try:
    res_gr = wilcoxon(weekly['ml_wape'], weekly['manual_wape'], alternative='greater')
    print("Wilcoxon greater (ML > Manual) on weekly WAPE:", res_gr.pvalue)
except Exception as e:
    print("Option B failed:", e)

# Option C: Wilcoxon greater (Manual > ML) on weekly WAPE series
try:
    res_gr2 = wilcoxon(weekly['manual_wape'], weekly['ml_wape'], alternative='greater')
    print("Wilcoxon greater (Manual > ML) on weekly WAPE:", res_gr2.pvalue)
except Exception as e:
    print("Option C failed:", e)

# Option D: Wilcoxon on row-level errors
# Let's check row level absolute errors
df['manual_ae'] = (df['Manual_Forecast'] - df['Actual_Offered']).abs()
df['ml_ae'] = (df['ML_Forecast'] - df['Actual_Offered']).abs()
# For Wilcoxon at row level, it might be too large, but let's see.

# Wait, how is effect_size = 0.0327 calculated?
# Let's check absolute improvement or relative improvement
# Relative improvement = (ml_wape - manual_wape) / ml_wape ?
# Let's calculate:
overall_manual_wape = (df['Manual_Forecast'] - df['Actual_Offered']).abs().sum() / df['Actual_Offered'].sum() * 100
overall_ml_wape = (df['ML_Forecast'] - df['Actual_Offered']).abs().sum() / df['Actual_Offered'].sum() * 100
abs_imp = overall_ml_wape - overall_manual_wape
rel_imp = abs_imp / overall_ml_wape
print(f"Overall Manual WAPE: {overall_manual_wape:.4f}%")
print(f"Overall ML WAPE: {overall_ml_wape:.4f}%")
print(f"Absolute diff: {abs_imp/100:.6f}")
print(f"Relative diff: {rel_imp:.6f}")
