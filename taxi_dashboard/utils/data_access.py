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
# Wir definieren die Pfade zentral, damit man sie leicht ändern kann
TABLE_FACT = "taxi-bi-project.dimensional.Fact_Trips"
TABLE_DIM_LOC = "taxi-bi-project.dimensional.dim_location"
# NEU: Die Aggregationstabelle
TABLE_AGG_PEAK = "taxi-bi-project.aggregational.agg_peak_hours"


def get_filter_options():
    """
    Lädt dynamisch die verfügbaren Filter-Optionen.
    """
    default_years = [2019, 2020, 2021, 2022, 2023]
    default_boroughs = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
    default_types = ["YELLOW", "GREEN", "FHV"]

    if not bq_client:
        return default_years, default_boroughs, default_types

    try:
        # 1. Jahre holen
        sql_years = f"""
            SELECT DISTINCT EXTRACT(YEAR FROM pickup_datetime) as year 
            FROM `{TABLE_FACT}` 
            WHERE pickup_datetime IS NOT NULL
            ORDER BY year DESC
        """
        years = bq_client.query(sql_years).to_dataframe()['year'].dropna().astype(int).tolist()

        # 2. Boroughs holen
        sql_boroughs = f"""
            SELECT DISTINCT borough 
            FROM `{TABLE_DIM_LOC}` 
            WHERE borough IS NOT NULL AND borough != 'Unknown' AND borough != 'NV'
            ORDER BY borough
        """
        boroughs = bq_client.query(sql_boroughs).to_dataframe()['borough'].tolist()

        # 3. Taxi Types holen
        sql_types = f"""
            SELECT DISTINCT source_system 
            FROM `{TABLE_FACT}` 
            WHERE source_system IS NOT NULL
            ORDER BY source_system
        """
        types = bq_client.query(sql_types).to_dataframe()['source_system'].tolist()

        return years, boroughs, types

    except Exception as e:
        print(f"Fehler beim Laden der Filter: {e}")
        return default_years, default_boroughs, default_types


def load_peak_hours(taxi_type="ALL", year=None, borough=None) -> pd.DataFrame:
    """
    LÄDT DATEN FÜR DAS STUNDEN-HISTOGRAMM.
    
    Quelle: taxi-bi-project.aggregational.agg_peak_hours
    Vorteil: Extrem schnell, da vor-aggregiert.
    """
    # Fallback, falls DB nicht da ist
    if not bq_client:
        return pd.DataFrame({"hour": list(range(24)), "trips": [0]*24})

    # Basis-Query auf die Aggregationstabelle
    # Wir summieren den 'trip_count', da die Tabelle ja Gruppen enthält (z.B. Yellow + Manhattan + 2023)
    query = f"""
        SELECT 
            hour, 
            SUM(trip_count) as trips 
        FROM `{TABLE_AGG_PEAK}`
    """
    
    # Filter dynamisch aufbauen
    filters = ["1=1"] 
    
    if year:
        filters.append(f"year = {year}")
    
    if borough:
        filters.append(f"borough = '{borough}'")
        
    if taxi_type and taxi_type != "ALL":
        filters.append(f"taxi_type = '{taxi_type}'")

    where_clause = " AND ".join(filters)
    
    final_sql = f"""
        {query}
        WHERE {where_clause}
        GROUP BY hour
        ORDER BY hour
    """

    try:
        df = bq_client.query(final_sql).to_dataframe()
        
        # WICHTIG: Lücken füllen!
        # Wenn z.B. um 3 Uhr nachts gar keine Fahrt war, fehlt die Zeile im SQL-Ergebnis.
        # Das Diagramm braucht aber zwingend 0-23 auf der x-Achse.
        
        # Wir setzen 'hour' als Index
        if not df.empty:
            df = df.set_index('hour')
            
            # Erstellen einen vollständigen Index von 0 bis 23
            full_idx = range(24)
            
            # Reindex füllt fehlende Stunden mit 0 auf
            df = df.reindex(full_idx, fill_value=0).reset_index()
            
            # Index heißt jetzt 'index', wir benennen ihn zurück in 'hour'
            df.rename(columns={'index': 'hour'}, inplace=True)
        else:
            # Falls Filter gar keine Ergebnisse liefert -> Leeres Gerüst zurückgeben
            return pd.DataFrame({"hour": list(range(24)), "trips": [0]*24})
            
        return df

    except Exception as e:
        print(f"Fehler bei load_peak_hours: {e}")
        # Leeres DataFrame zurückgeben, damit Dashboard nicht abstürzt
        return pd.DataFrame({"hour": list(range(24)), "trips": [0]*24})


