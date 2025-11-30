import os
import base64
import tempfile
from dash import dcc, html, Input, Output, State, callback, no_update, clientside_callback, dash_table
import dash_bootstrap_components as dbc
import dash_auth
import dash_daq as daq
import dash_leaflet as dlf
import dash_vtk
import gempy as gp
import gempy_viewer as gpv
import groundhog
from groundhog.siteinvestigation.insitutests.pcpt_processing import PCPTProcessing
from groundhog.general.soilprofile import SoilProfile
import xarray as xr
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import MinMaxScaler
from io import StringIO, BytesIO
import plotly.express as px
import plotly.graph_objects as go
import pyvista as pv
import matplotlib.pyplot as plt
try:
    import pyoma2
    PYOMA_AVAILABLE = True
except ImportError:
    PYOMA_AVAILABLE = False
import dash
import functools
from dash_iconify import DashIconify
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(PROJECT_DIR, 'data'), exist_ok=True)
os.makedirs(os.path.join(PROJECT_DIR, 'assets'), exist_ok=True)
if not os.path.exists(os.path.join(PROJECT_DIR, 'data', 'sensor_data.parquet')):
    time = pd.date_range('2023-01-01', periods=1000, freq='S')
    channel = [1, 2]
    ds = xr.Dataset(
        {'value': (['time', 'channel'], np.random.randn(1000, 2) * 10)},
        coords={'time': time, 'channel': channel}
    )
    ds.to_netcdf(os.path.join(PROJECT_DIR, 'data', 'sensor_data.parquet'))
if not os.path.exists(os.path.join(PROJECT_DIR, 'data', 'soil_data.csv')):
    soil_df = pd.DataFrame({
        'x': np.random.uniform(0, 10, 100),
        'y': np.random.uniform(0, 10, 100),
        'z': np.random.uniform(-50, 0, 100),
        'formation': np.random.choice(['Sand', 'Clay'], 100),
        'qc': np.random.uniform(1, 10, 100),
        'fs': np.random.uniform(0.1, 1, 100)
    })
    soil_df.to_csv(os.path.join(PROJECT_DIR, 'data', 'soil_data.csv'), index=False)
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''
dash_auth.BasicAuth(app, {'admin': 'secret'})
@functools.lru_cache(maxsize=128)
def load_sensor_data():
    file_path = os.path.join(PROJECT_DIR, 'data', 'sensor_data.parquet')
    if not os.path.exists(file_path):
        raise FileNotFoundError("Sensor data not found. Place 'sensor_data.parquet' in data dir.")
    ds = xr.open_dataset(file_path, engine='pyarrow')
    required_dims = {'time', 'channel'}
    if not required_dims.issubset(ds.dims):
        raise ValueError(f"Missing dimensions: {required_dims - set(ds.dims)}")
    if 'value' not in ds.variables:
        raise ValueError("Missing 'value' variable in dataset.")
    return ds
@functools.lru_cache(maxsize=128)
def load_soil_data():
    file_path = os.path.join(PROJECT_DIR, 'data', 'soil_data.csv')
    if not os.path.exists(file_path):
        raise FileNotFoundError("Soil data not found. Place 'soil_data.csv' in data dir.")
    df = pd.read_csv(file_path)
    required_cols = {'x', 'y', 'z', 'formation', 'qc', 'fs'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Missing columns in soil_data: {required_cols - set(df.columns)}")
    return df
def simulate_optumgx(material_strength, strain=np.linspace(0, 0.1, 100)):
    epsilon_f = 0.05 # Failure strain placeholder
    stress = material_strength * strain * (1 - strain / epsilon_f)
    return pd.DataFrame({'strain': strain, 'stress': stress})
def process_uploaded_file(contents, filename):
    if contents is None:
        return None
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    if filename.endswith('.csv'):
        return pd.read_csv(BytesIO(decoded))
    elif filename.endswith('.xlsx'):
        return pd.read_excel(BytesIO(decoded))
    else:
        raise ValueError(f"Unsupported file type: {filename}")
def process_vtk_file(contents, filename):
    if contents is None:
        return None
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    if not filename.endswith('.vtk'):
        raise ValueError(f"Unsupported file type: {filename}")
    return decoded
def simulate_pyoma2(data):
    freqs = np.fft.fftfreq(len(data), d=1/100)[:len(data)//2]
    amps = np.abs(np.fft.fft(data))[:len(data)//2]
    return freqs, amps
def matplotlib_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode("utf-8")
def create_bullet_chart(value, title="Average Sensor Value", ranges=[0, 60, 80, 100], colors=["lightgray", "gray"]):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title},
            delta={'reference': ranges[1]},
            gauge={
                'shape': "bullet",
                'axis': {'range': [ranges[0], ranges[-1]]},
                'threshold': {'line': {'color': "red", 'width': 2}, 'thickness': 0.75, 'value': ranges[-2]},
                'steps': [{'range': [ranges[i], ranges[i+1]], 'color': colors[i % len(colors)]} for i in range(len(ranges)-1)]
            }
        )
    )
    fig.update_layout(height=250)
    return fig
def create_gauge_chart(value, title="Max Sensor Value", min_val=0, max_val=100, colors=["green", "yellow", "red"], ranges=[0, 60, 80, 100]):
    steps = [{'range': [ranges[i], ranges[i+1]], 'color': colors[i]} for i in range(len(ranges)-1)]
    fig = go.Figure(
        go.Indicator(
            domain={'x': [0, 1], 'y': [0, 1]},
            value=value,
            mode="gauge+number+delta",
            title={'text': title},
            delta={'reference': (min_val + max_val)/2},
            gauge={
                'axis': {'range': [min_val, max_val]},
                'steps': steps,
                'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': max_val * 0.9}
            }
        )
    )
    return fig
