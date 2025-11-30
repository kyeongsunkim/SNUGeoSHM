from dash import dcc, html
import dash_bootstrap_components as dbc
import dash_leaflet as dlf

from common.utils import create_bullet_chart, create_gauge_chart

def layout():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H2("Overview"),
                html.P("Integrate simulations, models, and sensor data for digital twins."),

                # Action buttons
                dbc.Row([
                    dbc.Col([
                        dbc.Button("Run Processing Pipeline", id="pipeline-btn", color="primary", className="mb-3 me-2"),
                        dbc.Tooltip("Trigger sequential processing: OptumGX -> Groundhog -> GemPy -> PyOMA2, then update visualizations", target="pipeline-btn"),
                    ], width="auto"),
                    dbc.Col([
                        dbc.Button("Compare Sim vs Real", id="compare-btn", color="info", className="mb-3"),
                        dbc.Tooltip("Compare simulated vs real-time sensor data", target="compare-btn"),
                    ], width="auto"),
                ], className="mb-3"),

                dcc.Loading(html.Div(id="pipeline-output"), type="circle"),
                dcc.Loading(html.Div(id="comparison-output"), type="circle"),

                # KPI Charts
                html.H3("Key Performance Indicators", className="mt-4 mb-3"),
                dbc.Row(
                    [
                        dbc.Col(dcc.Graph(id="kpi-bullet-chart", figure=create_bullet_chart(220, ranges=[0, 150, 250, 300], colors=["lightgray", "gray"])), md=6, lg=4),
                        dbc.Col(dcc.Graph(id="kpi-gauge-chart", figure=create_gauge_chart(450, min_val=0, max_val=500, ranges=[0, 250, 400, 500], colors=["lightgray", "gray", "darkgray"])), md=6, lg=4),
                    ],
                    justify="center",
                ),

                # Wind Turbine Generator Viewer Section
                html.H3("Wind Turbine Generator Monitor", className="mt-4 mb-3"),
                dbc.Row([
                    dbc.Col([
                        html.Label("Select View Mode:"),
                        dbc.RadioItems(
                            id="wtg-view-mode",
                            options=[
                                {"label": "Map View", "value": "map"},
                                {"label": "Performance Charts", "value": "charts"},
                                {"label": "Combined View", "value": "combined"}
                            ],
                            value="combined",
                            inline=True,
                            className="mb-3"
                        )
                    ], width=12),
                ]),

                # WTG Map
                html.Div(id="wtg-map-container", children=[
                    dlf.Map(
                        id='wtg-map',
                        style={'width': '100%', 'height': '500px'},
                        center=[37.7749, -122.4194],
                        zoom=12,
                        children=[
                            dlf.TileLayer(),
                            dlf.GeoJSON(id='wtg-geojson', options=dict(pointToLayer=None))
                        ]
                    ),
                ]),

                # WTG Charts
                html.Div(id="wtg-charts-container", children=[
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(id='wtg-power-chart'),
                        ], md=6),
                        dbc.Col([
                            dcc.Graph(id='wtg-wind-chart'),
                        ], md=6),
                    ], className="mt-3"),
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(id='wtg-status-chart'),
                        ], md=6),
                        dbc.Col([
                            dcc.Graph(id='wtg-efficiency-chart'),
                        ], md=6),
                    ], className="mt-3"),
                ]),

                # Soil Data Map Section
                html.H3("Soil Investigation Sites", className="mt-4 mb-3"),
                dlf.Map(id="home-map", style={'width': '100%', 'height': '500px'}, center=[50, 4], zoom=4, children=[dlf.TileLayer()]),

                # 3D Visualization Section
                html.H3("3D Geological Visualization", className="mt-4 mb-3"),
                dcc.Loading(html.Div(id="3d-viewer"), type="circle"),
            ]
        )
    )