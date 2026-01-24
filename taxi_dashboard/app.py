from pathlib import Path
from dash import Dash, dcc, html, Input, Output

from layouts.layout_predefined import layout_predefined
from layouts.layout_creative import layout_creative
from layouts.layout_location import layout_location

from callbacks.predefined_callbacks import register_predefined_callbacks
from callbacks.creative_callbacks import register_creative_callbacks
from callbacks.location_callbacks import register_location_callbacks

# ---------------------------------------------------
# Pfade / Assets
# ---------------------------------------------------
# Basisverzeichnis dieses Files (für stabile relative Pfade)
BASE_DIR = Path(__file__).resolve().parent
# Assets (CSS, ggf. Bilder) werden von Dash automatisch geladen 
ASSETS_DIR = BASE_DIR / "assets"

# ---------------------------------------------------
# Dash App Setup
# ---------------------------------------------------
app = Dash(
    __name__,
    title="NYC Taxi Dashboard (Task 2b)",
    # nötig, weil Tab-Inhalte dynamisch nachgeladen werden (IDs existieren nicht immer sofort)
    suppress_callback_exceptions=True,
    # explizites Assets-Verzeichnis (hier liegt z. B. theme.css)
    assets_folder=str(ASSETS_DIR),
)

# ---------------------------------------------------
# UI-Bausteine: Sidebar-Filter
# ---------------------------------------------------
def sidebar_filters():
    """
    Linke Filter-Sidebar (Taxi-Typ, Jahr, Borough).
    Year/Borough-Optionen werden per Callback dynamisch befüllt.
    """
    return html.Div(
        className="card",
        children=[
            html.P("Filter", className="section-title"),
            html.Div(
                className="filters",
                children=[
                    # Taxi-Typ (fixe Optionsliste)
                    html.Div(
                        [
                            html.Div("Taxi-Typ", className="filter-label"),
                            dcc.Dropdown(
                                id="filter-taxi-type",
                                options=[
                                    {"label": "Alle", "value": "ALL"},
                                    {"label": "Green", "value": "GREEN"},
                                    {"label": "Yellow", "value": "YELLOW"},
                                    {"label": "FHV", "value": "FHV"},
                                ],
                                value="ALL",
                                clearable=False,
                            ),
                        ]
                    ),
                    # Jahr (Optionen kommen aus der Datenbasis)
                    html.Div(
                        [
                            html.Div("Jahr", className="filter-label"),
                            dcc.Dropdown(
                                id="filter-year",
                                options=[],  # wird in predefined_callbacks initialisiert
                                value=None,
                                placeholder="Alle Jahre",
                                clearable=True,
                            ),
                        ]
                    ),
                    # Pickup Borough (Optionen kommen aus der Datenbasis)
                    html.Div(
                        [
                            html.Div("Borough (Pickup)", className="filter-label"),
                            dcc.Dropdown(
                                id="filter-borough",
                                options=[],  # wird in predefined_callbacks initialisiert
                                value=None,
                                placeholder="Alle Boroughs",
                                clearable=True,
                            ),
                        ]
                    ),
                ],
            ),
        ],
    )

# ---------------------------------------------------
# UI-Bausteine: KPI-Leiste (oben)
# ---------------------------------------------------
def kpi_row():
    """
    KPI-Row mit 4 Kennzahlen.
    Werte werden später per Callbacks befüllt.
    """
    return html.Div(
        className="kpis",
        children=[
            # KPI 1: Anzahl Trips
            html.Div(
                className="kpi",
                children=[
                    html.P("Trips", className="kpi-title"),
                    html.P("—", id="kpi-trips", className="kpi-value"),
                    html.P("Gesamt im Filter", className="kpi-sub"),
                ],
            ),
            # KPI 2: Durchschnittlicher Fare
            html.Div(
                className="kpi success",
                children=[
                    html.P("Ø Fare", className="kpi-title"),
                    html.P("—", id="kpi-avg-fare", className="kpi-value"),
                    html.P("USD pro Trip", className="kpi-sub"),
                ],
            ),
            # KPI 3: Durchschnittliche Tip-Quote (nur Kartenzahlungen)
            html.Div(
                className="kpi warn",
                children=[
                    html.P("Ø Tip %", className="kpi-title"),
                    html.P("—", id="kpi-avg-tip", className="kpi-value"),
                    html.P("nur Card-Daten", className="kpi-sub"),
                ],
            ),
            # KPI 4: Anteil Ausreißer (IQR-Regel)
            html.Div(
                className="kpi danger",
                children=[
                    html.P("Outlier Share", className="kpi-title"),
                    html.P("—", id="kpi-outlier", className="kpi-value"),
                    html.P("IQR-Definition", className="kpi-sub"),
                ],
            ),
        ],
    )