def load_fares_by_borough(taxi_type="ALL", year=None) -> pd.DataFrame:
    """
    LÄDT BOXPLOT-STATISTIKEN FÜR PREISE PRO BOROUGH.
    
    Quelle: taxi-bi-project.aggregational.agg_fare_stats
    
    WICHTIG:
    Wir nutzen IMMER eine Aggregation (GROUP BY borough).
    Grund: Selbst wenn ein Jahr gewählt ist, gibt es oft mehrere Einträge pro Borough 
    (z.B. Yellow vs. Green). Diese müssen wir zu einem einzigen Boxplot verschmelzen.
    """
    if not bq_client:
        return pd.DataFrame()

    TABLE_AGG_FARES = "taxi-bi-project.aggregational.agg_fare_stats"
    
    # 1. Filter bauen
    filters = ["1=1"]
    
    if year:
        filters.append(f"year = {year}")
        
    if taxi_type and taxi_type != "ALL":
        filters.append(f"taxi_type = '{taxi_type}'")
        
    where_clause = " AND ".join(filters)

    # 2. Query bauen (Einheitliche Logik für ALLE Fälle)
    # Wir berechnen den gewichteten Durchschnitt der Quantile basierend auf 'trip_count'.
    sql = f"""
        SELECT 
            borough,
            SAFE_DIVIDE(SUM(min_fare * trip_count), SUM(trip_count)) as min_fare,
            SAFE_DIVIDE(SUM(q1_fare * trip_count), SUM(trip_count)) as q1_fare,
            SAFE_DIVIDE(SUM(median_fare * trip_count), SUM(trip_count)) as median_fare,
            SAFE_DIVIDE(SUM(q3_fare * trip_count), SUM(trip_count)) as q3_fare,
            SAFE_DIVIDE(SUM(max_fare * trip_count), SUM(trip_count)) as max_fare
        FROM `{TABLE_AGG_FARES}`
        WHERE {where_clause}
        GROUP BY borough
        ORDER BY median_fare DESC
    """

    try:
        return bq_client.query(sql).to_dataframe()
    except Exception as e:
        print(f"Fehler bei load_fares_by_borough: {e}")
        return pd.DataFrame()

def load_tip_percentage(taxi_type="ALL", year=None, borough=None) -> pd.DataFrame:
    """
    LÄDT DURCHSCHNITTLICHES TRINKGELD (%).
    
    Quelle: taxi-bi-project.aggregational.agg_tip_stats
    Basis: Nur Kartenzahlungen (wurde bereits bei Tabellenerstellung gefiltert).
    
    Logik:
    Wir berechnen den gewichteten Durchschnitt:
    (Summe aller Tips) / (Summe aller Fahrpreise) * 100
    
    Dynamische Gruppierung:
    - Wenn ein Borough gewählt ist, zeigen wir den Vergleich über Jahre.
    - Wenn kein Borough gewählt ist, vergleichen wir die Boroughs miteinander.
    """
    if not bq_client:
        return pd.DataFrame()

    TABLE_AGG_TIPS = "taxi-bi-project.aggregational.agg_tip_stats"
    
    # 1. Filter
    filters = ["1=1"]
    if taxi_type and taxi_type != "ALL":
        filters.append(f"taxi_type = '{taxi_type}'")
    if year:
        filters.append(f"year = {year}")
    if borough:
        filters.append(f"borough = '{borough}'")
        
    where_clause = " AND ".join(filters)

    # 2. Dynamische Gruppierung (x-Achse)
    # Szenario A: Borough ist ausgewählt -> Wir zeigen den Zeitverlauf (Jahre)
    if borough:
        group_col = "year"
        bucket_label = "year" # Label für den Plot
        order_clause = "year"
        
    # Szenario B: Kein Borough gewählt -> Wir vergleichen die Boroughs
    else:
        group_col = "borough"
        bucket_label = "borough"
        order_clause = "avg_tip_pct DESC"

    # 3. Query
    sql = f"""
        SELECT 
            CAST({group_col} AS STRING) as bucket, -- String für saubere x-Achse
            
            -- Die Formel für den echten Durchschnitt:
            SAFE_DIVIDE(SUM(total_tip), SUM(total_fare)) * 100 as avg_tip_pct
            
        FROM `{TABLE_AGG_TIPS}`
        WHERE {where_clause}
        GROUP BY 1
        ORDER BY {order_clause}
    """

    try:
        df = bq_client.query(sql).to_dataframe()
        return df
    except Exception as e:
        print(f"Fehler bei load_tip_percentage: {e}")
        return pd.DataFrame()

