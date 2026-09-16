import pandas as pd
import numpy as np
import os
import json
from src.cleaning.cleaners import (
    normalize_mandi_id, standardize_crop_name, convert_to_quintals,
    clean_price, standardize_date, convert_temp_celsius, convert_rain_mm,
    convert_distance_km, clean_vehicle_no
)

def build_crop_mapping(df_arrivals, df_prices):
    # Get unique crop names
    raw_crops = set(df_arrivals['crop_name'].dropna().unique()) | set(df_prices['crop_name'].dropna().unique())
    raw_crops = [str(c) for c in raw_crops]
    
    mapping = {}
    # A canonical mapping dictionary based on the data profile
    # Known canonicals
    canonicals = {
        'wheat': ['गेहूं', 'gehun', 'kanak', 'wheat', 'gehun'],
        'maize': ['maize', 'corn', 'मक्का', 'makka', 'makki'],
        'sugarcane': ['sugarcane', 'ganne', 'ganna', 'गन्ना'],
        'cotton': ['cotton', 'kapas', 'कपास', 'narma'],
        'mustard': ['mustard', 'sarso', 'sarson', 'सरसों'],
        'rice': ['rice', 'basmati', 'paddy', 'chawal', 'धान', 'dhaan', 'चावल']
    }
    
    for raw in raw_crops:
        clean_raw = raw.strip().lower()
        matched = False
        for canon, variants in canonicals.items():
            if clean_raw in variants:
                mapping[clean_raw] = canon.capitalize()
                matched = True
                break
        if not matched:
            mapping[clean_raw] = raw.strip().capitalize()
            
    return mapping

