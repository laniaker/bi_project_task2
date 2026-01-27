import pandas as pd
import json
from google.cloud import bigquery

# BigQuery Client initialisieren
PROJECT_ID = "taxi-bi-project"
try:
    bq_client = bigquery.Client(project=PROJECT_ID)
except Exception as e:
    print(f"Warnung: BigQuery Client konnte nicht initialisiert werden: {e}")
    bq_client = None

# --- KONFIGURATION DER TABELLEN ---
TABLE_FACT = "taxi-bi-project.dimensional.Fact_Trips"
TABLE_DIM_LOC = "taxi-bi-project.dimensional.dim_location"
TABLE_AGG_PEAK = "taxi-bi-project.aggregational.agg_peak_hours"


# ------------------------------------------------------------------------------
# HILFSFUNKTION FÜR MULTI-SELECT FILTER
# ------------------------------------------------------------------------------
def _build_sql_condition(field_name, value, is_string=True):
    """
    Erzeugt dynamisch die SQL WHERE-Bedingung für Multi-Select-Filter.
    """
    if not value: return "1=1"
    if not isinstance(value, list): value = [value]
    if "ALL" in value: return "1=1"
        
    if is_string:
        safe_values = [str(v).replace("'", "\\'") for v in value]
        val_str = "', '".join(safe_values)
        return f"{field_name} IN ('{val_str}')"
    else:
        val_str = ", ".join(str(v) for v in value)
        return f"{field_name} IN ({val_str})"


# ------------------------------------------------------------------------------
# DATEN-LADE-FUNKTIONEN
# ------------------------------------------------------------------------------

def get_filter_options():
    default_years = [2019, 2020, 2021, 2022, 2023]
    default_boroughs = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
    default_types = ["YELLOW", "GREEN", "FHV"]
    # NEU: Monate (1-12)
    default_months = list(range(1, 13))

    if not bq_client:
        return default_years, default_boroughs, default_types, default_months

    try:
        # Jahre
        sql_years = f"""
            SELECT DISTINCT EXTRACT(YEAR FROM pickup_datetime) as year 
            FROM `{TABLE_FACT}` 
            WHERE pickup_datetime IS NOT NULL ORDER BY year DESC
        """
        years = bq_client.query(sql_years).to_dataframe()['year'].dropna().astype(int).tolist()

        # Boroughs
        sql_boroughs = f"""
            SELECT DISTINCT borough FROM `{TABLE_DIM_LOC}` 
            WHERE borough NOT IN ('Unknown', 'NV') AND borough IS NOT NULL ORDER BY borough
        """
        boroughs = bq_client.query(sql_boroughs).to_dataframe()['borough'].tolist()

        # Typen
        sql_types = f"""
            SELECT DISTINCT source_system FROM `{TABLE_FACT}` 
            WHERE source_system IS NOT NULL ORDER BY source_system
        """
        types = bq_client.query(sql_types).to_dataframe()['source_system'].tolist()

        return years, boroughs, types, default_months
    except Exception as e:
        print(f"Fehler Filter-Optionen: {e}")
        return default_years, default_boroughs, default_types, default_months


def load_peak_hours(taxi_type="ALL", year=None, borough=None, month=None) -> pd.DataFrame:
    if not bq_client: return pd.DataFrame({"hour": list(range(24)), "trips": [0]*24})

    filters = ["1=1"]
    filters.append(_build_sql_condition("year", year, is_string=False))
    filters.append(_build_sql_condition("borough", borough, is_string=True))
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("month", month, is_string=False)) # NEU
    
    query = f"""
        SELECT hour, SUM(trip_count) as trips 
        FROM `{TABLE_AGG_PEAK}`
        WHERE {" AND ".join(filters)}
        GROUP BY hour
        ORDER BY hour
    """

    try:
        df = bq_client.query(query).to_dataframe()
        if not df.empty:
            df = df.set_index('hour').reindex(range(24), fill_value=0).reset_index().rename(columns={'index': 'hour'})
        else:
            return pd.DataFrame({"hour": list(range(24)), "trips": [0]*24})
        return df
    except Exception as e:
        return pd.DataFrame({"hour": list(range(24)), "trips": [0]*24})


