from dash import Input, Output
import plotly.express as px
import plotly.graph_objects as go
# Einheitliches Chart-Styling (Layout, Fonts, Farben, Spacing, Titel etc.)
from utils.plot_style import apply_exec_style

# Datenzugriff: gekapselte Loader-Funktionen (SQL/Files/ETL egal – hier nur Schnittstelle)
from utils.data_access import (
    load_demand_heatmap,
    load_scatter_fare_distance,
    load_flows,
    load_revenue_efficiency,
)


def register_creative_callbacks(app):
    """
    Registriert alle Callbacks für den 'Creative'-Tab.
    Idee: Pro Visualisierung ein eigener Callback, damit Filter/Chart-Logik sauber getrennt bleibt.
    """

    # ---------------------------------------------------
    # 1) Demand Heatmap: Trips nach Stunde × Wochentag
    # ---------------------------------------------------
    @app.callback(
        Output("fig-heatmap", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
        Input("filter-borough", "value"),
    )
    def fig_heatmap(taxi_type, year, borough):
        # Daten passend zu den aktuellen Filtern laden
        df = load_demand_heatmap(taxi_type, year, borough)

        # Guard: wenn keine Daten vorhanden sind, leere Figure mit Hinweis zurückgeben
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten")
            apply_exec_style(fig)
            return fig

        # Heatmap: Intensität = Anzahl Fahrten (Trips)
        fig = px.density_heatmap(df, x="hour", y="weekday", z="trips")
        fig.update_layout(xaxis_title="Stunde", yaxis_title="Wochentag")

        # Einheitliches Styling + Titel setzen
        apply_exec_style(fig, title="Demand Heatmap (Hour × Weekday)")
        return fig

    # ---------------------------------------------------
    # 2) Scatter: Fare vs Distance (Pricing-Logik / Ausreißer)
    # ---------------------------------------------------
    @app.callback(
        Output("fig-scatter-fare-distance", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
        Input("filter-borough", "value"),
    )
    def fig_scatter(taxi_type, year, borough):
        # Daten für Preis-/Distanz-Analyse laden
        df = load_scatter_fare_distance(taxi_type, year, borough)

        # Guard: kein Ergebnis für die Filterkombination
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten")
            apply_exec_style(fig)
            return fig

        # Scatter mit leichter Transparenz, um Punkt-Überlagerungen zu reduzieren
        fig = px.scatter(df, x="trip_distance", y="fare_amount", opacity=0.5)
        fig.update_layout(xaxis_title="Distanz", yaxis_title="Fare Amount")

        apply_exec_style(fig, title="Fare vs Distance (Pricing Logic)")
        return fig

    # ---------------------------------------------------
    # 3) Flows: Dominante Pickup → Dropoff Bewegungen (Boroughs)
    # ---------------------------------------------------
    @app.callback(
        Output("fig-flows", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
    )
    def fig_flows(taxi_type, year):
        # Aggregierte Flows laden (Pickup-Borough, Dropoff-Borough, Trips)
        df = load_flows(taxi_type, year)

        # Guard: keine Flows vorhanden
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten")
            apply_exec_style(fig)
            return fig

        # Balken: x = Pickup-Borough, y = Fahrten, Farbe = Dropoff-Borough
        fig = px.bar(df, x="pu_borough", y="trips", color="do_borough")
        fig.update_layout(xaxis_title="Pickup Borough", yaxis_title="Fahrten")

        apply_exec_style(fig, title="Pickup → Dropoff Dominant Flows")
        return fig

    # ---------------------------------------------------
    # 4) KPI: Revenue Efficiency (Fare pro Minute) nach Gruppen/Buckets
    # ---------------------------------------------------
    @app.callback(
        Output("fig-kpi-rev-eff", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
        Input("filter-borough", "value"),
    )
    def fig_rev_eff(taxi_type, year, borough):
        # KPI-Daten laden: rev_eff (z. B. fare / trip_duration_min) + bucket zur Gruppierung
        df = load_revenue_efficiency(taxi_type, year, borough)

        # Guard: keine KPI-Daten
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten")
            apply_exec_style(fig)
            return fig

        # Boxplot: Verteilung der Revenue Efficiency je Bucket
        fig = px.box(df, x="bucket", y="rev_eff")
        fig.update_layout(xaxis_title="Gruppe", yaxis_title="Fare pro Minute")

        apply_exec_style(fig, title="New KPI: Revenue Efficiency")
        return fig
