from dash import dcc, html

def layout_creative():
    """
    Erstellt das Layout für den Creative-Tab.
    Die Charts sind als Cards in einem Grid angeordnet (siehe CSS: .grid-main).
    """
    return html.Div(
        # Grid-Container für die Hauptcharts (2 Spalten auf Desktop)
        className="grid-main",
        children=[
            # ---------------------------------------------------
            # 1) Airport Value Map: Sunburst
            # ---------------------------------------------------
            html.Div(
                className="card",
                children=[
                    html.Div(
                        className="card-head",
                        children=[
                            html.H3("Airport Value Map"),
                            html.P("Umsatz & Tip-Qualität (Sunburst)."),
                        ],
                    ),
                    dcc.Graph(
                        id="fig-airport-analysis",
                        # Standard-Höhe wie die anderen Graphen
                        style={"height": "340px"},
                        config={"displayModeBar": False},
                    ),
                ],
            ),

            # ---------------------------------------------------
            # 1) Demand Heatmap: Stunde × Wochentag
            # ---------------------------------------------------
            html.Div(
                className="card",
                children=[
                    html.Div(
                        className="card-head",
                        children=[
                            html.H3("Demand Heatmap"),
                            html.P("Nachfrage nach Zeit & Wochentag."),
                        ],
                    ),
                    dcc.Graph(
                        id="fig-heatmap",
                        style={"height": "340px"}, # Explizit setzen für Einheitlichkeit
                        config={"displayModeBar": False},
                    ),
                ],
            ),

            # ---------------------------------------------------
            # 2) Scatter: Fare vs Distance
            # ---------------------------------------------------
            html.Div(
                className="card",
                children=[
                    html.Div(
                        className="card-head",
                        children=[
                            html.H3("Fare vs Distance"),
                            html.P("Preistruktur und Ausreißer."),
                        ],
                    ),
                    dcc.Graph(
                        id="fig-scatter-fare-distance",
                        style={"height": "340px"},
                        config={"displayModeBar": False},
                    ),
                ],
            ),

            # ---------------------------------------------------
            # 3) Borough Flows: Pickup → Dropoff
            # ---------------------------------------------------
            html.Div(
                className="card",
                children=[
                    html.Div(
                        className="card-head",
                        children=[
                            html.H3("Pickup → Dropoff Flows"),
                            html.P("Dominante Verkehrsströme."),
                        ],
                    ),
                    dcc.Graph(
                        id="fig-flows",
                        style={"height": "340px"},
                        config={"displayModeBar": False},
                    ),
                ],
            ),

            # ---------------------------------------------------
            # 4) KPI: Revenue Efficiency
            # ---------------------------------------------------
            html.Div(
                className="card",
                children=[
                    html.Div(
                        className="card-head",
                        children=[
                            html.H3("Revenue Efficiency"),
                            html.P("Umsatz pro Minute (Boxplot)."),
                        ],
                    ),
                    dcc.Graph(
                        id="fig-kpi-rev-eff",
                        style={"height": "340px"},
                        config={"displayModeBar": False},
                    ),
                ],
            ),
            
            # ---------------------------------------------------
            # 5) Weekly Traffic Patterns (Breite Card unten)
            # ---------------------------------------------------
            html.Div(
                className="card",
                style={"gridColumn": "1 / -1"},
                children=[
                    html.Div(
                        className="card-head",
                        children=[
                            html.H3("Weekly Traffic Patterns"),
                            html.P("Gesamtverlauf Mo–So."),
                        ],
                    ),
                    dcc.Graph(
                        id="fig-weekly-patterns-creative", 
                        style={"height": "340px"}, 
                        config={"displayModeBar": False}
                    ),
                ],
            ),
            
            # ---------------------------------------------------
            # 6) IT & Data Quality Audit (Breite Card unten)
            # ---------------------------------------------------
            html.Div(
                className="card",
                style={"gridColumn": "1 / -1"}, 
                children=[
                    html.Div(
                        className="card-head",
                        children=[
                            html.H3("Data Quality Audit"),
                            html.P("GPS-Ausfälle & Datenfehler."),
                        ],
                    ),
                    dcc.Graph(
                        id="fig-quality-audit",
                        style={"height": "340px"},
                        config={"displayModeBar": False},
                    ),
                ],
            ),
        ],
    )