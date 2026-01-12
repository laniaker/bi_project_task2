from dash import Input, Output
import plotly.express as px
import plotly.graph_objects as go

# Einheitliches Styling für alle Visuals
from utils.plot_style import apply_exec_style

# Datenzugriff
from utils.data_access import (
    get_filter_options,
    load_peak_hours,
    load_fares_by_borough,
    load_tip_percentage,
    load_demand_over_years,
)

def register_predefined_callbacks(app):
    """
    Registriert alle Callbacks für den 'Predefined'-Tab.
    Zuständig für die Interaktivität der Standard-Charts.
    """

    # ---------------------------------------------------
    # Initialisierung der Filteroptionen
    # ---------------------------------------------------
    @app.callback(
        Output("filter-year", "options"),
        Output("filter-borough", "options"),
        Output("filter-taxi-type", "options"),  
        Input("filter-taxi-type", "id"), 
    )
    def init_filter_options(_):
        # Abfrage der verfügbaren Filterwerte aus der Datenbank
        years, boroughs, taxi_types = get_filter_options()

        # Formatierung für Dash Dropdowns
        year_opts = [{"label": str(y), "value": y} for y in years]
        borough_opts = [{"label": b, "value": b} for b in boroughs]
        taxi_opts = [{"label": t, "value": t} for t in taxi_types]
        
        # Option 'All' hinzufügen
        taxi_opts.insert(0, {"label": "All Taxis", "value": "ALL"})

        return year_opts, borough_opts, taxi_opts

    # ---------------------------------------------------
    # Chart 1: Peak Hours (Balkendiagramm)
    # ---------------------------------------------------
    @app.callback(
        Output("fig-peak-hours", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
        Input("filter-borough", "value"),
    )
    def fig_peak_hours(taxi_type, year, borough):
        if not taxi_type: taxi_type = "ALL"
        
        df = load_peak_hours(taxi_type, year, borough)

        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten für diese Auswahl")
            apply_exec_style(fig)
            return fig

        fig = px.bar(df, x="hour", y="trips")
        fig.update_layout(xaxis_title="Stunde (0-23)", yaxis_title="Anzahl Fahrten")
        apply_exec_style(fig, title="Peak Hours – Nachfrage pro Tageszeit")
        return fig

    # ---------------------------------------------------
    # Chart 2: Fares by Borough (Boxplot)
    # ---------------------------------------------------
    @app.callback(
        Output("fig-fares-borough", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
    )
    def fig_fares(taxi_type, year):
        if not taxi_type: taxi_type = "ALL"

        # Lädt voraggregierte Statistik-Daten (Min, Q1, Median, Q3, Max)
        df = load_fares_by_borough(taxi_type, year)

        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten verfügbar")
            apply_exec_style(fig)
            return fig

        # Nutzung von go.Box für vorgefertigte Quantile
        fig = go.Figure()
        
        fig.add_trace(go.Box(
            x=df["borough"],
            lowerfence=df["min_fare"], 
            q1=df["q1_fare"],
            median=df["median_fare"],
            q3=df["q3_fare"],
            upperfence=df["max_fare"],
            name="Preisverteilung"
        ))

        fig.update_layout(xaxis_title="Stadtteil", yaxis_title="Fahrpreis ($)")
        apply_exec_style(fig, title="Fahrpreisverteilung nach Stadtteil (Boxplot)")
        return fig

    # ---------------------------------------------------
    # Chart 3: Tip Percentage
    # ---------------------------------------------------
    @app.callback(
        Output("fig-tip-percentage", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
        Input("filter-borough", "value"),
    )
    def fig_tip_pct(taxi_type, year, borough):
        if not taxi_type: taxi_type = "ALL"

        df = load_tip_percentage(taxi_type, year, borough)

        if df.empty:
            fig = go.Figure()
            apply_exec_style(fig)
            return fig

        fig = px.bar(df, x="bucket", y="avg_tip_pct")
        fig.update_layout(xaxis_title="Kategorie", yaxis_title="Ø Trinkgeld (%)")
        apply_exec_style(fig, title="Durchschnittliches Trinkgeld")
        return fig

    # ---------------------------------------------------
    # Chart 4: Demand Shift (Zeitreihe)
    # ---------------------------------------------------
    @app.callback(
        Output("fig-demand-years", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-borough", "value"),
    )
    def fig_demand_years(taxi_type, borough):
        if not taxi_type: taxi_type = "ALL"

        df = load_demand_over_years(taxi_type, borough)

        if df.empty:
            fig = go.Figure()
            apply_exec_style(fig)
            return fig

        fig = px.line(df, x="year", y="trips", markers=True)
        fig.update_layout(xaxis_title="Jahr", yaxis_title="Gesamtfahrten")
        apply_exec_style(fig, title="Entwicklung der Nachfrage über Jahre")
        return fig