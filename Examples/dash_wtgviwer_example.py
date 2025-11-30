# Standalone example for Dash Wind Turbine Generator (WTG) Viewer.
# Displays turbines on a map with popups, and charts for power/wind data.
# Extended with more sample data, tooltips, and responsive layout.
# Requires: pip install dash dash-leaflet plotly pandas dash-bootstrap-components
# Run with `python dash_wtgviewer_example.py`.

from dash import Dash, dcc, html, Input, Output
import dash_leaflet as dl
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

# Extended sample data for wind turbines (add more attributes for realism)
data = pd.DataFrame({
    'id': [1, 2, 3, 4],
    'lat': [37.7749, 37.7849, 37.7949, 37.8049],
    'lon': [-122.4194, -122.4294, -122.4394, -122.4494],
    'power_output': [150, 200, 180, 220],  # kW
    'wind_speed': [5.2, 6.1, 5.8, 6.5],  # m/s
    'status': ['Operational', 'Maintenance', 'Operational', 'Idle']
})

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("Wind Turbine Generator Viewer"),
    html.P("Interactive map of turbines. Click markers for details and charts."),
    dl.Map(id='map', style={'height': '50vh'}, center=[37.7749, -122.4194], zoom=12, children=[
        dl.TileLayer(),
        dl.GeoJSON(id='geojson')
    ]),
    dcc.Graph(id='power-chart'),
    dcc.Graph(id='wind-chart')
], fluid=True)

@app.callback(
    Output('geojson', 'data'),
    Input('map', 'bounds')
)
def update_geojson(bounds):
    # Generate GeoJSON features for turbines
    features = []
    for _, row in data.iterrows():
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [row['lon'], row['lat']]},
            'properties': {'id': row['id'], 'status': row['status']}
        })
    return {'type': 'FeatureCollection', 'features': features}

@app.callback(
    Output('power-chart', 'figure'),
    Input('geojson', 'click_feature')
)
def update_power_chart(feature):
    if feature is None:
        # Full dataset bar chart
        fig = px.bar(data, x='id', y='power_output', color='status', title='Power Output by Turbine')
    else:
        tid = feature['properties']['id']
        subset = data[data['id'] == tid]
        fig = px.bar(subset, x='id', y='power_output', color='status', title=f'Power Output for Turbine {tid}')
    fig.update_layout(xaxis_title='Turbine ID', yaxis_title='Power (kW)')
    return fig

@app.callback(
    Output('wind-chart', 'figure'),
    Input('geojson', 'click_feature')
)
def update_wind_chart(feature):
    if feature is None:
        # Full dataset line chart
        fig = px.line(data, x='id', y='wind_speed', color='status', title='Wind Speed by Turbine')
    else:
        tid = feature['properties']['id']
        subset = data[data['id'] == tid]
        fig = px.line(subset, x='id', y='wind_speed', color='status', title=f'Wind Speed for Turbine {tid}')
    fig.update_layout(xaxis_title='Turbine ID', yaxis_title='Wind Speed (m/s)')
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)