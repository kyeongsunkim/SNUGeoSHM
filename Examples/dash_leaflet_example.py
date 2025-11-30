# Standalone example for dash-leaflet: Interactive geospatial map.
# This extended version adds markers, popups, and a callback for clicking.
# Requires: pip install dash dash-leaflet
# Run with `python dash_leaflet_example.py` to launch the app.

from dash import Dash, html, Output, Input
import dash_leaflet as dl

# Sample locations for markers (e.g., cities)
locations = [
    {"lat": 56, "lon": 10, "name": "Copenhagen"},
    {"lat": 55.6761, "lon": 12.5683, "name": "Denmark Capital"},
    {"lat": 59.9139, "lon": 10.7522, "name": "Oslo"}
]

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Interactive Map Example"),
    html.P("Click on markers for details."),
    dl.Map(id='map', style={'height': '50vh'}, center=[56, 10], zoom=6, children=[
        dl.TileLayer(),  # Base map tiles
        # Add markers dynamically
        *[dl.Marker(position=[loc["lat"], loc["lon"]], children=[
            dl.Tooltip(loc["name"]),
            dl.Popup(f"Location: {loc['name']}")
        ]) for loc in locations]
    ]),
    html.Div(id='click-info')  # Output for click events
])

@app.callback(
    Output('click-info', 'children'),
    Input('map', 'click_lat_lng')
)
def map_click(click_lat_lng):
    if click_lat_lng is None:
        return "Click on the map to see coordinates."
    return f"You clicked at: Latitude {click_lat_lng[0]:.4f}, Longitude {click_lat_lng[1]:.4f}"

if __name__ == '__main__':
    app.run_server(debug=True)