def load_demand_over_years(taxi_type="ALL", borough=None) -> pd.DataFrame:
    """
    LÄDT JAHRES-TRENDS (Nachfrageentwicklung).
    
    Quelle: taxi-bi-project.aggregational.agg_demand_years
    Logik: Summiert die Fahrten pro Jahr basierend auf den gewählten Filtern.
    """
    if not bq_client:
        return pd.DataFrame()

    TABLE_AGG_DEMAND = "taxi-bi-project.aggregational.agg_demand_years"

    filters = ["1=1"]
    
    # Taxi Filter
    if taxi_type and taxi_type != "ALL":
        filters.append(f"taxi_type = '{taxi_type}'")
        
    # Borough Filter
    if borough:
        filters.append(f"borough = '{borough}'")

    where_clause = " AND ".join(filters)

    sql = f"""
        SELECT 
            year,
            SUM(total_trips) as trips
        FROM `{TABLE_AGG_DEMAND}`
        WHERE {where_clause}
        GROUP BY year
        ORDER BY year
    """

    try:
        return bq_client.query(sql).to_dataframe()
    except Exception as e:
        print(f"Fehler bei load_demand_over_years: {e}")
        return pd.DataFrame()

def load_weekly_patterns(taxi_type="ALL", year=None, borough=None):
    """
    Lädt Daten für Heatmap und Facet-Plots.
    Nutzt jetzt direkt die Spalten aus der neuen SQL-Tabelle (inkl. Sortier-Nummer).
    """
    if not bq_client: return pd.DataFrame()

    TABLE = "taxi-bi-project.aggregational.agg_weekly_patterns"
    
    filters = ["1=1"]
    if taxi_type and taxi_type != "ALL": filters.append(f"taxi_type = '{taxi_type}'")
    if year: filters.append(f"year = {year}")
    if borough: filters.append(f"borough = '{borough}'")
    
    where_clause = " AND ".join(filters)
    
    sql = f"""
        SELECT 
            day_name,
            day_of_week, 
            hour,
            taxi_type,
            SUM(trip_count) as trips
        FROM `{TABLE}`
        WHERE {where_clause}
        GROUP BY 1, 2, 3, 4
        ORDER BY day_of_week, hour
    """
    
    try:
        df = bq_client.query(sql).to_dataframe()
        return df
    except Exception as e:
        print(f"Fehler in load_weekly_patterns: {e}")
        return pd.DataFrame()

#def load_scatter_fare_distance(taxi_type="ALL", year=None, borough=None) -> pd.DataFrame:
#    return pd.DataFrame({"trip_distance": [], "fare_amount": []})

def load_agg_fare_dist(taxi_type="ALL", year=None, borough=None):
    """
    Lädt aggregierte Cluster-Daten für den Scatterplot.
    """
    if not bq_client: return pd.DataFrame()

    TABLE = "taxi-bi-project.aggregational.agg_fare_dist"
    
    filters = ["1=1"]
    if taxi_type and taxi_type != "ALL": filters.append(f"taxi_type = '{taxi_type}'")
    if year: filters.append(f"year = {year}")
    if borough: filters.append(f"borough = '{borough}'")
    
    where_clause = " AND ".join(filters)
    
    sql = f"""
        SELECT 
            dist_bin as distance,
            fare_bin as fare,
            taxi_type,
            SUM(trip_count) as trips
        FROM `{TABLE}`
        WHERE {where_clause}
        GROUP BY 1, 2, 3
        HAVING trips > 10 
    """
    
    try:
        df = bq_client.query(sql).to_dataframe()
        return df
    except Exception as e:
        print(f"Fehler in load_agg_fare_dist: {e}")
        return pd.DataFrame()

def load_borough_flows(taxi_type="ALL", year=None, borough=None):
    """
    Lädt Daten für die Flows (Pickup -> Dropoff).
    """
    if not bq_client: return pd.DataFrame()

    TABLE = "taxi-bi-project.aggregational.agg_borough_flows"
    
    filters = ["1=1"]
    if taxi_type and taxi_type != "ALL": filters.append(f"taxi_type = '{taxi_type}'")
    if year: filters.append(f"year = {year}")
    if borough: filters.append(f"pickup_borough = '{borough}'")
    
    where_clause = " AND ".join(filters)
    
    sql = f"""
        SELECT 
            pickup_borough,
            dropoff_borough,
            SUM(trips) as trips
        FROM `{TABLE}`
        WHERE {where_clause}
        GROUP BY 1, 2
        ORDER BY trips DESC
    """
    
    try:
        df = bq_client.query(sql).to_dataframe()
        return df
    except Exception as e:
        print(f"Fehler in load_borough_flows: {e}")
        return pd.DataFrame()

