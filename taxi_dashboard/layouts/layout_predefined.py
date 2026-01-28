from dash import dcc, html

def _card(title, graph_id, subtitle=None, extra_header_content=None):
    """ Standard-Card Komponente """
    header_children = [
        html.Div([
            html.H3(title),
            html.P(subtitle or ""),
        ])
    ]
    if extra_header_content:
        header_children.append(html.Div(extra_header_content))

    return html.Div(
        className="card",
        children=[
            html.Div(
                className="card-head",
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-start"},
                children=header_children,
            ),
            dcc.Graph(
                id=graph_id,
                config={"displayModeBar": False, "responsive": True},
                style={"height": "340px"},
            ),
        ],
    )

# --- MODAL 1: PEAK HOURS (DEEP DIVE) ---
def _modal_overlay_peak():
    return html.Div(
        id="modal-peak-hours",
        className="modal-overlay",
        style={"display": "none"}, 
        children=[
            html.Div(
                className="card modal-card-extended",
                children=[
                    html.Div(
                        className="card-head modal-header-extended",
                        children=[
                            html.Div([html.H3("Weekly Traffic Analysis"), html.P("Detaillierte Wochenansicht.")]),
                            html.Button("✕", id="btn-close-modal", className="btn-icon-round btn-close-round"),
                        ]
                    ),
                    html.Div(
                        className="modal-body-grid",
                        children=[
                            html.Div(className="modal-chart-container", children=[
                                # 1. Wochenverlauf (Bleibt oben)
                                html.Div(className="card", children=[
                                    html.Div(className="card-head", children=[html.H3("Wochenverlauf"), html.P("Aufschlüsselung nach Zeit.")]),
                                    dcc.Graph(id="fig-peak-hours-deepdive", style={"height": "340px"}, config={"displayModeBar": False})
                                ]),

                                # 2. Passenger Profile (HIERHER VERSCHOBEN & Volle Größe)
                                html.Div(className="card", style={"marginTop": "16px"}, children=[
                                    html.Div(className="card-head", children=[
                                        html.H3("Passenger Profile"), 
                                        html.P("Ø Passagiere (Solo vs. Gruppen).")
                                    ]),
                                    dcc.Graph(id="fig-peak-passengers", style={"height": "340px"}, config={"displayModeBar": False})
                                ]),

                                # 3. Heatmap (Rutscht eins runter)
                                html.Div(className="card", style={"marginTop": "16px"}, children=[
                                    html.Div(className="card-head", children=[html.H3("Demand Heatmap"), html.P("Intensität: Stunde vs. Wochentag.")]),
                                    dcc.Graph(id="fig-peak-hours-heatmap", style={"height": "340px"}, config={"displayModeBar": False})
                                ]),

                                # 4. Distance (Rutscht nach ganz unten & Volle Größe)
                                html.Div(className="card", style={"marginTop": "16px"}, children=[
                                    html.Div(className="card-head", children=[
                                        html.H3("Trip Distance"), 
                                        html.P("Ø Meilen pro Fahrt.")
                                    ]),
                                    dcc.Graph(id="fig-peak-distance", style={"height": "340px"}, config={"displayModeBar": False})
                                ]),
                            ]),
                            html.Div(className="modal-stats-sidebar", children=[html.H4("Insights"), html.Div(id="modal-extra-stats")])
                        ]
                    )
                ]
            )
        ]
    )

