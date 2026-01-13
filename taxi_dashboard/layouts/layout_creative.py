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
            # 1) Demand Heatmap: Stunde × Wochentag
            # ---------------------------------------------------
            html.Div(
                className="card",
                children=[
                    # Card-Header: Titel + kurze inhaltliche Einordnung
                    html.Div(
                        className="card-head",
                        children=[
                            html.H3("Demand Heatmap (Hour × Weekday)"),
                            html.P(
                                "Hohe Informationsdichte: Muster der Nachfrage "
                                "nach Wochentag und Tageszeit."
                            ),
                        ],
                    ),
                    # Plotly-Graph (Figure wird per Callback befüllt)
                    dcc.Graph(
                        id="fig-heatmap",
                        config={"displayModeBar": False},  # reduzierte UI, Fokus auf Inhalt
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
                            html.H3("Fare vs Distance (Scatter)"),
                            html.P(
                                "Erlaubt das Erkennen von Ausreißern, z. B. "
                                "hohe Fahrpreise bei kurzer Distanz oder umgekehrt."
                            ),
                        ],
                    ),
                    dcc.Graph(
                        id="fig-scatter-fare-distance",
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
                            html.P(
                                "Visualisiert dominante Verkehrsströme zwischen "
                                "den Boroughs, farblich nach Dropoff-Ziel."
                            ),
                        ],
                    ),
                    dcc.Graph(
                        id="fig-flows",
                        config={"displayModeBar": False},
                    ),
                ],
            ),

            # ---------------------------------------------------
            # 4) KPI: Revenue Efficiency (Fare pro Minute)
            # ---------------------------------------------------
            html.Div(
                className="card",
                children=[
                    html.Div(
                        className="card-head",
                        children=[
                            html.H3("Revenue Efficiency (Fare per Minute)"),
                            html.P(
                                "Boxplot zur Analyse der Verteilung, Streuung "
                                "und Ausreißer je definierter Gruppe (Bucket)."
                            ),
                        ],
                    ),
                    dcc.Graph(
                        id="fig-kpi-rev-eff",
                        config={"displayModeBar": False},
                    ),
                ],
            ),
            # ---------------------------------------------------
            # 5) Weekly Traffic Patterns
            # ---------------------------------------------------
            html.Div(
                className="card",
                style={"gridColumn": "1 / -1"},
                children=[
                    html.Div(
                        className="card-head",
                        children=[
                            html.H3("Weekly Traffic Patterns (Linear)"),
                            html.P("Gesamtverlauf Mo–So (gestapelt nach Taxi-Typ)."),
                        ],
                    ),
                    dcc.Graph(id="fig-weekly-patterns-creative", style={"height": "340px"}, config={"displayModeBar": False}),
                ],
            ),
        ],
    )
