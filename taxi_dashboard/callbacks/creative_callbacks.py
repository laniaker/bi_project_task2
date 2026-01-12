from dash import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Einheitliches Chart-Styling
from utils.plot_style import apply_exec_style

# Datenzugriff
from utils.data_access import (
    load_weekly_patterns,  # <--- Das ist die neue Funktion, die wir gebaut haben
    # Die anderen Importe (load_scatter..., load_flows...) lassen wir weg, 
    # bis wir die SQL-Tabellen dafür gebaut haben.
)

def register_creative_callbacks(app):
    """
    Registriert alle Callbacks für den 'Creative'-Tab.
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
        if not taxi_type: taxi_type = "ALL"

        # 1. Daten laden (aus unserer neuen agg_weekly_patterns Tabelle)
        df = load_weekly_patterns(taxi_type, year, borough)

        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten")
            apply_exec_style(fig)
            return fig

        # 2. Aggregieren & Sortieren
        # Falls "ALL" gewählt ist, summieren wir Yellow+Green+FHV pro Zelle
        df_grouped = df.groupby(["day_name", "day_of_week", "hour"])['trips'].sum().reset_index()
        
        # Wichtig: Sortieren nach nummerischem Wochentag (1=Monday...), damit y-Achse stimmt
        df_grouped = df_grouped.sort_values("day_of_week")

        # 3. Plotten
        fig = px.density_heatmap(
            df_grouped, 
            x="hour", 
            y="day_name", 
            z="trips",
            nbinsx=24,
            nbinsy=7,
            color_continuous_scale="Viridis",
            category_orders={
                "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            }
        )
        
        fig.update_layout(
            xaxis_title="Stunde (0-23)", 
            yaxis_title="Wochentag",
            coloraxis_colorbar=dict(title="Trips")
        )

        # Dein Styling anwenden
        apply_exec_style(fig, title="Demand Heatmap (Hour × Weekday)")
        return fig

    # ---------------------------------------------------
    # 2) Scatter: Fare vs Distance (PLATZHALTER)
    # ---------------------------------------------------
    @app.callback(
        Output("fig-scatter-fare-distance", "figure"),
        Input("filter-taxi-type", "value"),
    )
    def fig_scatter(taxi_type):
        # Platzhalter, bis wir Task 2c angehen
        fig = go.Figure()
        fig.update_layout(
            title="Fare vs Distance (Coming Soon)",
            xaxis={"visible": False}, 
            yaxis={"visible": False}
        )
        apply_exec_style(fig)
        return fig

    # ---------------------------------------------------
    # 3) Flows: Dominante Pickup → Dropoff (PLATZHALTER)
    # ---------------------------------------------------
    @app.callback(
        Output("fig-flows", "figure"),
        Input("filter-taxi-type", "value"),
    )
    def fig_flows(taxi_type):
        # Platzhalter
        fig = go.Figure()
        fig.update_layout(
            title="Borough Flows (Coming Soon)",
            xaxis={"visible": False}, 
            yaxis={"visible": False}
        )
        apply_exec_style(fig)
        return fig

    # ---------------------------------------------------
    # 4) KPI: Revenue Efficiency (PLATZHALTER)
    # ---------------------------------------------------
    @app.callback(
        Output("fig-kpi-rev-eff", "figure"),
        Input("filter-taxi-type", "value"),
    )
    def fig_rev_eff(taxi_type):
        # Platzhalter
        fig = go.Figure()
        fig.update_layout(
            title="Revenue Efficiency (Coming Soon)",
            xaxis={"visible": False}, 
            yaxis={"visible": False}
        )
        apply_exec_style(fig)
        return fig