def run_etl_pipeline(raw_dir, processed_dir, reports_dir):
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)
    
    dq_stats = []

    print("Loading raw data...")
    df_mandi = pd.read_csv(os.path.join(raw_dir, "track3_mandi_master.csv"))
    df_arr = pd.read_csv(os.path.join(raw_dir, "track3_mandi_arrivals.csv"))
    with open(os.path.join(raw_dir, "track3_price_and_msp.json"), 'r', encoding='utf-8') as f:
        df_price = pd.DataFrame(json.load(f))
    df_weather = pd.read_excel(os.path.join(raw_dir, "track3_weather_sensors.xlsx"), sheet_name="sensor_logs")
    df_trans = pd.read_csv(os.path.join(raw_dir, "track3_transport_logistics.csv"))
    
    # 1. Mandi Master
    print("Processing Mandi Master...")
    dq_stats.append({"Dataset": "mandi_master", "Raw rows": len(df_mandi), "Missing values": df_mandi.isnull().sum().sum(), "Duplicate rows": df_mandi.duplicated().sum()})
    df_mandi.drop_duplicates(inplace=True)
    df_mandi['mandi_id'] = df_mandi['mandi_id'].apply(normalize_mandi_id)
    df_mandi.dropna(subset=['mandi_id'], inplace=True)
    df_mandi['mandi_type'] = df_mandi['mandi_type'].str.upper()
    df_mandi.to_csv(os.path.join(processed_dir, "mandi_master.csv"), index=False)
    
    # Crop mapping
    crop_mapping = build_crop_mapping(df_arr, df_price)
    pd.DataFrame(list(crop_mapping.items()), columns=['raw_crop_name', 'canonical_crop_name']).to_csv(
        os.path.join(processed_dir, "crop_mapping.csv"), index=False
    )
    
    # 2. Mandi Arrivals
    print("Processing Mandi Arrivals...")
    dq_stats.append({"Dataset": "mandi_arrivals", "Raw rows": len(df_arr), "Missing values": df_arr.isnull().sum().sum(), "Duplicate rows": df_arr.duplicated().sum()})
    df_arr.drop_duplicates(inplace=True)
    df_arr['mandi_id'] = df_arr['mandi_id'].apply(normalize_mandi_id)
    df_arr['crop_name_clean'] = df_arr['crop_name'].apply(lambda x: standardize_crop_name(x, crop_mapping))
    df_arr['date_clean'] = df_arr['date'].apply(standardize_date)
    df_arr['quantity_quintals'] = df_arr.apply(lambda row: convert_to_quintals(row['arrival_quantity'], row['unit']), axis=1)
    
    # Drop rows without valid keys or quantity
    df_arr.dropna(subset=['mandi_id', 'date_clean', 'quantity_quintals'], inplace=True)
    df_arr.to_csv(os.path.join(processed_dir, "mandi_arrivals.csv"), index=False)
    
    # 3. Price & MSP
    print("Processing Price & MSP...")
    dq_stats.append({"Dataset": "price_and_msp", "Raw rows": len(df_price), "Missing values": df_price.isnull().sum().sum(), "Duplicate rows": df_price.duplicated().sum()})
    df_price.drop_duplicates(inplace=True)
    df_price['mandi_id'] = df_price['mandi_id'].apply(normalize_mandi_id)
    df_price['crop_name_clean'] = df_price['crop_name'].apply(lambda x: standardize_crop_name(x, crop_mapping))
    df_price['date_clean'] = df_price['date'].apply(standardize_date)
    
    df_price['min_price_clean'] = df_price['min_price'].apply(clean_price)
    df_price['max_price_clean'] = df_price['max_price'].apply(clean_price)
    df_price['modal_price_clean'] = df_price['modal_price'].apply(clean_price)
    df_price['msp_clean'] = df_price['msp'].apply(clean_price)
    
    df_price.dropna(subset=['date_clean', 'modal_price_clean'], inplace=True)
    df_price.to_csv(os.path.join(processed_dir, "price_and_msp.csv"), index=False)
    
    # 4. Weather Sensors
    print("Processing Weather Sensors...")
    dq_stats.append({"Dataset": "weather_sensors", "Raw rows": len(df_weather), "Missing values": df_weather.isnull().sum().sum(), "Duplicate rows": df_weather.duplicated().sum()})
    df_weather.drop_duplicates(inplace=True)
    df_weather['timestamp_clean'] = pd.to_datetime(df_weather['timestamp'].str.replace(' IST', '').str.replace(' UTC', ''), errors='coerce')
    # Actually need timezone handling for UTC -> IST
    def parse_and_convert_tz(ts_str):
        if pd.isna(ts_str): return pd.NaT
        ts_str = str(ts_str)
        try:
            if 'UTC' in ts_str:
                dt = pd.to_datetime(ts_str.replace(' UTC', ''))
                return dt + pd.Timedelta(hours=5, minutes=30)
            elif 'IST' in ts_str:
                return pd.to_datetime(ts_str.replace(' IST', ''))
            else:
                return pd.to_datetime(ts_str)
        except:
            return pd.NaT
            
    df_weather['timestamp_ist'] = df_weather['timestamp'].apply(parse_and_convert_tz)
    df_weather['date_clean'] = df_weather['timestamp_ist'].dt.date
    df_weather['temp_celsius'] = df_weather.apply(lambda row: convert_temp_celsius(row['temperature'], row['temp_unit']), axis=1)
    df_weather['rain_mm'] = df_weather.apply(lambda row: convert_rain_mm(row['rainfall'], row['rain_unit']), axis=1)
    
    df_weather.dropna(subset=['timestamp_ist'], inplace=True)
    df_weather.to_csv(os.path.join(processed_dir, "weather_sensors.csv"), index=False)
    
    # 5. Transport Logistics
    print("Processing Transport Logistics...")
    dq_stats.append({"Dataset": "transport_logistics", "Raw rows": len(df_trans), "Missing values": df_trans.isnull().sum().sum(), "Duplicate rows": df_trans.duplicated().sum()})
    df_trans.drop_duplicates(subset=['trip_id'], keep='first', inplace=True)
    df_trans['mandi_id'] = df_trans['mandi_id'].apply(normalize_mandi_id)
    df_trans['distance_km'] = df_trans.apply(lambda row: convert_distance_km(row['distance'], row['distance_unit']), axis=1)
    df_trans['vehicle_no_clean'] = df_trans['vehicle_no'].apply(clean_vehicle_no)
    
    df_trans['departure_time_clean'] = pd.to_datetime(df_trans['departure_time'], errors='coerce')
    df_trans['arrival_time_clean'] = pd.to_datetime(df_trans['arrival_time'], errors='coerce')
    df_trans['transit_hours'] = pd.to_numeric(df_trans['transit_hours'], errors='coerce')
    
    # Transport Exceptions
    invalid_mask = (df_trans['transit_hours'] < 0) | (df_trans['arrival_time_clean'] < df_trans['departure_time_clean'])
    df_exceptions = df_trans[invalid_mask].copy()
    df_exceptions['reason'] = 'Negative transit time or arrival before departure'
    df_exceptions['recommended_action'] = 'Exclude from transit average KPIs'
    df_exceptions.to_csv(os.path.join(processed_dir, "transport_exceptions.csv"), index=False)
    
    # Clean transport
    df_trans_clean = df_trans[~invalid_mask].copy()
    df_trans_clean.to_csv(os.path.join(processed_dir, "transport_logistics.csv"), index=False)
    
    # Save Data Quality Report
    pd.DataFrame(dq_stats).to_csv(os.path.join(reports_dir, "data_quality_report.csv"), index=False)
    print("ETL complete!")

if __name__ == "__main__":
    run_etl_pipeline("data/raw", "data/processed", "reports")
