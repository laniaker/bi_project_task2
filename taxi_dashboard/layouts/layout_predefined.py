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
                                html.Div(className="card", children=[
                                    html.Div(className="card-head", children=[html.H3("Wochenverlauf"), html.P("Aufschlüsselung nach Zeit.")]),
                                    dcc.Graph(id="fig-peak-hours-deepdive", style={"height": "340px"}, config={"displayModeBar": False})
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
                                html.H3("Revenue & Route Analysis"), 
                                html.P("Woher kommt der Umsatz? Top-Routen und Durchschnittspreise.")
                            ]),
                            html.Button("✕", id="btn-close-modal-fare", className="btn-icon-round btn-close-round"),
                        ]
                    ),
                    html.Div(
                        className="modal-body-grid",
                        children=[
                            html.Div(
                                className="modal-chart-container",
                                children=[
                                    # Plot 1: Top Routes
                                    html.Div(
                                        className="card",
                                        children=[
                                            html.Div(className="card-head", children=[
                                                html.H3("Top Revenue Routes"),
                                                html.P("Welche Verbindungen generieren den meisten Umsatz?")
                                            ]),
                                            dcc.Graph(id="fig-fare-routes", style={"height": "340px"}, config={"displayModeBar": False})
                                        ]
                                    ),
                                ]
                            ),
                            html.Div(
                                className="modal-stats-sidebar",
                                children=[
                                    html.H4("Route Insights", className="section-title"),
                                    html.Div(id="modal-fare-stats")
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    )

# --- MODAL 3: TIP BEHAVIOR (DEEP DIVE) ---
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
                            html.Div([html.H3("Passenger Tipping Behavior"), html.P("Trinkgeld-Verteilung.")]),
                            html.Button("✕", id="btn-close-modal-tip", className="btn-icon-round btn-close-round"),
                        ]
                    ),
                    html.Div(
                        className="modal-body-grid",
                        children=[
                            html.Div(className="modal-chart-container", children=[
                                html.Div(className="card", children=[
                                    html.Div(className="card-head", children=[html.H3("Verteilung"), html.P("Histogramm.")]),
                                    dcc.Graph(id="fig-tip-distribution", style={"height": "340px"}, config={"displayModeBar": False})
                                ]),
                            ]),
                            html.Div(className="modal-stats-sidebar", children=[html.H4("Top Zones"), html.Div(id="modal-tip-zones-list")])
                        ]
                    )
                ]
            )
        ]
    )

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
                            html.Div([html.H3("Market Evolution"), html.P("Saisonalität & Wettbewerb.")]),
                            html.Button("✕", id="btn-close-modal-demand", className="btn-icon-round btn-close-round"),
                        ]
                    ),
                    html.Div(
                        className="modal-body-grid",
                        children=[
                            html.Div(className="modal-chart-container", children=[
                                html.Div(className="card", children=[
                                    html.Div(className="card-head", children=[html.H3("Saisonalität"), html.P("Jahresvergleich.")]),
                                    dcc.Graph(id="fig-monthly-seasonality", style={"height": "340px"}, config={"displayModeBar": False})
                                ]),
                                html.Div(className="card", children=[
                                    html.Div(className="card-head", children=[html.H3("Taxi War"), html.P("Marktanteile.")]),
                                    dcc.Graph(id="fig-taxi-war", style={"height": "340px"}, config={"displayModeBar": False})
                                ]),
                            ]),
                            html.Div(className="modal-stats-sidebar", children=[html.H4("Insights"), html.Div(id="modal-demand-stats")])
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