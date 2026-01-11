import pandas as pd
from google.cloud import bigquery

# BigQuery Client initialisieren
PROJECT_ID = "taxi-bi-project"
try:
    bq_client = bigquery.Client(project=PROJECT_ID)
except Exception as e:
    print(f"Warnung: BigQuery Client konnte nicht initialisiert werden: {e}")
    bq_client = None

    
# Diese Funktionen sind bewusst als "Interface" gedacht.
# Später Dummy-Daten ersetzen

def get_filter_options():
    """
    Lädt dynamisch die verfügbaren Filter-Optionen aus BigQuery:
    1. Jahre (aus Fact_Trips)
    2. Boroughs (aus dim_location)
    3. Taxi Types (aus Fact_Trips source_system)
    """
    
    # Fallback-Werte, falls DB nicht erreichbar
    default_years = [2019, 2020, 2021, 2022, 2023]
    default_boroughs = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
    default_types = ["YELLOW", "GREEN", "FHV"]

    if not bq_client:
        return default_years, default_boroughs, default_types

    # Tabellennamen
    fact_table = "taxi-bi-project.dimensional.Fact_Trips"
    dim_location = "taxi-bi-project.dimensional.dim_location"

    try:
        # 1. Jahre abfragen
        # Wir sortieren absteigend, damit das aktuellste Jahr oben steht
        sql_years = f"""
            SELECT DISTINCT EXTRACT(YEAR FROM pickup_datetime) as year 
            FROM `{fact_table}` 
            WHERE pickup_datetime IS NOT NULL
            ORDER BY year DESC
        """
        df_years = bq_client.query(sql_years).to_dataframe()
        years = df_years['year'].dropna().astype(int).tolist()

        # 2. Boroughs abfragen
        # "Unknown" und "EWR" filtern wir oft raus, da sie analytisch meist stören, 
        sql_boroughs = f"""
            SELECT DISTINCT borough 
            FROM `{dim_location}` 
            WHERE borough IS NOT NULL AND borough != 'Unknown'
            ORDER BY borough
        """
        df_boroughs = bq_client.query(sql_boroughs).to_dataframe()
        boroughs = df_boroughs['borough'].tolist()

        # 3. Taxi Types abfragen
        sql_types = f"""
            SELECT DISTINCT source_system 
            FROM `{fact_table}` 
            WHERE source_system IS NOT NULL
            ORDER BY source_system
        """
        df_types = bq_client.query(sql_types).to_dataframe()
        taxi_types = df_types['source_system'].tolist()

        return years, boroughs, taxi_types

    except Exception as e:
        print(f"Fehler beim Laden der Filter-Optionen: {e}")
        # Im Fehlerfall Fallback zurückgeben
        return default_years, default_boroughs, default_types

def load_peak_hours(taxi_type="ALL", year=None, borough=None) -> pd.DataFrame:
    """
    Lädt Peak Hours aus Fact_Trips.
    UPDATE: Nutzt jetzt dim_datetime für Stunden und Jahre.
    
    Filtert nach:
    - Jahr (via dim_datetime.year)
    - Borough (via JOIN mit dim_location)
    - Taxi Typ (via source_system Spalte)
    """
    if not bq_client:
        return pd.DataFrame({"hour": list(range(24)), "trips": [0]*24})

    # Tabellennamen definieren
    fact_table = "taxi-bi-project.dimensional.Fact_Trips"
    dim_location = "taxi-bi-project.dimensional.dim_location"
    dim_datetime = "taxi-bi-project.dimensional.dim_datetime"

    # Basis Query mit 2 JOINs (Location & Datetime)
    query = f"""
        SELECT 
            dt.hour as hour, 
            COUNT(*) as trips 
        FROM `{fact_table}` f
        JOIN `{dim_location}` l
          ON f.pickup_location_id = l.location_id
        JOIN `{dim_datetime}` dt
          ON TIMESTAMP_TRUNC(f.pickup_datetime, HOUR) = dt.datetime_key
    """
    
    # Filterliste aufbauen
    filters = ["1=1"] 
    
    # 1. Jahr Filter 
    if year:
        filters.append(f"dt.year = {year}")
    
    # 2. Borough Filter
    if borough:
        filters.append(f"l.borough = '{borough}'")
        
    # 3. Taxi Type Filter
    if taxi_type != "ALL":
        filters.append(f"f.source_system = '{taxi_type}'")

    # WHERE Clause zusammenbauen
    where_clause = " AND ".join(filters)
    
    # Finales SQL zusammensetzen
    final_sql = f"""
        {query}
        WHERE {where_clause}
        GROUP BY 1
        ORDER BY 1
    """

    try:
        # Query ausführen
        return bq_client.query(final_sql).to_dataframe()
    except Exception as e:
        print(f"Fehler bei load_peak_hours: {e}")
        return pd.DataFrame({"hour": [], "trips": []})

