from dash import Input, Output
import plotly.graph_objects as go
from utils.plot_style import apply_exec_style

def register_location_callbacks(app):
    """
    Registriert Callbacks für den Location-Tab.
    """

    @app.callback(
        Output("fig-location-map", "figure"),
        Input("filter-taxi-type", "value"),
        Input("filter-year", "value"),
        Input("filter-borough", "value"),
    )
    def fig_location_placeholder(taxi_type, year, borough):
        # Einfacher Platzhalter-Plot
        fig = go.Figure()
        
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            annotations=[dict(
                text="Hier kommt die Karte hin 🗺️",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20, color="gray")
            )]
        )
        
        apply_exec_style(fig, title=f"Location Map Placeholder ({year if year else 'Alle Jahre'})")
        
        return fig