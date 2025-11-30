from dash import callback, Input, Output, State, html, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_leaflet as dlf
import pandas as pd
import pyvista as pv
import os
import plotly.graph_objects as go
import plotly.express as px
import xarray as xr
import numpy as np
import gempy as gp
import gempy_viewer as gpv
import tempfile
import matplotlib.pyplot as plt
from groundhog.siteinvestigation.insitutests.pcpt_processing import PCPTProcessing
from groundhog.general.soilprofile import SoilProfile
try:
    import pyoma2
    PYOMA_AVAILABLE = True
except ImportError:
    PYOMA_AVAILABLE = False
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

from common.constants import PROJECT_DIR
from common.utils import load_soil_data_sync, load_sensor_data_sync, simulate_optumgx, simulate_pyoma2, matplotlib_to_base64
from pages.home.wtg_data import WTG_DATA, get_wtg_time_series, get_status_color

# TODO: Refactor large callbacks into smaller, testable functions
# TODO: Add comprehensive error handling for all external library calls
# TODO: Implement caching strategy for expensive computations
# TODO: Add progress indicators for long-running operations
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@callback(
    Output("home-map", "children"),
    Input("global-store", "data"),
)
def update_map(data):
    # TODO: Add marker clustering for large datasets
    # TODO: Implement custom marker icons based on formation type
    # TODO: Add popup with detailed soil information
    # TODO: Optimize performance for >1000 markers using MarkerCluster
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
        raise PreventUpdate
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
                export_path = os.path.join(PROJECT_DIR, 'assets', '3d_soil.html')
                plotter.export_html(export_path)
                logging.info("3D view generated.")
                return html.Iframe(src='/assets/3d_soil.html', style={"width": "100%", "height": "600px"})
        return dbc.Alert("No soil data for 3D view.", color="warning")
    except Exception as e:
        logging.error(str(e))
        return dbc.Alert(str(e), color="danger")

@callback(
    [Output('pipeline-output', 'children'), Output('global-store', 'data', allow_duplicate=True)],
    Input('pipeline-btn', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
async def run_pipeline(n_clicks, store_data):
    if not n_clicks:
        raise PreventUpdate
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
                refinement=4,
                importer_helper=importer
            )
            gp.map_stack_to_surfaces(geo_model, {"Formations": surfaces['surface'].unique() if 'surface' in surfaces else surfaces['formation'].unique()})
            gp.compute_model(geo_model)
            store_update['gempy_model'] = geo_model.solutions.to_dict()
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
                freqs, amps = [], []  # Replace with alg results
            else:
                freqs, amps = simulate_pyoma2(data[0])
            store_update['pyoma2_result'] = {'freqs': freqs.tolist(), 'amps': amps.tolist()}
            outputs.append(html.P("PyOMA2 completed."))
        else:
            outputs.append(html.P("PyOMA2 skipped: missing data."))
        outputs.append(html.P("Pipeline finished. Results stored for visualization."))
        logging.info("Pipeline ran successfully.")
        return outputs, store_update
    except Exception as e:
        logging.error(str(e))
        store_update['error'] = str(e)
        return [dbc.Alert(str(e), color="danger")], store_update

@callback(
    Output('comparison-output', 'children'),
    Input('compare-btn', 'n_clicks'),
    Input('digital-twin-interval', 'n_intervals'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
async def compare_sim_real(n_clicks, n_intervals, store_data):
    from dash import callback_context
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    if 'optumgx_result' not in store_data or 'sensor' not in store_data:
        if 'sensor' not in store_data:
            try:
                loop = asyncio.get_running_loop()
                with ThreadPoolExecutor() as executor:
                    store_data['sensor'] = await loop.run_in_executor(executor, load_sensor_data_sync).to_dict()
            except Exception as e:
                logging.error(str(e))
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
        logging.info("Comparison generated.")
        return dcc.Graph(id="compare-graph", figure=fig)
    except Exception as e:
        logging.error(str(e))
        return dbc.Alert(str(e), color="danger")