from dash import dcc, html


def _card(title, graph_id, subtitle=None):
    """
    Interne Helper-Funktion zur Erstellung einer einheitlichen Chart-Card.
    Vermeidet Code-Duplikation und stellt ein konsistentes Layout sicher.
    """
    return html.Div(
        className="card",
        children=[
            # Card-Header mit Titel und optionalem Untertitel
            html.Div(
                className="card-head",
                children=[
                    html.H3(title),
                    html.P(subtitle or ""),  # leerer Text, falls kein Subtitle übergeben wird
                ],
            ),
            # Plotly-Graph: Figure wird über Callbacks gesetzt
            dcc.Graph(
                id=graph_id,
                config={
                    "displayModeBar": False,  # reduzierte UI für Executive-View
                    "responsive": True,       # reagiert auf Container-Größe
                },
                # feste Höhe für ruhiges Layout ohne Resize-Artefakte
                style={"height": "340px"},
            ),
        ],
    )


def layout_predefined():
    """
    Erstellt das Layout für den Predefined-Tab.
    Die Charts sind als Cards in einem Grid angeordnet (siehe CSS: .grid-main).
    """
    return html.Div(
        className="grid-main",
        children=[
            _card(
                "Peak Hours – Taxi Demand",
                "fig-peak-hours",
                "Trips pro Stunde (0–23).",
            ),
            _card(
                "Fares by Borough",
                "fig-fares-borough",
                "Boxplot: Median, Streuung, Ausreißer.",
            ),
            _card(
                "Average Tip Percentage",
                "fig-tip-percentage",
                "Ø Tip % (z. B. nach Jahr/Borough).",
            ),
            _card(
                "Demand Shift over Years",
                "fig-demand-years",
                "Zeitreihe: Nachfrageentwicklung.",
            ),
        ],
    )
