import sqlite3
import pandas as pd
from typing import Dict, Any, List

DB_PATH = "data/processed/agritech.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def _build_where_clause(filters: Dict[str, Any]) -> tuple[str, list]:
    conditions = []
    params = []
    
    if filters.get('start_date'):
        conditions.append("date >= ?")
        params.append(filters['start_date'])
    if filters.get('end_date'):
        conditions.append("date <= ?")
        params.append(filters['end_date'])
        
    if filters.get('state'):
        # For parameterized IN clause
        placeholders = ','.join(['?'] * len(filters['state']))
        conditions.append(f"state IN ({placeholders})")
        params.extend(filters['state'])
        
    if filters.get('district'):
        placeholders = ','.join(['?'] * len(filters['district']))
        conditions.append(f"district IN ({placeholders})")
        params.extend(filters['district'])
        
    if filters.get('mandi'):
        placeholders = ','.join(['?'] * len(filters['mandi']))
        conditions.append(f"mandi_name IN ({placeholders})")
        params.extend(filters['mandi'])
        
    if filters.get('crop'):
        placeholders = ','.join(['?'] * len(filters['crop']))
        conditions.append(f"crop IN ({placeholders})")
        params.extend(filters['crop'])
        
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    return f"WHERE {where_clause}", params


def fetch_distress_base_data(filters: Dict[str, Any]) -> pd.DataFrame:
    """
    Fetches the base joined data for the Distress Sale Index computation.
    """
    # Build conditions based on the joined columns available
    conditions = []
    params = []
    
    if filters.get('start_date'):
        conditions.append("a.date_clean >= ?")
        params.append(filters['start_date'])
    if filters.get('end_date'):
        conditions.append("a.date_clean <= ?")
        params.append(filters['end_date'])
    if filters.get('state'):
        placeholders = ','.join(['?'] * len(filters['state']))
        conditions.append(f"m.state IN ({placeholders})")
        params.extend(filters['state'])
    if filters.get('district'):
        placeholders = ','.join(['?'] * len(filters['district']))
        conditions.append(f"m.district IN ({placeholders})")
        params.extend(filters['district'])
    if filters.get('mandi'):
        placeholders = ','.join(['?'] * len(filters['mandi']))
        conditions.append(f"m.mandi_name IN ({placeholders})")
        params.extend(filters['mandi'])
    if filters.get('crop'):
        placeholders = ','.join(['?'] * len(filters['crop']))
        conditions.append(f"a.crop_name_clean IN ({placeholders})")
        params.extend(filters['crop'])
        
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
    SELECT 
        a.date_clean AS date,
        a.mandi_id,
        m.mandi_name,
        m.district,
        m.state,
        a.crop_name_clean AS crop,
        a.quantity_quintals,
        p.modal_price_clean,
        p.msp_clean
    FROM mandi_arrivals a
    JOIN mandi_master m ON a.mandi_id = m.mandi_id
    LEFT JOIN price_msp p 
        ON a.date_clean = p.date_clean 
        AND a.crop_name_clean = p.crop_name_clean
        AND (
            a.mandi_id = p.mandi_id 
            OR (p.mandi_id IS NULL AND m.district = p.district)
        )
    WHERE p.modal_price_clean IS NOT NULL 
      AND p.msp_clean IS NOT NULL
      AND {where_clause}
    """
    conn = get_connection()
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

# Columns available per view — determines which filter params can be applied
_VIEW_COLUMNS = {
    "vw_daily_arrivals": {"date", "state", "district", "mandi_name", "crop"},
    "vw_price_vs_msp": {"date", "state", "mandi_name", "crop"},
    "vw_mandi_summary": {"state", "district", "mandi_name"},
    "vw_transport_performance": {"mandi_name"},
    "vw_weather_arrival": {"date", "district"},
}


def fetch_data(view_name: str, filters: Dict[str, Any]) -> pd.DataFrame:
    """Generic fetcher for pre-built views — only applies filters valid for that view."""
    available = _VIEW_COLUMNS.get(view_name, {"date", "state", "district", "mandi_name", "crop"})
    active_filters: Dict[str, Any] = {}
    if "date" in available:
        if filters.get("start_date"):
            active_filters["start_date"] = filters["start_date"]
        if filters.get("end_date"):
            active_filters["end_date"] = filters["end_date"]
    if "state" in available and filters.get("state"):
        active_filters["state"] = filters["state"]
    if "district" in available and filters.get("district"):
        active_filters["district"] = filters["district"]
    if "mandi_name" in available and filters.get("mandi"):
        active_filters["mandi"] = filters["mandi"]
    if "crop" in available and filters.get("crop"):
        active_filters["crop"] = filters["crop"]

    conditions, params = _build_where_clause(active_filters)
    query = f"SELECT * FROM {view_name} {conditions}"
    conn = get_connection()
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def fetch_filter_options() -> Dict[str, List]:
    """Fetch distinct states, districts, mandis, crops for filters."""
    conn = get_connection()
    df_mandi = pd.read_sql("SELECT DISTINCT state, district, mandi_name FROM mandi_master", conn)
    df_crop = pd.read_sql("SELECT DISTINCT crop_name_clean FROM mandi_arrivals", conn)
    conn.close()
    
    return {
        'master': df_mandi,
        'crops': sorted(df_crop['crop_name_clean'].dropna().unique().tolist())
    }

def get_max_date() -> str:
    """Get the maximum date across datasets for relative filtering."""
    conn = get_connection()
    max_date = pd.read_sql("SELECT MAX(date_clean) as max_date FROM mandi_arrivals", conn).iloc[0]['max_date']
    conn.close()
    return max_date
