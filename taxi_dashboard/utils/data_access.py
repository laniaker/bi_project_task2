import pandas as pd

# Diese Funktionen sind bewusst als "Interface" gedacht.
# Später Dummy-Daten ersetzen

def get_filter_options():
    """Return years + borough options. In echt: SELECT DISTINCT ... aus dim/agg Tabellen."""
    years = [2019, 2020, 2021, 2022, 2023]
    boroughs = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
    return years, boroughs

def load_peak_hours(taxi_type="ALL", year=None, borough=None) -> pd.DataFrame:
    # Erwartete Spalten: hour (0-23), trips
    return pd.DataFrame({"hour": list(range(24)), "trips": [0]*24})

def load_fares_by_borough(taxi_type="ALL", year=None) -> pd.DataFrame:
    # Erwartete Spalten: borough, fare_amount (für Boxplot: viele Zeilen)
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
