import pandas as pd
import numpy as np
import pytest
import sys, os

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.visualization.kpis import (
    compute_total_arrivals,
    compute_distress_sale_index,
    compute_msp_gap_pct,
    compute_delay_rate,
    compute_avg_transit_time,
    compute_price_crash_instances,
    compute_farmers_served,
    compute_active_mandis,
)


@pytest.fixture
def sample_distress_df():
    """Known data: 3 rows. Row 1 and 2 are below MSP, row 3 is above."""
    return pd.DataFrame({
        "date": ["2026-01-01", "2026-01-02", "2026-01-03"],
        "mandi_id": ["MANDI001", "MANDI002", "MANDI003"],
        "crop": ["Wheat", "Wheat", "Rice"],
        "quantity_quintals": [100.0, 50.0, 200.0],  # Total = 350
        "modal_price_clean": [1800.0, 2000.0, 2500.0],
        "msp_clean": [2275.0, 2275.0, 2183.0],
    })


@pytest.fixture
def sample_arrivals_df():
    return pd.DataFrame({
        "date": ["2026-01-01", "2026-01-01", "2026-01-02"],
        "mandi_id": ["MANDI001", "MANDI002", "MANDI001"],
        "crop": ["Wheat", "Rice", "Wheat"],
        "quantity_quintals": [100.0, 200.0, 150.0],  # ← matches kpis.py
        "total_arrival_quintals": [100.0, 200.0, 150.0],
        "farmer_count": [10.0, 20.0, 15.0],
    })


@pytest.fixture
def sample_transport_df():
    return pd.DataFrame({
        "trip_id": ["T1", "T2", "T3", "T4"],
        "transit_hours": [5.0, 12.0, 8.0, -1.0],   # T4 invalid
        "distance_km": [150.0, 200.0, 100.0, 80.0],
        "is_delayed": [0, 1, 0, 0],
    })


# ── Test 1: Total Arrivals
def test_compute_total_arrivals(sample_arrivals_df):
    assert compute_total_arrivals(sample_arrivals_df) == pytest.approx(450.0)


def test_compute_total_arrivals_empty():
    assert compute_total_arrivals(pd.DataFrame()) == 0.0


# ── Test 2: Distress Sale Index (core quantity-weighted test)
def test_compute_distress_sale_index_weighted(sample_distress_df):
    """
    Manual check:
    Row 1: 100 Qtl @ 1800 < 2275 MSP → distress
    Row 2:  50 Qtl @ 2000 < 2275 MSP → distress
    Row 3: 200 Qtl @ 2500 > 2183 MSP → not distress
    Distress qty = 150, Total = 350
    DSI = 150/350 * 100 = 42.857...%
    """
    dsi = compute_distress_sale_index(sample_distress_df)
    assert dsi == pytest.approx(150 / 350 * 100, rel=1e-3)


def test_compute_distress_sale_index_zero_when_all_above():
    df = pd.DataFrame({
        "quantity_quintals": [100.0, 200.0],
        "modal_price_clean": [3000.0, 3500.0],
        "msp_clean": [2275.0, 2275.0],
    })
    assert compute_distress_sale_index(df) == pytest.approx(0.0)


def test_compute_distress_sale_index_100_when_all_below():
    df = pd.DataFrame({
        "quantity_quintals": [100.0, 200.0],
        "modal_price_clean": [1500.0, 1800.0],
        "msp_clean": [2275.0, 2275.0],
    })
    assert compute_distress_sale_index(df) == pytest.approx(100.0)


def test_compute_distress_sale_index_empty():
    assert compute_distress_sale_index(pd.DataFrame()) == 0.0


# ── Test 3: MSP Gap %
def test_compute_msp_gap_pct(sample_distress_df):
    """
    Gaps: (1800-2275)/2275, (2000-2275)/2275, (2500-2183)/2183
    = -0.2088..., -0.1209..., +0.1452...
    Avg = -0.0615... * 100 = -6.15...%
    """
    gap = compute_msp_gap_pct(sample_distress_df)
    expected = (
        ((1800 - 2275) / 2275 + (2000 - 2275) / 2275 + (2500 - 2183) / 2183) / 3 * 100
    )
    assert gap == pytest.approx(expected, rel=1e-3)


# ── Test 4: Delay Rate
def test_compute_delay_rate(sample_transport_df):
    """
    T1: 5 hrs, 150 km → threshold = 150/40 + 2 = 5.75 → NOT delayed
    T2: 12 hrs, 200 km → threshold = 200/40 + 2 = 7.0  → DELAYED
    T3: 8 hrs, 100 km  → threshold = 100/40 + 2 = 4.5  → DELAYED
    T4: -1 hrs → excluded
    Valid = 3 trips, delayed = 2 → rate = 66.67%
    """
    rate, total = compute_delay_rate(sample_transport_df)
    assert total == 3
    assert rate == pytest.approx(2 / 3 * 100, rel=1e-3)


# ── Test 5: Price Crash Instances
def test_compute_price_crash_instances(sample_distress_df):
    # Rows 1 and 2 are below MSP
    assert compute_price_crash_instances(sample_distress_df) == 2


# ── Test 6: Farmers Served
def test_compute_farmers_served(sample_arrivals_df):
    assert compute_farmers_served(sample_arrivals_df) == 45


# ── Test 7: Active Mandis
def test_compute_active_mandis(sample_arrivals_df):
    # MANDI001 and MANDI002
    assert compute_active_mandis(sample_arrivals_df) == 2


# ── Test 8: Avg Transit excludes negatives
def test_compute_avg_transit_time(sample_transport_df):
    # T1=5, T2=12, T3=8, T4=-1 excluded → avg(5,12,8) = 8.333...
    avg = compute_avg_transit_time(sample_transport_df)
    assert avg == pytest.approx((5 + 12 + 8) / 3, rel=1e-3)