def create_navbar():
    navbar = dbc.Navbar(
        children=[
            dbc.NavbarBrand("Offshore Wind Turbine Monitoring Dashboard", style={"color": "white"}),
            daq.BooleanSwitch(id="theme-switch", on=True, label="Dark Mode", className="ms-auto"),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavItem(
                            dbc.NavLink(
                                [DashIconify(icon="fa-solid:house", width=20, className="me-2"), "Home"],
                                id="home-link",
                                n_clicks=0,
                                active=False,
                                style={"color": "white"},
                            )
                        ),
                        dbc.NavItem(
                            className="dropdown",
                            children=dbc.DropdownMenu(
                                children=[
                                    dbc.DropdownMenuItem(
                                        [DashIconify(icon="mdi:chart-bell-curve-cumulative", width=20, className="me-2"), "OptumGX"],
                                        id="optumgx-link",
                                        n_clicks=0,
                                    ),
                                    dbc.DropdownMenuItem(
                                        [DashIconify(icon="mdi:excavator", width=20, className="me-2"), "Groundhog"],
                                        id="groundhog-link",
                                        n_clicks=0,
                                    ),
                                    dbc.DropdownMenuItem(
                                        [DashIconify(icon="mdi:layers-triple", width=20, className="me-2"), "Gempy"],
                                        id="gempy-link",
                                        n_clicks=0,
                                    ),
                                    dbc.DropdownMenuItem(
                                        [DashIconify(icon="mdi:bridge", width=20, className="me-2"), "OpenSeesPy"],
                                        id="openseespy-link",
                                        n_clicks=0,
                                    ),
                                    dbc.DropdownMenuItem(
                                        [DashIconify(icon="mdi:cube-scan", width=20, className="me-2"), "3D Viewer"],
                                        id="iframe-link",
                                        n_clicks=0,
                                    ),
                                ],
                                label=[DashIconify(icon="fa-solid:cubes", width=20, className="me-2"), "FEM"],
                                nav=True,
                            ),
                        ),
                        dbc.NavItem(
                            className="dropdown",
                            children=dbc.DropdownMenu(
                                children=[
                                    dbc.DropdownMenuItem(
                                        [DashIconify(icon="mdi:database-cog", width=20, className="me-2"), "Preprocessing"],
                                        id="preprocessing-link",
                                        n_clicks=0,
                                    ),
                                    dbc.DropdownMenuItem(
                                        [DashIconify(icon="mdi:waveform", width=20, className="me-2"), "PyOMA2"],
                                        id="pyoma2-link",
                                        n_clicks=0,
                                    ),
                                    dbc.DropdownMenuItem(
                                        [DashIconify(icon="fa-solid:location-crosshairs", width=20, className="me-2"), "Tracker"],
                                        id="tracker-link",
                                        n_clicks=0,
                                    ),
                                ],
                                label=[DashIconify(icon="fa-solid:database", width=20, className="me-2"), "Data"],
                                nav=True,
                            ),
                        ),
                    ],
                    className="ms-auto",
                    navbar=True,
                ),
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ],
        id="navbar",
        color="#1a1a1a",
        dark=True,
        sticky="top",
    )
    return navbar
def home_layout():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H2("Overview"),
                html.P("Integrate simulations, models, and sensor data for digital twins."),
                dbc.Button("Run Processing Pipeline", id="pipeline-btn", color="primary", className="mb-3"),
                dbc.Tooltip("Trigger sequential processing: OptumGX -> Groundhog -> GemPy -> PyOMA2, then update visualizations", target="pipeline-btn"),
                dcc.Loading(html.Div(id="pipeline-output"), type="circle"),
                dbc.Button("Compare Sim vs Real", id="compare-btn", className="mb-3"),
                dbc.Tooltip("Compare simulated vs real-time sensor data", target="compare-btn"),
                dcc.Loading(html.Div(id="comparison-output"), type="circle"),
                dbc.Row(
                    [
                        dbc.Col(dcc.Graph(figure=create_bullet_chart(220, ranges=[0, 150, 250, 300], colors=["lightgray", "gray"])), md=6, lg=4),
                        dbc.Col(dcc.Graph(figure=create_gauge_chart(450, min_val=0, max_val=500, ranges=[0, 250, 400, 500], colors=["lightgray", "gray", "darkgray"])), md=6, lg=4),
                    ],
                    justify="center",
                ),
                html.H3("Interactive Map"),
                dlf.Map(id="home-map", style={'width': '100%', 'height': '500px'}, center=[50, 4], zoom=4, children=[dlf.TileLayer()]),
                html.H3("3D Visualization"),
                dcc.Loading(html.Div(id="3d-viewer"), type="circle"),
            ]
        )
    )
def optumgx_layout():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H2("FEM Simulation with OptumGX"),
                dcc.Upload(id="upload-optumgx", children=dbc.Button("Upload soilprofile_basic.xlsx", className="mr-2"), multiple=False),
                html.Div(id="upload-optumgx-status"),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                dash_table.DataTable(id="optumgx-data-table", editable=True, row_deletable=True, page_size=10),
                                dbc.Button("Fix Missing Values", id="fix-optumgx-btn", className="mt-2"),
                                html.Div(id="optumgx-fix-status"),
                            ],
                            title="View/Edit Data",
                        ),
                        dbc.AccordionItem(
                            dcc.Graph(id="optumgx-data-viz"),
                            title="Visualize Data",
                        ),
                    ],
                    start_collapsed=True,
                ),
                html.Label("Material Strength (MPa)"),
                dbc.Input(type="number", id="material-input", value=100, min=0),
                dbc.Button("Run Simulation", id="run-optumgx-btn"),
                dbc.Tooltip("Run finite element simulation on uploaded soil profile or default", target="run-optumgx-btn"),
                dcc.Loading(html.Div(id="optumgx-output"), type="circle"),
                dbc.Button("Download Results", id="download-optumgx-btn"),
            ]
        )
    )
