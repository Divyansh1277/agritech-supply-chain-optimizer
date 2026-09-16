import pandas as pd
import numpy as np
from typing import Optional


def compute_total_arrivals(df: pd.DataFrame) -> float:
    """SUM(quantity_quintals) over filtered rows."""
    if df.empty or 'quantity_quintals' not in df.columns:
        return 0.0
    return float(df['quantity_quintals'].sum())


def compute_avg_modal_price(df: pd.DataFrame) -> float:
    """AVG(modal_price_clean)."""
    if df.empty or 'modal_price_clean' not in df.columns:
        return 0.0
    return float(df['modal_price_clean'].mean())


def compute_avg_msp(df: pd.DataFrame) -> float:
    """AVG(msp_clean)."""
    if df.empty or 'msp_clean' not in df.columns:
        return 0.0
    return float(df['msp_clean'].mean())


def compute_msp_gap_pct(df: pd.DataFrame) -> float:
    """AVG((modal_price_clean - msp_clean) / msp_clean) * 100. Negative = below MSP."""
    if df.empty or 'modal_price_clean' not in df.columns or 'msp_clean' not in df.columns:
        return 0.0
    valid = df.dropna(subset=['modal_price_clean', 'msp_clean'])
    valid = valid[valid['msp_clean'] > 0]
    if valid.empty:
        return 0.0
    gaps = (valid['modal_price_clean'] - valid['msp_clean']) / valid['msp_clean'] * 100
    return float(gaps.mean())


def compute_distress_sale_index(df: pd.DataFrame) -> float:
    """
    Quantity-weighted share of arrivals transacted below MSP.
    DSI = SUM(qty WHERE modal < msp) / SUM(qty) * 100
    """
    if df.empty or 'quantity_quintals' not in df.columns:
        return 0.0
    total_qty = df['quantity_quintals'].sum()
    if total_qty == 0:
        return 0.0
    distress_mask = df['modal_price_clean'] < df['msp_clean']
    distress_qty = df.loc[distress_mask, 'quantity_quintals'].sum()
    return float(distress_qty / total_qty * 100)


def compute_price_crash_instances(df: pd.DataFrame) -> int:
    """Count of mandi-crop-days where modal_price < msp."""
    if df.empty or 'modal_price_clean' not in df.columns:
        return 0
    return int((df['modal_price_clean'] < df['msp_clean']).sum())


def compute_avg_transit_time(df: pd.DataFrame) -> float:
    """AVG(transit_hours) excluding quarantined trips."""
    if df.empty or 'transit_hours' not in df.columns:
        return 0.0
    valid = df[df['transit_hours'] >= 0]
    if valid.empty:
        return 0.0
    return float(valid['transit_hours'].mean())


def compute_delay_rate(df: pd.DataFrame) -> tuple[float, int]:
    """
    Share of trips where transit_hours > distance_km/40 + 2.
    Returns (rate_pct, total_trips).
    """
    if df.empty or 'transit_hours' not in df.columns or 'distance_km' not in df.columns:
        return 0.0, 0
    valid = df.dropna(subset=['transit_hours', 'distance_km'])
    valid = valid[valid['transit_hours'] >= 0]
    total = len(valid)
    if total == 0:
        return 0.0, 0
    threshold = valid['distance_km'] / 40.0 + 2
    delayed = (valid['transit_hours'] > threshold).sum()
    return float(delayed / total * 100), total


def compute_farmers_served(df: pd.DataFrame) -> int:
    """SUM(farmer_count)."""
    if df.empty or 'farmer_count' not in df.columns:
        return 0
    return int(df['farmer_count'].sum())


def compute_active_mandis(df: pd.DataFrame) -> int:
    """Count distinct mandis in the data."""
    if df.empty or 'mandi_id' not in df.columns:
        return 0
    return int(df['mandi_id'].nunique())


def compute_lag_correlations(df: pd.DataFrame, max_lag: int = 14) -> pd.DataFrame:
    """
    Compute Pearson correlation between rain at t-N and arrivals at t, for N in 0..max_lag.
    Expects df with columns: date, avg_rain_mm, total_arrival_quintals.
    """
    if df.empty:
        return pd.DataFrame({'lag': [], 'correlation': []})
    df = df.copy().sort_values('date')
    results = []
    arrivals = df['total_arrival_quintals'].values
    rain = df['avg_rain_mm'].values
    for lag in range(0, max_lag + 1):
        if lag == 0:
            corr = pd.Series(rain).corr(pd.Series(arrivals))
        else:
            lagged_rain = rain[:-lag]
            curr_arrivals = arrivals[lag:]
            corr = pd.Series(lagged_rain).corr(pd.Series(curr_arrivals))
        results.append({'lag': lag, 'correlation': round(float(corr) if not np.isnan(corr) else 0.0, 3)})
    return pd.DataFrame(results)


def compute_glut_flags(df: pd.DataFrame, price_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Glut = arrivals > 1.5x 30-day rolling mean AND price below MSP.
    df must have: date, crop, total_arrival_quintals.
    Returns df with 'is_glut' column.
    """
    if df.empty:
        return df
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    df['rolling_mean_30'] = df.groupby('crop')['total_arrival_quintals'].transform(
        lambda x: x.rolling(30, min_periods=5).mean()
    )
    df['is_supply_spike'] = df['total_arrival_quintals'] > (1.5 * df['rolling_mean_30'])
    df['is_glut'] = False
    if price_df is not None and not price_df.empty:
        price_df['date'] = pd.to_datetime(price_df['date'])
        crash_dates = set(
            price_df[price_df['modal_price'] < price_df['msp']].apply(
                lambda row: f"{row['date']}_{row['crop']}", axis=1
            )
        )
        df['is_glut'] = df.apply(
            lambda row: row['is_supply_spike'] and f"{row['date']}_{row['crop']}" in crash_dates, axis=1
        )
    else:
        df['is_glut'] = df['is_supply_spike']
    return df
