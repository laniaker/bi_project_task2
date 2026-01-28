import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from google.cloud import bigquery
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose

# --- CONFIG ---
PROJECT_ID = "taxi-bi-project"
client = bigquery.Client(project=PROJECT_ID)

def get_taxi_data(taxi_label="GREEN", start_year="2015"):
    """Lädt aggregierte Tagesdaten aus BigQuery."""
    query = f"""
    SELECT 
        DATE(pickup_datetime) as date,
        COUNT(*) as total_trips
    FROM `{PROJECT_ID}.dimensional.Fact_Trips`
    WHERE source_system = '{taxi_label}'
      AND pickup_datetime >= '{start_year}-01-01'
    GROUP BY date
    ORDER BY date
    """
    print(f"\n[1/4] Lade Daten für {taxi_label}...")
    df = client.query(query).to_dataframe()
    if df.empty:
        return None
    
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    # Lücken füllen mit 0 (essentiell für mathematische Modelle)
    df = df.resample('D').asfreq().fillna(0)
    return df

def check_stationarity(df):
    """Prüft, ob die Zeitreihe stationär ist."""
    print("[2/4] Führe Augmented Dickey-Fuller Test aus...")
    result = adfuller(df['total_trips'])
    p_value = result[1]
    print(f'   - ADF Statistic: {result[0]:.4f}')
    print(f'   - p-value: {p_value:.4f}')
    return p_value <= 0.05

def decompose_and_plot(df, taxi_label):
    """Zerlegt die Zeitreihe in Trend, Saisonalität und Rauschen."""
    print(f"[3/4] Dekomponiere Zeitreihe (Saisonalität)...")
    
    # 7-Tage Periode für wöchentliche Muster
    decomposition = seasonal_decompose(df['total_trips'], model='additive', period=7)
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12), sharex=True)
    decomposition.trend.plot(ax=ax1, title=f"Trend - {taxi_label}", color='blue')
    decomposition.seasonal.plot(ax=ax2, title="Wöchentliche Saisonalität", color='green')
    decomposition.resid.plot(ax=ax3, title="Residuen (Rauschen)", color='red', style='.')
    plt.tight_layout()
    plt.show()

def apply_differencing(df):
    """Macht die Zeitreihe durch Differenzierung stationär."""
    print("[4/4] Wende Differenzierung an (Trend entfernen)...")
    # delta y = y(t) - y(t-1)
    df_diff = df.diff().dropna()
    
    plt.figure(figsize=(15, 4))
    plt.plot(df_diff, color='orange')
    plt.title("Stationarisierte Zeitreihe (Tägliche Änderungen)")
    plt.show()
    
    # Erneuter Test
    new_p = adfuller(df_diff['total_trips'])[1]
    print(f"   - Neuer p-value nach Differenzierung: {new_p:.4f}")
    return df_diff

# ==========================================
# HAUPTPROGRAMM
# ==========================================

# 1. ANALYSE FÜR GREEN (ODER FHV) - VOLLSTÄNDIG
# ------------------------------------------
# check_stationarity("GREEN") # <--- Alter Aufruf auskommentiert

df_green = get_taxi_data("GREEN")
if df_green is not None:
    is_stationary = check_stationarity(df_green)
    
    if not is_stationary:
        print("Daten sind nicht stationär. Trend wird entfernt...")
        decompose_plot = decompose_and_plot(df_green, "GREEN")
        df_stationary = apply_differencing(df_green)
    else:
        print("Daten sind bereits stationär.")


# 2. SPEZIAL-LOGIK FÜR YELLOW (JUN & 2023)
# ------------------------------------------
print("\n" + "="*40)
print("STRATEGIE FÜR YELLOW CABS (LÜCKENHAFT)")
print("="*40)

# Hier laden wir nur 2023, um das "Saisonalitäts-Profil" zu lernen
df_yellow_2023 = get_taxi_data("YELLOW", start_year="2023")
if df_yellow_2023 is not None:
    # Wir filtern auf 2023 begrenzt
    df_yellow_2023 = df_yellow_2023[df_yellow_2023.index.year == 2023]
    
    print("Extrahiere Saisonalitäts-Muster aus 2023 für Yellow...")
    decomp_y = seasonal_decompose(df_yellow_2023['total_trips'], model='additive', period=7)
    
    plt.figure(figsize=(12, 4))
    plt.plot(decomp_y.seasonal[:14]) # Zeige die ersten 2 Wochen
    plt.title("Typisches 2-Wochen-Muster der Yellow Cabs (basiert auf 2023)")
    plt.ylabel("Abweichung vom Durchschnitt")
    plt.show()
    
    print("\nNÄCHSTER SCHRITT FÜR DEN FORECAST:")
    print("1. Wir nehmen den Juni-Trend (2010-2025).")
    print("2. Wir legen das 2023-Wochenmuster über die Juni-Prognose.")