def load_fares_by_borough(taxi_type="ALL", year=None, month=None) -> pd.DataFrame:
    if not bq_client: return pd.DataFrame()

    filters = ["1=1"]
    filters.append(_build_sql_condition("year", year, is_string=False))
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("month", month, is_string=False)) # NEU

    sql = f"""
        SELECT 
            borough,
            SAFE_DIVIDE(SUM(min_fare * trip_count), SUM(trip_count)) as min_fare,
            SAFE_DIVIDE(SUM(q1_fare * trip_count), SUM(trip_count)) as q1_fare,
            SAFE_DIVIDE(SUM(median_fare * trip_count), SUM(trip_count)) as median_fare,
            SAFE_DIVIDE(SUM(q3_fare * trip_count), SUM(trip_count)) as q3_fare,
            SAFE_DIVIDE(SUM(max_fare * trip_count), SUM(trip_count)) as max_fare
        FROM `taxi-bi-project.aggregational.agg_fare_stats`
        WHERE {" AND ".join(filters)}
        GROUP BY borough
        ORDER BY median_fare DESC
    """
    try:
        return bq_client.query(sql).to_dataframe()
    except Exception:
        return pd.DataFrame()


def load_tip_percentage(taxi_type="ALL", year=None, borough=None, month=None) -> pd.DataFrame:
    if not bq_client: return pd.DataFrame()
    
    filters = ["1=1"]
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("year", year, is_string=False))
    filters.append(_build_sql_condition("borough", borough, is_string=True))
    filters.append(_build_sql_condition("month", month, is_string=False)) # NEU

    group_col = "borough"
    order_clause = "avg_tip_pct DESC"

    sql = f"""
        SELECT 
            CAST({group_col} AS STRING) as bucket,
            SAFE_DIVIDE(SUM(total_tip), SUM(total_fare)) * 100 as avg_tip_pct
        FROM `taxi-bi-project.aggregational.agg_tip_stats`
        WHERE {" AND ".join(filters)}
        GROUP BY 1
        ORDER BY {order_clause}
    """
    try:
        return bq_client.query(sql).to_dataframe()
    except Exception:
        return pd.DataFrame()


def load_demand_over_years(taxi_type="ALL", borough=None, month=None) -> pd.DataFrame:
    if not bq_client: return pd.DataFrame()

    filters = ["1=1"]
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("borough", borough, is_string=True))
    filters.append(_build_sql_condition("month", month, is_string=False)) # NEU

    sql = f"""
        SELECT year, SUM(total_trips) as trips
        FROM `taxi-bi-project.aggregational.agg_demand_years`
        WHERE {" AND ".join(filters)}
        GROUP BY year ORDER BY year
    """
    try:
        return bq_client.query(sql).to_dataframe()
    except Exception:
        return pd.DataFrame()


# 1. Heatmap & Weekly Patterns (hatten wir schon, hier zur Sicherheit)
def load_weekly_patterns(taxi_type="ALL", year=None, borough=None, month=None):
    if not bq_client: return pd.DataFrame()
    filters = ["1=1"]
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("year", year, is_string=False))
    filters.append(_build_sql_condition("borough", borough, is_string=True))
    filters.append(_build_sql_condition("month", month, is_string=False)) # NEU
    
    sql = f"""
        SELECT day_name, day_of_week, hour, taxi_type, SUM(trip_count) as trips
        FROM `taxi-bi-project.aggregational.agg_weekly_patterns`
        WHERE {" AND ".join(filters)}
        GROUP BY 1, 2, 3, 4
        ORDER BY day_of_week, hour
    """
    try: return bq_client.query(sql).to_dataframe()
    except Exception: return pd.DataFrame()

