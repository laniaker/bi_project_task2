from dash import dcc, html

def _card(title, graph_id, subtitle=None, extra_header_content=None):
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

# --- MODAL 1: PEAK HOURS ---
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
                            html.Div([html.H3("Weekly Traffic Analysis (Deep Dive)"), html.P("Detaillierte Wochenansicht.")]),
                            html.Button("✕", id="btn-close-modal", className="btn-icon-round btn-close-round"),
                        ]
                    ),
                    html.Div(
                        className="modal-body-grid",
                        children=[
                            html.Div(
                                className="modal-chart-container",
                                children=[dcc.Graph(id="fig-peak-hours-deepdive", style={"height": "100%"}, config={"displayModeBar": False})]
                            ),
                            html.Div(
                                className="modal-stats-sidebar",
                                children=[
                                    html.H4("Insights", className="section-title"),
                                    html.P("Nutze die Filter links.", style={"color": "var(--muted)", "fontSize": "13px"}),
                                    html.Div(id="modal-extra-stats")
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    )

# --- MODAL 2: TIP BEHAVIOR ---
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
                                html.H3("Passenger Tipping Behavior"),
                                html.P("Verteilung der Trinkgelder & Top-Zonen (Kreditkarte)."),
                            ]),
                            html.Button("✕", id="btn-close-modal-tip", className="btn-icon-round btn-close-round"),
                        ]
                    ),
                    html.Div(
                        className="modal-body-grid",
                        children=[
                            # Links: Das Histogramm
                            html.Div(
                                className="modal-chart-container",
                                children=[
                                    dcc.Graph(
                                        id="fig-tip-distribution", 
                                        style={"height": "100%"}, 
                                        config={"displayModeBar": False}
                                    )
                                ]
                            ),
                            # Rechts: Top Tipping Zones Liste
                            html.Div(
                                className="modal-stats-sidebar",
                                children=[
                                    html.H4("Top Tipping Zones", className="section-title"),
                                    html.P("Wo sind Passagiere am großzügigsten?", style={"color": "var(--muted)", "fontSize": "12px", "marginBottom": "15px"}),
                                    html.Div(id="modal-tip-zones-list")
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
            # Beide Modals einbinden (sie sind standardmäßig unsichtbar)
            _modal_overlay_peak(),
            _modal_overlay_tip(),
            
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
                    ),
                ],
            )
        ]
    )