from dash import Input, Output
import plotly.express as px
import plotly.graph_objects as go

# Einheitliches Styling für alle Visuals (Layout, Typografie, Abstände, Titel)
from utils.plot_style import apply_exec_style

# Datenzugriff: Loader + Hilfsfunktion für Filter-Optionen
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
    Fokus: vordefinierte Standard-Analysen, die direkt auf den Filtern basieren.
    """

    # ---------------------------------------------------
    # 0) Initialisierung der Filteroptionen (Year/Borough)
    #    -> wird beim Tab-Wechsel getriggert, damit Dropdowns sauber befüllt sind
    # ---------------------------------------------------
    @app.callback(
        Output("filter-year", "options"),
        Output("filter-borough", "options"),
        Input("main-tabs", "value"),
    )
    def init_filter_options(_):
        # verfügbare Werte aus der Datenbasis holen (z. B. distinct years/boroughs)
        years, boroughs = get_filter_options()

        # Dash-Dropdown erwartet eine Liste von Dicts (label/value)
        year_opts = [{"label": str(y), "value": y} for y in years]
        borough_opts = [{"label": b, "value": b} for b in boroughs]
        return year_opts, borough_opts

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
        # aggregierte Trips pro Stunde für die aktuellen Filter laden
        df = load_peak_hours(taxi_type, year, borough)

        # Guard: keine Daten für die Filterkombination
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten")
            apply_exec_style(fig)
            return fig

        # Balken-Chart: x = Stunde, y = Anzahl Fahrten
        fig = px.bar(df, x="hour", y="trips")
        fig.update_layout(xaxis_title="Stunde", yaxis_title="Fahrten")
        apply_exec_style(fig, title="Peak Hours – Taxi Demand")
        return fig

    # ---------------------------------------------------
    # 2) Fares by Borough: Verteilung der Fare Amounts je Borough
    # ---------------------------------------------------
    @app.callback(
        Output("fig-fares-borough", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
    )
    def fig_fares(taxi_type, year):
        # Fare-Daten je Borough laden (typisch für Boxplot bereits "long format")
        df = load_fares_by_borough(taxi_type, year)

        # Guard: kein Ergebnis
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten")
            apply_exec_style(fig)
            return fig

        # Boxplot: zeigt Median/Quartile/Ausreißer pro Borough
        fig = px.box(df, x="borough", y="fare_amount")
        fig.update_layout(xaxis_title="Borough", yaxis_title="Fare Amount")
        apply_exec_style(fig, title="Fares by Borough")
        return fig

    # ---------------------------------------------------
    # 3) Average Tip Percentage: durchschnittliche Trinkgeldquote je Bucket
    # ---------------------------------------------------
    @app.callback(
        Output("fig-tip-percentage", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
        Input("filter-borough", "value"),
    )
    def fig_tip_pct(taxi_type, year, borough):
        # Tip-Buckets laden (z. B. Distanz-/Preisgruppen oder definierte Segmente)
        df = load_tip_percentage(taxi_type, year, borough)

        # Guard: keine Daten
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten")
            apply_exec_style(fig)
            return fig

        # Balken: x = Bucket/Gruppe, y = Ø Trinkgeldquote
        fig = px.bar(df, x="bucket", y="avg_tip_pct")
        fig.update_layout(xaxis_title="Gruppe", yaxis_title="Ø Tip %")
        apply_exec_style(fig, title="Average Tip Percentage")
        return fig

    # ---------------------------------------------------
    # 4) Demand Shift over Years: Entwicklung der Trips über die Jahre
    # ---------------------------------------------------
    @app.callback(
        Output("fig-demand-years", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-borough", "value"),
    )
    def fig_demand_years(taxi_type, borough):
        # Trips pro Jahr laden (Zeitreihe / Trend)
        df = load_demand_over_years(taxi_type, borough)

        # Guard: keine Daten
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten")
            apply_exec_style(fig)
            return fig

        # Linienchart mit Markern für bessere Lesbarkeit einzelner Jahre
        fig = px.line(df, x="year", y="trips", markers=True)
        fig.update_layout(xaxis_title="Jahr", yaxis_title="Fahrten")
        apply_exec_style(fig, title="Demand Shift over Years")
        return fig
