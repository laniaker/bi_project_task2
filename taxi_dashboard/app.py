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
    # Helper-Listen (Monate bleiben statisch, Jahre werden jetzt dynamisch)
    import calendar
    month_names = [{"label": calendar.month_name[i], "value": i} for i in range(1, 13)]

    return html.Div(
        className="card",
        style={"padding": "15px"}, 
        children=[
            # Header
            html.Div(
                style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "10px"},
                children=[
                    # HIER GEÄNDERT: Label statt P für Einheitlichkeit
                    html.Label("Filter", className="filter-label", style={"marginBottom": "0"}),
                ]
            ),
            
            # 1. MODUS SWITCH
            html.Div(
                className="radio-group",
                style={"marginBottom": "20px"},
                children=[
                    dcc.RadioItems(
                        id="time-filter-mode",
                        options=[
                            {"label": "Einzelauswahl", "value": "flexible"},
                            {"label": "Zeitstrahl", "value": "range"},
                        ],
                        value="flexible",
                        labelStyle={"display": "inline-block", "margin": "0"}, 
                        inputStyle={"marginRight": "5px"}
                    )
                ]
            ),

            html.Div(
                className="filters",
                children=[
                    # Taxi Typ
                    html.Div([
                        html.Label("Taxi Typ", className="filter-label"),
                        dcc.Checklist(
                            id="filter-taxi-type",
                            options=[], # Wird dynamisch befüllt
                            value=["YELLOW", "GREEN", "FHV"], 
                            inline=True,
                            className="taxi-checklist"
                        )
                    ], style={"marginBottom": "20px"}),

                    # --- CONTAINER A: FLEXIBEL (Einzelauswahl) ---
                    html.Div(
                        id="container-time-flexible",
                        children=[
                            html.Div([
                                html.Label("Jahre", className="filter-label"),
                                # HIER GEÄNDERT: options=[]
                                dcc.Dropdown(id="filter-year", options=[], value=[], placeholder="Wählen...", multi=True)
                            ], style={"marginBottom": "10px"}),
                            html.Div([
                                html.Label("Monate", className="filter-label"),
                                dcc.Dropdown(id="filter-month", options=month_names, value=[], placeholder="Wählen...", multi=True)
                            ])
                        ]
                    ),

                    # --- CONTAINER B: ZEITRAUM (Range / Zeitstrahl) ---
                    html.Div(
                        id="container-time-range",
                        style={"display": "none"},
                        children=[
                            html.Div(
                                style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "5px"},
                                children=[
                                    html.Label("Zeitraum definieren", className="filter-label", style={"marginBottom": 0}),
                                    html.Button("Reset", id="btn-reset-range", className="btn-ghost-sm")
                                ]
                            ),
                            
                            # Start
                            html.Div(
                                style={"display": "flex", "gap": "5px", "marginBottom": "8px"},
                                children=[
                                    dcc.Dropdown(id="range-start-month", options=month_names, placeholder="Start M.", style={"flex": 1}, clearable=False),
                                    # HIER GEÄNDERT: options=[]
                                    dcc.Dropdown(id="range-start-year", options=[], placeholder="J.", style={"flex": 0.6}, clearable=False),
                                ]
                            ),
                            
                            # Ende
                            html.Div(
                                style={"display": "flex", "gap": "5px"},
                                children=[
                                    dcc.Dropdown(id="range-end-month", options=month_names, placeholder="Ende M.", style={"flex": 1}, clearable=False),
                                    # HIER GEÄNDERT: options=[]
                                    dcc.Dropdown(id="range-end-year", options=[], placeholder="J.", style={"flex": 0.6}, clearable=False),
                                ]
                            ),
                            html.P("Zeitraum zwischen Start und Ende.", style={"fontSize": "10px", "color": "#94a3b8", "marginTop": "6px"})
                        ]
                    ),

                    # Borough
                    html.Div([
                        html.Label("Borough", className="filter-label", style={"marginTop": "15px"}),
                        dcc.Dropdown(id="filter-borough", options=[], value=[], placeholder="Alle...", multi=True)
                    ]),
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
# Callback: Zeitstrahl leeren (Reset Button Funktion)
# ---------------------------------------------------
@app.callback(
    [Output("range-start-year", "value"),
     Output("range-start-month", "value"),
     Output("range-end-year", "value"),
     Output("range-end-month", "value")],
    Input("btn-reset-range", "n_clicks"),
    prevent_initial_call=True
)
def reset_range_filters(n_clicks):
    return None, None, None, None

# ---------------------------------------------------
# Registrierung der Callbacks (Logik)
# ---------------------------------------------------
register_predefined_callbacks(app)
register_creative_callbacks(app)
register_location_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True)