from dash import dcc, html

def layout_location():
    """
    Layout für den neuen 'Location'-Tab.
    Aktuell: Ein Platzhalter für eine Karte oder geografische Analyse.
    """
    return html.Div(
        className="grid-one-col", # Oder "grid-main" wenn du später mehr willst
        children=[
            html.Div(
                className="card",
                children=[
                    html.Div(
                        className="card-head",
                        children=[
                            html.H3("Geografische Analyse"),
                            html.P("Platzhalter für Mapbox Choropleth oder Scatter Map."),
                        ],
                    ),
                    dcc.Graph(
                        id="fig-location-map",
                        config={"displayModeBar": False},
                        style={"height": "600px"} # Etwas höher für Karten
                    ),
                ],
            ),
        ],
    )