-- views.sql
-- Analytics views for the Dashboard

-- 1. Daily Arrivals View
DROP VIEW IF EXISTS vw_daily_arrivals;
CREATE VIEW vw_daily_arrivals AS
SELECT 
    a.date_clean AS date,
    a.mandi_id,
    m.mandi_name,
    m.district,
    m.state,
    a.crop_name_clean AS crop,
    SUM(a.quantity_quintals) AS total_arrival_quintals
FROM mandi_arrivals a
JOIN mandi_master m ON a.mandi_id = m.mandi_id
GROUP BY a.date_clean, a.mandi_id, m.mandi_name, m.district, m.state, a.crop_name_clean;

-- 2. Price vs MSP View (Price Crash)
DROP VIEW IF EXISTS vw_price_vs_msp;
CREATE VIEW vw_price_vs_msp AS
SELECT 
    p.date_clean AS date,
    p.mandi_id,
    m.mandi_name,
    m.state,
    p.crop_name_clean AS crop,
    p.modal_price_clean AS modal_price,
    p.msp_clean AS msp,
    (p.modal_price_clean - p.msp_clean) AS msp_gap,
    CASE WHEN p.modal_price_clean < p.msp_clean THEN 1 ELSE 0 END AS is_price_crash
FROM price_msp p
JOIN mandi_master m ON p.mandi_id = m.mandi_id
WHERE p.modal_price_clean IS NOT NULL AND p.msp_clean IS NOT NULL;

-- 3. Mandi Summary
DROP VIEW IF EXISTS vw_mandi_summary;
CREATE VIEW vw_mandi_summary AS
SELECT 
    a.mandi_id,
    m.mandi_name,
    m.district,
    m.state,
    SUM(a.quantity_quintals) AS total_volume_quintals
FROM mandi_arrivals a
JOIN mandi_master m ON a.mandi_id = m.mandi_id
GROUP BY a.mandi_id, m.mandi_name, m.district, m.state;

-- 4. Transport Performance
DROP VIEW IF EXISTS vw_transport_performance;
CREATE VIEW vw_transport_performance AS
SELECT 
    t.trip_id,
    t.mandi_id,
    m.mandi_name,
    t.destination_warehouse,
    t.departure_time_clean,
    t.arrival_time_clean,
    t.transit_hours,
    t.distance_km,
    CASE WHEN t.transit_hours > (t.distance_km / 40.0) + 2 THEN 1 ELSE 0 END AS is_delayed
FROM transport_logistics t
JOIN mandi_master m ON t.mandi_id = m.mandi_id
WHERE t.transit_hours IS NOT NULL AND t.transit_hours >= 0;

-- 5. Weather & Arrival Correlation
DROP VIEW IF EXISTS vw_weather_arrival;
CREATE VIEW vw_weather_arrival AS
SELECT 
    a.date,
    a.district,
    a.total_arrival_quintals,
    AVG(w.rain_mm) AS avg_rain_mm,
    AVG(w.temp_celsius) AS avg_temp_celsius
FROM vw_daily_arrivals a
-- Map weather sensor implicitly via the date, ignoring exact spatial mapping as per dataset notes approximation
JOIN weather_daily w ON a.date = w.date_clean
GROUP BY a.date, a.district, a.total_arrival_quintals;