# ---------------------------------------------------
# UI-Bausteine: Insights Panel (Executive Summary + Tabellen)
# ---------------------------------------------------
def insights_panel():
    """
    Rechte/Linke Info-Card für Executive Insights:
    - Kurztext (automatisch/regelbasiert möglich)
    - Top Boroughs (Trips)
    - Top Hours (Trips)
    """
    return html.Div(
        className="card",
        children=[
            html.P("Executive Insights", className="section-title"),

            # Kurztext, der sich je nach Filter/Ergebnis ändern kann
            html.Div(
                id="insight-text",
                style={"color": "#0f172a", "fontSize": "13px", "marginBottom": "10px"},
                children="Wähle Filter, um die wichtigsten Muster zu sehen.",
            ),

            # Tabelle 1: Top Boroughs
            html.H4("Top Boroughs (Trips)", style={"margin": "10px 0 6px 0", "fontSize": "13px"}),
            html.Table(
                className="table-lite",
                children=[
                    html.Thead(html.Tr([html.Th("Borough"), html.Th("Trips")])),
                    # Body wird dynamisch befüllt
                    html.Tbody(id="tbl-top-boroughs", children=[]),
                ],
            ),

            # Tabelle 2: Top Hours
            html.H4("Top Hours", style={"margin": "12px 0 6px 0", "fontSize": "13px"}),
            html.Table(
                className="table-lite",
                children=[
                    html.Thead(html.Tr([html.Th("Hour"), html.Th("Trips")])),
                    # Body wird dynamisch befüllt
                    html.Tbody(id="tbl-top-hours", children=[]),
                ],
            ),
        ],
    )

# ---------------------------------------------------
# App Layout (Seitenaufbau)
# ---------------------------------------------------
app.layout = html.Div(
    className="container",
    children=[
        # Header / Titelbereich
        html.Div(
            className="header",
            children=[
                html.Div(
                    className="title",
                    children=[
                        html.H1("NYC Taxi – Dashboard"),
                        html.P("Pre-defined Reports & Creative Insights"),
                    ],
                ),
            ],
        ),

        # KPI-Leiste oben
        kpi_row(),

        # Hauptbereich: Sidebar + Main Content
        html.Div(
            className="shell",
            children=[
                # Sidebar (Filter + Insights)
                html.Div(
                    className="sidebar",
                    children=[
                        sidebar_filters(),
                        insights_panel(),
                    ],
                ),

                # Main Content (Tabs + Tab-Inhalt)
                html.Div(
                    className="main",
                    children=[
                        # Tabs in eigener Card (optisch abgesetzt)
                        html.Div(
                            className="card",
                            style={"marginBottom": "12px"},
                            children=[
                                dcc.Tabs(
                                    id="main-tabs",
                                    value="tab-predefined",
                                    children=[
                                        dcc.Tab(label="Pre-defined", value="tab-predefined"),
                                        dcc.Tab(label="Creative", value="tab-creative"),
                                        dcc.Tab(label="Location", value="tab-location"), 
                                    ],
                                )
                            ],
                        ),
                        # Tab-Content wird dynamisch gerendert
                        html.Div(id="tab-content"),
                    ],
                ),
            ],
        ),
    ],
)

# ---------------------------------------------------
# Tab Rendering: je nach Tab wird das passende Layout zurückgegeben
# ---------------------------------------------------
@app.callback(Output("tab-content", "children"), Input("main-tabs", "value"))
def render_tab(tab):
    if tab == "tab-creative":
        return layout_creative()
    elif tab == "tab-location":   
        return layout_location()
    else:
        return layout_predefined()

# ---------------------------------------------------
# Callback-Registrierung (Charts, Filter-Initialisierung etc.)
# ---------------------------------------------------
register_predefined_callbacks(app)
register_creative_callbacks(app)
register_location_callbacks(app)

# ---------------------------------------------------
# Lokaler Start
# ---------------------------------------------------
if __name__ == "__main__":
    # debug=True: Auto-Reload + Fehlerausgabe (für Entwicklung)
    app.run(debug=True)