def groundhog_layout():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H2("Soil/CPT Processing with Groundhog"),
                dcc.Upload(id="upload-groundhog-cpt", children=dbc.Button("Upload excel_example_cpt.xlsx", className="mr-2"), multiple=False),
                html.Div(id="upload-groundhog-cpt-status"),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                dash_table.DataTable(id="groundhog-cpt-data-table", editable=True, row_deletable=True, page_size=10),
                                dbc.Button("Fix Missing Values", id="fix-groundhog-cpt-btn", className="mt-2"),
                                html.Div(id="groundhog-cpt-fix-status"),
                            ],
                            title="View/Edit CPT Data",
                        ),
                        dbc.AccordionItem(
                            dcc.Graph(id="groundhog-cpt-data-viz"),
                            title="Visualize CPT Data",
                        ),
                    ],
                    start_collapsed=True,
                ),
                dcc.Upload(id="upload-groundhog-layering", children=dbc.Button("Upload excel_example_layering.xlsx", className="mr-2"), multiple=False),
                html.Div(id="upload-groundhog-layering-status"),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                dash_table.DataTable(id="groundhog-layering-data-table", editable=True, row_deletable=True, page_size=10),
                                dbc.Button("Fix Missing Values", id="fix-groundhog-layering-btn", className="mt-2"),
                                html.Div(id="groundhog-layering-fix-status"),
                            ],
                            title="View/Edit Layering Data",
                        ),
                        dbc.AccordionItem(
                            dcc.Graph(id="groundhog-layering-data-viz"),
                            title="Visualize Layering Data",
                        ),
                    ],
                    start_collapsed=True,
                ),
                dbc.Button("Process CPT", id="run-groundhog-btn"),
                dbc.Tooltip("Process uploaded CPT and layering data", target="run-groundhog-btn"),
                dcc.Loading(html.Div(id="groundhog-output"), type="circle"),
                dbc.Button("Download Results", id="download-groundhog-btn"),
            ]
        )
    )
def gempy_layout():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H2("Geological Visualization with GemPy"),
                dcc.Upload(id="upload-gempy-surfaces", children=dbc.Button("Upload model1_surface_points.csv", className="mr-2"), multiple=False),
                html.Div(id="upload-gempy-surfaces-status"),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                dash_table.DataTable(id="gempy-surfaces-data-table", editable=True, row_deletable=True, page_size=10),
                                dbc.Button("Fix Missing Values", id="fix-gempy-surfaces-btn", className="mt-2"),
                                html.Div(id="gempy-surfaces-fix-status"),
                            ],
                            title="View/Edit Surfaces Data",
                        ),
                        dbc.AccordionItem(
                            dcc.Graph(id="gempy-surfaces-data-viz"),
                            title="Visualize Surfaces Data",
                        ),
                    ],
                    start_collapsed=True,
                ),
                dcc.Upload(id="upload-gempy-orientations", children=dbc.Button("Upload model1_orientations.csv", className="mr-2"), multiple=False),
                html.Div(id="upload-gempy-orientations-status"),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                dash_table.DataTable(id="gempy-orientations-data-table", editable=True, row_deletable=True, page_size=10),
                                dbc.Button("Fix Missing Values", id="fix-gempy-orientations-btn", className="mt-2"),
                                html.Div(id="gempy-orientations-fix-status"),
                            ],
                            title="View/Edit Orientations Data",
                        ),
                        dbc.AccordionItem(
                            dcc.Graph(id="gempy-orientations-data-viz"),
                            title="Visualize Orientations Data",
                        ),
                    ],
                    start_collapsed=True,
                ),
                dbc.Button("Generate Model", id="run-gempy-btn"),
                dbc.Tooltip("Generate 3D geological model from uploaded data", target="run-gempy-btn"),
                dcc.Loading(html.Div(id="gempy-output"), type="circle"),
                dbc.Button("Download Model", id="download-gempy-btn"),
            ]
        )
    )
def pyoma2_layout():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H2("Operational Modal Analysis with PyOMA2"),
                dcc.Upload(id="upload-pyoma2", children=dbc.Button("Upload Sensor Time Series CSV", className="mr-2"), multiple=False),
                html.Div(id="upload-pyoma2-status"),
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                dash_table.DataTable(id="pyoma2-data-table", editable=True, row_deletable=True, page_size=10),
                                dbc.Button("Fix Missing Values", id="fix-pyoma2-btn", className="mt-2"),
                                html.Div(id="pyoma2-fix-status"),
                            ],
                            title="View/Edit Data",
                        ),
                        dbc.AccordionItem(
                            dcc.Graph(id="pyoma2-data-viz"),
                            title="Visualize Data",
                        ),
                    ],
                    start_collapsed=True,
                ),
                dbc.Button("Run Analysis", id="run-pyoma2-btn"),
                dbc.Tooltip("Run modal analysis on uploaded sensor time series data (columns: time, channel1, channel2, ...)", target="run-pyoma2-btn"),
                dcc.Loading(html.Div(id="pyoma2-output"), type="circle"),
                dbc.Button("Download Results", id="download-pyoma2-btn"),
            ]
        )
    )
def iframe_layout():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H2("3D VTK Viewer"),
                dcc.Upload(id="upload-vtk", children=dbc.Button("Upload VTK File", className="mr-2"), multiple=False),
                html.Div(id="upload-vtk-status"),
                dbc.Button("View 3D Model", id="view-3d-btn"),
                dbc.Tooltip("Load and view uploaded VTK file in 3D", target="view-3d-btn"),
                dcc.Loading(html.Iframe(id="3d-content", style={"border": "none", "width": "100%", "height": "800px"}), type="circle"),
            ]
        )
    )
def openseespy_layout():
    return dbc.Card(
        dbc.CardBody(
            html.H2("OpenSeesPy - Under Development")
        )
    )
def preprocessing_layout():
    return dbc.Card(
        dbc.CardBody(
            html.H2("Preprocessing - Under Development")
        )
    )
def tracker_layout():
    return dbc.Card(
        dbc.CardBody(
            html.H2("Tracker - Under Development")
        )
    )
