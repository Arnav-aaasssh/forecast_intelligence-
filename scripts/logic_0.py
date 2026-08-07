"""
analytics_v2.py -- Corrected data layer for Dashboard V2.

Built against the REAL dataset: 13 of 99 weeks have realized actuals
(2026-03-13 to 2026-06-05). Every calculation here is scoped strictly
to those 13 weeks unless explicitly noted as "planned/forecast" data.

Key corrections vs. the V1 (99-week) pipeline, per the V2 Implementation Plan:
  - No row pooling across forecast-only weeks -- only Actual_Offered-populated
    rows contribute to any accuracy metric.
  - Confidence tiers gain a 4th state, "Inconclusive", for cases where the
    win split is near 50/50 AND effect size is below the practical floor --
    distinct from "Low" (a real but statistically unproven directional signal).
  - Model Champion eligibility is WEEK-COVERAGE based (>= 8 of 13 weeks
    present), not row-count based.
  - Stability metric is Max Absolute Weekly Error, not IQR (unreliable at n=13).
  - Anomaly / historical-baseline comparisons are computed PER-SEGMENT
    (per Forecast_Name) using that segment's own Mean/StdDev (Hist. Contacts)
    columns, then rolled up as a COUNT/SHARE of anomalous segments --
    never as a single pooled z-score built from summed independent variances
    (that approach was tested and found to be wrong; see planning doc Sec. 19).
"""
import pandas as pd
import numpy as np

PATH = '/mnt/user-data/uploads/19June_FinalForecast_With_Risk_Flagging202852.xlsx'

# ---- Config (mirrors the plan's recommendations) ----
WEEK_COVERAGE_MIN = 8          # of 13 actual weeks, for Model Champion eligibility
TIE_WIN_BAND = 0.15            # +/- 15 points around 50% counts as "near tied"
EFFECT_SIZE_FLOOR = 0.015      # pp, same practical-significance floor as V1
SEGMENT_Z_ANOMALY = 2.5        # per-segment anomaly z-score threshold

WEIGHTS = {'WAPE': 0.35, 'Bias': 0.20, 'MaxError': 0.20, 'Hit10': 0.25}
HIT_BAND = 0.10


def load():
    df = pd.read_excel(PATH)
    bt = df[df['Actual_Offered'].notna()].copy()
    bt['err'] = bt['ML_Forecast'] - bt['Actual_Offered']
    bt['abs_err'] = bt['err'].abs()
    with np.errstate(divide='ignore', invalid='ignore'):
        bt['pct_err'] = bt['err'] / bt['Actual_Offered']
    bt['pct_err'] = bt['pct_err'].replace([np.inf, -np.inf], np.nan)
    return df, bt


def wape(f, a):
    if a.sum() == 0:
        return np.nan
    return (f - a).abs().sum() / a.sum()


# ============================================================
# 1. STRATEGY ASSESSMENT -- 13-week win-count framing
# ============================================================
def strategy_assessment(bt: pd.DataFrame) -> dict:
    wk = bt.groupby('Week_Ending').apply(lambda g: pd.Series({
        'manual': wape(g['Manual_Forecast'], g['Actual_Offered']),
        'ml': wape(g['ML_Forecast'], g['Actual_Offered']),
    })).sort_index()
    n_weeks = len(wk)
    manual_wins = int((wk['manual'] < wk['ml']).sum())
    ml_wins = int((wk['ml'] < wk['manual']).sum())
    ties = n_weeks - manual_wins - ml_wins

    manual_wape = wape(bt['Manual_Forecast'], bt['Actual_Offered'])
    ml_wape = wape(bt['ML_Forecast'], bt['Actual_Offered'])
    effect_size = abs(ml_wape - manual_wape)
    win_rate = manual_wins / n_weeks if n_weeks else np.nan

    near_tied = abs(win_rate - 0.5) <= TIE_WIN_BAND
    if near_tied and effect_size < EFFECT_SIZE_FLOOR:
        confidence = 'Inconclusive'
    elif manual_wins >= 10 or ml_wins >= 10:
        confidence = 'High' if effect_size >= EFFECT_SIZE_FLOOR else 'Medium'
    elif effect_size >= EFFECT_SIZE_FLOOR:
        confidence = 'Medium'
    else:
        confidence = 'Low'

    series = [{'week': w.strftime('%Y-%m-%d'),
               'manual_wape': round(float(r['manual']) * 100, 2),
               'ml_wape': round(float(r['ml']) * 100, 2)} for w, r in wk.iterrows()]

    return {
        'n_weeks': n_weeks, 'manual_wins': manual_wins, 'ml_wins': ml_wins, 'ties': ties,
        'manual_wape': round(float(manual_wape) * 100, 2), 'ml_wape': round(float(ml_wape) * 100, 2),
        'effect_size': round(float(effect_size), 4), 'confidence': confidence, 'series': series,
    }