# 2. Scatter Plot (Fare Distribution)
def load_agg_fare_dist(taxi_type="ALL", year=None, borough=None, month=None):
    if not bq_client: return pd.DataFrame()
    filters = ["1=1"]
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("year", year, is_string=False))
    filters.append(_build_sql_condition("borough", borough, is_string=True))
    filters.append(_build_sql_condition("month", month, is_string=False)) # JETZT AKTIVIEREN
    
    sql = f"""
        SELECT dist_bin as distance, fare_bin as fare, taxi_type, SUM(trip_count) as trips
        FROM `taxi-bi-project.aggregational.agg_fare_dist`
        WHERE {" AND ".join(filters)}
        GROUP BY 1, 2, 3
        HAVING trips > 10 
    """
    try: return bq_client.query(sql).to_dataframe()
    except Exception: return pd.DataFrame()


# 3. Borough Flows
def load_borough_flows(taxi_type="ALL", year=None, borough=None, month=None):
    if not bq_client: return pd.DataFrame()
    filters = ["1=1"]
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("year", year, is_string=False))
    filters.append(_build_sql_condition("pickup_borough", borough, is_string=True))
    filters.append(_build_sql_condition("month", month, is_string=False)) # NEU
    
    sql = f"""
        SELECT pickup_borough, dropoff_borough, SUM(trips) as trips
        FROM `taxi-bi-project.aggregational.agg_borough_flows`
        WHERE {" AND ".join(filters)}
        GROUP BY 1, 2
        ORDER BY trips DESC
    """
    try: return bq_client.query(sql).to_dataframe()
    except Exception: return pd.DataFrame()

# 4. Revenue Efficiency
def load_revenue_efficiency(taxi_type="ALL", year=None, borough=None, month=None):
    if not bq_client: return pd.DataFrame()
    filters = ["1=1"]
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("year", year, is_string=False))
    filters.append(_build_sql_condition("borough", borough, is_string=True))
    filters.append(_build_sql_condition("month", month, is_string=False)) # NEU
    
    sql = f"""
        SELECT 
            trip_category,
            SUM(total_trips) as trips,
            AVG(quantiles[OFFSET(0)]) as min_val,
            AVG(quantiles[OFFSET(1)]) as q1_val,
            AVG(quantiles[OFFSET(2)]) as median_val,
            AVG(quantiles[OFFSET(3)]) as q3_val,
            AVG(quantiles[OFFSET(4)]) as max_val
        FROM `taxi-bi-project.aggregational.agg_revenue_efficiency`
        WHERE {" AND ".join(filters)}
        GROUP BY 1 ORDER BY 1
    """
    try: return bq_client.query(sql).to_dataframe()
    except Exception: return pd.DataFrame()


def get_kpi_data(taxi_type="ALL", year=None, borough=None, month=None):
    if not bq_client: return 0, 0, 0, 0

    filters = ["1=1"]
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("year", year, is_string=False))
    filters.append(_build_sql_condition("borough", borough, is_string=True))
    # Achtung: agg_global_kpis bräuchte auch ein Update für Monate!
    # Wenn wir agg_kpis_main (Predefined) nehmen, sollte es gehen wenn wir es upgedatet haben.
    # Da wir agg_global_kpis nicht angefasst haben, lassen wir den Filter hier weg oder nehmen agg_monthly_kpis
    # Wir filtern hier vorerst NICHT nach Monat, um Crash zu vermeiden, bis die Tabelle aktualisiert ist.
    
    sql = f"""
        SELECT 
            SUM(total_trips) as trips,
            SUM(sum_total_amount) as revenue,
            SUM(sum_tip_card) as tip_amt,
            SUM(sum_fare_card) as fare_amt_card,
            SUM(outlier_count) as outliers
        FROM `taxi-bi-project.aggregational.agg_global_kpis`
        WHERE {" AND ".join(filters)}
    """
    try:
        df = bq_client.query(sql).to_dataframe()
        if df.empty or pd.isna(df['trips'][0]) or df['trips'][0] == 0:
            return 0, 0.0, 0.0, 0.0
        
        trips = df['trips'][0]
        revenue = df['revenue'][0]
        avg_fare = revenue / trips
        avg_tip_pct = (df['tip_amt'][0] / df['fare_amt_card'][0] * 100) if df['fare_amt_card'][0] > 0 else 0
        outlier_share = (df['outliers'][0] / trips * 100)
        
        return trips, avg_fare, avg_tip_pct, outlier_share
    except Exception:
        return 0, 0.0, 0.0, 0.0