def load_revenue_efficiency(taxi_type="ALL", year=None, borough=None):
    """
    Lädt Boxplot-Statistiken (Duration Categories).
    """
    if not bq_client: return pd.DataFrame()

    TABLE = "taxi-bi-project.aggregational.agg_revenue_efficiency"
    
    filters = ["1=1"]
    if taxi_type and taxi_type != "ALL": filters.append(f"taxi_type = '{taxi_type}'")
    if year: filters.append(f"year = {year}")
    
    if borough: filters.append(f"borough = '{borough}'")
    
    where_clause = " AND ".join(filters)
    
    sql = f"""
        SELECT 
            trip_category,
            SUM(total_trips) as trips,
            
            -- Wir mitteln die Quantile der gefilterten Gruppen
            AVG(quantiles[OFFSET(0)]) as min_val,
            AVG(quantiles[OFFSET(1)]) as q1_val,
            AVG(quantiles[OFFSET(2)]) as median_val,
            AVG(quantiles[OFFSET(3)]) as q3_val,
            AVG(quantiles[OFFSET(4)]) as max_val
        FROM `{TABLE}`
        WHERE {where_clause}
        GROUP BY 1
        ORDER BY 1
    """
    
    try:
        df = bq_client.query(sql).to_dataframe()
        return df
    except Exception as e:
        print(f"Fehler in load_revenue_efficiency: {e}")
        return pd.DataFrame()

def get_kpi_data(taxi_type="ALL", year=None, borough=None):
    """
    Holt NUR die 4 KPIs für die obere Leiste.
    """
    if not bq_client:
        return 0, 0, 0, 0

    TABLE_KPI = "taxi-bi-project.aggregational.agg_global_kpis"
    
    filters = ["1=1"]
    if taxi_type and taxi_type != "ALL": filters.append(f"taxi_type = '{taxi_type}'")
    if year: filters.append(f"year = {year}")
    if borough: filters.append(f"borough = '{borough}'")
    where_clause = " AND ".join(filters)
    
    sql = f"""
        SELECT 
            SUM(total_trips) as trips,
            SUM(sum_total_amount) as revenue,
            SUM(sum_tip_card) as tip_amt,
            SUM(sum_fare_card) as fare_amt_card,
            SUM(outlier_count) as outliers
        FROM `{TABLE_KPI}`
        WHERE {where_clause}
    """
    
    try:
        df = bq_client.query(sql).to_dataframe()
        
        if df.empty or pd.isna(df['trips'][0]) or df['trips'][0] == 0:
            return 0, 0.0, 0.0, 0.0
            
        trips = df['trips'][0]
        revenue = df['revenue'][0]
        # Sicherstellen, dass wir nicht durch 0 teilen
        avg_fare = revenue / trips
        avg_tip_pct = (df['tip_amt'][0] / df['fare_amt_card'][0] * 100) if df['fare_amt_card'][0] > 0 else 0
        outlier_share = (df['outliers'][0] / trips * 100)
        
        return trips, avg_fare, avg_tip_pct, outlier_share
        
    except Exception as e:
        print(f"Fehler KPI: {e}")
        return 0, 0.0, 0.0, 0.0
    
def get_top_boroughs(taxi_type="ALL", year=None):
    """
    Liefert die Top 5 Boroughs nach Anzahl Fahrten.
    Quelle: agg_demand_years (sehr schnell).
    """
    if not bq_client: return []
    
    filters = ["1=1"]
    if taxi_type and taxi_type != "ALL": filters.append(f"taxi_type = '{taxi_type}'")
    if year: filters.append(f"year = {year}")
    # Wichtig: Wir schließen 'Unknown' aus, das interessiert das Management meist nicht
    filters.append("borough != 'Unknown'")
    
    where_clause = " AND ".join(filters)
    
    sql = f"""
        SELECT borough as Borough, SUM(total_trips) as Trips
        FROM `taxi-bi-project.aggregational.agg_demand_years`
        WHERE {where_clause}
        GROUP BY 1
        ORDER BY 2 DESC
        LIMIT 5
    """
    try:
        return bq_client.query(sql).to_dataframe().to_dict('records')
    except Exception as e:
        print(f"Fehler Top Boroughs: {e}")
        return []

