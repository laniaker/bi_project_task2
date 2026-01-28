from dash import Input, Output, State, html, dcc, ctx, no_update
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import calendar # Für Monatsnamen

# Einheitliches Styling für alle Visuals
from utils.plot_style import apply_exec_style

# Datenzugriff
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
    load_top_routes,
    load_revenue_efficiency,
    load_hourly_distance,
    load_weekly_passenger_split,
    load_hourly_price_curve,
    load_fare_breakdown,
    load_borough_flows,
    load_hourly_tip_trend, 
    load_tip_by_distance
)

def register_predefined_callbacks(app):
    """
    Registriert alle Callbacks für den 'Predefined'-Tab.
    Zuständig für die Interaktivität der Standard-Charts und der Deep Dive Modals.
    """

    # ---------------------------------------------------
    # Initialisierung der Filteroptionen
    # ---------------------------------------------------
    @app.callback(
        Output("filter-year", "options"),
        Output("range-start-year", "options"), 
        Output("range-end-year", "options"),   
        Output("filter-borough", "options"),
        Output("filter-taxi-type", "options"), 
        Output("filter-month", "options"),
        Input("filter-taxi-type", "id"), 
    )
    def init_filter_options(_):
        results = get_filter_options()
        
        if len(results) == 3:
            years, boroughs, taxi_types = results
            months = list(range(1, 13))
        else:
            years, boroughs, taxi_types, months = results

        # Wunsch-Reihenfolge für Taxis (wie besprochen)
        desired_order = ["YELLOW", "GREEN", "FHV"]
        taxi_types_sorted = sorted(
            taxi_types, 
            key=lambda x: desired_order.index(x) if x in desired_order else 999
        )

        # Optionen erstellen
        year_opts = [{"label": str(y), "value": y} for y in years]
        borough_opts = [{"label": b, "value": b} for b in boroughs]
        taxi_opts = [{"label": t, "value": t} for t in taxi_types_sorted]
        month_opts = [{"label": calendar.month_name[m], "value": m} for m in months]

        # WICHTIG: year_opts wird jetzt dreimal zurückgegeben
        return year_opts, year_opts, year_opts, borough_opts, taxi_opts, month_opts

    # ---------------------------------------------------
    # Chart 1: Peak Hours (Standard Balkendiagramm)
    # ---------------------------------------------------
    @app.callback(
        Output("fig-peak-hours", "figure"),
        [
            Input("filter-taxi-type", "value"),
            Input("filter-year", "value"),
            Input("filter-borough", "value"),
            Input("filter-month", "value"),
            # NEUE INPUTS
            Input("time-filter-mode", "value"),
            Input("range-start-year", "value"),
            Input("range-start-month", "value"),
            Input("range-end-year", "value"),
            Input("range-end-month", "value")
        ]
    )
    def fig_peak_hours(taxi_type, year, borough, month, mode, sy, sm, ey, em):
        if not taxi_type: taxi_type = "ALL"
        
        # Keyword Arguments nutzen, um sicherzugehen
        df = load_peak_hours(
            taxi_type=taxi_type, borough=borough, 
            mode=mode, years=year, months=month, 
            sy=sy, sm=sm, ey=ey, em=em
        )

        if df.empty:
            fig = go.Figure()
            fig.update_layout(title="Keine Daten für diese Auswahl")
            apply_exec_style(fig) # Style auch bei leerem Plot!
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
        [
            Input("filter-taxi-type", "value"),
            Input("filter-year", "value"),
            Input("filter-month", "value"),
            # NEUE INPUTS
            Input("time-filter-mode", "value"),
            Input("range-start-year", "value"),
            Input("range-start-month", "value"),
            Input("range-end-year", "value"),
            Input("range-end-month", "value")
        ]
    )
    def fig_fares(taxi_type, year, month, mode, sy, sm, ey, em):
        if not taxi_type: taxi_type = "ALL"

        df = load_fares_by_borough(
            taxi_type=taxi_type, 
            mode=mode, years=year, months=month, 
            sy=sy, sm=sm, ey=ey, em=em
        )

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
        [
            Input("filter-taxi-type", "value"),
            Input("filter-year", "value"),
            Input("filter-borough", "value"),
            Input("filter-month", "value"),
            # NEUE INPUTS
            Input("time-filter-mode", "value"),
            Input("range-start-year", "value"),
            Input("range-start-month", "value"),
            Input("range-end-year", "value"),
            Input("range-end-month", "value")
        ]
    )
    def fig_tip_pct(taxi_type, year, borough, month, mode, sy, sm, ey, em):
        if not taxi_type: taxi_type = "ALL"

        df = load_tip_percentage(
            taxi_type=taxi_type, borough=borough,
            mode=mode, years=year, months=month, 
            sy=sy, sm=sm, ey=ey, em=em
        )

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
        [
            Input("filter-taxi-type", "value"),
            Input("filter-borough", "value"),
            Input("filter-month", "value"),
            # NEUE INPUTS
            Input("time-filter-mode", "value"),
            Input("filter-year", "value"), # Year hier explizit mitnehmen für Mode Switch
            Input("range-start-year", "value"),
            Input("range-start-month", "value"),
            Input("range-end-year", "value"),
            Input("range-end-month", "value")
        ]
    )
    def fig_demand_years(taxi_type, borough, month, mode, year, sy, sm, ey, em):
        if not taxi_type: taxi_type = "ALL"

        df = load_demand_over_years(
            taxi_type=taxi_type, borough=borough,
            mode=mode, years=year, months=month, 
            sy=sy, sm=sm, ey=ey, em=em
        )

        if df.empty:
            fig = go.Figure()
            apply_exec_style(fig)
            return fig

        fig = px.line(df, x="year", y="trips", markers=True)
        fig.update_layout(xaxis_title="Jahr", yaxis_title="Gesamtfahrten")
        apply_exec_style(fig, title="Entwicklung der Nachfrage über Jahre")
        return fig
    
    # ---------------------------------------------------
    # KPI-Update (Obere Leiste & Deep Dive Modal)
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
            Input("filter-month", "value"),
            # NEUE INPUTS
            Input("time-filter-mode", "value"),
            Input("range-start-year", "value"),
            Input("range-start-month", "value"),
            Input("range-end-year", "value"),
            Input("range-end-month", "value")
        ]
    )
    def update_kpis_only(taxi_type, year, borough, month, mode, sy, sm, ey, em):
        if not taxi_type: taxi_type = "ALL"

        trips, fare, tip, outlier = get_kpi_data(
            taxi_type=taxi_type, borough=borough,
            mode=mode, years=year, months=month, 
            sy=sy, sm=sm, ey=ey, em=em
        )
        
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
            Input("filter-month", "value"),
            # NEUE INPUTS
            Input("time-filter-mode", "value"),
            Input("range-start-year", "value"),
            Input("range-start-month", "value"),
            Input("range-end-year", "value"),
            Input("range-end-month", "value")
        ]
    )
    def update_insights_panel(taxi_type, year, borough, month, mode, sy, sm, ey, em):
        if not taxi_type: taxi_type = "ALL"

        top_b_data = get_top_boroughs(
            taxi_type=taxi_type, 
            mode=mode, years=year, months=month, 
            sy=sy, sm=sm, ey=ey, em=em
        )
        top_h_data = get_top_hours(
            taxi_type=taxi_type, borough=borough, 
            mode=mode, years=year, months=month, 
            sy=sy, sm=sm, ey=ey, em=em
        )

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

    # ---------------------------------------------------
    # Modal Open/Close Logic (Deep Dive 1: Peak Hours)
    # ---------------------------------------------------
    @app.callback(
        Output("modal-peak-hours", "style"),
        [Input("btn-open-modal", "n_clicks"),
         Input("btn-close-modal", "n_clicks")],
        [State("modal-peak-hours", "style")]
    )
    def toggle_modal(n_open, n_close, current_style):
        if not n_open and not n_close:
            return current_style 

        trigger_id = ctx.triggered_id
        if trigger_id == "btn-open-modal":
            return {"display": "flex"} 
        elif trigger_id == "btn-close-modal":
            return {"display": "none"} 
        return current_style

    # ---------------------------------------------------
    # Inhalt des Deep-Dive Modals 1 (Weekly + Heatmap + Distance + Pax Split)
    # ---------------------------------------------------
    @app.callback(
        [Output("fig-peak-hours-deepdive", "figure"),
         Output("fig-peak-hours-heatmap", "figure"),
         Output("fig-peak-distance", "figure"),
         Output("fig-peak-passengers", "figure"),      
         Output("modal-extra-stats", "children")],
        [
            Input("filter-taxi-type", "value"),
            Input("filter-year", "value"),      
            Input("filter-borough", "value"),   
            Input("filter-month", "value"),
            Input("time-filter-mode", "value"),
            Input("range-start-year", "value"),
            Input("range-start-month", "value"),
            Input("range-end-year", "value"),
            Input("range-end-month", "value"),
            Input("btn-open-modal", "n_clicks")
        ],
        [State("modal-peak-hours", "style")]
    )
    def update_peak_deepdive(taxi, year, borough, month, mode, sy, sm, ey, em, n_clicks, modal_style):
        
        if not taxi: taxi = "ALL"

        # 1. Daten laden (Patterns für Hauptcharts)
        df = load_weekly_patterns(
            taxi_type=taxi, borough=borough, 
            mode=mode, years=year, months=month, 
            sy=sy, sm=sm, ey=ey, em=em
        )
        
        if df.empty:
            empty = go.Figure()
            apply_exec_style(empty, title="Keine Daten")
            return empty, empty, empty, empty, "Keine Daten."

        # Gemeinsame Sortierung für Wochenverlauf
        week_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # --- CHART 1: Balken (Volumen) ---
        df["day_name"] = pd.Categorical(df["day_name"], categories=week_order, ordered=True)
        df = df.sort_values(by=["day_name", "hour"])
        df["time_label"] = df["day_name"].astype(str) + " " + df["hour"].astype(str).str.zfill(2) + ":00"

        color_map = {"YELLOW": "#f1c40f", "GREEN": "#2ecc71", "FHV": "#636e72", "FHV - High Volume": "#636e72"}
        taxi_stack_order = ["FHV", "FHV - High Volume", "GREEN", "YELLOW"]

        fig_bar = px.bar(
            df, x="time_label", y="trips", color="taxi_type", 
            category_orders={"taxi_type": taxi_stack_order}, color_discrete_map=color_map
        )
        fig_bar.update_layout(
            xaxis_title=None, yaxis_title="Trips", legend_title=None,
            xaxis=dict(tickangle=-45, nticks=15), margin=dict(t=40, b=40, l=40, r=20), bargap=0.0
        )
        apply_exec_style(fig_bar, title="Wochenverlauf (Detailansicht)")

        # --- CHART 2: Heatmap ---
        df_grouped = df.groupby(["day_name", "day_of_week", "hour"])['trips'].sum().reset_index()
        df_grouped = df_grouped.sort_values("day_of_week")

        fig_heat = px.density_heatmap(
            df_grouped, x="hour", y="day_name", z="trips",
            nbinsx=24, nbinsy=7, color_continuous_scale="Viridis",
            category_orders={"day_name": week_order}
        )
        fig_heat.update_layout(
            xaxis_title="Stunde (0-23)", yaxis_title=None, coloraxis_colorbar=dict(title="Trips"),
            margin=dict(t=40, b=40, l=60, r=20)
        )
        apply_exec_style(fig_heat, title="Heatmap: Wann ist am meisten los?")

        # --- CHART 3: DISTANCE (Links unten) ---
        df_dist = load_hourly_distance(
            taxi_type=taxi, borough=borough, mode=mode, years=year, months=month, 
            sy=sy, sm=sm, ey=ey, em=em
        )
        if df_dist.empty:
            fig_dist = go.Figure()
            apply_exec_style(fig_dist)
        else:
            fig_dist = px.line(df_dist, x="hour", y="avg_distance", markers=True, line_shape="spline")
            fig_dist.update_traces(line_color="#e74c3c", line_width=3)
            fig_dist.update_layout(
                xaxis_title="Uhrzeit", yaxis_title="Ø Meilen",
                margin=dict(t=40, b=40, l=40, r=20), xaxis=dict(tickmode='linear', tick0=0, dtick=4)
            )
            apply_exec_style(fig_dist, title="Fahrtdistanz-Profil (Tageszeit)")

        # --- CHART 4: WEEKLY PASSENGER SPLIT (Rechts unten - NEU!) ---
        df_pax = load_weekly_passenger_split(
            taxi_type=taxi, borough=borough, mode=mode, years=year, months=month, 
            sy=sy, sm=sm, ey=ey, em=em
        )
        
        if df_pax.empty:
            fig_pax = go.Figure()
            apply_exec_style(fig_pax, title="Keine Daten")
        else:
            # Sortierung sicherstellen
            df_pax["day_name"] = pd.Categorical(df_pax["day_name"], categories=week_order, ordered=True)
            df_pax = df_pax.sort_values(by=["day_name", "hour"])
            
            # X-Achse bauen (Gleiches Format wie oben)
            df_pax["time_label"] = df_pax["day_name"].astype(str) + " " + df_pax["hour"].astype(str).str.zfill(2) + ":00"

            # Farben definieren
            pax_colors = {
                "1 Passagier": "#3498db",    # Blau (Standard)
                "2 Passagiere": "#f1c40f",   # Gelb
                "3+ Passagiere": "#e74c3c"   # Rot (Gruppe)
            }

            fig_pax = px.line(
                df_pax, 
                x="time_label", 
                y="trips", 
                color="pax_group",
                color_discrete_map=pax_colors,
                category_orders={"pax_group": ["1 Passagier", "2 Passagiere", "3+ Passagiere"]}
            )
            
            fig_pax.update_layout(
                xaxis_title=None, 
                yaxis_title="Trips",
                margin=dict(t=40, b=40, l=40, r=20), 
                xaxis=dict(tickangle=-45, nticks=15), # Gleiche Achse wie Chart 1
                legend=dict(
                    orientation="h", 
                    yanchor="bottom", y=1.02, 
                    xanchor="right", x=1
                )
            )
            apply_exec_style(fig_pax, title="Passagiere im Wochenverlauf")

        # --- STATS (Bleiben gleich) ---
        df_sorted = df_grouped.sort_values(by="trips", ascending=False)
        top1 = df_sorted.iloc[0]
        top2 = df_sorted.iloc[1] if len(df_sorted) > 1 else None
        top3 = df_sorted.iloc[2] if len(df_sorted) > 2 else None

        weekend_days = ["Saturday", "Sunday"]
        total_trips = df_grouped['trips'].sum()
        weekend_trips = df_grouped[df_grouped['day_name'].isin(weekend_days)]['trips'].sum()
        weekend_share = (weekend_trips / total_trips * 100) if total_trips > 0 else 0
        
        stats_html = html.Div([
            html.Div(className="insight-card", children=[
                html.Span("🏆 Busiest Peak", className="insight-label"),
                html.H3(f"{top1['day_name']}, {top1['hour']}:00", className="insight-value"),
                html.P(f"{int(top1['trips']):,} Fahrten (Max)", className="insight-sub")
            ]),
            html.Div(className="insight-card", children=[
                html.Span("Nächste Spitzenzeiten", className="insight-label", style={"marginBottom": "10px"}),
                html.Div(style={"display": "flex", "justifyContent": "space-between", "marginBottom": "6px", "alignItems": "center"}, children=[
                    html.Span(f"🥈 {top2['day_name']} {top2['hour']}:00" if top2 is not None else "-", style={"fontWeight": "600", "fontSize": "13px", "color": "#334155"}),
                    html.Span(f"{int(top2['trips']):,}" if top2 is not None else "-", style={"fontSize": "12px", "color": "#64748b"})
                ]),
                html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"}, children=[
                    html.Span(f"🥉 {top3['day_name']} {top3['hour']}:00" if top3 is not None else "-", style={"fontWeight": "600", "fontSize": "13px", "color": "#334155"}),
                    html.Span(f"{int(top3['trips']):,}" if top3 is not None else "-", style={"fontSize": "12px", "color": "#64748b"})
                ]),
                html.P("Alternative Stoßzeiten.", className="insight-sub", style={"marginTop": "8px"})
            ]),
            html.Div(className="insight-card", children=[
                html.Span("Wochenend-Anteil", className="insight-label"),
                html.H3(f"{weekend_share:.1f}%", className="insight-value"),
                html.Div([
                    html.Div(className="progress-container", children=[
                        html.Div(className="progress-bar-fill", style={"width": f"{weekend_share}%"}) 
                    ]),
                    html.P("Anteil am Gesamtvolumen", className="insight-sub", style={"marginTop": "6px"})
                ])
            ])
        ])

        return fig_bar, fig_heat, fig_dist, fig_pax, stats_html

    # ---------------------------------------------------
    # Modal Open/Close Logic (Deep Dive 2: Fare Deep Dive)
    # ---------------------------------------------------
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

    @app.callback(
        [Output("fig-fare-hourly", "figure"),
         Output("fig-flows", "figure"),            # <--- NEUER OUTPUT 2
         Output("fig-fare-routes", "figure"),
         Output("fig-fare-breakdown", "figure"),
         Output("fig-kpi-rev-eff", "figure"),
         Output("modal-fare-stats", "children")],
        [
            Input("filter-taxi-type", "value"),
            Input("filter-year", "value"),
            Input("filter-borough", "value"),
            Input("filter-month", "value"),
            Input("time-filter-mode", "value"),
            Input("range-start-year", "value"),
            Input("range-start-month", "value"),
            Input("range-end-year", "value"),
            Input("range-end-month", "value"),
            Input("btn-open-modal-fare", "n_clicks")
        ],
        [State("modal-fare-deepdive", "style")]
    )
    def update_fare_deepdive(taxi_type, year, borough, month, mode, sy, sm, ey, em, n_clicks, modal_style):
        # Lazy Loading
        is_open = modal_style and modal_style.get("display") == "flex"
        if ctx.triggered_id != "btn-open-modal-fare" and not is_open:
            return no_update, no_update, no_update, no_update, no_update, no_update # 6 Returns!

        if not taxi_type: taxi_type = "ALL"

        # --- 1. HERO: HOURLY PRICE CURVE ---
        df_hourly = load_hourly_price_curve(taxi_type=taxi_type, borough=borough, mode=mode, years=year, months=month, sy=sy, sm=sm, ey=ey, em=em)
        if df_hourly.empty:
            fig_hourly = go.Figure()
            apply_exec_style(fig_hourly, title="Keine Daten")
            hourly_stats = None
        else:
            fig_hourly = px.line(df_hourly, x="hour", y="avg_price", markers=True, line_shape="spline")
            fig_hourly.update_traces(line_color="#e74c3c", line_width=3, fill='tozeroy', fillcolor="rgba(231, 76, 60, 0.1)")
            fig_hourly.update_layout(
                xaxis_title="Uhrzeit", yaxis_title="Ø Gesamtpreis ($)",
                margin=dict(t=40, b=40, l=60, r=20), xaxis=dict(tickmode='linear', tick0=0, dtick=2)
            )
            apply_exec_style(fig_hourly, title="Preisentwicklung im Tagesverlauf ($)")
            max_price_row = df_hourly.loc[df_hourly["avg_price"].idxmax()]
            min_price_row = df_hourly.loc[df_hourly["avg_price"].idxmin()]
            hourly_stats = (max_price_row, min_price_row)

        # --- 2. FLOWS (Pickup -> Dropoff) ---
        df_flows = load_borough_flows(taxi_type=taxi_type, borough=borough, mode=mode, years=year, months=month, sy=sy, sm=sm, ey=ey, em=em)
        if df_flows.empty:
            fig_flows = go.Figure()
            apply_exec_style(fig_flows, title="Keine Flow-Daten")
        else:
            fig_flows = px.bar(
                df_flows,
                x="pickup_borough",
                y="trips",
                color="dropoff_borough",
                # Schöne qualitative Farben für Unterscheidung
                color_discrete_sequence=px.colors.qualitative.Prism 
            )
            fig_flows.update_layout(
                xaxis_title=None, yaxis_title="Anzahl Fahrten", legend_title="Ziel",
                barmode="stack", margin=dict(l=40, r=40, t=40, b=40)
            )
            apply_exec_style(fig_flows, title="Verkehrsströme (Pickup → Dropoff)")

        # --- 3. TOP ROUTES ---
        df_routes = load_top_routes(taxi_type=taxi_type, borough=borough, mode=mode, years=year, months=month, sy=sy, sm=sm, ey=ey, em=em)
        if df_routes.empty:
            fig_routes = go.Figure()
            apply_exec_style(fig_routes)
            top_route_stats = None
        else:
            df_routes["route_label"] = df_routes["pickup_borough"] + " → " + df_routes["dropoff_borough"]
            fig_routes = px.bar(df_routes, x="revenue", y="route_label", orientation='h', text="avg_fare", color="revenue", color_continuous_scale="Blues")
            fig_routes.update_traces(texttemplate='$%{text:.2f}', textposition='inside')
            fig_routes.update_layout(yaxis={'categoryorder':'total ascending'})
            apply_exec_style(fig_routes, title="Top 10 Routen (Revenue)")
            top_route_stats = df_routes.iloc[0]

        # --- 4. BREAKDOWN ---
        df_break = load_fare_breakdown(taxi_type=taxi_type, borough=borough, mode=mode, years=year, months=month, sy=sy, sm=sm, ey=ey, em=em)
        if df_break.empty:
            fig_break = go.Figure()
            apply_exec_style(fig_break)
        else:
            fig_break = px.bar(
                df_break, x="borough", y=["avg_base_fare", "avg_fees_tolls", "avg_tip"],
                color_discrete_map={"avg_base_fare": "#3498db", "avg_fees_tolls": "#95a5a6", "avg_tip": "#f1c40f"}
            )
            fig_break.update_layout(barmode="stack", xaxis_title=None, yaxis_title="Ø Kosten ($)", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            new_names = {"avg_base_fare": "Fahrpreis", "avg_fees_tolls": "Gebühren/Maut", "avg_tip": "Trinkgeld"}
            fig_break.for_each_trace(lambda t: t.update(name = new_names.get(t.name, t.name)))
            apply_exec_style(fig_break, title="Preiszusammensetzung")

        # --- 5. EFFICIENCY ---
        df_eff = load_revenue_efficiency(taxi_type=taxi_type, borough=borough, mode=mode, years=year, months=month, sy=sy, sm=sm, ey=ey, em=em)
        if df_eff.empty:
            fig_eff = go.Figure()
            apply_exec_style(fig_eff)
        else:
            fig_eff = go.Figure()
            categories = sorted(df_eff["trip_category"].unique())
            for cat in categories:
                cat_data = df_eff[df_eff["trip_category"] == cat]
                fig_eff.add_trace(go.Box(
                    name=cat, x=[cat], 
                    q1=[cat_data["q1_val"].mean()], median=[cat_data["median_val"].mean()], q3=[cat_data["q3_val"].mean()],
                    lowerfence=[cat_data["min_val"].mean()], upperfence=[cat_data["max_val"].mean()],
                    marker_color="#3498db", showlegend=False
                ))
            fig_eff.update_layout(yaxis_title="$/min (Log)", yaxis=dict(type="log", autorange=True))
            apply_exec_style(fig_eff, title="Umsatz-Effizienz")

        # --- STATS SIDEBAR ---
        stats_content = []
        if hourly_stats:
            max_r, min_r = hourly_stats
            price_diff = max_r['avg_price'] - min_r['avg_price']
            stats_content.append(html.Div(className="insight-card", children=[
                html.Span("Teuerste Uhrzeit 📈", className="insight-label"),
                html.H3(f"{int(max_r['hour'])}:00 Uhr", className="insight-value"),
                html.P(f"${max_r['avg_price']:.2f} (vs. ${min_r['avg_price']:.2f} Minimum)", className="insight-sub"),
                html.Div(className="progress-container", style={"marginTop":"8px"}, children=[
                    html.Div(className="progress-bar-fill", style={"width": "80%", "background": "#e74c3c"}) 
                ]),
                html.P(f"Preisspanne: +${price_diff:.2f}", className="insight-sub", style={"fontSize": "11px"})
            ]))

        if top_route_stats is not None:
            stats_content.append(html.Div(className="insight-card", children=[
                html.Span("Top Route (Revenue)", className="insight-label"),
                html.H3(f"{top_route_stats['route_label']}", className="insight-value", style={"fontSize": "14px"}),
                html.P(f"${top_route_stats['revenue']:,.0f} Umsatz", className="insight-sub")
            ]))

        if not stats_content:
            stats_content = html.P("Keine Daten verfügbar.")
        else:
            stats_content = html.Div(stats_content)

        return fig_hourly, fig_flows, fig_routes, fig_break, fig_eff, stats_content

    # ---------------------------------------------------
    # Modal Open/Close Logic (Deep Dive 3: Tip Behavior)
    # ---------------------------------------------------
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

    # ---------------------------------------------------
    # Inhalt des Deep-Dive Modals 3 (Tip Behavior)
    # ---------------------------------------------------
    @app.callback(
        [Output("fig-tip-hourly", "figure"),
         Output("fig-tip-distribution", "figure"),
         Output("fig-tip-distance", "figure"),
         Output("modal-tip-zones-list", "children")],
        [
            Input("filter-taxi-type", "value"),
            Input("filter-year", "value"),
            Input("filter-borough", "value"),
            Input("filter-month", "value"),
            Input("time-filter-mode", "value"),
            Input("range-start-year", "value"),
            Input("range-start-month", "value"),
            Input("range-end-year", "value"),
            Input("range-end-month", "value"),
            Input("btn-open-modal-tip", "n_clicks")
        ],
        [State("modal-tip-deepdive", "style")]
    )
    def update_tip_deepdive(taxi_type, year, borough, month, mode, sy, sm, ey, em, n_clicks, modal_style):
        is_open = modal_style and modal_style.get("display") == "flex"
        if ctx.triggered_id != "btn-open-modal-tip" and not is_open:
            return no_update, no_update, no_update, no_update

        if not taxi_type: taxi_type = "ALL"

        # --- 1. HOURLY TREND ---
        df_trend = load_hourly_tip_trend(taxi_type=taxi_type, borough=borough, mode=mode, years=year, months=month, sy=sy, sm=sm, ey=ey, em=em)
        if df_trend.empty:
            fig_trend = go.Figure()
            apply_exec_style(fig_trend, title="Keine Daten")
        else:
            fig_trend = px.line(df_trend, x="hour", y="avg_tip_pct", markers=True, line_shape="spline")
            fig_trend.update_traces(line_color="#16a34a", line_width=3, fill='tozeroy', fillcolor="rgba(22, 163, 74, 0.1)")
            fig_trend.update_layout(
                xaxis_title="Uhrzeit", yaxis_title="Ø Trinkgeld (%)",
                margin=dict(t=40, b=40, l=40, r=20), xaxis=dict(tickmode='linear', tick0=0, dtick=2)
            )
            apply_exec_style(fig_trend, title="Tageszeit-Trend")

        # --- 2. DISTRIBUTION ---
        df_dist = load_tip_distribution(taxi_type=taxi_type, borough=borough, mode=mode, years=year, months=month, sy=sy, sm=sm, ey=ey, em=em)
        if df_dist.empty:
            fig_dist = go.Figure()
            apply_exec_style(fig_dist)
        else:
            fig_dist = px.bar(df_dist, x="tip_bin", y="trips", text_auto='.2s')
            fig_dist.update_traces(marker_color="#16a34a")
            fig_dist.update_layout(xaxis_title="Tip Bucket", yaxis_title="Anzahl Fahrten", bargap=0.1)
            apply_exec_style(fig_dist, title="Verteilung der Trinkgelder")

        # --- 3. DISTANCE (UPDATE: Granulare Meilen) ---
        df_distance = load_tip_by_distance(taxi_type=taxi_type, borough=borough, mode=mode, years=year, months=month, sy=sy, sm=sm, ey=ey, em=em)
        if df_distance.empty:
            fig_dist_plot = go.Figure()
            apply_exec_style(fig_dist_plot)
        else:
            # Wir verlassen uns auf die SQL-Sortierung (sort_key), daher kein category_orders nötig
            fig_dist_plot = px.bar(df_distance, x="dist_bucket", y="avg_tip_pct")
            fig_dist_plot.update_traces(marker_color="#86efac")
            fig_dist_plot.update_layout(
                xaxis_title="Distanz (Meilen)", 
                yaxis_title="Ø Trinkgeld (%)",
                xaxis=dict(tickangle=-45) # Labels schräg stellen, damit sie hinpassen
            )
            apply_exec_style(fig_dist_plot, title="Tip nach Distanz (Detail)")

        # --- 4. TOP ZONES LIST ---
        top_zones = load_top_tipping_zones(taxi_type=taxi_type, borough=borough, mode=mode, years=year, months=month, sy=sy, sm=sm, ey=ey, em=em)
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

        return fig_trend, fig_dist, fig_dist_plot, list_html

    # ---------------------------------------------------
    # Modal Open/Close Logic (Deep Dive 4: Demand)
    # ---------------------------------------------------
    @app.callback(
        Output("modal-demand-deepdive", "style"),
        [Input("btn-open-modal-demand", "n_clicks"),
         Input("btn-close-modal-demand", "n_clicks")],
        [State("modal-demand-deepdive", "style")]
    )
    def toggle_modal_demand(n_open, n_close, current_style):
        # Wenn noch nie geklickt wurde
        if not n_open and not n_close:
            return current_style 
        
        trigger_id = ctx.triggered_id
        
        if trigger_id == "btn-open-modal-demand":
            return {"display": "flex"} 
        elif trigger_id == "btn-close-modal-demand":
            return {"display": "none"}
            
        return current_style
    
    # ---------------------------------------------------
    # Inhalt des Deep-Dive Modals 4 (Seasonality & Taxi War)
    # ---------------------------------------------------
    @app.callback(
        [Output("fig-taxi-war", "figure"),
         Output("fig-yoy-growth", "figure"),
         Output("fig-monthly-seasonality", "figure"),
         Output("modal-demand-stats", "children")],
        [
            Input("filter-taxi-type", "value"),
            Input("filter-borough", "value"),
            # Wir nehmen die Zeit-Filter als Input, nutzen sie aber selektiv
            Input("filter-year", "value"), 
            Input("filter-month", "value"),
            Input("time-filter-mode", "value"),
            Input("range-start-year", "value"),
            Input("range-start-month", "value"),
            Input("range-end-year", "value"),
            Input("range-end-month", "value"),
            Input("btn-open-modal-demand", "n_clicks")
        ],
        [State("modal-demand-deepdive", "style")]
    )
    def update_demand_deepdive(taxi, borough, year, month, mode, sy, sm, ey, em, n_clicks, modal_style):
        is_open = modal_style and modal_style.get("display") == "flex"
        if ctx.triggered_id != "btn-open-modal-demand" and not is_open:
            return no_update, no_update, no_update, no_update

        if not taxi: taxi = "ALL"

        # -----------------------------------------------------------
        # WICHTIG: Für Trend-Analysen ignorieren wir den spezifischen Zeit-Filter
        # (years=None), damit wir immer die volle Entwicklung sehen.
        # Borough & Taxi Type werden aber strikt beachtet!
        # -----------------------------------------------------------

        # --- 1. TAXI WAR (Marktanteile) ---
        df_war = load_market_share_trend(
            taxi_type=taxi, borough=borough, 
            mode="flexible", years=None, months=None # Volle Historie erzwingen
        )
        
        if df_war.empty:
            fig_war = go.Figure()
            apply_exec_style(fig_war, title="Keine Daten")
        else:
            df_war["date_col"] = pd.to_datetime(df_war["year"].astype(str) + "-" + df_war["month"].astype(str) + "-01")
            color_map = {"YELLOW": "#f1c40f", "GREEN": "#2ecc71", "FHV": "#636e72", "FHV - High Volume": "#636e72"}
            fig_war = px.area(df_war, x="date_col", y="trips", color="taxi_type", color_discrete_map=color_map, groupnorm='percent')
            fig_war.update_layout(xaxis_title="Zeitraum", yaxis_title="Marktanteil (%)")
            apply_exec_style(fig_war, title="Der Taxi War (Marktanteile)")

        # --- 2. YOY GROWTH (Wachstumsraten) ---
        # Auch hier: Volle Historie laden, damit wir YoY berechnen können
        df_growth = load_demand_over_years(
            taxi_type=taxi, borough=borough, 
            mode="flexible", years=None, months=None 
        )

        if df_growth.empty:
            fig_growth = go.Figure()
            apply_exec_style(fig_growth)
        else:
            df_growth = df_growth.sort_values("year")
            # Prozentuale Änderung berechnen
            df_growth["pct_change"] = df_growth["trips"].pct_change() * 100
            
            # Farbe: Grün (>0) vs Rot (<0)
            df_growth["color"] = df_growth["pct_change"].apply(lambda x: "#2ecc71" if x >= 0 else "#e74c3c")
            
            fig_growth = go.Figure(go.Bar(
                x=df_growth["year"], 
                y=df_growth["pct_change"],
                marker_color=df_growth["color"],
                text=df_growth["pct_change"].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else ""),
                textposition="outside"
            ))
            # Y-Achse formatieren
            fig_growth.update_layout(xaxis_title="Jahr", yaxis_title="Wachstum (%)")
            apply_exec_style(fig_growth, title="Jährliches Wachstum (YoY)")

        # --- 3. SEASONALITY ---
        # Hier ist es okay, auf Jahre zu filtern, wenn man will. 
        # Aber für den Vergleich ist "Alle Jahre" meist besser. Wir lassen es auf "Alle".
        df_seas = load_seasonality_data(
            taxi_type=taxi, borough=borough,
            mode="flexible", years=None, months=None
        )
        
        if df_seas.empty:
            fig_seas = go.Figure()
            apply_exec_style(fig_seas)
        else:
            fig_seas = px.line(
                df_seas, x="month_name", y="trips", color="year", markers=True,
                category_orders={"month_name": list(calendar.month_name)[1:]}
            )
            fig_seas.update_layout(xaxis_title="Monat", yaxis_title="Trips")
            apply_exec_style(fig_seas, title="Saisonale Muster")

        # --- STATS SIDEBAR (INSIGHTS) ---
        stats_content = []
        
        if not df_growth.empty:
            # A) Recovery Rate (Vergleich letztes verfügbares Jahr vs. 2019)
            # Wir suchen das Jahr 2019 und das letzte Jahr im Datensatz
            row_2019 = df_growth[df_growth['year'] == 2019]
            last_year = df_growth['year'].max()
            row_last = df_growth[df_growth['year'] == last_year]

            if not row_2019.empty and not row_last.empty:
                val_2019 = row_2019.iloc[0]['trips']
                val_last = row_last.iloc[0]['trips']
                
                if val_2019 > 0:
                    recovery_rate = (val_last / val_2019) * 100
                    
                    # Farbe Logik
                    rec_color = "#e74c3c" # Rot
                    if recovery_rate >= 90: rec_color = "#2ecc71" # Grün
                    elif recovery_rate >= 70: rec_color = "#f1c40f" # Gelb

                    stats_content.append(html.Div(className="insight-card", children=[
                        html.Span(f"Recovery Rate ({last_year} vs '19)", className="insight-label"),
                        html.H3(f"{recovery_rate:.1f}%", className="insight-value", style={"color": rec_color}),
                        html.Div(className="progress-container", style={"marginTop":"8px"}, children=[
                            html.Div(className="progress-bar-fill", style={"width": f"{min(recovery_rate, 100)}%", "backgroundColor": rec_color}) 
                        ]),
                        html.P(f"Erholung gegenüber dem Vor-Corona Niveau.", className="insight-sub", style={"marginTop": "6px"})
                    ]))

            # B) Peak Year (Wann war am meisten los?)
            # Wir suchen das Jahr mit dem Maximum an Trips
            peak_row = df_growth.loc[df_growth['trips'].idxmax()]
            
            stats_content.append(html.Div(className="insight-card", children=[
                html.Span("Peak Year (Rekordjahr)", className="insight-label"),
                html.H3(f"{int(peak_row['year'])}", className="insight-value"),
                html.P(f"Höchste Nachfrage im betrachteten Zeitraum: {int(peak_row['trips']):,} Fahrten.", className="insight-sub")
            ]))
            
            # C) Kleiner Text-Hinweis zum Taxi War (nur wenn Daten da sind)
            if not df_war.empty:
                 stats_content.append(html.Div(className="insight-card", style={"border": "none", "boxShadow": "none", "background": "transparent", "padding": "0"}, children=[
                    html.P("Der Chart oben links zeigt deutlich die Verschiebung der Marktanteile von Yellow Cabs hin zu High-Volume FHVs (Uber/Lyft).", 
                           style={"fontSize": "12px", "color": "#64748b", "fontStyle": "italic"})
                ]))

        if not stats_content:
            stats_content = html.P("Keine Daten verfügbar.")
        else:
            stats_content = html.Div(stats_content)

        return fig_war, fig_growth, fig_seas, stats_content