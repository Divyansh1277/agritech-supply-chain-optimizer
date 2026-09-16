# Data Dictionary

## mandi_master
| Column | Type | Description |
|---|---|---|
| mandi_id | TEXT | Standardized unique identifier for the Mandi (e.g., MANDI001). |
| mandi_name | TEXT | Name of the Mandi. |
| district | TEXT | District where the Mandi is located. |
| state | TEXT | State where the Mandi is located. |
| mandi_type | TEXT | Type of Mandi (e.g., APMC, Private). |
| total_area_acres | REAL | Area of the Mandi in acres. |

## crop_master
| Column | Type | Description |
|---|---|---|
| raw_crop_name | TEXT | Original messy name of the crop. |
| canonical_crop_name | TEXT | Standardized English name of the crop (e.g., Wheat). |

## mandi_arrivals
| Column | Type | Description |
|---|---|---|
| arrival_id | TEXT | Unique ID for the arrival record. |
| date_clean | TEXT | Standardized ISO date of arrival. |
| mandi_id | TEXT | Mandi identifier. |
| crop_name_clean | TEXT | Standardized canonical crop name. |
| variety | TEXT | Variety of the crop. |
| quantity_quintals | REAL | Standardized quantity arrived in Quintals. |

## price_msp
| Column | Type | Description |
|---|---|---|
| record_id | TEXT | Unique ID for the price record. |
| date_clean | TEXT | Standardized ISO date. |
| mandi_id | TEXT | Mandi identifier. |
| crop_name_clean | TEXT | Standardized canonical crop name. |
| modal_price_clean | REAL | Cleaned numeric modal wholesale price in INR. |
| msp_clean | REAL | Cleaned numeric Minimum Support Price in INR. |

## weather_daily
| Column | Type | Description |
|---|---|---|
| sensor_id | TEXT | Unique ID of the IoT weather sensor. |
| timestamp_ist | TEXT | Standardized ISO timestamp in IST (Indian Standard Time). |
| date_clean | TEXT | Date extracted from timestamp. |
| temp_celsius | REAL | Standardized temperature in Celsius. |
| rain_mm | REAL | Standardized rainfall in millimeters. |

## transport_logistics
| Column | Type | Description |
|---|---|---|
| trip_id | TEXT | Unique ID for the transport trip. |
| mandi_id | TEXT | Origin Mandi identifier. |
| destination_warehouse | TEXT | Destination warehouse name. |
| departure_time_clean | TEXT | Standardized departure timestamp. |
| arrival_time_clean | TEXT | Standardized arrival timestamp. |
| transit_hours | REAL | Number of transit hours. Invalid negative times dropped. |
| distance_km | REAL | Standardized distance in Kilometers. |
| vehicle_no_clean | TEXT | Standardized alphanumeric vehicle registration number. |
