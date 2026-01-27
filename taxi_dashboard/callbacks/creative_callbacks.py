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
    JETZT MIT MONATSFILTER!
    """

    # ---------------------------------------------------
    # 1) Demand Heatmap: Trips nach Stunde × Wochentag
    # ---------------------------------------------------
    @app.callback(
        Output("fig-heatmap", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
        Input("filter-borough", "value"),
        Input("filter-month", "value"), # NEU
    )
    def fig_heatmap(taxi_type, year, borough, month):
        if not taxi_type: taxi_type = "ALL"

        df = load_weekly_patterns(taxi_type, year, borough, month)

        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten")
            apply_exec_style(fig)
            return fig

        df_grouped = df.groupby(["day_name", "day_of_week", "hour"])['trips'].sum().reset_index()
        df_grouped = df_grouped.sort_values("day_of_week")

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
        Input("filter-month", "value"), # NEU
    )
    def fig_scatter(taxi_type, year, borough, month):
        if not taxi_type: taxi_type = "ALL"
        
        df = load_agg_fare_dist(taxi_type, year, borough, month)
        
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten")
            apply_exec_style(fig)
            return fig

        fig = px.scatter(
            df, 
            x="distance", 
            y="fare", 
            size="trips",
            color="taxi_type",
            opacity=0.8,
            size_max=25,
            color_discrete_map={
                "YELLOW": "#f1c40f", "GREEN": "#2ecc71", 
                "FHV": "#3498db", "FHV - High Volume": "#3498db"
            },
            hover_data=["trips"]
        )
        
        fig.update_traces(marker=dict(line=dict(width=0), sizemin=3))
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
        Input("filter-month", "value"), # NEU
    )
    def fig_flows(taxi_type, year, borough, month):
        if not taxi_type: taxi_type = "ALL"
        
        df = load_borough_flows(taxi_type, year, borough, month)
        
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten")
            apply_exec_style(fig)
            return fig

        fig = px.bar(
            df,
            x="pickup_borough",
            y="trips",
            color="dropoff_borough",
            color_discrete_sequence=px.colors.qualitative.Prism 
        )
        
        fig.update_layout(
            xaxis_title="Start-Bezirk (Pickup)",
            yaxis_title="Anzahl Fahrten",
            legend_title="Ziel-Bezirk (Dropoff)",
            barmode="stack",
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
        Input("filter-month", "value"),
    )
    def fig_efficiency(taxi_type, year, borough, month):
        if not taxi_type: taxi_type = "ALL"
        
        df = load_revenue_efficiency(taxi_type, year, borough, month)
        
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
            yaxis_title="Umsatz pro Minute ($) [Log-Skala]",
            yaxis=dict(type="log", autorange=True),
            margin=dict(l=50, r=20, t=50, b=40)
        )
        
        apply_exec_style(fig, title="Effizienz: Kurzstrecke vs. Langstrecke")
        return fig
    
    # ---------------------------------------------------
    # 6) IT & Data Quality Audit (Stacked Area)
    # ---------------------------------------------------
    @app.callback(
        Output("fig-quality-audit", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
        Input("filter-month", "value"), # NEU
    )
    def fig_quality_audit(taxi_type, year, month):
        df = load_quality_audit(taxi_type, year, month)
        
        if df.empty:
            fig = go.Figure()
            apply_exec_style(fig, title="Keine Audit-Daten")
            return fig

        df_melted = df.melt(
            id_vars=["month"], 
            value_vars=["gps_failures", "unknown_locations"],
            var_name="issue_type", 
            value_name="count"
        )

        fig = px.area(
            df_melted, 
            x="month", 
            y="count", 
            color="issue_type",
            color_discrete_map={
                "gps_failures": "#ef4444",      
                "unknown_locations": "#f59e0b"  
            },
            labels={"month": "Zeitraum", "count": "Anzahl Issues", "issue_type": "Fehler-Typ"}
        )

        fig.update_layout(
            xaxis_title=None,
            yaxis_title="Anzahl Artefakte",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        apply_exec_style(fig, title="Data Quality Monitoring")
        return fig
    
    # ---------------------------------------------------
    # 7) Airport Sunburst
    # ---------------------------------------------------
    @app.callback(
        Output("fig-airport-analysis", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
        Input("filter-month", "value"),
    )
    def fig_airport_sunburst(taxi_type, year, month):
        df = load_airport_sunburst_data(taxi_type, year, month)
        
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten für diese Auswahl")
            apply_exec_style(fig)
            return fig

        # Hierarchie bilden
        cols_to_sum = ["total_revenue", "total_trips", "total_tip", "total_fare_all", "total_fare_card"]
        
        lvl1 = df.groupby("airport")[cols_to_sum].sum().reset_index()
        lvl1["id"] = lvl1["airport"]
        lvl1["parent"] = "" 
        lvl1["label"] = lvl1["airport"]

        lvl2 = df.groupby(["airport", "direction"])[cols_to_sum].sum().reset_index()
        lvl2["id"] = lvl2["airport"] + " - " + lvl2["direction"]
        lvl2["parent"] = lvl2["airport"] 
        lvl2["label"] = lvl2["direction"]

        lvl3 = df.copy()
        lvl3["id"] = lvl3["airport"] + " - " + lvl3["direction"] + " - " + lvl3["connected_borough"]
        lvl3["parent"] = lvl3["airport"] + " - " + lvl3["direction"]
        lvl3["label"] = lvl3["connected_borough"]
        
        df_all = pd.concat([lvl1, lvl2, lvl3], ignore_index=True)

        # KPIs berechnen
        df_all["avg_tip_pct"] = (df_all["total_tip"] / df_all["total_fare_card"] * 100).fillna(0)
        df_all["avg_fare"] = (df_all["total_fare_all"] / df_all["total_trips"]).fillna(0)

        fig = go.Figure(go.Sunburst(
            ids=df_all["id"],
            labels=df_all["label"],
            parents=df_all["parent"],
            values=df_all["total_revenue"],
            
            # --- HIER IST DER FIX FÜR DIE FARBEN ---
            marker=dict(
                colors=df_all["avg_tip_pct"],
                colorscale="RdYlGn", # Rot -> Gelb -> Grün
                cmin=0,   # Startet fest bei 0% (Rot)
                cmax=30,  # Endet fest bei 30% (Sattes Grün)
                # Alles über 30% wird jetzt einfach als sattes Grün dargestellt,
                # statt die Skala zu verzerren.
                colorbar=dict(title="Ø Tip %"),
                line=dict(color='black', width=0.5)
            ),
            # ---------------------------------------
            
            customdata=df_all[["total_revenue", "total_trips", "avg_tip_pct", "avg_fare"]],
            hovertemplate=(
                "<b>%{label}</b><br>" +
                "Umsatz: %{customdata[0]:,.0f} $<br>" +
                "Fahrten: %{customdata[1]:,.0f}<br>" +
                "Ø Fare: %{customdata[3]:.2f} $<br>" + 
                "Ø Tip: %{customdata[2]:.1f}%" + # Zeigt den ECHTEN Wert (z.B. 81%) im Tooltip
                "<extra></extra>"
            ),
            insidetextorientation='auto',
            branchvalues="total" 
        ))

        fig.update_layout(margin=dict(t=30, l=10, r=10, b=10))
        apply_exec_style(fig, title="Airport Value Map (Klick zum Zoomen)")
        return fig