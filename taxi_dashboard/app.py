from pathlib import Path
from dash import Dash, dcc, html, Input, Output

# Layouts
from layouts.layout_predefined import layout_predefined
from layouts.layout_creative import layout_creative
from layouts.layout_location import layout_location

# Callbacks
from callbacks.predefined_callbacks import register_predefined_callbacks
from callbacks.creative_callbacks import register_creative_callbacks
from callbacks.location_callbacks import register_location_callbacks

# ---------------------------------------------------
# Pfade / Assets
# ---------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"

# ---------------------------------------------------
# Dash App Setup
# ---------------------------------------------------
app = Dash(
    __name__,
    title="NYC Taxi Dashboard (Task 2b)",
    suppress_callback_exceptions=True,
    assets_folder=str(ASSETS_DIR),
)

# ---------------------------------------------------
# UI-Bausteine: Sidebar-Filter
# ---------------------------------------------------
def sidebar_filters():
    """
    Linke Filter-Sidebar.
    Enthält Filter für Taxi-Typ, Jahr, Monat und Borough.
    """
    return html.Div(
        className="card",
        children=[
            html.P("Filter", className="section-title"),
            html.Div(
                className="filters",
                children=[
                    # Taxi-Typ (Multi-Select)
                    html.Div(
                        [
                            html.Div("Taxi-Typ", className="filter-label"),
                            dcc.Dropdown(
                                id="filter-taxi-type",
                                options=[], # Wird vom Callback gefüllt
                                value=[], 
                                placeholder="Alle Taxi-Typen",
                                multi=True,    
                                clearable=True, 
                            ),
                        ]
                    ),
                    # Jahr (Multi-Select)
                    html.Div(
                        [
                            html.Div("Jahr", className="filter-label"),
                            dcc.Dropdown(
                                id="filter-year",
                                options=[], 
                                value=[],      
                                placeholder="Alle Jahre",
                                multi=True,    
                                clearable=True,
                            ),
                        ]
                    ),
                    # Monat (Multi-Select) - HIER IST DER NEUE FILTER
                    html.Div(
                        [
                            html.Div("Monat", className="filter-label"),
                            dcc.Dropdown(
                                id="filter-month",
                                options=[], # Wird vom Callback gefüllt (Jan-Dez)
                                value=[],   # Leer = Alle Monate
                                placeholder="Alle Monate",
                                multi=True,    
                                clearable=True,
                            ),
                        ]
                    ),
                    # Borough (Multi-Select)
                    html.Div(
                        [
                            html.Div("Borough (Pickup)", className="filter-label"),
                            dcc.Dropdown(
                                id="filter-borough",
                                options=[], 
                                value=[],      
                                placeholder="Alle Boroughs",
                                multi=True,    
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
    return html.Div(
        className="kpis",
        children=[
            html.Div(
                className="kpi",
                children=[
                    html.P("Trips", className="kpi-title"),
                    html.P("—", id="kpi-trips", className="kpi-value"),
                    html.P("Gesamt im Filter", className="kpi-sub"),
                ],
            ),
            html.Div(
                className="kpi success",
                children=[
                    html.P("Ø Fare", className="kpi-title"),
                    html.P("—", id="kpi-avg-fare", className="kpi-value"),
                    html.P("USD pro Trip", className="kpi-sub"),
                ],
            ),
            html.Div(
                className="kpi warn",
                children=[
                    html.P("Ø Tip %", className="kpi-title"),
                    html.P("—", id="kpi-avg-tip", className="kpi-value"),
                    html.P("nur Card-Daten", className="kpi-sub"),
                ],
            ),
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
# UI-Bausteine: Insights Panel
# ---------------------------------------------------
def insights_panel():
    return html.Div(
        className="card",
        children=[
            html.P("Executive Insights", className="section-title"),
            html.Div(
                id="insight-text",
                style={"color": "#0f172a", "fontSize": "13px", "marginBottom": "10px"},
                children="Wähle Filter, um die wichtigsten Muster zu sehen.",
            ),
            html.H4("Top Boroughs (Trips)", style={"margin": "10px 0 6px 0", "fontSize": "13px"}),
            html.Table(
                className="table-lite",
                children=[
                    html.Thead(html.Tr([html.Th("Borough"), html.Th("Trips")])),
                    html.Tbody(id="tbl-top-boroughs", children=[]),
                ],
            ),
            html.H4("Top Hours", style={"margin": "12px 0 6px 0", "fontSize": "13px"}),
            html.Table(
                className="table-lite",
                children=[
                    html.Thead(html.Tr([html.Th("Hour"), html.Th("Trips")])),
                    html.Tbody(id="tbl-top-hours", children=[]),
                ],
            ),
        ],
    )

# ---------------------------------------------------
# App Layout
# ---------------------------------------------------
app.layout = html.Div(
    className="container",
    children=[
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
        kpi_row(),
        html.Div(
            className="shell",
            children=[
                html.Div(
                    className="sidebar",
                    children=[
                        sidebar_filters(),
                        insights_panel(),
                    ],
                ),
                html.Div(
                    className="main",
                    children=[
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
                        html.Div(id="tab-content"),
                    ],
                ),
            ],
        ),
    ],
)

# ---------------------------------------------------
# Callback für Tab-Wechsel
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
# Registrierung der Callbacks (Logik)
# ---------------------------------------------------
register_predefined_callbacks(app)
register_creative_callbacks(app)
register_location_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True)