navbar = create_navbar()
app.layout = dbc.Container(
    fluid=True,
    children=[
        html.Link(id="theme-sheet", rel="stylesheet", href=dbc.themes.DARKLY),
        navbar,
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(id='home-page', children=home_layout(), style={'display': 'block'}),
                        html.Div(id='optumgx-page', children=optumgx_layout(), style={'display': 'none'}),
                        html.Div(id='groundhog-page', children=groundhog_layout(), style={'display': 'none'}),
                        html.Div(id='gempy-page', children=gempy_layout(), style={'display': 'none'}),
                        html.Div(id='pyoma2-page', children=pyoma2_layout(), style={'display': 'none'}),
                        html.Div(id='iframe-page', children=iframe_layout(), style={'display': 'none'}),
                        html.Div(id='openseespy-page', children=openseespy_layout(), style={'display': 'none'}),
                        html.Div(id='preprocessing-page', children=preprocessing_layout(), style={'display': 'none'}),
                        html.Div(id='tracker-page', children=tracker_layout(), style={'display': 'none'}),
                        dcc.Store(id='global-store', data={}),
                        dcc.Download(id='download-component'),
                        dbc.Modal(
                            [
                                dbc.ModalHeader(dbc.ModalTitle("Error")),
                                dbc.ModalBody(html.Div(id="error-message")),
                            ],
                            id="error-modal",
                            is_open=False,
                        ),
                        dcc.Interval(id='digital-twin-interval', interval=60*1000, n_intervals=0),
                        html.Div(id="dummy-export", style={"display": "none"}),
                    ],
                    width=12,
                ),
            ],
            className="h-100",
        ),
    ],
    style={"padding": 0},
)
@callback(
    [
        Output('home-page', 'style'),
        Output('optumgx-page', 'style'),
        Output('groundhog-page', 'style'),
        Output('gempy-page', 'style'),
        Output('pyoma2-page', 'style'),
        Output('iframe-page', 'style'),
        Output('openseespy-page', 'style'),
        Output('preprocessing-page', 'style'),
        Output('tracker-page', 'style'),
        Output('home-link', 'active'),
        Output('optumgx-link', 'active'),
        Output('groundhog-link', 'active'),
        Output('gempy-link', 'active'),
        Output('pyoma2-link', 'active'),
        Output('iframe-link', 'active'),
        Output('openseespy-link', 'active'),
        Output('preprocessing-link', 'active'),
        Output('tracker-link', 'active'),
    ],
    [
        Input('home-link', 'n_clicks'),
        Input('optumgx-link', 'n_clicks'),
        Input('groundhog-link', 'n_clicks'),
        Input('gempy-link', 'n_clicks'),
        Input('pyoma2-link', 'n_clicks'),
        Input('iframe-link', 'n_clicks'),
        Input('openseespy-link', 'n_clicks'),
        Input('preprocessing-link', 'n_clicks'),
        Input('tracker-link', 'n_clicks'),
    ],
)
def display_page(home_n, optumgx_n, groundhog_n, gempy_n, pyoma2_n, iframe_n, openseespy_n, preprocessing_n, tracker_n):
    ctx = dash.callback_context
    show = {'display': 'block'}
    hide = {'display': 'none'}
    if not ctx.triggered:
        return show, hide, hide, hide, hide, hide, hide, hide, hide, True, False, False, False, False, False, False, False, False
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if button_id == 'home-link':
        return show, hide, hide, hide, hide, hide, hide, hide, hide, True, False, False, False, False, False, False, False, False
    elif button_id == 'optumgx-link':
        return hide, show, hide, hide, hide, hide, hide, hide, hide, False, True, False, False, False, False, False, False, False
    elif button_id == 'groundhog-link':
        return hide, hide, show, hide, hide, hide, hide, hide, hide, False, False, True, False, False, False, False, False, False
    elif button_id == 'gempy-link':
        return hide, hide, hide, show, hide, hide, hide, hide, hide, False, False, False, True, False, False, False, False, False
    elif button_id == 'pyoma2-link':
        return hide, hide, hide, hide, show, hide, hide, hide, hide, False, False, False, False, True, False, False, False, False
    elif button_id == 'iframe-link':
        return hide, hide, hide, hide, hide, show, hide, hide, hide, False, False, False, False, False, True, False, False, False
    elif button_id == 'openseespy-link':
        return hide, hide, hide, hide, hide, hide, show, hide, hide, False, False, False, False, False, False, True, False, False
    elif button_id == 'preprocessing-link':
        return hide, hide, hide, hide, hide, hide, hide, show, hide, False, False, False, False, False, False, False, True, False
    elif button_id == 'tracker-link':
        return hide, hide, hide, hide, hide, hide, hide, hide, show, False, False, False, False, False, False, False, False, True
    return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
@callback(
    [
        Output("theme-sheet", "href"),
        Output("navbar", "color"),
        Output("navbar", "dark"),
    ],
    Input("theme-switch", "on"),
)
def switch_theme(on):
    if on:
        return dbc.themes.DARKLY, "#1a1a1a", True
    return dbc.themes.BOOTSTRAP, "light", False
@callback(
    [Output('error-modal', 'is_open'), Output('error-message', 'children')],
    Input('global-store', 'data')
)
def show_error(store_data):
    if 'error' in store_data:
        return True, store_data['error']
    return False, no_update
@callback(
    Output('global-store', 'data', allow_duplicate=True),
    Input('digital-twin-interval', 'n_intervals'),
    prevent_initial_call=True
)
def auto_load_data(n):
    data = {'soil': load_soil_data().to_dict('records'), 'sensor': load_sensor_data().to_dict()}
    return data
@callback(
    Output("home-map", "children"),
    Input("global-store", "data"),
)
def update_map(data):
    children = [dlf.TileLayer()]
    if "soil" in data:
        df = pd.DataFrame(data["soil"])
        for idx, row in df.iterrows():
            if 'x' in row and 'y' in row:
                children.append(dlf.Marker(id=f"marker-{idx}", position=[row['y'], row['x']], children=dlf.Tooltip(row.get('formation', 'Soil Point'))))
    return children
@callback(
    Output("3d-viewer", "children"),
    Input("home-map", "click_lat_lng"),
    State("global-store", "data"),
    prevent_initial_call=True
)
def show_3d(click, data):
    if not click:
        raise dash.exceptions.PreventUpdate
    lat, lon = click
    try:
        if "soil" in data:
            df = pd.DataFrame(data["soil"])
            if df.empty:
                return dbc.Alert("No soil data available.", color="warning")
            if 'x' in df.columns and 'y' in df.columns:
                dist = ((df['y'] - lat)**2 + (df['x'] - lon)**2)**0.5
                nearest_idx = dist.argmin()
                nearest = df.iloc[nearest_idx]
                points = pv.wrap(df[['x', 'y', 'z']].values)
                plotter = pv.Plotter(off_screen=True)
                plotter.add_points(points, scalars=df['qc'], point_size=10, render_points_as_spheres=True)
                plotter.add_points(pv.wrap([[nearest['x'], nearest['y'], nearest['z']]]), color='red', point_size=20)
                export_path = os.path.join('assets', '3d_soil.html')
                plotter.export_html(export_path)
                return html.Iframe(src=export_path, style={"width": "100%", "height": "600px"})
        return dbc.Alert("No soil data for 3D view.", color="warning")
    except Exception as e:
        return dbc.Alert(str(e), color="danger")