# ============================================================
# 2. MODEL CHAMPION -- week-coverage eligibility, Max-Error stability
# ============================================================
def model_champion(bt: pd.DataFrame) -> dict:
    n_actual_weeks = bt['Week_Ending'].nunique()

    def raw_metrics(g):
        denom = g['Actual_Offered'].sum()
        return pd.Series({
            'n_rows': len(g),
            'n_weeks_present': g['Week_Ending'].nunique(),
            'WAPE': g['abs_err'].sum() / denom if denom else np.nan,
            'Bias': abs(g['err'].sum() / denom) if denom else np.nan,
            'MaxError': g['pct_err'].abs().max(),
            'Hit10': (g['pct_err'].abs() <= HIT_BAND).mean(),
            'Hit10_count': int((g['pct_err'].abs() <= HIT_BAND).sum()),
        })

    raw = bt.groupby('Model').apply(raw_metrics)
    eligible = raw[raw['n_weeks_present'] >= WEEK_COVERAGE_MIN].copy()
    excluded_n = len(raw) - len(eligible)

    if eligible.empty:
        return {'n_eligible': 0, 'n_excluded': excluded_n, 'n_actual_weeks': n_actual_weeks, 'leaderboard': []}

    def norm(s, best, worst, invert):
        lo, hi = min(best, worst), max(best, worst)
        c = s.clip(lo, hi)
        return (worst - c) / (worst - best) if invert else (c - worst) / (best - worst)

    eligible['s_wape'] = norm(eligible['WAPE'], 0.05, 0.40, invert=True)
    eligible['s_bias'] = norm(eligible['Bias'], 0.00, 0.20, invert=True)
    eligible['s_maxerr'] = norm(eligible['MaxError'], 0.00, 0.50, invert=True)
    eligible['s_hit10'] = norm(eligible['Hit10'], 0.90, 0.30, invert=False)

    eligible['CompositeScore'] = 100 * (
        WEIGHTS['WAPE'] * eligible['s_wape'] + WEIGHTS['Bias'] * eligible['s_bias']
        + WEIGHTS['MaxError'] * eligible['s_maxerr'] + WEIGHTS['Hit10'] * eligible['s_hit10']
    )
    eligible = eligible.sort_values('CompositeScore', ascending=False)

    lb = eligible.reset_index()[['Model', 'n_rows', 'n_weeks_present', 'WAPE', 'Bias', 'MaxError',
                                  'Hit10', 'Hit10_count', 'CompositeScore',
                                  's_wape', 's_bias', 's_maxerr', 's_hit10']].copy()
    lb['WAPE'] = (lb['WAPE'] * 100).round(2)
    lb['Bias'] = (lb['Bias'] * 100).round(2)
    lb['MaxError'] = (lb['MaxError'] * 100).round(2)
    lb['Hit10'] = (lb['Hit10'] * 100).round(2)
    lb['CompositeScore'] = lb['CompositeScore'].round(2)
    lb['s_wape'] = (lb['s_wape'] * 100).round(1)
    lb['s_bias'] = (lb['s_bias'] * 100).round(1)
    lb['s_maxerr'] = (lb['s_maxerr'] * 100).round(1)
    lb['s_hit10'] = (lb['s_hit10'] * 100).round(1)

    # Family-level summary (which technique family performs best, on average)
    fam = bt.loc[bt['Model'].isin(eligible.index)].drop_duplicates('Model')[['Model', 'Family']].set_index('Model')
    lb_fam = lb.set_index('Model').join(fam)
    family_summary = (lb_fam.groupby('Family')['CompositeScore'].agg(['mean', 'count'])
                       .rename(columns={'mean': 'avg_score', 'count': 'n_models'}).reset_index())
    family_summary['avg_score'] = family_summary['avg_score'].round(1)
    family_summary = family_summary.sort_values('avg_score', ascending=False)

    return {
        'n_eligible': len(eligible), 'n_excluded': excluded_n, 'n_total_models': len(raw),
        'n_actual_weeks': n_actual_weeks, 'week_coverage_min': WEEK_COVERAGE_MIN,
        'leaderboard': lb.to_dict('records'),
        'family_summary': family_summary.to_dict('records'),
    }