def get_top_hours(taxi_type="ALL", year=None, borough=None):
    """
    Liefert die Top 5 Stunden nach Anzahl Fahrten.
    Quelle: agg_peak_hours.
    """
    if not bq_client: return []
    
    filters = ["1=1"]
    if taxi_type and taxi_type != "ALL": filters.append(f"taxi_type = '{taxi_type}'")
    if year: filters.append(f"year = {year}")
    if borough: filters.append(f"borough = '{borough}'")
    
    where_clause = " AND ".join(filters)
    
    sql = f"""
        SELECT hour as Hour, SUM(trip_count) as Trips
        FROM `taxi-bi-project.aggregational.agg_peak_hours`
        WHERE {where_clause}
        GROUP BY 1
        ORDER BY 2 DESC
        LIMIT 5
    """
    try:
        return bq_client.query(sql).to_dataframe().to_dict('records')
    except Exception as e:
        print(f"Fehler Top Hours: {e}")
        return []
    
def load_trips_and_geometries(taxi_type="ALL", year=None, borough=None):
    """
    Lädt aggregierte Trip-Daten und zugehörige Geometrien aus dem BigQuery-DWH.
    Konvertiert die Ergebnisse in ein Pandas DataFrame und ein valides GeoJSON-Format.
    """
    if not bq_client: 
        return pd.DataFrame(), {}

    # Zugriff auf die optimierte Aggregationstabelle
    TABLE = "taxi-bi-project.aggregational.agg_location_map"
    
    # Dynamischer Aufbau der SQL-Filterbedingungen basierend auf der Nutzerauswahl
    filters = ["1=1"]
    if taxi_type and taxi_type != "ALL": 
        filters.append(f"taxi_type = '{taxi_type}'")
    if year: 
        filters.append(f"year = {year}")
    if borough: 
        filters.append(f"borough = '{borough}'")
    
    where_clause = " AND ".join(filters)
    
    # SQL-Abfrage zur Selektion der geografischen Kennzahlen und Namen
    sql = f"""
        SELECT 
            location_id,
            zone,
            borough,
            geojson_str,
            SUM(trip_count) as trip_count
        FROM `{TABLE}`
        WHERE {where_clause}
        GROUP BY 1, 2, 3, 4
    """
    
    try:
        # Ausführung der Query und Konvertierung in ein DataFrame
        df = bq_client.query(sql).to_dataframe()
        if df.empty: 
            return df, {}

        # Transformation der GeoJSON-Strings in eine FeatureCollection für Plotly
        features = []
        for _, row in df.iterrows():
            if row['geojson_str']:
                feature = {
                    "type": "Feature",
                    "geometry": json.loads(row['geojson_str']),
                    "id": str(row['location_id']), 
                    "properties": {
                        "zone": row['zone'], 
                        "borough": row['borough']
                    }
                }
                features.append(feature)
        
        geojson_data = {"type": "FeatureCollection", "features": features}
        return df, geojson_data
        
    except Exception as e:
        print(f"Fehler beim Laden der Geodaten: {e}")
        return pd.DataFrame(), {}
    
def load_quality_audit(taxi_type="ALL", year=None):
    """
    Lädt monatliche Statistiken zur Datenqualität (GPS-Fehler, unbekannte Standorte).
    Basierend auf agg_quality_audit.
    """
    if not bq_client: return pd.DataFrame()

    TABLE = "taxi-bi-project.aggregational.agg_quality_audit"
    
    filters = ["1=1"]
    if taxi_type and taxi_type != "ALL":
        filters.append(f"source_system = '{taxi_type}'")
    if year:
        # Extrahiert das Jahr aus dem 'month' Feld (DATE_TRUNC)
        filters.append(f"EXTRACT(YEAR FROM month) = {year}")
    
    where_clause = " AND ".join(filters)
    
    sql = f"""
        SELECT 
            month,
            SUM(total_trips) as total_trips,
            SUM(gps_failures) as gps_failures,
            SUM(unknown_locations) as unknown_locations
        FROM `{TABLE}`
        WHERE {where_clause}
        GROUP BY 1
        ORDER BY 1
    """
    try:
        return bq_client.query(sql).to_dataframe()
    except Exception as e:
        print(f"Fehler in load_quality_audit: {e}")
        return pd.DataFrame()