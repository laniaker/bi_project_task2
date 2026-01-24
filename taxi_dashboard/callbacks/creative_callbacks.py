from dash import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Einheitliches Chart-Styling
from utils.plot_style import apply_exec_style

# Datenzugriff
from utils.data_access import (
    load_weekly_patterns, load_agg_fare_dist,
    load_borough_flows, load_revenue_efficiency,
    load_quality_audit, load_airport_sunburst_data
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
    # 2) Scatter: Fare vs Distance (Clean Bubble)
    # ---------------------------------------------------
    @app.callback(
        Output("fig-scatter-fare-distance", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
        Input("filter-borough", "value"),
    )
    def fig_scatter(taxi_type, year, borough):
        if not taxi_type: taxi_type = "ALL"
        
        # 1. Daten laden
        df = load_agg_fare_dist(taxi_type, year, borough)
        
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten")
            apply_exec_style(fig)
            return fig

        # 2. Plotten als Bubble Chart
        fig = px.scatter(
            df, 
            x="distance", 
            y="fare", 
            size="trips",
            color="taxi_type",
            opacity=0.8,
            size_max=25,
            color_discrete_map={
                "YELLOW": "#f1c40f",
                "GREEN": "#2ecc71",
                "FHV": "#3498db",
                "FHV - High Volume": "#3498db"
            },
            hover_data=["trips"]
        )
        
        fig.update_traces(marker=dict(line=dict(width=0), sizemin=3))
        
        # 3. Styling
        fig.update_layout(
            xaxis_title="Distanz (Meilen)",
            yaxis_title="Fahrpreis (USD)",
            legend_title="Taxi Typ",
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        apply_exec_style(fig, title=f"Preisstruktur (Datenbasis: {len(df)} Cluster)")
        
        return fig
    
    # ---------------------------------------------------
    # 3) Flows: Pickup -> Dropoff (Stacked Bar)
    # ---------------------------------------------------
    @app.callback(
        Output("fig-flows", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
        Input("filter-borough", "value"),
    )
    def fig_flows(taxi_type, year, borough):
        if not taxi_type: taxi_type = "ALL"
        
        # 1. Daten laden
        df = load_borough_flows(taxi_type, year, borough)
        
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten")
            apply_exec_style(fig)
            return fig

        # 2. Plotten als Stacked Bar Chart
        # x = Wo steigen sie ein?
        # y = Wie viele?
        # color = Wo wollen sie hin? (Der Stapel)
        fig = px.bar(
            df,
            x="pickup_borough",
            y="trips",
            color="dropoff_borough",
            title="Verkehrsströme (Pickup → Dropoff)",
            # Optional: Eine schöne Farbpalette für die Dropoff-Ziele
            color_discrete_sequence=px.colors.qualitative.Prism 
        )
        
        # 3. Styling
        fig.update_layout(
            xaxis_title="Start-Bezirk (Pickup)",
            yaxis_title="Anzahl Fahrten",
            legend_title="Ziel-Bezirk (Dropoff)",
            barmode="stack", # Stellt sicher, dass gestapelt wird
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        apply_exec_style(fig, title="Verkehrsströme (Pickup → Dropoff)")
        
        return fig

    # ---------------------------------------------------
    # 4) Revenue Efficiency (Boxplot)
    # ---------------------------------------------------
    @app.callback(
        Output("fig-kpi-rev-eff", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
        Input("filter-borough", "value"),
    )
    def fig_efficiency(taxi_type, year, borough):
        if not taxi_type: taxi_type = "ALL"
        
        df = load_revenue_efficiency(taxi_type, year, borough)
        
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten")
            apply_exec_style(fig)
            return fig
        
        fig = go.Figure()

        categories = sorted(df["trip_category"].unique())
        
        for cat in categories:
            cat_data = df[df["trip_category"] == cat]
            
            fig.add_trace(go.Box(
                name=cat,
                x=[cat], 
                q1=[cat_data["q1_val"].mean()],
                median=[cat_data["median_val"].mean()],
                q3=[cat_data["q3_val"].mean()],
                lowerfence=[cat_data["min_val"].mean()],
                upperfence=[cat_data["max_val"].mean()],
                marker_color="#3498db",
                showlegend=False
            ))

        fig.update_layout(
            title="Effizienz: Kurzstrecke vs. Langstrecke",
            yaxis_title="Umsatz pro Minute ($)",
            yaxis=dict(range=[0, 3]),
            margin=dict(l=50, r=20, t=50, b=40)
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
    
    # ---------------------------------------------------
    # 6) IT & Data Quality Audit (Stacked Area)
    # ---------------------------------------------------
    @app.callback(
        Output("fig-quality-audit", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
    )
    def fig_quality_audit(taxi_type, year):
        # 1. Daten laden
        df = load_quality_audit(taxi_type, year)
        
        if df.empty:
            fig = go.Figure()
            apply_exec_style(fig, title="Keine Audit-Daten")
            return fig

        # 2. Daten für Plotly transformieren (Melt)
        df_melted = df.melt(
            id_vars=["month"], 
            value_vars=["gps_failures", "unknown_locations"],
            var_name="issue_type", 
            value_name="count"
        )

        # 3. Plotten
        fig = px.area(
            df_melted, 
            x="month", 
            y="count", 
            color="issue_type",
            color_discrete_map={
                "gps_failures": "#ef4444",      # Soft Red
                "unknown_locations": "#f59e0b"  # Amber/Orange
            },
            labels={
                "month": "Zeitraum", 
                "count": "Anzahl Issues", 
                "issue_type": "Fehler-Typ"
            }
        )

        # 4. Styling
        fig.update_layout(
            xaxis_title=None,
            yaxis_title="Anzahl Artefakte",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        apply_exec_style(fig, title="Data Quality Monitoring (System Health)")
        
        return fig
    
    # ---------------------------------------------------
    # 7) Airport Sunburst (Final: Umsatz, Trips, Tip & Fare)
    # ---------------------------------------------------
    @app.callback(
        Output("fig-airport-analysis", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
    )
    def fig_airport_sunburst(taxi_type, year):
        # 1. Daten laden
        df = load_airport_sunburst_data(taxi_type, year)
        
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten für diese Auswahl")
            apply_exec_style(fig)
            return fig

        # -------------------------------------------------------
        # Manuelle Hierarchie-Bildung
        # -------------------------------------------------------
        # Wir summieren alle nötigen Spalten für die Ebenen
        cols_to_sum = ["total_revenue", "total_trips", "total_tip", "total_fare_all", "total_fare_card"]
        
        # A) Ebene 1: Airports
        lvl1 = df.groupby("airport")[cols_to_sum].sum().reset_index()
        lvl1["id"] = lvl1["airport"]
        lvl1["parent"] = "" 
        lvl1["label"] = lvl1["airport"]

        # B) Ebene 2: Direction
        lvl2 = df.groupby(["airport", "direction"])[cols_to_sum].sum().reset_index()
        lvl2["id"] = lvl2["airport"] + " - " + lvl2["direction"]
        lvl2["parent"] = lvl2["airport"] 
        lvl2["label"] = lvl2["direction"]

        # C) Ebene 3: Boroughs
        lvl3 = df.copy()
        lvl3["id"] = lvl3["airport"] + " - " + lvl3["direction"] + " - " + lvl3["connected_borough"]
        lvl3["parent"] = lvl3["airport"] + " - " + lvl3["direction"]
        lvl3["label"] = lvl3["connected_borough"]
        
        # D) Alles zusammenfügen
        df_all = pd.concat([lvl1, lvl2, lvl3], ignore_index=True)

        # E) Kennzahlen berechnen
        # 1. Tip % berechnen wir NUR auf Basis der Credit Card Fares
        # (Vermeidet Division durch Null mit np.where oder fillna)
        df_all["avg_tip_pct"] = (df_all["total_tip"] / df_all["total_fare_card"] * 100).fillna(0)
        
        # 2. Durchschnittspreis berechnen wir auf Basis ALLER Fares
        df_all["avg_fare"] = (df_all["total_fare_all"] / df_all["total_trips"]).fillna(0)

        # -------------------------------------------------------
        # Plotten
        # -------------------------------------------------------
        fig = go.Figure(go.Sunburst(
            ids=df_all["id"],
            labels=df_all["label"],
            parents=df_all["parent"],
            values=df_all["total_revenue"],
            
            marker=dict(
                colors=df_all["avg_tip_pct"],
                colorscale="RdYlGn",
                cmid=15, 
                colorbar=dict(title="Ø Tip % (Card Only)"),
                line=dict(color='black', width=0.5)
            ),
            
            customdata=df_all[["total_revenue", "total_trips", "avg_tip_pct", "avg_fare"]],
            
            hovertemplate=(
                "<b>%{label}</b><br>" +
                "Umsatz: %{customdata[0]:,.0f} $<br>" +
                "Fahrten: %{customdata[1]:,.0f}<br>" +
                "Ø Fare: %{customdata[3]:.2f} $<br>" + 
                "Ø Tip: %{customdata[2]:.1f}%" +
                "<extra></extra>"
            ),
            
            insidetextorientation='auto',
            branchvalues="total" 
        ))

        fig.update_layout(
            margin=dict(t=30, l=10, r=10, b=10),
        )
        
        apply_exec_style(fig, title="Airport Value Map (Klick zum Zoomen)")

        return fig