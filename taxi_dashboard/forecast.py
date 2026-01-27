import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from google.cloud import bigquery
from prophet import Prophet
import logging

# Warnungen unterdrücken für eine saubere Ausgabe
logging.getLogger('prophet').setLevel(logging.ERROR)
logging.getLogger('cmdstanpy').setLevel(logging.ERROR)

# --- CONFIG ---
PROJECT_ID = "taxi-bi-project"
client = bigquery.Client(project=PROJECT_ID)

def get_taxi_data(taxi_label):
    """Lädt aggregierte Tagesdaten aus BigQuery."""
    year_filter = "2010" if taxi_label == "YELLOW" else "2015"
    
    query = f"""
    SELECT 
        DATE(pickup_datetime) as date,
        COUNT(*) as total_trips
    FROM `{PROJECT_ID}.dimensional.Fact_Trips`
    WHERE source_system = '{taxi_label}'
      AND pickup_datetime >= '{year_filter}-01-01'
    GROUP BY date
    ORDER BY date
    """
    print(f"\n" + "="*50)
    print(f"DATENANALYSE FÜR: {taxi_label}")
    print("="*50)
    
    df = client.query(query).to_dataframe()
    if df.empty:
        print(f"Keine Daten für {taxi_label} gefunden.")
        return None
    
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df = df.resample('D').asfreq().fillna(0)
    return df

def analyze_kpis(df, taxi_label):
    """Berechnet historische Kennzahlen zur Einordnung des Trends."""
    print(f"--- Historische Kennzahlen ({taxi_label}) ---")
    
    # Durchschnittliche Fahrten pro Tag (nur Tage mit Betrieb > 0)
    active_days = df[df['total_trips'] > 0]
    avg_trips = active_days['total_trips'].mean()
    
    # Jahresvergleich (nur Juni, falls vorhanden)
    df_june = df[df.index.month == 6]
    june_trend = df_june.groupby(df_june.index.year)['total_trips'].sum()
    
    print(f"Durchschn. Fahrten pro Tag: {int(avg_trips):,}")
    if len(june_trend) > 1:
        last_year = june_trend.index[-1]
        prev_year = june_trend.index[-2]
        growth = ((june_trend.iloc[-1] / june_trend.iloc[-2]) - 1) * 100
        print(f"Trend Juni {prev_year} zu {last_year}: {growth:+.2f}%")
    print("-" * 40)

def run_prophet_forecast(df, taxi_label):
    # 1. Wir beschränken uns für das Training auf die Zeit nach 2023
    # Das verhindert, dass 10 Jahre alte Trends die Prognose ruinieren
    df_recent = df[df.index >= '2023-01-01'].reset_index().rename(columns={'date': 'ds', 'total_trips': 'y'})
    
    if df_recent.empty:
        print(f"Zu wenig aktuelle Daten für {taxi_label}")
        return None

    # 2. Modell-Konfiguration für "stabile" Märkte
    # Wir schalten den automatischen Trend-Wechsel fast aus (prior_scale)
    model = Prophet(
        growth='linear',
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.001 # Macht den Trend extrem stabil/unflexibel
    )
    model.add_country_holidays(country_name='US')
    
    # 3. Floor setzen: Fahrten können nicht unter einen gewissen Wert fallen
    # Wir nehmen 50% des aktuellen Durchschnitts als absoluten Floor
    current_avg = df_recent['y'].mean()
    df_recent['floor'] = current_avg * 0.5 
    
    print(f"Training läuft für {taxi_label} (Fokus auf aktuelle Daten)...")
    model.fit(df_recent)
    
    # 4. Forecast
    future = model.make_future_dataframe(periods=180)
    future['floor'] = current_avg * 0.5
    
    forecast = model.predict(future)
    
    # 5. yhat Korrektur: Falls Prophet trotzdem unter den Floor will
    forecast['yhat'] = forecast['yhat'].clip(lower=current_avg * 0.5)

    # Visualisierung (Wichtig: Schau dir hier die blaue Linie an!)
    fig = model.plot(forecast)
    plt.title(f"BI-Forecast {taxi_label}: Fokus 2023-2026")
    plt.show()

    june_2026 = forecast[(forecast['ds'] >= '2026-06-01') & (forecast['ds'] <= '2026-06-30')]
    print(f"PROGNOSE JUNI 2026: {int(june_2026['yhat'].sum()):,} Fahrten")

# --- HAUPTPROGRAMM ---
if __name__ == "__main__":
    systems = ["GREEN", "YELLOW", "FHV"]
    
    for sys in systems:
        data = get_taxi_data(sys)
        if data is not None:
            analyze_kpis(data, sys)
            run_prophet_forecast(data, sys)