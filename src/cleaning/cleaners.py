import pandas as pd
import numpy as np
import re

def normalize_mandi_id(mandi_id):
    if pd.isna(mandi_id) or str(mandi_id).strip() == '':
        return np.nan
    mandi_id = str(mandi_id).strip().upper()
    mandi_id = re.sub(r'[^A-Z0-9]', '', mandi_id)
    if mandi_id.startswith('MANDI'):
        return mandi_id
    elif mandi_id.startswith('M'):
        return 'MANDI' + mandi_id[1:].zfill(3)
    elif mandi_id.isdigit():
        return 'MANDI' + mandi_id.zfill(3)
    return mandi_id

def standardize_crop_name(crop, crop_mapping_dict):
    if pd.isna(crop) or str(crop).strip() == '':
        return np.nan
    crop_clean = str(crop).strip().lower()
    return crop_mapping_dict.get(crop_clean, str(crop).strip())

def convert_to_quintals(quantity, unit):
    if pd.isna(quantity):
        return np.nan
    
    quantity = pd.to_numeric(quantity, errors='coerce')
    if pd.isna(quantity):
        return np.nan
        
    unit = str(unit).strip().lower()
    if unit in ['qtl', 'q', 'quintal', 'quintals']:
        return quantity
    elif unit in ['kg', 'kgs', 'kilo']:
        return quantity / 100.0
    elif unit in ['mt', 't', 'tonnes', 'tonne']:
        return quantity * 10.0
    
    # If unit is missing but we have a valid quantity, we might have to reject it or assume.
    # The requirement says "Convert all arrival quantities into Quintals".
    return np.nan

def clean_price(price_str):
    if pd.isna(price_str) or str(price_str).strip() == '':
        return np.nan
    price_str = str(price_str).strip()
    # Strip currency labels like Rs., INR, ₹, and trailing /- or whitespace
    price_str = re.sub(r'(?i)\b(rs|inr)\b\.?', '', price_str)
    price_str = re.sub(r'[₹/,\s-]', '', price_str)
    
    clean_str = re.sub(r'[^\d.]', '', price_str)
    
    # Check for multiple decimals
    parts = clean_str.split('.')
    if len(parts) > 2:
        clean_str = ''.join(parts[:-1]) + '.' + parts[-1]
        
    try:
        return float(clean_str)
    except:
        return np.nan

def standardize_date(date_str):
    if pd.isna(date_str) or str(date_str).strip() == '':
        return pd.NaT
    try:
        return pd.to_datetime(date_str, format='mixed', dayfirst=True)
    except:
        return pd.NaT
        
def convert_temp_celsius(temp, unit):
    if pd.isna(temp):
        return np.nan
    unit = str(unit).strip().lower()
    if unit in ['f', '°f', 'fahrenheit']:
        return (temp - 32) * 5.0 / 9.0
    return temp

def convert_rain_mm(rain, unit):
    if pd.isna(rain):
        return np.nan
    unit = str(unit).strip().lower()
    if unit in ['inches', 'in', 'inch']:
        return rain * 25.4
    return rain

def convert_distance_km(distance, unit):
    if pd.isna(distance):
        return np.nan
    distance = pd.to_numeric(distance, errors='coerce')
    if pd.isna(distance):
        return np.nan
        
    unit = str(unit).strip().lower()
    if unit in ['miles', 'mile']:
        return distance * 1.60934
    return distance

def clean_vehicle_no(veh_no):
    if pd.isna(veh_no) or str(veh_no).strip() == '':
        return np.nan
    veh_no = str(veh_no).strip().upper()
    return re.sub(r'[^A-Z0-9]', '', veh_no)
