from dash import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from utils.data_access import load_trips_and_geometries
from utils.plot_style import apply_exec_style

# Fokus-Koordinaten und Zoom-Stufen
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
        [
            Input("filter-taxi-type", "value"),
            Input("filter-year", "value"),
            Input("filter-borough", "value"),
            Input("filter-month", "value") # Monats-Input
        ]
    )
    def update_map(taxi_type, year, borough, month):
        
        # 1. Zoom-Logik bestimmen
        target_view_key = "ALL" 
        if borough:
            if isinstance(borough, list):
                if len(borough) == 1:
                    target_view_key = borough[0]
                else:
                    target_view_key = "ALL"
            elif isinstance(borough, str):
                target_view_key = borough
        
        view = BOROUGH_VIEWS.get(target_view_key, BOROUGH_VIEWS["ALL"])

        # 2. Daten laden (mit Monat!)
        df, geojson_data = load_trips_and_geometries(taxi_type, year, borough, month)
        
        # Fallback: Keine Daten
        if df.empty or not geojson_data:
            fig = px.scatter_mapbox(
                lat=[], lon=[],
                center={"lat": view["lat"], "lon": view["lon"]}, 
                zoom=view["zoom"], 
            )
            fig.update_layout(
                mapbox_style="carto-positron",
                title="Keine Daten verfügbar"
            )
            return fig

        # 3. Karte erstellen
        fig = px.choropleth_mapbox(
            df,
            geojson=geojson_data,
            locations="location_id",
            featureidkey="id", # Greift auf die 'id' im GeoJSON Root zu
            color="trip_count",
            color_continuous_scale="Viridis",
            mapbox_style="carto-positron",
            center={"lat": view["lat"], "lon": view["lon"]},
            zoom=view["zoom"],
            opacity=0.6,
            hover_name="zone", 
            hover_data={
                "location_id": False, 
                "borough": True,
                "trip_count": ":,"
            },
            labels={
                "borough": "Bezirk",
                "trip_count": "Fahrten"
            }
        )

        # 4. Styling & Layout
        # Dynamischer Titel basierend auf Filtern
        title_parts = ["Taxi Demand Map"]
        if borough and isinstance(borough, list) and len(borough) == 1:
            title_parts.append(f"- {borough[0]}")
        if month:
            import calendar
            # Falls month eine Zahl oder String-Zahl ist
            try:
                m_name = calendar.month_name[int(month)]
                title_parts.append(f"({m_name})")
            except:
                pass

        fig.update_layout(
            margin={"r": 0, "t": 30, "l": 0, "b": 0},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            coloraxis_colorbar=dict(title="Anzahl Fahrten"),
            title=dict(text=" ".join(title_parts), x=0.02, y=0.98, font=dict(size=14))
        )
        
        return fig