def get_top_boroughs(taxi_type="ALL", year=None, month=None):
    if not bq_client: return []
    filters = ["borough != 'Unknown'"]
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("year", year, is_string=False))
    filters.append(_build_sql_condition("month", month, is_string=False)) # NEU (agg_demand_years hat Monat)

    sql = f"""
        SELECT borough as Borough, SUM(total_trips) as Trips
        FROM `taxi-bi-project.aggregational.agg_demand_years`
        WHERE {" AND ".join(filters)}
        GROUP BY 1 ORDER BY 2 DESC LIMIT 5
    """
    try:
        return bq_client.query(sql).to_dataframe().to_dict('records')
    except Exception:
        return []


def get_top_hours(taxi_type="ALL", year=None, borough=None, month=None):
    if not bq_client: return []
    filters = ["1=1"]
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("year", year, is_string=False))
    filters.append(_build_sql_condition("borough", borough, is_string=True))
    filters.append(_build_sql_condition("month", month, is_string=False)) # NEU (agg_peak_hours hat Monat)

    sql = f"""
        SELECT hour as Hour, SUM(trip_count) as Trips
        FROM `taxi-bi-project.aggregational.agg_peak_hours`
        WHERE {" AND ".join(filters)}
        GROUP BY 1 ORDER BY 2 DESC LIMIT 5
    """
    try:
        return bq_client.query(sql).to_dataframe().to_dict('records')
    except Exception:
        return []


def load_trips_and_geometries(taxi_type="ALL", year=None, borough=None, month=None):
    if not bq_client: return pd.DataFrame(), {}
    
    filters = ["1=1"]
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("year", year, is_string=False))
    filters.append(_build_sql_condition("borough", borough, is_string=True))
    filters.append(_build_sql_condition("month", month, is_string=False)) # NEU
    
    # Wir summieren trip_count für die gefilterte Auswahl.
    # geojson_str ist im Group By, damit wir es pro Zone zurückbekommen.
    sql = f"""
        SELECT 
            location_id, 
            zone, 
            borough, 
            geojson_str, 
            SUM(trip_count) as trip_count,
            AVG(avg_amount) as avg_amount
        FROM `taxi-bi-project.aggregational.agg_location_map`
        WHERE {" AND ".join(filters)}
        GROUP BY 1, 2, 3, 4
    """
    try:
        df = bq_client.query(sql).to_dataframe()
        if df.empty: return df, {}
        
        # GeoJSON FeatureCollection bauen
        features = []
        for _, row in df.iterrows():
            if row['geojson_str']:
                # Wir parsen den String zurück zu JSON
                geom = json.loads(row['geojson_str'])
                features.append({
                    "type": "Feature",
                    "geometry": geom,
                    "id": str(row['location_id']), 
                    "properties": {
                        "zone": row['zone'], 
                        "borough": row['borough'],
                        "trips": row['trip_count'],
                        "avg_amount": row['avg_amount']
                    }
                })
        
        return df, {"type": "FeatureCollection", "features": features}
    except Exception as e:
        print(f"!!! FEHLER in load_trips_and_geometries: {e}") # <--- DAS HIER EINFÜGEN
        return pd.DataFrame(), {}


