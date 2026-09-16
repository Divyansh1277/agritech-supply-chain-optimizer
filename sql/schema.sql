-- schema.sql
-- SQLite Database Schema for AgriTech Supply Chain Optimizer

CREATE TABLE IF NOT EXISTS mandi_master (
    mandi_id TEXT PRIMARY KEY,
    mandi_name TEXT,
    district TEXT,
    state TEXT,
    mandi_type TEXT,
    total_area_acres REAL
);

CREATE TABLE IF NOT EXISTS crop_master (
    raw_crop_name TEXT PRIMARY KEY,
    canonical_crop_name TEXT
);

CREATE TABLE IF NOT EXISTS mandi_arrivals (
    arrival_id TEXT PRIMARY KEY,
    date TEXT,
    mandi_id TEXT,
    crop_name TEXT,
    variety TEXT,
    arrival_quantity REAL,
    unit TEXT,
    farmer_count REAL,
    crop_name_clean TEXT,
    date_clean TEXT,
    quantity_quintals REAL,
    FOREIGN KEY (mandi_id) REFERENCES mandi_master(mandi_id)
);

CREATE TABLE IF NOT EXISTS price_msp (
    record_id TEXT PRIMARY KEY,
    date TEXT,
    mandi_id TEXT,
    district TEXT,
    crop_name TEXT,
    min_price TEXT,
    max_price TEXT,
    modal_price TEXT,
    msp TEXT,
    crop_name_clean TEXT,
    date_clean TEXT,
    min_price_clean REAL,
    max_price_clean REAL,
    modal_price_clean REAL,
    msp_clean REAL,
    FOREIGN KEY (mandi_id) REFERENCES mandi_master(mandi_id)
);

CREATE TABLE IF NOT EXISTS weather_daily (
    sensor_id TEXT,
    timestamp TEXT,
    temperature REAL,
    temp_unit TEXT,
    rainfall REAL,
    rain_unit TEXT,
    humidity_percent REAL,
    timestamp_clean TEXT,
    timestamp_ist TEXT,
    date_clean TEXT,
    temp_celsius REAL,
    rain_mm REAL
);

CREATE TABLE IF NOT EXISTS transport_logistics (
    trip_id TEXT PRIMARY KEY,
    mandi_id TEXT,
    destination_warehouse TEXT,
    departure_time TEXT,
    arrival_time TEXT,
    transit_hours REAL,
    distance REAL,
    distance_unit TEXT,
    vehicle_no TEXT,
    driver_id TEXT,
    distance_km REAL,
    vehicle_no_clean TEXT,
    departure_time_clean TEXT,
    arrival_time_clean TEXT,
    FOREIGN KEY (mandi_id) REFERENCES mandi_master(mandi_id)
);
