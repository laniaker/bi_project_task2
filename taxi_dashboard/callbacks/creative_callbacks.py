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
    
    # ---------------------------------------------------
    # 5) Weekly Patterns (Linearer Verlauf Mo -> So)
    # ---------------------------------------------------
    @app.callback(
        Output("fig-weekly-patterns-creative", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
        Input("filter-borough", "value"),
    )
    def fig_weekly_linear(taxi_type, year, borough):
        if not taxi_type: taxi_type = "ALL"
        
        # 1. Daten laden
        df = load_weekly_patterns(taxi_type, year, borough)
        
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten")
            apply_exec_style(fig)
            return fig

        # 2. Sortierung erzwingen: Montag zuerst!
        week_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        df["day_name"] = pd.Categorical(df["day_name"], categories=week_order, ordered=True)
        df = df.sort_values(by=["day_name", "hour"])

        # 3. Label bauen
        df["time_label"] = df["day_name"].astype(str) + " " + df["hour"].astype(str).str.zfill(2) + ":00"

        # Farb-Mapping
        color_map = {
            "YELLOW": "#f1c40f",
            "GREEN": "#2ecc71",
            "FHV": "#3498db",
            "FHV - High Volume": "#3498db"
        }

        # Feste Reihenfolge für die Stapelung
        taxi_stack_order = ["FHV", "FHV - High Volume", "GREEN", "YELLOW"]

        # 4. Plotten
        fig = px.bar(
            df, 
            x="time_label", 
            y="trips", 
            color="taxi_type", 
            category_orders={
                "time_label": df["time_label"].tolist(),
                "taxi_type": taxi_stack_order
            },
            color_discrete_map=color_map
        )
        
        # 5. Styling
        fig.update_layout(
            xaxis_title=None,
            yaxis_title="Anzahl Fahrten",
            legend_title=None,
            xaxis=dict(
                tickangle=-45,
                nticks=20,
                type="category"
            ),
            margin=dict(t=40, b=60, l=40, r=20),
            bargap=0.0
        )
        
        apply_exec_style(fig, title="Wochenverlauf (Start: Montag)")
        
        return fig