# ============================================================
# 3. BUSINESS CONTEXT -- realized vs. planned split, segment-level baseline
# ============================================================
def business_context(df: pd.DataFrame, bt: pd.DataFrame) -> dict:
    realized_vol = bt.groupby('Week_Ending')['Actual_Offered'].sum().sort_index()
    realized_series = [{'week': w.strftime('%Y-%m-%d'), 'volume': int(v)} for w, v in realized_vol.items()]

    planned_vol = df.groupby('Week_Ending')['Manual_Forecast'].sum().sort_index()
    planned_series = [{'week': w.strftime('%Y-%m-%d'), 'volume': int(v)} for w, v in planned_vol.items()]

    in_sample_cv = float(realized_vol.std() / realized_vol.mean()) * 100 if realized_vol.mean() else None

    seg_base = df.drop_duplicates('Forecast_Name')[
        ['Forecast_Name', 'Mean (Hist. Contacts) (Last 1 yr.)', 'Std Dev (Hist. Contacts)']
    ].set_index('Forecast_Name')
    hist_cv_per_segment = (seg_base['Std Dev (Hist. Contacts)'] / seg_base['Mean (Hist. Contacts) (Last 1 yr.)']).replace([np.inf, -np.inf], np.nan)
    historical_cv = float(hist_cv_per_segment.median()) * 100

    below_share_by_week = []
    for wk, g in bt.groupby('Week_Ending'):
        below = (g['Actual_Offered'] < g['Mean (Hist. Contacts) (Last 1 yr.)']).mean()
        below_share_by_week.append({'week': wk.strftime('%Y-%m-%d'), 'share_below_pct': round(float(below) * 100, 1)})

    overall_below_share = float((bt['Actual_Offered'] < bt['Mean (Hist. Contacts) (Last 1 yr.)']).mean()) * 100

    return {
        'realized_series': realized_series, 'planned_series': planned_series,
        'in_sample_cv': round(in_sample_cv, 2) if in_sample_cv else None,
        'historical_cv_median_segment': round(historical_cv, 2),
        'overall_share_below_baseline': round(overall_below_share, 1),
        'share_below_by_week': below_share_by_week,
    }


# ============================================================
# 4. ANOMALY DETECTION -- segment-level z-scores, rolled up as a count/share
# ============================================================
def anomaly_detection(df: pd.DataFrame, bt: pd.DataFrame) -> dict:
    bt2 = bt.copy()
    std = bt2['Std Dev (Hist. Contacts)'].replace(0, np.nan)
    bt2['seg_z'] = (bt2['Actual_Offered'] - bt2['Mean (Hist. Contacts) (Last 1 yr.)']) / std
    bt2['is_anomalous_segment'] = bt2['seg_z'].abs() > SEGMENT_Z_ANOMALY

    per_week = []
    for wk, g in bt2.groupby('Week_Ending'):
        n_anom = int(g['is_anomalous_segment'].sum())
        n_total = len(g)
        per_week.append({
            'week': wk.strftime('%Y-%m-%d'),
            'n_anomalous_segments': n_anom, 'n_total_segments': n_total,
            'share_anomalous_pct': round(n_anom / n_total * 100, 1) if n_total else 0,
            'mean_seg_z': round(float(g['seg_z'].mean()), 2),
        })

    total_anomalous = sum(w['n_anomalous_segments'] for w in per_week)
    weeks_with_any_sharp_anomaly = sum(1 for w in per_week if w['n_anomalous_segments'] > 0)

    return {
        'per_week': per_week,
        'total_anomalous_segment_weeks': total_anomalous,
        'weeks_with_any_sharp_anomaly': weeks_with_any_sharp_anomaly,
        'n_weeks_evaluated': len(per_week),
        'method_note': 'Segment-level z-score vs. each Forecast_Name\'s own historical mean/std; '
                        'rolled up as a count/share of anomalous segments per week -- '
                        'not a pooled company-wide z-score (see planning doc Sec. 19 for why).',
    }


if __name__ == '__main__':
    df, bt = load()
    sa = strategy_assessment(bt)
    print('=== Strategy Assessment ===')
    print(f"Manual won {sa['manual_wins']} of {sa['n_weeks']} weeks; ML won {sa['ml_wins']}; ties {sa['ties']}")
    print(f"Manual WAPE {sa['manual_wape']}%  ML WAPE {sa['ml_wape']}%  effect size {sa['effect_size']}")
    print(f"Confidence: {sa['confidence']}")
    print()
    mc = model_champion(bt)
    print('=== Model Champion ===')
    print(f"{mc['n_eligible']} of {mc['n_total_models']} models meet >= {mc['week_coverage_min']}/{mc['n_actual_weeks']}-week coverage")
    for row in mc['leaderboard'][:5]:
        print(f"  {row['Model']:<20} score={row['CompositeScore']:>6.2f}  WAPE={row['WAPE']}%  weeks={row['n_weeks_present']}")
    print()
    bc = business_context(df, bt)
    print('=== Business Context ===')
    print(f"In-sample CV (13 weeks): {bc['in_sample_cv']}%   Historical median segment CV: {bc['historical_cv_median_segment']}%")
    print(f"Overall share of segment-weeks below historical baseline: {bc['overall_share_below_baseline']}%")
    print()
    ad = anomaly_detection(df, bt)
    print('=== Anomaly Detection ===')
    print(f"Weeks with >=1 sharp anomalous segment: {ad['weeks_with_any_sharp_anomaly']} of {ad['n_weeks_evaluated']}")
    for w in ad['per_week']:
        print(f"  {w['week']}: {w['n_anomalous_segments']} anomalous / {w['n_total_segments']} segments ({w['share_anomalous_pct']}%)  mean_z={w['mean_seg_z']}")
