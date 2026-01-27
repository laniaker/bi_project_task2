from pathlib import Path
from dash import Dash, dcc, html, Input, Output
import calendar

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
    Sidebar mit Umschalter zwischen 'Flexibel' (beliebige Auswahl) 
    und 'Zeitraum' (Von-Bis).
    """
    # Listen für die Dropdowns vorbereiten
    month_names = [{"label": calendar.month_name[i], "value": i} for i in range(1, 13)]
    years = [{"label": str(y), "value": y} for y in range(2019, 2026)]

    return html.Div(
        className="card",
        children=[
            html.P("Filter", className="section-title"),
            
            html.Div(
                className="filters",
                children=[
                    # 1. Taxi-Typ (Bleibt immer sichtbar)
                    html.Div(
                        [
                            html.Div("Taxi-Typ", className="filter-label"),
                            dcc.Dropdown(
                                id="filter-taxi-type",
                                options=[], # Wird via Callback gefüllt
                                value=[], 
                                placeholder="Alle Typen",
                                multi=True,    
                                clearable=True, 
                            ),
                        ],
                        style={"marginBottom": "20px"}
                    ),

                    # 2. Der Modus-Schalter (Radio Buttons)
                    html.Div(
                        style={
                            "backgroundColor": "#f8fafc", 
                            "padding": "10px", 
                            "borderRadius": "8px",
                            "marginBottom": "15px",
                            "border": "1px solid #e2e8f0"
                        },
                        children=[
                            html.Label("Zeit-Modus:", className="filter-label", style={"marginBottom": "8px"}),
                            dcc.RadioItems(
                                id="time-filter-mode",
                                options=[
                                    {"label": " Flexibel (Einzelwahl)", "value": "flexible"},
                                    {"label": " Zeitraum (Von → Bis)", "value": "range"},
                                ],
                                value="flexible", # Standard
                                labelStyle={"display": "block", "cursor": "pointer", "marginBottom": "4px", "fontSize": "13px"},
                                inputStyle={"marginRight": "8px"}
                            )
                        ]
                    ),

                    # 3. CONTAINER A: FLEXIBEL 
                    html.Div(
                        id="container-time-flexible",
                        children=[
                            html.Div(
                                [
                                    html.Div("Jahre wählen", className="filter-label"),
                                    dcc.Dropdown(
                                        id="filter-year",
                                        options=years, 
                                        value=[],      
                                        placeholder="Jahre...",
                                        multi=True,    
                                    ),
                                ],
                                style={"marginBottom": "10px"}
                            ),
                            html.Div(
                                [
                                    html.Div("Monate wählen", className="filter-label"),
                                    dcc.Dropdown(
                                        id="filter-month",
                                        options=month_names,
                                        value=[],   
                                        placeholder="Monate...",
                                        multi=True,    
                                    ),
                                ]
                            ),
                        ]
                    ),

                    # 4. CONTAINER B: ZEITRAUM 
                    html.Div(
                        id="container-time-range",
                        style={"display": "none"}, 
                        children=[
                            html.Label("Start Datum", className="filter-label", style={"marginTop": "5px"}),
                            html.Div(
                                style={"display": "flex", "gap": "5px", "marginBottom": "10px"},
                                children=[
                                    dcc.Dropdown(
                                        id="range-start-month",
                                        options=month_names,
                                        placeholder="Monat",
                                        style={"flex": 1},
                                        clearable=False
                                    ),
                                    dcc.Dropdown(
                                        id="range-start-year",
                                        options=years,
                                        placeholder="Jahr",
                                        style={"flex": 1},
                                        clearable=False
                                    ),
                                ]
                            ),
                            
                            # End Datum
                            html.Label("End Datum", className="filter-label"),
                            html.Div(
                                style={"display": "flex", "gap": "5px"},
                                children=[
                                    dcc.Dropdown(
                                        id="range-end-month",
                                        options=month_names,
                                        placeholder="Monat",
                                        style={"flex": 1},
                                        clearable=False
                                    ),
                                    dcc.Dropdown(
                                        id="range-end-year",
                                        options=years,
                                        placeholder="Jahr",
                                        style={"flex": 1},
                                        clearable=False
                                    ),
                                ]
                            ),
                            html.P("Filtert exakt den Zeitstrahl zwischen Start und Ende.", 
                                   style={"fontSize": "11px", "color": "#64748b", "marginTop": "10px", "fontStyle": "italic"})
                        ]
                    ),

                    # 5. Borough (Immer sichtbar)
                    html.Div(
                        [
                            html.Div("Borough", className="filter-label", style={"marginTop": "20px"}),
                            dcc.Dropdown(
                                id="filter-borough",
                                options=[], 
                                value=[],      
                                placeholder="Alle Boroughs",
                                multi=True,    
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
# UI Callback: Sichtbarkeit der Zeit-Filter steuern
# ---------------------------------------------------
@app.callback(
    [Output("container-time-flexible", "style"),
     Output("container-time-range", "style")],
    Input("time-filter-mode", "value")
)
def toggle_filter_mode(mode):
    if mode == "range":
        # Flexibel ausblenden, Range anzeigen
        return {"display": "none"}, {"display": "block"}
    else:
        # Flexibel anzeigen (Block), Range ausblenden (None)
        return {"display": "block"}, {"display": "none"}

# ---------------------------------------------------
# Registrierung der Callbacks (Logik)
# ---------------------------------------------------
register_predefined_callbacks(app)
register_creative_callbacks(app)
register_location_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True)