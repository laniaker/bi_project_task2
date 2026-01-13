from dash import dcc, html

def layout_location():
    """
    Erstellt das Layout für den Location-Tab.
    Die Karte wird innerhalb eines Grids dargestellt und nutzt Callbacks für die Datenvisualisierung.
    """
    return html.Div(
        className="grid-main", # Nutzung des globalen Grid-Systems für konsistente Abstände
        children=[
            html.Div(
                className="card",
                # Die Card wird über zwei Spalten gestreckt, um die volle Breite zu nutzen
                style={
                    "gridColumn": "span 2", 
                },
                children=[
                    # Header-Bereich der Card mit Titeln
                    html.Div(
                        className="card-head",
                        children=[
                            html.H3("Geografische Analyse NYC"),
                            html.P("Pickup-Hotspots im Überblick."),
                        ],
                    ),
                    # Karten-Komponente zur Darstellung der geografischen Daten
                    dcc.Graph(
                        id="fig-location-map",
                        config={
                            "displayModeBar": False, # Deaktiviert die Standard-Menüleiste von Plotly
                            "scrollZoom": True,      # Ermöglicht das Zoomen mit dem Mausrad
                            "responsive": True       # Passt die Grafik automatisch an Container-Größen an
                        },
                        # Höhe ist auf 340px gesetzt, um die Konsistenz zu anderen Dashboard-Plots zu wahren
                        style={
                            "height": "340px", 
                            "width": "100%"
                        } 
                    ),
                ],
            ),
        ],
    )