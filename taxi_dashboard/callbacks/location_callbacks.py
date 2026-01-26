from dash import Input, Output
import plotly.express as px
from utils.data_access import load_trips_and_geometries

# Fokus-Koordinaten und Zoom-Stufen für die verschiedenen Stadtteile
BOROUGH_VIEWS = {
    "Manhattan": {"lat": 40.7831, "lon": -73.9712, "zoom": 11},
    "Brooklyn": {"lat": 40.6782, "lon": -73.9442, "zoom": 10.5},
    "Queens": {"lat": 40.7282, "lon": -73.7949, "zoom": 10},
    "Bronx": {"lat": 40.8448, "lon": -73.8648, "zoom": 11},
    "Staten Island": {"lat": 40.5795, "lon": -74.1502, "zoom": 11},
    "ALL": {"lat": 40.7128, "lon": -74.0060, "zoom": 9}
}

def register_location_callbacks(app):
    @app.callback(
        Output("fig-location-map", "figure"),
        [Input("filter-taxi-type", "value"),
         Input("filter-year", "value"),
         Input("filter-borough", "value")]
    )
    def update_map(taxi_type, year, borough):
        
        # 1. Zoom-Logik anpassen 
        target_view_key = "ALL" # Standard

        if borough:
            if isinstance(borough, list):
                if len(borough) == 1:
                    # Wenn genau EINER ausgewählt ist, zoomen wir dort hin
                    target_view_key = borough[0]
                else:
                    # Bei mehreren (oder 0) bleiben wir auf der Gesamtansicht
                    target_view_key = "ALL"
            # Falls es aus irgendeinem Grund doch ein String ist (Sicherheitsnetz)
            elif isinstance(borough, str):
                target_view_key = borough
        
        view = BOROUGH_VIEWS.get(target_view_key, BOROUGH_VIEWS["ALL"])


        # 2. Daten laden
        df, geojson_data = load_trips_and_geometries(taxi_type, year, borough)
        
        if df.empty or not geojson_data:
            # Leere Karte mit dem korrekten Zoom (view) anzeigen
            return px.scatter_mapbox(
                lat=[], lon=[],
                center={"lat": view["lat"], "lon": view["lon"]}, 
                zoom=view["zoom"], 
                title="Keine Daten"
            )

        # 3. Erstellung der Choropleth-Karte
        fig = px.choropleth_mapbox(
            df,
            geojson=geojson_data,
            locations="location_id",
            featureidkey="id",
            color="trip_count",
            color_continuous_scale="Viridis",
            mapbox_style="carto-positron",
            center={"lat": view["lat"], "lon": view["lon"]},
            zoom=view["zoom"],
            opacity=0.6,
            hover_name="zone", 
            hover_data={
                "location_id": True, 
                "borough": True,
                "trip_count": ":,"
            },
            labels={
                "location_id": "Location ID",
                "borough": "Borough",
                "trip_count": "Fahrten"
            }
        )

        fig.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
        return fig