# 5. Quality Audit (Achtung: Hier Logik anpassen, da 'month' ein Datum war)
def load_quality_audit(taxi_type="ALL", year=None, month=None):
    if not bq_client: return pd.DataFrame()
    filters = ["1=1"]
    filters.append(_build_sql_condition("source_system", taxi_type, is_string=True))
    filters.append(_build_sql_condition("EXTRACT(YEAR FROM month)", year, is_string=False))
    # Filter für Monat hinzufügen (wir extrahieren den Monat aus dem Datum)
    filters.append(_build_sql_condition("EXTRACT(MONTH FROM month)", month, is_string=False)) 
    
    sql = f"""
        SELECT month, SUM(total_trips) as total_trips, SUM(gps_failures) as gps_failures, SUM(unknown_locations) as unknown_locations
        FROM `taxi-bi-project.aggregational.agg_quality_audit`
        WHERE {" AND ".join(filters)}
        GROUP BY 1 ORDER BY 1
    """
    try: return bq_client.query(sql).to_dataframe()
    except Exception: return pd.DataFrame()


# 6. Airport Sunburst
def load_airport_sunburst_data(taxi_type="ALL", year=None, month=None):
    if not bq_client: return pd.DataFrame()
    filters = ["1=1"]
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("year", year, is_string=False))
    filters.append(_build_sql_condition("month", month, is_string=False))

    query = f"""
        SELECT 
            airport, direction, connected_borough,
            SUM(total_revenue) as total_revenue,
            SUM(total_trips) as total_trips,
            SUM(total_tip) as total_tip,
            SUM(total_fare_all) as total_fare_all,
            SUM(total_fare_card) as total_fare_card
        FROM `taxi-bi-project.aggregational.agg_airport_connectivity`
        WHERE {" AND ".join(filters)} AND connected_borough != 'Unknown'
        GROUP BY 1, 2, 3
        HAVING total_revenue > 1000 
    """
    try:
        return bq_client.query(query).to_dataframe()
    except Exception as e:
        print(f"!!! FEHLER in load_airport_sunburst_data: {e}")  # <-- Zeigt  den Fehler im Terminal
        return pd.DataFrame()
    
def load_tip_distribution(taxi_type="ALL", year=None, borough=None, month=None):
    if not bq_client: return pd.DataFrame()

    filters = ["1=1"]
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("year", year, is_string=False))
    filters.append(_build_sql_condition("borough", borough, is_string=True))
    filters.append(_build_sql_condition("month", month, is_string=False)) 

    sql = f"""
        SELECT tip_bin, bin_order, SUM(trip_count) as trips
        FROM `taxi-bi-project.aggregational.agg_tip_distribution`
        WHERE {" AND ".join(filters)}
        GROUP BY 1, 2
        ORDER BY bin_order
    """
    try:
        return bq_client.query(sql).to_dataframe()
    except Exception:
        return pd.DataFrame()

def load_top_tipping_zones(taxi_type="ALL", year=None, borough=None, month=None):
    if not bq_client: return []

    filters = ["1=1"]
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("year", year, is_string=False))
    filters.append(_build_sql_condition("borough", borough, is_string=True))
    filters.append(_build_sql_condition("month", month, is_string=False)) 

    sql = f"""
        SELECT zone, SUM(trips) as total_trips, 
               SAFE_DIVIDE(SUM(avg_tip_pct * trips), SUM(trips)) as weighted_tip_pct
        FROM `taxi-bi-project.aggregational.agg_tip_zone_ranking`
        WHERE {" AND ".join(filters)}
        GROUP BY 1
        HAVING total_trips > 500
        ORDER BY weighted_tip_pct DESC
        LIMIT 10
    """
    try:
        return bq_client.query(sql).to_dataframe().to_dict('records')
    except Exception:
        return []

def load_top_routes(taxi_type="ALL", year=None, borough=None, month=None):
    if not bq_client: return pd.DataFrame()

    filters = ["1=1"]
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("year", year, is_string=False))
    filters.append(_build_sql_condition("pickup_borough", borough, is_string=True))
    filters.append(_build_sql_condition("month", month, is_string=False)) 
    
    sql = f"""
        SELECT 
            pickup_borough, 
            dropoff_borough,
            SUM(total_revenue) as revenue,
            SUM(total_trips) as trips,
            SAFE_DIVIDE(SUM(total_revenue), SUM(total_trips)) as avg_fare
        FROM `taxi-bi-project.aggregational.agg_route_revenues`
        WHERE {" AND ".join(filters)}
        GROUP BY 1, 2
        ORDER BY revenue DESC
        LIMIT 10
    """
    try:
        return bq_client.query(sql).to_dataframe()
    except Exception:
        return pd.DataFrame()