@callback(
    Output('pipeline-output', 'children'),
    Input('pipeline-btn', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def run_pipeline(n_clicks, store_data):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    outputs = []
    store_update = store_data.copy()
    try:
        # OptumGX step
        material = store_data.get('material_input', 100)
        df_sim = simulate_optumgx(material)
        store_update['optumgx_result'] = df_sim.to_dict('records')
        outputs.append(html.P("OptumGX completed."))
        # Groundhog step
        if 'groundhog_cpt' in store_data and 'groundhog_layering' in store_data:
            cpt_df = pd.DataFrame(store_data['groundhog_cpt'])
            layering_df = pd.DataFrame(store_data['groundhog_layering'])
            cpt = PCPTProcessing(title='CPT Example')
            cpt.load_pandas(cpt_df, z_key='z [m]', qc_key='qc [MPa]', fs_key='fs [MPa]')
            cpt.normalise_pcpt()
            cpt.apply_correlation(name="relativedensity_ncsand_baldi", outputs={"Dr": "Dr [%]"}, apply_for_soiltypes=["Sand"])
            profile = SoilProfile(layering_df)
            store_update['groundhog_cpt_processed'] = cpt.data.to_dict('records')
            store_update['groundhog_profile'] = profile.layering.to_dict('records')
            outputs.append(html.P("Groundhog completed."))
        else:
            outputs.append(html.P("Groundhog skipped: missing data."))
        # GemPy step
        if 'gempy_surfaces' in store_data and 'gempy_orientations' in store_data:
            surfaces = pd.DataFrame(store_data['gempy_surfaces'])
            orientations = pd.DataFrame(store_data['gempy_orientations'])
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_surfaces, tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_orientations:
                surfaces.to_csv(tmp_surfaces.name, index=False)
                orientations.to_csv(tmp_orientations.name, index=False)
                importer = gp.data.ImporterHelper(
                    path_to_surface_points=tmp_surfaces.name,
                    path_to_orientations=tmp_orientations.name
                )
            extent = [surfaces.X.min(), surfaces.X.max(), surfaces.Y.min(), surfaces.Y.max(), surfaces.Z.min(), surfaces.Z.max()]
            geo_model = gp.create_geomodel(
                project_name='WindTurbine',
                extent=extent,
                refinement=4, # Reduced for performance
                importer_helper=importer
            )
            gp.map_stack_to_surfaces(geo_model, {"Formations": surfaces['surface'].unique() if 'surface' in surfaces else surfaces['formation'].unique()})
            gp.compute_model(geo_model)
            store_update['gempy_model'] = geo_model.solutions.to_dict() # Placeholder dict export
            outputs.append(html.P("GemPy completed."))
            os.unlink(tmp_surfaces.name)
            os.unlink(tmp_orientations.name)
        else:
            outputs.append(html.P("GemPy skipped: missing data."))
        # PyOMA2 step
        if 'pyoma2_data' in store_data:
            df = pd.DataFrame(store_data['pyoma2_data'])
            data = df.drop(columns=['time'] if 'time' in df.columns else []).values.T
            fs = 100
            if PYOMA_AVAILABLE:
                alg = pyoma2.MSSI_COV(name='OMA', data=data, fs=fs, br=10)
                alg.run()
                freqs, amps = [], [] # Replace with alg results
            else:
                freqs, amps = simulate_pyoma2(data[0])
            store_update['pyoma2_result'] = {'freqs': freqs.tolist(), 'amps': amps.tolist()}
            outputs.append(html.P("PyOMA2 completed."))
        else:
            outputs.append(html.P("PyOMA2 skipped: missing data."))
        # Future: Use GemPy for OpenSees input (e.g., export mesh)
        outputs.append(html.P("Pipeline finished. Results stored for visualization."))
        return outputs
    except Exception as e:
        store_update['error'] = str(e)
        return [dbc.Alert(str(e), color="danger")]
@callback(
    [
        Output("upload-optumgx-status", "children"),
        Output('global-store', 'data', allow_duplicate=True),
        Output("optumgx-data-table", "data"),
        Output("optumgx-data-table", "columns"),
        Output("optumgx-data-viz", "figure"),
    ],
    Input("upload-optumgx", "contents"),
    State("upload-optumgx", "filename"),
    State("global-store", "data"),
    prevent_initial_call=True,
)
def handle_optumgx_upload(contents, filename, store_data):
    try:
        df = process_uploaded_file(contents, filename)
        store_update = store_data.copy()
        store_update['optumgx_data'] = df.to_dict('records')
        columns = [{"name": i, "id": i} for i in df.columns]
        fig = px.line(df, x="Depth from [m]", y="qt [MPa]", title="OptumGX Data Visualization") if "Depth from [m]" in df.columns and "qt [MPa]" in df.columns else px.scatter()
        return dbc.Alert(f"{filename} uploaded successfully.", color="success"), store_update, df.to_dict('records'), columns, fig
    except Exception as e:
        store_update = store_data.copy()
        store_update['error'] = str(e)
        return dbc.Alert(str(e), color="danger"), store_update, [], [], go.Figure()
@callback(
    [
        Output("optumgx-fix-status", "children"),
        Output('global-store', 'data', allow_duplicate=True),
    ],
    Input("fix-optumgx-btn", "n_clicks"),
    State("optumgx-data-table", "data"),
    State("global-store", "data"),
    prevent_initial_call=True,
)
def fix_optumgx_data(n, table_data, store_data):
    if not n:
        raise dash.exceptions.PreventUpdate
    df = pd.DataFrame(table_data)
    df = df.fillna(0)
    store_update = store_data.copy()
    store_update['optumgx_data'] = df.to_dict('records')
    return dbc.Alert("Missing values filled with 0.", color="info"), store_update
@callback(
    [Output('optumgx-output', 'children'), Output('global-store', 'data', allow_duplicate=True)],
    Input('run-optumgx-btn', 'n_clicks'),
    State('material-input', 'value'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def run_optumgx(n_clicks, material, store_data):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    try:
        if 'optumgx_data' in store_data:
            df = pd.DataFrame(store_data['optumgx_data'])
            if 'qt [MPa]' in df.columns:
                material = df['qt [MPa]'].mean()
        if 'groundhog_cpt_processed' in store_data: # Interop example
            material = pd.DataFrame(store_data['groundhog_cpt_processed'])['Dr [%]'].mean() or material
        df_sim = simulate_optumgx(material)
        fig = px.line(df_sim, x='strain', y='stress', title="Stress-Strain Curve")
        output = [
            dcc.Graph(id="optumgx-graph", figure=fig),
            dbc.Button("Export PNG", id="export-optumgx-png", className="ml-2"),
            dbc.Button("Export PDF", id="export-optumgx-pdf", className="ml-2"),
        ]
        store_update = store_data.copy()
        store_update['optumgx_result'] = df_sim.to_dict('records')
        return output, store_update
    except Exception as e:
        store_update = store_data.copy()
        store_update['error'] = str(e)
        return [dbc.Alert(str(e), color="danger")], store_update
@callback(
    [
        Output("upload-groundhog-cpt-status", "children"),
        Output('global-store', 'data', allow_duplicate=True),
        Output("groundhog-cpt-data-table", "data"),
        Output("groundhog-cpt-data-table", "columns"),
        Output("groundhog-cpt-data-viz", "figure"),
    ],
    Input("upload-groundhog-cpt", "contents"),
    State("upload-groundhog-cpt", "filename"),
    State("global-store", "data"),
    prevent_initial_call=True,
)
def handle_groundhog_cpt_upload(contents, filename, store_data):
    try:
        df = process_uploaded_file(contents, filename)
        store_update = store_data.copy()
        store_update['groundhog_cpt'] = df.to_dict('records')
        columns = [{"name": i, "id": i} for i in df.columns]
        fig = px.line(df, x="z [m]", y="qc [MPa]", title="CPT Data") if "z [m]" in df.columns and "qc [MPa]" in df.columns else px.scatter()
        return dbc.Alert(f"{filename} uploaded.", color="success"), store_update, df.to_dict('records'), columns, fig
    except Exception as e:
        store_update = store_data.copy()
        store_update['error'] = str(e)
        return dbc.Alert(str(e), color="danger"), store_update, [], [], go.Figure()
@callback(
    [
        Output("upload-groundhog-layering-status", "children"),
        Output('global-store', 'data', allow_duplicate=True),
        Output("groundhog-layering-data-table", "data"),
        Output("groundhog-layering-data-table", "columns"),
        Output("groundhog-layering-data-viz", "figure"),
    ],
    Input("upload-groundhog-layering", "contents"),
    State("upload-groundhog-layering", "filename"),
    State("global-store", "data"),
    prevent_initial_call=True,
)
def handle_groundhog_layering_upload(contents, filename, store_data):
    try:
        df = process_uploaded_file(contents, filename)
        store_update = store_data.copy()
        store_update['groundhog_layering'] = df.to_dict('records')
        columns = [{"name": i, "id": i} for i in df.columns]
        fig = px.bar(df, x="Soil type", y="Depth from [m]", title="Layering Data") if "Soil type" in df.columns and "Depth from [m]" in df.columns else px.scatter()
        return dbc.Alert(f"{filename} uploaded.", color="success"), store_update, df.to_dict('records'), columns, fig
    except Exception as e:
        store_update = store_data.copy()
        store_update['error'] = str(e)
        return dbc.Alert(str(e), color="danger"), store_update, [], [], go.Figure()
@callback(
    [
        Output("groundhog-cpt-fix-status", "children"),
        Output('global-store', 'data', allow_duplicate=True),
    ],
    Input("fix-groundhog-cpt-btn", "n_clicks"),
    State("groundhog-cpt-data-table", "data"),
    State("global-store", "data"),
    prevent_initial_call=True,
)
def fix_groundhog_cpt_data(n, table_data, store_data):
    if not n:
        raise dash.exceptions.PreventUpdate
    df = pd.DataFrame(table_data)
    df = df.fillna(0)
    store_update = store_data.copy()
    store_update['groundhog_cpt'] = df.to_dict('records')
    return dbc.Alert("Missing values filled with 0.", color="info"), store_update
@callback(
    [
        Output("groundhog-layering-fix-status", "children"),
        Output('global-store', 'data', allow_duplicate=True),
    ],
    Input("fix-groundhog-layering-btn", "n_clicks"),
    State("groundhog-layering-data-table", "data"),
    State("global-store", "data"),
    prevent_initial_call=True,
)
def fix_groundhog_layering_data(n, table_data, store_data):
    if not n:
        raise dash.exceptions.PreventUpdate
    df = pd.DataFrame(table_data)
    df = df.fillna(0)
    store_update = store_data.copy()
    store_update['groundhog_layering'] = df.to_dict('records')
    return dbc.Alert("Missing values filled with 0.", color="info"), store_update
@callback(
    [Output('groundhog-output', 'children'), Output('global-store', 'data', allow_duplicate=True)],
    Input('run-groundhog-btn', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def run_groundhog(n_clicks, store_data):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    try:
        if 'groundhog_cpt' not in store_data or 'groundhog_layering' not in store_data:
            raise ValueError("Missing CPT or layering data.")
        cpt_df = pd.DataFrame(store_data['groundhog_cpt'])
        layering_df = pd.DataFrame(store_data['groundhog_layering'])
        cpt = PCPTProcessing(title='CPT Process')
        cpt.load_pandas(cpt_df, z_key='z [m]', qc_key='qc [MPa]', fs_key='fs [MPa]')
        cpt.normalise_pcpt()
        cpt.apply_correlation(name="relativedensity_ncsand_baldi", outputs={"Dr": "Dr [%]"}, apply_for_soiltypes=["Sand"])
        profile = SoilProfile(layering_df)
        # Plot example
        fig, ax = plt.subplots()
        cpt.plot_raw_pcpt(plot_rf=True, zlines=[0, 5, 10])
        img_src = matplotlib_to_base64(fig)
        output = [html.Img(src=img_src, style={'width': '100%'})]
        store_update = store_data.copy()
        store_update['groundhog_cpt_processed'] = cpt.data.to_dict('records')
        store_update['groundhog_profile'] = profile.layering.to_dict('records')
        return output, store_update
    except Exception as e:
        store_update = store_data.copy()
        store_update['error'] = str(e)
        return [dbc.Alert(str(e), color="danger")], store_update
@callback(
    [
        Output("upload-gempy-surfaces-status", "children"),
        Output('global-store', 'data', allow_duplicate=True),
        Output("gempy-surfaces-data-table", "data"),
        Output("gempy-surfaces-data-table", "columns"),
        Output("gempy-surfaces-data-viz", "figure"),
    ],
    Input("upload-gempy-surfaces", "contents"),
    State("upload-gempy-surfaces", "filename"),
    State("global-store", "data"),
    prevent_initial_call=True,
)
def handle_gempy_surfaces_upload(contents, filename, store_data):
    try:
        df = process_uploaded_file(contents, filename)
        store_update = store_data.copy()
        store_update['gempy_surfaces'] = df.to_dict('records')
        columns = [{"name": i, "id": i} for i in df.columns]
        fig = px.scatter_3d(df, x="X", y="Y", z="Z", color="formation", title="Surfaces Data") if all(col in df for col in ["X", "Y", "Z", "formation"]) else px.scatter()
        return dbc.Alert(f"{filename} uploaded.", color="success"), store_update, df.to_dict('records'), columns, fig
    except Exception as e:
        store_update = store_data.copy()
        store_update['error'] = str(e)
        return dbc.Alert(str(e), color="danger"), store_update, [], [], go.Figure()
@callback(
    [
        Output("upload-gempy-orientations-status", "children"),
        Output('global-store', 'data', allow_duplicate=True),
        Output("gempy-orientations-data-table", "data"),
        Output("gempy-orientations-data-table", "columns"),
        Output("gempy-orientations-data-viz", "figure"),
    ],
    Input("upload-gempy-orientations", "contents"),
    State("upload-gempy-orientations", "filename"),
    State("global-store", "data"),
    prevent_initial_call=True,
)
def handle_gempy_orientations_upload(contents, filename, store_data):
    try:
        df = process_uploaded_file(contents, filename)
        store_update = store_data.copy()
        store_update['gempy_orientations'] = df.to_dict('records')
        columns = [{"name": i, "id": i} for i in df.columns]
        fig = px.scatter_3d(df, x="X", y="Y", z="Z", color="formation", title="Orientations Data") if all(col in df for col in ["X", "Y", "Z", "formation"]) else px.scatter()
        return dbc.Alert(f"{filename} uploaded.", color="success"), store_update, df.to_dict('records'), columns, fig
    except Exception as e:
        store_update = store_data.copy()
        store_update['error'] = str(e)
        return dbc.Alert(str(e), color="danger"), store_update, [], [], go.Figure()
@callback(
    [
        Output("gempy-surfaces-fix-status", "children"),
        Output('global-store', 'data', allow_duplicate=True),
    ],
    Input("fix-gempy-surfaces-btn", "n_clicks"),
    State("gempy-surfaces-data-table", "data"),
    State("global-store", "data"),
    prevent_initial_call=True,
)
def fix_gempy_surfaces_data(n, table_data, store_data):
    if not n:
        raise dash.exceptions.PreventUpdate
    df = pd.DataFrame(table_data)
    df = df.fillna(0)
    store_update = store_data.copy()
    store_update['gempy_surfaces'] = df.to_dict('records')
    return dbc.Alert("Missing values filled with 0.", color="info"), store_update
@callback(
    [
        Output("gempy-orientations-fix-status", "children"),
        Output('global-store', 'data', allow_duplicate=True),
    ],
    Input("fix-gempy-orientations-btn", "n_clicks"),
    State("gempy-orientations-data-table", "data"),
    State("global-store", "data"),
    prevent_initial_call=True,
)
def fix_gempy_orientations_data(n, table_data, store_data):
    if not n:
        raise dash.exceptions.PreventUpdate
    df = pd.DataFrame(table_data)
    df = df.fillna(0)
    store_update = store_data.copy()
    store_update['gempy_orientations'] = df.to_dict('records')
    return dbc.Alert("Missing values filled with 0.", color="info"), store_update
@callback(
    [Output('gempy-output', 'children'), Output('global-store', 'data', allow_duplicate=True)],
    Input('run-gempy-btn', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def run_gempy(n_clicks, store_data):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    try:
        if 'gempy_surfaces' not in store_data or 'gempy_orientations' not in store_data:
            raise ValueError("Missing surfaces or orientations data.")
        surfaces = pd.DataFrame(store_data['gempy_surfaces'])
        orientations = pd.DataFrame(store_data['gempy_orientations'])
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_surfaces, tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_orientations:
            surfaces.to_csv(tmp_surfaces.name, index=False)
            orientations.to_csv(tmp_orientations.name, index=False)
            importer = gp.data.ImporterHelper(
                path_to_surface_points=tmp_surfaces.name,
                path_to_orientations=tmp_orientations.name
            )
        extent = [surfaces.X.min(), surfaces.X.max(), surfaces.Y.min(), surfaces.Y.max(), surfaces.Z.min(), surfaces.Z.max()]
        geo_model = gp.create_geomodel(
            project_name='GemPy Model',
            extent=extent,
            refinement=4,
            importer_helper=importer
        )
        if 'groundhog_profile' in store_data: # Interop: Use Groundhog formations
            formations = pd.DataFrame(store_data['groundhog_profile'])['Soil type'].unique()
        else:
            formations = surfaces['formation'].unique()
        gp.map_stack_to_surfaces(geo_model, {"Formations": formations})
        gp.compute_model(geo_model)
        # Visualization
        plot = gpv.plot_3d(geo_model, off_screen=True, plotter_type='basic')
        export_path = os.path.join('assets', 'gempy_3d.html')
        plot.p.export_html(export_path)
        output = [html.Iframe(src=export_path, style={"width": "100%", "height": "600px"})]
        store_update = store_data.copy()
        store_update['gempy_model'] = geo_model.solutions.to_dict()
        os.unlink(tmp_surfaces.name)
        os.unlink(tmp_orientations.name)
        return output, store_update
    except Exception as e:
        store_update = store_data.copy()
        store_update['error'] = str(e)
        return [dbc.Alert(str(e), color="danger")], store_update
@callback(
    [
        Output("upload-pyoma2-status", "children"),
        Output('global-store', 'data', allow_duplicate=True),
        Output("pyoma2-data-table", "data"),
        Output("pyoma2-data-table", "columns"),
        Output("pyoma2-data-viz", "figure"),
    ],
    Input("upload-pyoma2", "contents"),
    State("upload-pyoma2", "filename"),
    State("global-store", "data"),
    prevent_initial_call=True,
)
def handle_pyoma2_upload(contents, filename, store_data):
    try:
        df = process_uploaded_file(contents, filename)
        store_update = store_data.copy()
        store_update['pyoma2_data'] = df.to_dict('records')
        columns = [{"name": i, "id": i} for i in df.columns]
        fig = px.line(df, x="time", y=df.columns[1], title="Sensor Data") if "time" in df.columns else px.scatter()
        return dbc.Alert(f"{filename} uploaded.", color="success"), store_update, df.to_dict('records'), columns, fig
    except Exception as e:
        store_update = store_data.copy()
        store_update['error'] = str(e)
        return dbc.Alert(str(e), color="danger"), store_update, [], [], go.Figure()
@callback(
    [
        Output("pyoma2-fix-status", "children"),
        Output('global-store', 'data', allow_duplicate=True),
    ],
    Input("fix-pyoma2-btn", "n_clicks"),
    State("pyoma2-data-table", "data"),
    State("global-store", "data"),
    prevent_initial_call=True,
)
def fix_pyoma2_data(n, table_data, store_data):
    if not n:
        raise dash.exceptions.PreventUpdate
    df = pd.DataFrame(table_data)
    df = df.fillna(0)
    store_update = store_data.copy()
    store_update['pyoma2_data'] = df.to_dict('records')
    return dbc.Alert("Missing values filled with 0.", color="info"), store_update
@callback(
    [Output('pyoma2-output', 'children'), Output('global-store', 'data', allow_duplicate=True)],
    Input('run-pyoma2-btn', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def run_pyoma2(n_clicks, store_data):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate
    try:
        if 'pyoma2_data' not in store_data:
            raise ValueError("Missing PyOMA2 data.")
        df = pd.DataFrame(store_data['pyoma2_data'])
        data = df.drop(columns=['time'] if 'time' in df.columns else []).values.T
        fs = 100
        if PYOMA_AVAILABLE:
            alg = pyoma2.MSSI_COV(name='OMA', data=data, fs=fs, br=10)
            alg.run()
            freqs, amps = [], [] # Extract real results here
        else:
            freqs, amps = simulate_pyoma2(data[0])
        fig = px.line(x=freqs, y=amps, title="Frequency Spectrum")
        output = [dcc.Graph(figure=fig)]
        store_update = store_data.copy()
        store_update['pyoma2_result'] = {'freqs': freqs.tolist(), 'amps': amps.tolist()}
        return output, store_update
    except Exception as e:
        store_update = store_data.copy()
        store_update['error'] = str(e)
        return [dbc.Alert(str(e), color="danger")], store_update
@callback(
    Output('comparison-output', 'children'),
    Input('compare-btn', 'n_clicks'),
    Input('digital-twin-interval', 'n_intervals'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def compare_sim_real(n_clicks, n_intervals, store_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    if 'optumgx_result' not in store_data or 'sensor' not in store_data:
        if 'sensor' not in store_data:
            try:
                store_data['sensor'] = load_sensor_data().to_dict()
            except Exception as e:
                return dbc.Alert(str(e), color="danger")
        if 'optumgx_result' not in store_data:
            return dbc.Alert("Run OptumGX simulation first.", color="warning")
    try:
        sim = pd.DataFrame(store_data['optumgx_result'])['stress']
        ds = xr.Dataset.from_dict(store_data['sensor'])
        real = ds['value'].mean(dim='channel')[-len(sim):].values
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=sim, name='Sim'))
        fig.add_trace(go.Scatter(y=real, name='Real'))
        fig.update_layout(title="Sim vs Real Comparison")
        return dcc.Graph(id="compare-graph", figure=fig)
    except Exception as e:
        return dbc.Alert(str(e), color="danger")
@callback(
    Output('download-component', 'data', allow_duplicate=True),
    Input('download-optumgx-btn', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def download_optumgx(n_clicks, store_data):
    if not n_clicks or 'optumgx_result' not in store_data:
        raise dash.exceptions.PreventUpdate
    df = pd.DataFrame(store_data['optumgx_result'])
    return dcc.send_data_frame(df.to_csv, 'optumgx_results.csv', index=False)
@callback(
    Output('download-component', 'data', allow_duplicate=True),
    Input('download-groundhog-btn', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def download_groundhog(n_clicks, store_data):
    if not n_clicks or 'groundhog_cpt_processed' not in store_data:
        raise dash.exceptions.PreventUpdate
    df = pd.DataFrame(store_data['groundhog_cpt_processed'])
    return dcc.send_data_frame(df.to_csv, 'groundhog_results.csv', index=False)
@callback(
    Output('download-component', 'data', allow_duplicate=True),
    Input('download-gempy-btn', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def download_gempy(n_clicks, store_data):
    if not n_clicks or 'gempy_model' not in store_data:
        raise dash.exceptions.PreventUpdate
    df = pd.DataFrame(store_data['gempy_model']) # Simplified
    return dcc.send_data_frame(df.to_json, 'gempy_model.json')
@callback(
    Output('download-component', 'data', allow_duplicate=True),
    Input('download-pyoma2-btn', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def download_pyoma2(n_clicks, store_data):
    if not n_clicks or 'pyoma2_result' not in store_data:
        raise dash.exceptions.PreventUpdate
    df = pd.DataFrame(store_data['pyoma2_result'])
    return dcc.send_data_frame(df.to_csv, 'pyoma2_results.csv', index=False)
clientside_callback(
    """
    function(n_clicks, graph_id) {
        if (n_clicks > 0) {
            Plotly.downloadImage(graph_id, {format: 'png', width: 800, height: 600, filename: 'graph'});
        }
        return null;
    }
    """,
    Output('dummy-export', 'children'),
    Input('export-optumgx-png', 'n_clicks'),
    State('optumgx-graph', 'id'),
    prevent_initial_call=True
)
clientside_callback(
    """
    function(n_clicks, graph_id) {
        if (n_clicks > 0) {
            Plotly.downloadImage(graph_id, {format: 'pdf', width: 800, height: 600, filename: 'graph'});
        }
        return null;
    }
    """,
    Output('dummy-export', 'children', allow_duplicate=True),
    Input('export-optumgx-pdf', 'n_clicks'),
    State('optumgx-graph', 'id'),
    prevent_initial_call=True
)
if __name__ == '__main__':
    app.run(debug=True, port=8050)