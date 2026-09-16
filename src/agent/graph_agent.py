import sqlite3
import pandas as pd
import plotly.express as px
import re

DB_PATH = "data/processed/agritech.db"
ACCENT = "#2E8B57"
WARNING = "#DC143C"


def run_agent_query(user_query: str) -> dict:
    """
    Intelligent graph-first NL agent query executor for AgriTech Supply Chain.
    Extracts intent, entities, executes optimized read-only SQL, and produces Plotly figures & summaries.
    """
    query_lower = user_query.lower()

    result = {
        "intent": "Unknown",
        "entities": {},
        "sql": "",
        "summary": "I'm sorry, I couldn't understand that query. Please try one of the example queries above."
    }

    conn = sqlite3.connect(DB_PATH)

    try:
        # Preset 1: Wheat trend in Amritsar
        if ("arrival" in query_lower or "trend" in query_lower or "price" in query_lower) and "wheat" in query_lower and "amritsar" in query_lower:
            result["intent"] = "Price vs MSP Trend Analysis"
            result["entities"] = {"Crop": "Wheat", "Location": "Amritsar (District / Mandis)", "Timespan": "Last 30 records"}
            result["sql"] = """SELECT p.date_clean AS date, m.mandi_name, m.district,
       p.modal_price_clean AS modal_price, p.msp_clean AS msp
FROM price_msp p
JOIN mandi_master m ON p.mandi_id = m.mandi_id
WHERE p.crop_name_clean = 'Wheat' AND (m.mandi_name LIKE '%Amritsar%' OR m.district LIKE '%Amritsar%')
ORDER BY p.date_clean DESC LIMIT 30;"""
            df = pd.read_sql(result["sql"], conn)
            if not df.empty:
                df = df.sort_values("date")
                fig = px.line(df, x="date", y=["modal_price", "msp"],
                              title="Wheat Modal Price vs MSP in Amritsar District Mandis (Last 30 Records)",
                              labels={"value": "Price (₹/Qtl)", "date": "Date", "variable": "Metric"},
                              color_discrete_map={"modal_price": ACCENT, "msp": WARNING})
                result["chart"] = fig
                avg_modal = df["modal_price"].mean()
                avg_msp = df["msp"].mean()
                gap = avg_modal - avg_msp
                status = f"crashing below MSP by an average of ₹{abs(gap):.0f}/Qtl" if gap < 0 else f"trading above MSP by ₹{gap:.0f}/Qtl"
                result["summary"] = (
                    f"In Amritsar district mandis for Wheat, average modal price was ₹{avg_modal:,.0f}/Qtl compared to "
                    f"an MSP of ₹{avg_msp:,.0f}/Qtl ({status}). Mandis covered: {', '.join(df['mandi_name'].unique())}."
                )

        # Preset 2: Total arrivals by crop type
        elif ("arrival" in query_lower or "volume" in query_lower) and ("by crop" in query_lower or "crop type" in query_lower):
            result["intent"] = "Aggregate Arrivals by Crop"
            result["entities"] = {"Metric": "total_arrival_quintals", "Group By": "crop"}
            result["sql"] = """SELECT crop, ROUND(SUM(total_arrival_quintals), 0) AS total_arrivals_qtl,
       COUNT(DISTINCT mandi_name) AS mandi_count
FROM vw_daily_arrivals
GROUP BY crop
ORDER BY total_arrivals_qtl DESC;"""
            df = pd.read_sql(result["sql"], conn)
            if not df.empty:
                fig = px.bar(df, x="crop", y="total_arrivals_qtl",
                             title="Total Crop Arrivals (Quintals)",
                             labels={"total_arrivals_qtl": "Total Arrivals (Qtl)", "crop": "Crop"},
                             color="total_arrivals_qtl",
                             color_continuous_scale="Viridis")
                fig.update_layout(coloraxis_showscale=False)
                result["chart"] = fig
                top_crop = df.iloc[0]["crop"]
                top_vol = df.iloc[0]["total_arrivals_qtl"]
                result["summary"] = (
                    f"The crop with the highest cumulative arrival volume is **{top_crop}** with "
                    f"{top_vol:,.0f} Quintals recorded across {int(df.iloc[0]['mandi_count'])} mandis."
                )

        # Preset 3: Mandi with highest transit delay
        elif "delay" in query_lower or ("mandi" in query_lower and "transit" in query_lower):
            result["intent"] = "Transit Delay Hotspot Analysis"
            result["entities"] = {"Metric": "is_delayed", "Group By": "mandi_name", "Min Trips": "10"}
            result["sql"] = """SELECT mandi_name, 
       COUNT(*) AS total_trips,
       ROUND(AVG(is_delayed) * 100, 1) AS delay_rate_pct,
       ROUND(AVG(transit_hours), 1) AS avg_transit_hours
FROM vw_transport_performance
GROUP BY mandi_name
HAVING total_trips >= 10
ORDER BY delay_rate_pct DESC
LIMIT 10;"""
            df = pd.read_sql(result["sql"], conn)
            if not df.empty:
                fig = px.bar(df, x="delay_rate_pct", y="mandi_name", orientation="h",
                             title="Top 10 Mandis by Transit Delay Rate (%)",
                             labels={"delay_rate_pct": "Delay Rate (%)", "mandi_name": "Mandi"},
                             color="delay_rate_pct",
                             color_continuous_scale=[[0, ACCENT], [1, WARNING]])
                fig.update_layout(coloraxis_showscale=False, yaxis={"categoryorder": "total ascending"})
                result["chart"] = fig
                worst = df.iloc[0]
                result["summary"] = (
                    f"**{worst['mandi_name']}** has the highest transit delay rate at **{worst['delay_rate_pct']}%** "
                    f"across {int(worst['total_trips'])} outbound trips (avg transit: {worst['avg_transit_hours']} hrs)."
                )

        # Preset 4: Rainfall comparison
        elif "rain" in query_lower or "weather" in query_lower:
            result["intent"] = "Rainfall & Weather Trend Analysis"
            result["entities"] = {"Metric": "rain_mm", "Period": "Last 90 days"}
            result["sql"] = """SELECT date_clean AS date,
       ROUND(AVG(rain_mm), 2) AS avg_rainfall_mm,
       ROUND(AVG(temp_celsius), 1) AS avg_temp_c
FROM weather_daily
GROUP BY date_clean
ORDER BY date_clean DESC
LIMIT 90;"""
            df = pd.read_sql(result["sql"], conn)
            if not df.empty:
                df = df.sort_values("date")
                fig = px.bar(df, x="date", y="avg_rainfall_mm",
                             title="Daily Rainfall (mm) — National Sensor Aggregate (Last 90 Days)",
                             labels={"avg_rainfall_mm": "Rainfall (mm)", "date": "Date"},
                             color_discrete_sequence=["#3B82F6"])
                result["chart"] = fig
                total_rain = df["avg_rainfall_mm"].sum()
                max_rain = df["avg_rainfall_mm"].max()
                max_date = df.loc[df["avg_rainfall_mm"].idxmax(), "date"]
                result["summary"] = (
                    f"*(Note: Sensor logs lack district mapping; aggregated nationally).* "
                    f"Total rainfall over the last 90 days was {total_rain:.1f} mm. "
                    f"The wettest day was {max_date} with {max_rain:.1f} mm."
                )

        # Preset 5: Price distribution for Rice (or other crops)
        elif "distribution" in query_lower or ("price" in query_lower and ("rice" in query_lower or "wheat" in query_lower or "maize" in query_lower)):
            target_crop = "Rice"
            for c in ["Rice", "Wheat", "Maize", "Cotton", "Sugarcane", "Mustard"]:
                if c.lower() in query_lower:
                    target_crop = c
                    break

            result["intent"] = f"Price Distribution Analysis for {target_crop}"
            result["entities"] = {"Crop": target_crop, "Metric": "modal_price"}
            result["sql"] = f"""SELECT modal_price, msp, date
FROM vw_price_vs_msp
WHERE crop = '{target_crop}' AND modal_price IS NOT NULL;"""
            df = pd.read_sql(result["sql"], conn)
            if not df.empty:
                fig = px.histogram(df, x="modal_price", nbins=35,
                                   title=f"Wholesale Modal Price Distribution for {target_crop} (₹/Qtl)",
                                   labels={"modal_price": "Modal Price (₹/Qtl)"},
                                   color_discrete_sequence=[ACCENT])
                if not df["msp"].isna().all():
                    msp_val = df["msp"].dropna().iloc[0]
                    fig.add_vline(x=msp_val, line_dash="dash", line_color=WARNING,
                                  annotation_text=f"MSP: ₹{msp_val:,.0f}")
                result["chart"] = fig
                p_min = df["modal_price"].min()
                p_max = df["modal_price"].max()
                p_mean = df["modal_price"].mean()
                result["summary"] = (
                    f"{target_crop} modal prices ranged from ₹{p_min:,.0f} to ₹{p_max:,.0f}/Qtl "
                    f"with an average of ₹{p_mean:,.0f}/Qtl."
                )

        # Preset 6: Warehouse volume
        elif "warehouse" in query_lower:
            result["intent"] = "Warehouse Inbound Volume"
            result["entities"] = {"Metric": "trip_count", "Group By": "destination_warehouse"}
            result["sql"] = """SELECT destination_warehouse,
       COUNT(*) AS trip_count,
       ROUND(AVG(transit_hours), 1) AS avg_transit_hours,
       ROUND(AVG(is_delayed) * 100, 1) AS delay_rate_pct
FROM vw_transport_performance
GROUP BY destination_warehouse
ORDER BY trip_count DESC;"""
            df = pd.read_sql(result["sql"], conn)
            if not df.empty:
                fig = px.bar(df, x="destination_warehouse", y="trip_count",
                             title="Inbound Trips by Destination Warehouse",
                             labels={"trip_count": "Number of Trips", "destination_warehouse": "Warehouse"},
                             color="avg_transit_hours",
                             color_continuous_scale="Blues")
                result["chart"] = fig
                top_wh = df.iloc[0]
                result["summary"] = (
                    f"**{top_wh['destination_warehouse']}** receives the highest logistical traffic with "
                    f"**{int(top_wh['trip_count'])}** inbound trips (avg transit: {top_wh['avg_transit_hours']} hrs, "
                    f"delay rate: {top_wh['delay_rate_pct']}%)."
                )

        # General NL fallback: Top mandis by arrival
        else:
            result["intent"] = "General Mandi Volume Overview"
            result["entities"] = {"Metric": "total_volume_quintals", "Source": "vw_mandi_summary"}
            result["sql"] = """SELECT mandi_name, state, district, total_volume_quintals
FROM vw_mandi_summary
ORDER BY total_volume_quintals DESC
LIMIT 10;"""
            df = pd.read_sql(result["sql"], conn)
            if not df.empty:
                fig = px.bar(df, x="total_volume_quintals", y="mandi_name", orientation="h",
                             title="Top Mandis by Total Volume (Quintals)",
                             labels={"total_volume_quintals": "Volume (Qtl)", "mandi_name": "Mandi"},
                             color_discrete_sequence=[ACCENT])
                fig.update_layout(yaxis={"categoryorder": "total ascending"})
                result["chart"] = fig
                result["summary"] = (
                    f"Displaying top mandis by volume based on your query '{user_query}'. "
                    f"Top mandi is {df.iloc[0]['mandi_name']} with {df.iloc[0]['total_volume_quintals']:,.0f} Qtl."
                )

    except Exception as e:
        result["summary"] = f"Error evaluating query: {str(e)}"
    finally:
        conn.close()

    return result