def load_agg_dist_dist(taxi_type="ALL", year=None, borough=None):
    if not bq_client: return pd.DataFrame()
    filters = ["1=1"]
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("year", year, is_string=False))
    filters.append(_build_sql_condition("borough", borough, is_string=True))
    sql = f"""
        SELECT dist_bin, sort_order, SUM(trip_count) as trips
        FROM `taxi-bi-project.aggregational.agg_distance_distribution`
        WHERE {" AND ".join(filters)}
        GROUP BY 1, 2
        ORDER BY sort_order
    """
    try: return bq_client.query(sql).to_dataframe()
    except Exception: return pd.DataFrame()

def load_scatter_sample(taxi_type="ALL", year=None, borough=None, limit=2000):
    if not bq_client: return pd.DataFrame()
    filters = ["1=1"]
    filters.append(_build_sql_condition("source_system", taxi_type, is_string=True))
    filters.append(_build_sql_condition("EXTRACT(YEAR FROM pickup_datetime)", year, is_string=False))
    sql = f"""
        SELECT trip_distance, fare_amount, tip_amount, total_amount, source_system as taxi_type
        FROM `taxi-bi-project.dimensional.Fact_Trips`
        WHERE {" AND ".join(filters)} AND trip_distance > 0 AND fare_amount > 0 AND total_amount > 0 AND RAND() < 0.005
        LIMIT {limit}
    """
    try: return bq_client.query(sql).to_dataframe()
    except Exception: return pd.DataFrame()

def load_map_data(taxi_type="ALL", year=None):
    if not bq_client: return pd.DataFrame()
    filters = ["1=1"]
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("year", year, is_string=False))
    sql = f"""
        SELECT pickup_location_id, SUM(total_trips) as trips, AVG(avg_fare) as avg_fare
        FROM `taxi-bi-project.aggregational.agg_kpis_main` 
        WHERE {" AND ".join(filters)} GROUP BY 1
    """
    try: return bq_client.query(sql).to_dataframe()
    except Exception: return pd.DataFrame()

def load_seasonality_data(taxi_type="ALL", borough=None, year=None):
    if not bq_client: return pd.DataFrame()
    filters = ["1=1"]
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("borough", borough, is_string=True))
    filters.append(_build_sql_condition("year", year, is_string=False))
    sql = f"""
        SELECT year, month, month_name, SUM(total_trips) as trips
        FROM `taxi-bi-project.aggregational.agg_seasonality_borough`
        WHERE {" AND ".join(filters)}
        GROUP BY 1, 2, 3 ORDER BY year, month
    """
    try: return bq_client.query(sql).to_dataframe()
    except Exception: return pd.DataFrame()

def load_market_share_trend(taxi_type="ALL", year=None, borough=None, month=None):
    """ 
    Lädt Daten für Marktanteile (Taxi War).
    UPDATE: Lädt jetzt auf MONATS-Ebene, damit auch bei Auswahl eines einzelnen 
    Jahres ein Verlauf (Jan-Dez) sichtbar ist.
    """
    if not bq_client: return pd.DataFrame()

    filters = ["1=1"]
    filters.append(_build_sql_condition("taxi_type", taxi_type, is_string=True))
    filters.append(_build_sql_condition("borough", borough, is_string=True))
    filters.append(_build_sql_condition("year", year, is_string=False))
    filters.append(_build_sql_condition("month", month, is_string=False))
    
    sql = f"""
        SELECT year, month, taxi_type, SUM(total_trips) as trips
        FROM `taxi-bi-project.aggregational.agg_seasonality_borough`
        WHERE {" AND ".join(filters)}
        GROUP BY 1, 2, 3
        ORDER BY year, month
    """
    try:
        return bq_client.query(sql).to_dataframe()
    except Exception:
        return pd.DataFrame()