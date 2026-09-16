import pytest
import pandas as pd
import numpy as np
from src.cleaning.cleaners import (
    normalize_mandi_id,
    convert_to_quintals,
    clean_price,
    convert_temp_celsius,
    convert_distance_km
)

def test_normalize_mandi_id():
    assert normalize_mandi_id('MANDI001') == 'MANDI001'
    assert normalize_mandi_id('MANDI-050') == 'MANDI050'
    assert normalize_mandi_id('mandi_057') == 'MANDI057'
    assert normalize_mandi_id('M031') == 'MANDI031'
    assert normalize_mandi_id('013') == 'MANDI013'
    assert pd.isna(normalize_mandi_id(np.nan))

def test_convert_to_quintals():
    assert convert_to_quintals(150, 'Qtl') == 150.0
    assert convert_to_quintals(100, 'KG') == 1.0
    assert convert_to_quintals(2.5, 'Tonnes') == 25.0
    assert pd.isna(convert_to_quintals(100, 'Unknown'))

def test_clean_price():
    assert clean_price('₹7,570.17') == 7570.17
    assert clean_price('Rs. 7,299') == 7299.0
    assert clean_price('INR 2,183') == 2183.0
    assert clean_price('5,878.62/-') == 5878.62
    assert pd.isna(clean_price(''))
    assert pd.isna(clean_price(np.nan))

def test_convert_temp_celsius():
    assert convert_temp_celsius(32, 'F') == 0.0
    assert convert_temp_celsius(212, 'Fahrenheit') == 100.0
    assert convert_temp_celsius(25.5, 'C') == 25.5
    assert convert_temp_celsius(25.5, 'Celsius') == 25.5

def test_convert_distance_km():
    assert convert_distance_km(100, 'km') == 100.0
    assert round(convert_distance_km(10, 'miles'), 2) == 16.09
    assert pd.isna(convert_distance_km('invalid', 'km'))
