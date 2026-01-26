from dash import Input, Output, State, html, dcc, ctx, no_update
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Einheitliches Styling für alle Visuals
from utils.plot_style import apply_exec_style

# Datenzugriff - Importiert aus utils.data_access
from utils.data_access import (
    get_filter_options,
    load_peak_hours,
    load_fares_by_borough,
    load_tip_percentage,
    load_demand_over_years,
    get_kpi_data,
    get_top_boroughs,
    get_top_hours,
    load_weekly_patterns,     
    load_tip_distribution,     
    load_top_tipping_zones,
    load_seasonality_data,
    load_market_share_trend,
    load_top_routes
)

def register_predefined_callbacks(app):
    """
    Registriert alle Callbacks für den 'Predefined'-Tab.
    Zuständig für die Interaktivität der Standard-Charts und der 3 Deep Dive Modals.
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
        years, boroughs, taxi_types = get_filter_options()

        year_opts = [{"label": str(y), "value": y} for y in years]
        borough_opts = [{"label": b, "value": b} for b in boroughs]
        taxi_opts = [{"label": t, "value": t} for t in taxi_types]

        return year_opts, borough_opts, taxi_opts

    # ---------------------------------------------------
    # Chart 1: Peak Hours (Standard Balkendiagramm)
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

        df = load_fares_by_borough(taxi_type, year)

        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten verfügbar")
            apply_exec_style(fig)
            return fig

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
    
    # ---------------------------------------------------
    # KPI-Update (Obere Leiste)
    # ---------------------------------------------------
    @app.callback(
        [
            Output("kpi-trips", "children"),
            Output("kpi-avg-fare", "children"),
            Output("kpi-avg-tip", "children"),
            Output("kpi-outlier", "children"),
        ],
        [
            Input("filter-taxi-type", "value"),
            Input("filter-year", "value"),
            Input("filter-borough", "value"),
        ]
    )
    def update_kpis_only(taxi_type, year, borough):
        if not taxi_type: taxi_type = "ALL"

        trips, fare, tip, outlier = get_kpi_data(taxi_type, year, borough)
        
        return (
            f"{int(trips):,}".replace(",", "."), 
            f"{fare:.2f} $",                      
            f"{tip:.1f} %",                       
            f"{outlier:.1f} %"                    
        )

    # ---------------------------------------------------
    # Executive Insights Panel (Unten Links)
    # ---------------------------------------------------
    @app.callback(
        [
            Output("tbl-top-boroughs", "children"),
            Output("tbl-top-hours", "children"),
            Output("insight-text", "children")
        ],
        [
            Input("filter-taxi-type", "value"),
            Input("filter-year", "value"),
            Input("filter-borough", "value"),
        ]
    )
    def update_insights_panel(taxi_type, year, borough):
        if not taxi_type: taxi_type = "ALL"

        top_b_data = get_top_boroughs(taxi_type, year)
        top_h_data = get_top_hours(taxi_type, year, borough)

        if top_b_data:
            rows_boroughs = [
                html.Tr([
                    html.Td(row['Borough']), 
                    html.Td(f"{int(row['Trips']):,}".replace(",", "."))
                ]) for row in top_b_data
            ]
            winner_borough = top_b_data[0]['Borough']
        else:
            rows_boroughs = [html.Tr([html.Td("-"), html.Td("-")])]
            winner_borough = "Unbekannt"

        if top_h_data:
            rows_hours = [
                html.Tr([
                    html.Td(f"{row['Hour']}:00"), 
                    html.Td(f"{int(row['Trips']):,}".replace(",", "."))
                ]) for row in top_h_data
            ]
            peak_hour = top_h_data[0]['Hour']
        else:
            rows_hours = [html.Tr([html.Td("-"), html.Td("-")])]
            peak_hour = "?"

        text_parts = []
        
        if borough:
            if isinstance(borough, list):
                names = ", ".join(borough)
                text_parts.append(f"Fokus auf **{names}**.")
            else:
                text_parts.append(f"Fokus auf **{borough}**.")
        else:
            text_parts.append(f"**{winner_borough}** ist der nachfragestärkste Bezirk.")

        if peak_hour != "?":
            if 6 <= peak_hour < 10: time_of_day = "im morgendlichen Berufsverkehr"
            elif 16 <= peak_hour < 20: time_of_day = "zum Feierabend"
            elif 0 <= peak_hour < 5: time_of_day = "im Nachtleben"
            else: time_of_day = "tagsüber"
            
            text_parts.append(f"Die höchste Auslastung zeigt sich um **{peak_hour}:00 Uhr** ({time_of_day}).")

        insight_msg = " ".join(text_parts)

        return rows_boroughs, rows_hours, dcc.Markdown(insight_msg)

    # ===================================================
    # DEEP DIVE 1: PEAK HOURS (Weekly Patterns)
    # ===================================================
    
    # Toggle Logic
    @app.callback(
        Output("modal-peak-hours", "style"),
        [Input("btn-open-modal", "n_clicks"),
         Input("btn-close-modal", "n_clicks")],
        [State("modal-peak-hours", "style")]
    )
    def toggle_modal_peak(n_open, n_close, current_style):
        if not n_open and not n_close:
            return current_style 
        
        trigger_id = ctx.triggered_id
        if trigger_id == "btn-open-modal":
            return {"display": "flex"} 
        elif trigger_id == "btn-close-modal":
            return {"display": "none"}
            
        return current_style

    # Content Update
    @app.callback(
        Output("fig-peak-hours-deepdive", "figure"),
        [Input("filter-taxi-type", "value"),
         Input("filter-year", "value"),
         Input("filter-borough", "value"),
         Input("btn-open-modal", "n_clicks")],
        [State("modal-peak-hours", "style")]
    )
    def update_peak_deepdive(taxi_type, year, borough, n_clicks, modal_style):
        # Lazy Loading Check
        is_open = modal_style and modal_style.get("display") == "flex"
        if ctx.triggered_id != "btn-open-modal" and not is_open:
            return no_update

        if not taxi_type: taxi_type = "ALL"

        df = load_weekly_patterns(taxi_type, year, borough)
        
        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten")
            apply_exec_style(fig)
            return fig

        week_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        df["day_name"] = pd.Categorical(df["day_name"], categories=week_order, ordered=True)
        df = df.sort_values(by=["day_name", "hour"])
        
        df["time_label"] = df["day_name"].astype(str) + " " + df["hour"].astype(str).str.zfill(2) + ":00"

        color_map = {
            "YELLOW": "#f1c40f", 
            "GREEN": "#2ecc71",
            "FHV": "#636e72",                 
            "FHV - High Volume": "#636e72"    
        }
        taxi_stack_order = ["FHV", "FHV - High Volume", "GREEN", "YELLOW"]

        fig = px.bar(
            df, 
            x="time_label", 
            y="trips", 
            color="taxi_type", 
            category_orders={"time_label": df["time_label"].tolist(), "taxi_type": taxi_stack_order},
            color_discrete_map=color_map
        )
        
        fig.update_layout(
            xaxis_title=None,
            yaxis_title="Anzahl Fahrten",
            legend_title=None,
            xaxis=dict(tickangle=-45, nticks=20),
            margin=dict(t=40, b=80, l=40, r=20),
            bargap=0.0
        )
        
        apply_exec_style(fig, title="Wochenverlauf (Detailansicht)")
        return fig
    
    # ===================================================
    # DEEP DIVE 2: FARE ANALYSIS (Routes)
    # ===================================================

    # Toggle Logic
    @app.callback(
        Output("modal-fare-deepdive", "style"),
        [Input("btn-open-modal-fare", "n_clicks"),
         Input("btn-close-modal-fare", "n_clicks")],
        [State("modal-fare-deepdive", "style")]
    )
    def toggle_modal_fare(n_open, n_close, current_style):
        if not n_open and not n_close:
            return current_style 
        
        trigger_id = ctx.triggered_id
        if trigger_id == "btn-open-modal-fare":
            return {"display": "flex"} 
        elif trigger_id == "btn-close-modal-fare":
            return {"display": "none"}
            
        return current_style

    # Content Update
    @app.callback(
        [Output("fig-fare-routes", "figure"),
         Output("modal-fare-stats", "children")],
        [Input("filter-taxi-type", "value"),
         Input("filter-year", "value"),
         Input("filter-borough", "value"),
         Input("btn-open-modal-fare", "n_clicks")],
        [State("modal-fare-deepdive", "style")]
    )
    def update_fare_deepdive(taxi_type, year, borough, n_clicks, modal_style):
        # Lazy Loading
        is_open = modal_style and modal_style.get("display") == "flex"
        if ctx.triggered_id != "btn-open-modal-fare" and not is_open:
            return no_update, no_update

        if not taxi_type: taxi_type = "ALL"

        # Daten laden
        df = load_top_routes(taxi_type, year, borough)
        
        if df.empty:
            fig = go.Figure()
            apply_exec_style(fig, title="Keine Daten")
            return fig, html.P("Keine Daten.")

        # Plot: Horizontales Balkendiagramm für Routen
        df["route_label"] = df["pickup_borough"] + " → " + df["dropoff_borough"]
        
        fig = px.bar(
            df,
            x="revenue",
            y="route_label",
            orientation='h',
            text="avg_fare", # Zeigt Durchschnittspreis im Balken
            color="revenue",
            color_continuous_scale="Blues"
        )
        
        # Text formatieren (Avg Fare)
        fig.update_traces(texttemplate='$%{text:.2f}', textposition='inside')
        
        fig.update_layout(
            xaxis_title="Gesamtumsatz ($)",
            yaxis_title=None,
            yaxis={'categoryorder':'total ascending'} 
        )
        apply_exec_style(fig, title="Top 10 Routen nach Umsatz")

        # Stats Sidebar
        top_route = df.iloc[0]
        stats_html = html.Div([
            html.Div(
                className="kpi",
                style={"marginBottom": "10px"},
                children=[
                    html.P("Top Route (Umsatz)", className="kpi-title"),
                    html.H3(f"{top_route['route_label']}", style={"fontSize": "16px", "margin": "5px 0"}),
                    html.P(f"${top_route['revenue']:,.0f}", className="kpi-value", style={"color": "var(--primary)"})
                ]
            ),
             html.Div(
                className="kpi",
                children=[
                    html.P("Durchschnittspreis Top Route", className="kpi-title"),
                    html.H3(f"${top_route['avg_fare']:.2f}", className="kpi-value")
                ]
            ),
            html.P("Der Chart zeigt, welche Borough-Verbindungen das meiste Geld einbringen. Der Wert im Balken ist der Ø Fahrpreis pro Trip.", 
                   style={"fontSize": "12px", "color": "var(--muted)", "marginTop": "20px"})
        ])

        return fig, stats_html

    # ===================================================
    # DEEP DIVE 3: TIPS (Distribution & Zones)
    # ===================================================

    # Toggle Logic
    @app.callback(
        Output("modal-tip-deepdive", "style"),
        [Input("btn-open-modal-tip", "n_clicks"),
         Input("btn-close-modal-tip", "n_clicks")],
        [State("modal-tip-deepdive", "style")]
    )
    def toggle_modal_tip(n_open, n_close, current_style):
        if not n_open and not n_close:
            return current_style 
        
        trigger_id = ctx.triggered_id
        if trigger_id == "btn-open-modal-tip":
            return {"display": "flex"} 
        elif trigger_id == "btn-close-modal-tip":
            return {"display": "none"}
            
        return current_style

    # Content Update
    @app.callback(
        [Output("fig-tip-distribution", "figure"),
         Output("modal-tip-zones-list", "children")],
        [Input("filter-taxi-type", "value"),
         Input("filter-year", "value"),
         Input("filter-borough", "value"),
         Input("btn-open-modal-tip", "n_clicks")],
        [State("modal-tip-deepdive", "style")]
    )
    def update_tip_deepdive(taxi_type, year, borough, n_clicks, modal_style):
        is_open = modal_style and modal_style.get("display") == "flex"
        if ctx.triggered_id != "btn-open-modal-tip" and not is_open:
            return no_update, no_update

        if not taxi_type: taxi_type = "ALL"

        # 1. Histogramm laden
        df_dist = load_tip_distribution(taxi_type, year, borough)
        
        if df_dist.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten")
            apply_exec_style(fig)
        else:
            fig = px.bar(
                df_dist, 
                x="tip_bin", 
                y="trips",
                title="Verteilung der Trinkgelder (Passenger Psychology)",
                text_auto='.2s'
            )
            fig.update_layout(
                xaxis_title="Trinkgeld Anteil (%)",
                yaxis_title="Anzahl Fahrten",
                bargap=0.1
            )
            apply_exec_style(fig)

        # 2. Top Zonen laden
        top_zones = load_top_tipping_zones(taxi_type, year, borough)
        
        if not top_zones:
            list_html = html.P("Keine Daten verfügbar.")
        else:
            rows = []
            for i, zone in enumerate(top_zones):
                medal = "🥇 " if i==0 else ("🥈 " if i==1 else ("🥉 " if i==2 else f"{i+1}. "))
                
                rows.append(html.Div(
                    className="kpi", 
                    style={"padding": "10px", "marginBottom": "8px", "boxShadow": "none", "border": "1px solid #eee"},
                    children=[
                        html.Div(f"{medal}{zone['zone']}", style={"fontWeight": "600", "fontSize": "13px"}),
                        html.Div(
                            style={"display": "flex", "justifyContent": "space-between", "marginTop": "4px"},
                            children=[
                                html.Span(f"Ø {zone['weighted_tip_pct']:.1f}%", style={"color": "#16a34a", "fontWeight": "bold"}),
                                html.Span(f"{int(zone['total_trips']):,} Trips", style={"color": "#94a3b8", "fontSize": "11px"})
                            ]
                        )
                    ]
                ))
            list_html = html.Div(rows)

        return fig, list_html

    # ===================================================
    # DEEP DIVE 4: DEMAND SHIFT (Market Evolution)
    # ===================================================

    # Toggle Logic
    @app.callback(
        Output("modal-demand-deepdive", "style"),
        [Input("btn-open-modal-demand", "n_clicks"),
         Input("btn-close-modal-demand", "n_clicks")],
        [State("modal-demand-deepdive", "style")]
    )
    def toggle_modal_demand(n_open, n_close, current_style):
        if not n_open and not n_close:
            return current_style 
        
        trigger_id = ctx.triggered_id
        if trigger_id == "btn-open-modal-demand":
            return {"display": "flex"} 
        elif trigger_id == "btn-close-modal-demand":
            return {"display": "none"}
            
        return current_style

    # Content Update
    @app.callback(
        [Output("fig-monthly-seasonality", "figure"),
         Output("fig-taxi-war", "figure"),
         Output("modal-demand-stats", "children")],
        [Input("filter-taxi-type", "value"),
         Input("filter-borough", "value"),
         Input("filter-year", "value"),
         Input("btn-open-modal-demand", "n_clicks")],
        [State("modal-demand-deepdive", "style")]
    )
    def update_demand_deepdive(taxi_type, borough, year, n_clicks, modal_style):
        is_open = modal_style and modal_style.get("display") == "flex"
        if ctx.triggered_id != "btn-open-modal-demand" and not is_open:
            return no_update, no_update, no_update

        if not taxi_type: taxi_type = "ALL"

        # --- Chart 1: Seasonality ---
        df_seas = load_seasonality_data(taxi_type, borough, year)
        
        if df_seas.empty:
            fig_seas = go.Figure()
            apply_exec_style(fig_seas, title="Keine Daten")
        else:
            fig_seas = px.line(
                df_seas, 
                x="month_name", 
                y="trips", 
                color="year", 
                markers=True,
                category_orders={"month_name": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]}
            )
            fig_seas.update_layout(xaxis_title="Monat", yaxis_title="Anzahl Fahrten")
            
            # Dynamischer Titel
            year_title = "Alle Jahre"
            if year:
                if isinstance(year, list):
                    year_title = ", ".join(map(str, year))
                else:
                    year_title = str(year)
                    
            apply_exec_style(fig_seas, title=f"Saisonalität ({year_title})")

        # --- Chart 2: Taxi War ---
        df_war = load_market_share_trend(borough)
        
        if df_war.empty:
            fig_war = go.Figure()
            apply_exec_style(fig_war, title="Keine Daten")
        else:
            color_map = {"YELLOW": "#f1c40f", "GREEN": "#2ecc71", "FHV": "#636e72", "FHV - High Volume": "#2d3436"}
            fig_war = px.area(
                df_war, 
                x="year", 
                y="trips", 
                color="taxi_type", 
                color_discrete_map=color_map
            )
            fig_war.update_layout(xaxis_title="Jahr", yaxis_title="Marktanteile (Trips)")
            apply_exec_style(fig_war, title=f"Marktentwicklung ({borough if borough else 'NYC Gesamt'})")

        # --- Stats Text ---
        stats_html = html.Div([
            html.P("Analyse:", style={"fontWeight": "bold", "marginBottom": "5px"}),
            html.Ul([
                html.Li(f"Oben: Saisonaler Verlauf für die gewählten Jahre ({year_title})."),
                html.Li(f"Unten: Langfristige Verdrängung im Gebiet '{borough if borough else 'NYC (Gesamt)'}'."),
                html.Li("FHV (Uber/Lyft) sind jetzt vollständig enthalten.")
            ], style={"fontSize": "12px", "paddingLeft": "15px", "color": "var(--text)"})
        ])

        return fig_seas, fig_war, stats_html