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
    """

    # ---------------------------------------------------
    # 0) Initialisierung der Filteroptionen (Year/Borough/Taxi)
    #    -> Holt sich die Daten dynamisch aus BigQuery via get_filter_options
    # ---------------------------------------------------
    @app.callback(
        Output("filter-year", "options"),
        Output("filter-borough", "options"),
        Output("filter-taxi-type", "options"),  
        Input("main-tabs", "value"),
    )
    def init_filter_options(_):
        # 1. Daten holen (gibt jetzt 3 Listen zurück!)
        years, boroughs, taxi_types = get_filter_options()

        # 2. Optionen für Dash formatieren (Label/Value Dicts)
        year_opts = [{"label": str(y), "value": y} for y in years]
        borough_opts = [{"label": b, "value": b} for b in boroughs]
        
        # Taxi-Typen formatieren (z.B. YELLOW, GREEN, FHV)
        taxi_opts = [{"label": t, "value": t} for t in taxi_types]
        
        # Option "ALL" manuell hinzufügen, falls gewünscht
        taxi_opts.insert(0, {"label": "All Taxis", "value": "ALL"})

        # 3. Alle drei Listen zurückgeben
        return year_opts, borough_opts, taxi_opts

    # ---------------------------------------------------
    # 1) Peak Hours: Nachfrage je Stunde (Trips)
    # ---------------------------------------------------
    @app.callback(
        Output("fig-peak-hours", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
        Input("filter-borough", "value"),
    )
    def fig_peak_hours(taxi_type, year, borough):
        # Fallback, falls Dropdowns noch laden (None sind)
        if not taxi_type: taxi_type = "ALL"
        
        df = load_peak_hours(taxi_type, year, borough)

        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten für diese Auswahl")
            apply_exec_style(fig)
            return fig

        # Balken-Chart
        fig = px.bar(df, x="hour", y="trips")
        fig.update_layout(xaxis_title="Stunde (0-23)", yaxis_title="Anzahl Fahrten")
        apply_exec_style(fig, title="Peak Hours – Nachfrage pro Tageszeit")
        return fig

    # ---------------------------------------------------
    # 2) Fares by Borough
    # ---------------------------------------------------
    @app.callback(
        Output("fig-fares-borough", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
    )
    def fig_fares(taxi_type, year):
        if not taxi_type: taxi_type = "ALL"

        df = load_fares_by_borough(taxi_type, year)

        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten verfügbar")
            apply_exec_style(fig)
            return fig

        fig = px.box(df, x="borough", y="fare_amount")
        fig.update_layout(xaxis_title="Stadtteil", yaxis_title="Fahrpreis ($)")
        apply_exec_style(fig, title="Fahrpreisverteilung nach Stadtteil")
        return fig

    # ---------------------------------------------------
    # 3) Tip Percentage
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
            fig.update_layout(title="Keine Daten verfügbar")
            apply_exec_style(fig)
            return fig

        fig = px.bar(df, x="bucket", y="avg_tip_pct")
        fig.update_layout(xaxis_title="Kategorie", yaxis_title="Ø Trinkgeld (%)")
        apply_exec_style(fig, title="Durchschnittliches Trinkgeld")
        return fig

    # ---------------------------------------------------
    # 4) Demand Shift (Jahresvergleich)
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
            fig.update_layout(title="Keine historischen Daten")
            apply_exec_style(fig)
            return fig

        fig = px.line(df, x="year", y="trips", markers=True)
        fig.update_layout(xaxis_title="Jahr", yaxis_title="Gesamtfahrten")
        apply_exec_style(fig, title="Entwicklung der Nachfrage über Jahre")
        return fig