# --- MODAL 2: FARE ANALYSIS (DEEP DIVE) ---
def _modal_overlay_fare():
    return html.Div(
        id="modal-fare-deepdive",
        className="modal-overlay",
        style={"display": "none"}, 
        children=[
            html.Div(
                className="card modal-card-extended",
                children=[
                    html.Div(
                        className="card-head modal-header-extended",
                        children=[
                            html.Div([
                                html.H3("Revenue & Pricing Analysis"), 
                                html.P("Preisanalyse im Detail: Zeit, Routen, Struktur und Effizienz.")
                            ]),
                            html.Button("✕", id="btn-close-modal-fare", className="btn-icon-round btn-close-round"),
                        ]
                    ),
                    html.Div(
                        className="modal-body-grid",
                        children=[
                            html.Div(
                                className="modal-chart-container",
                                style={"display": "flex", "flexDirection": "column", "gap": "16px"},
                                children=[
                                    
                                    # 1. Hourly Pricing Curve
                                    html.Div(className="card", children=[
                                        html.Div(className="card-head", children=[
                                            html.H3("Hourly Price Curve"),
                                            html.P("Durchschnittspreis im Tagesverlauf (Surge Pricing Indikator).")
                                        ]),
                                        dcc.Graph(id="fig-fare-hourly", style={"height": "340px"}, config={"displayModeBar": False})
                                    ]),

                                    # 2. NEU: Borough Flows (Hier eingefügt!)
                                    html.Div(className="card", children=[
                                        html.Div(className="card-head", children=[
                                            html.H3("Traffic Flows"),
                                            html.P("Wohin fahren die Taxis? (Pickup → Dropoff Verteilung).")
                                        ]),
                                        # Wir nutzen die ID 'fig-flows' wieder
                                        dcc.Graph(id="fig-flows", style={"height": "340px"}, config={"displayModeBar": False})
                                    ]),

                                    # 3. Top Routes
                                    html.Div(className="card", children=[
                                        html.Div(className="card-head", children=[
                                            html.H3("Top Revenue Routes"),
                                            html.P("Verbindungen mit höchstem Umsatz.")
                                        ]),
                                        dcc.Graph(id="fig-fare-routes", style={"height": "340px"}, config={"displayModeBar": False})
                                    ]),

                                    # 4. Cost Breakdown
                                    html.Div(className="card", children=[
                                        html.Div(className="card-head", children=[
                                            html.H3("Cost Structure"),
                                            html.P("Zusammensetzung des Preises (Fare vs. Fees vs. Tip).")
                                        ]),
                                        dcc.Graph(id="fig-fare-breakdown", style={"height": "340px"}, config={"displayModeBar": False})
                                    ]),

                                    # 5. Efficiency
                                    html.Div(className="card", children=[
                                        html.Div(className="card-head", children=[
                                            html.H3("Revenue Efficiency"),
                                            html.P("Umsatz pro Minute (Kurz vs. Lang)."),
                                        ]),
                                        dcc.Graph(id="fig-kpi-rev-eff", style={"height": "340px"}, config={"displayModeBar": False})
                                    ]),
                                ]
                            ),
                            # Sidebar
                            html.Div(
                                className="modal-stats-sidebar",
                                children=[
                                    html.H4("Analysis", className="section-title"),
                                    html.Div(id="modal-fare-stats")
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    )

# --- MODAL 3: TIP ANALYSIS (DEEP DIVE) ---
def _modal_overlay_tip():
    return html.Div(
        id="modal-tip-deepdive",
        className="modal-overlay",
        style={"display": "none"}, 
        children=[
            html.Div(
                className="card modal-card-extended",
                children=[
                    html.Div(
                        className="card-head modal-header-extended",
                        children=[
                            html.Div([
                                html.H3("Tipping Behavior & Psychology"), 
                                html.P("Wer gibt wann wie viel Trinkgeld?")
                            ]),
                            html.Button("✕", id="btn-close-modal-tip", className="btn-icon-round btn-close-round"),
                        ]
                    ),
                    html.Div(
                        className="modal-body-grid",
                        children=[
                            html.Div(
                                className="modal-chart-container",
                                style={"display": "flex", "flexDirection": "column", "gap": "16px"},
                                children=[
                                    
                                    # 1. Trend (NEU)
                                    html.Div(className="card", children=[
                                        html.Div(className="card-head", children=[
                                            html.H3("Generosity over Time"),
                                            html.P("Durchschnittliches Trinkgeld (%) nach Tageszeit.")
                                        ]),
                                        dcc.Graph(id="fig-tip-hourly", style={"height": "340px"}, config={"displayModeBar": False})
                                    ]),

                                    # 2. Distribution (Bestehend)
                                    html.Div(className="card", children=[
                                        html.Div(className="card-head", children=[
                                            html.H3("Tip Distribution"),
                                            html.P("Wie viele geben gar nichts, 15% oder 20%+?")
                                        ]),
                                        dcc.Graph(id="fig-tip-distribution", style={"height": "340px"}, config={"displayModeBar": False})
                                    ]),

                                    # 3. Distance (NEU)
                                    html.Div(className="card", children=[
                                        html.Div(className="card-head", children=[
                                            html.H3("Tip vs. Distance"),
                                            html.P("Einfluss der Fahrtdauer auf die Spendenfreudigkeit.")
                                        ]),
                                        dcc.Graph(id="fig-tip-distance", style={"height": "340px"}, config={"displayModeBar": False})
                                    ]),
                                ]
                            ),
                            # Sidebar
                            html.Div(
                                className="modal-stats-sidebar",
                                children=[
                                    html.H4("Top Tipping Zones", className="section-title"),
                                    html.Div(id="modal-tip-zones-list")
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    )

# --- MODAL 4: DEMAND SHIFT (DEEP DIVE) ---
# --- MODAL 4: DEMAND SHIFT (DEEP DIVE) ---
def _modal_overlay_demand():
    return html.Div(
        id="modal-demand-deepdive",
        className="modal-overlay",
        style={"display": "none"}, 
        children=[
            html.Div(
                className="card modal-card-extended",
                children=[
                    html.Div(
                        className="card-head modal-header-extended",
                        children=[
                            html.Div([
                                html.H3("Demand Shift Analysis"), 
                                html.P("Marktanteile und Wachstumsdynamik im Zeitverlauf.")
                            ]),
                            html.Button("✕", id="btn-close-modal-demand", className="btn-icon-round btn-close-round"),
                        ]
                    ),
                    html.Div(
                        className="modal-body-grid",
                        children=[
                            html.Div(
                                className="modal-chart-container",
                                style={"display": "flex", "flexDirection": "column", "gap": "16px"},
                                children=[
                                    
                                    # 1. Taxi War (Oben)
                                    html.Div(className="card", children=[
                                        html.Div(className="card-head", children=[
                                            html.H3("The Taxi War"),
                                            html.P("Marktanteile: Yellow Cab vs. FHV (Uber/Lyft).")
                                        ]),
                                        dcc.Graph(id="fig-taxi-war", style={"height": "340px"}, config={"displayModeBar": False})
                                    ]),

                                    # 2. YoY Growth (Mitte - NEU)
                                    html.Div(className="card", children=[
                                        html.Div(className="card-head", children=[
                                            html.H3("Year-over-Year Growth"),
                                            html.P("Jährliche Wachstumsrate (YoY) in Prozent.")
                                        ]),
                                        dcc.Graph(id="fig-yoy-growth", style={"height": "340px"}, config={"displayModeBar": False})
                                    ]),

                                    # 3. Seasonality (Unten)
                                    html.Div(className="card", children=[
                                        html.Div(className="card-head", children=[
                                            html.H3("Seasonal Patterns"),
                                            html.P("Saisonalität: Vergleich der Monatstrends.")
                                        ]),
                                        dcc.Graph(id="fig-monthly-seasonality", style={"height": "340px"}, config={"displayModeBar": False})
                                    ]),
                                ]
                            ),
                            # Sidebar Stats
                            html.Div(
                                className="modal-stats-sidebar",
                                children=[
                                    html.H4("Key Trends", className="section-title"),
                                    html.Div(id="modal-demand-stats")
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    )

def layout_predefined():
    return html.Div(
        children=[
            _modal_overlay_peak(),
            _modal_overlay_fare(),
            _modal_overlay_tip(),
            _modal_overlay_demand(),
            
            html.Div(
                className="grid-main",
                children=[
                    _card(
                        "Peak Hours – Taxi Demand",
                        "fig-peak-hours",
                        "Trips pro Stunde (0–23).",
                        extra_header_content=html.Button("🔍", id="btn-open-modal", className="btn-icon-round")
                    ),
                    _card(
                        "Fares by Borough",
                        "fig-fares-borough",
                        "Boxplot: Median, Streuung, Ausreißer.",
                        extra_header_content=html.Button("🔍", id="btn-open-modal-fare", className="btn-icon-round")
                    ),
                    _card(
                        "Average Tip Percentage",
                        "fig-tip-percentage",
                        "Ø Tip % (nach Borough).",
                        extra_header_content=html.Button("🔍", id="btn-open-modal-tip", className="btn-icon-round")
                    ),
                    _card(
                        "Demand Shift over Years",
                        "fig-demand-years",
                        "Zeitreihe: Nachfrageentwicklung.",
                        extra_header_content=html.Button("🔍", id="btn-open-modal-demand", className="btn-icon-round")
                    ),
                ],
            )
        ]
    )