def load_fares_by_borough(taxi_type="ALL", year=None) -> pd.DataFrame:
    """
    Lädt die Preise (Total Amount) pro Borough für Boxplots.
    Nutzt Sampling (RAND + LIMIT), um das Dashboard performant zu halten.
    """
    if not bq_client:
        return pd.DataFrame({"borough": [], "fare_amount": []})

    fact_table = "taxi-bi-project.dimensional.Fact_Trips"
    dim_location = "taxi-bi-project.dimensional.dim_location"

    # Basis Query
    query = f"""
        SELECT 
            l.borough,
            f.total_amount as fare_amount
        FROM `{fact_table}` f
        JOIN `{dim_location}` l
          ON f.pickup_location_id = l.location_id
    """

    # Filter aufbauen
    filters = ["1=1"]

    # 1. Jahr Filter
    if year:
        filters.append(f"EXTRACT(YEAR FROM f.pickup_datetime) = {year}")
    
    # 2. Taxi Typ Filter
    if taxi_type != "ALL":
        filters.append(f"f.source_system = '{taxi_type}'")

    # 3. Datenbereinigung
    filters.append("f.total_amount BETWEEN 0.1 AND 500")
    filters.append("l.borough IS NOT NULL")
    filters.append("l.borough != 'Unknown'")

    where_clause = " AND ".join(filters)
    
    # Finales SQL mit Sampling
    final_sql = f"""
        {query}
        WHERE {where_clause}
        ORDER BY RAND()
        LIMIT 5000
    """

    try:
        return bq_client.query(final_sql).to_dataframe()
    except Exception as e:
        print(f"Fehler bei load_fares_by_borough: {e}")
        return pd.DataFrame({"borough": [], "fare_amount": []})

def load_tip_percentage(taxi_type="ALL", year=None, borough=None) -> pd.DataFrame:
    # Erwartete Spalten: bucket (z.B. year oder borough), avg_tip_pct
    return pd.DataFrame({"bucket": [], "avg_tip_pct": []})

def load_demand_over_years(taxi_type="ALL", borough=None) -> pd.DataFrame:
    # Erwartete Spalten: year, trips (oder month)
    return pd.DataFrame({"year": [], "trips": []})

# Creative
def load_demand_heatmap(taxi_type="ALL", year=None, borough=None) -> pd.DataFrame:
    # Erwartete Spalten: weekday (0-6 oder name), hour (0-23), trips
    return pd.DataFrame({"weekday": [], "hour": [], "trips": []})

def load_scatter_fare_distance(taxi_type="ALL", year=None, borough=None) -> pd.DataFrame:
    # Erwartete Spalten: trip_distance, fare_amount
    return pd.DataFrame({"trip_distance": [], "fare_amount": []})

def load_flows(taxi_type="ALL", year=None) -> pd.DataFrame:
    # Erwartete Spalten: pu_borough, do_borough, trips
    return pd.DataFrame({"pu_borough": [], "do_borough": [], "trips": []})

def load_revenue_efficiency(taxi_type="ALL", year=None, borough=None) -> pd.DataFrame:
    # Erwartete Spalten: bucket (borough oder year), rev_eff (fare/duration)
    return pd.DataFrame({"bucket": [], "rev_eff": []})