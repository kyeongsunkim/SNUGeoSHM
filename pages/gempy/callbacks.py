from dash import callback, Input, Output, State, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dash_table import DataTable as dash_table
import gempy as gp
import gempy_viewer as gpv
import tempfile
import os
import logging
import dash as dcc
from common.utils import process_uploaded_file
from common.constants import PROJECT_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        if df is None:
            raise ValueError("No data uploaded.")

        # Validate required columns
        required_cols = {'X', 'Y', 'Z', 'formation'}
        if not required_cols.issubset(set(df.columns)):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}. Please check your file format.")

        store_update = store_data.copy()
        store_update['gempy_surfaces'] = df.to_dict('records')
        columns = [{"name": i, "id": i} for i in df.columns]
        fig = px.scatter_3d(df, x="X", y="Y", z="Z", color="formation", title="Surfaces Data") if all(col in df for col in ["X", "Y", "Z", "formation"]) else px.scatter()
        logging.info(f"Surfaces file {filename} uploaded successfully.")
        return dbc.Alert(f"{filename} uploaded.", color="success"), store_update, df.to_dict('records'), columns, fig
    except Exception as e:
        store_update = store_data.copy()
        store_update['error'] = str(e)
        logging.error(f"Surfaces upload error: {str(e)}")
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
        if df is None:
            raise ValueError("No data uploaded.")

        # Validate required columns
        required_cols = {'X', 'Y', 'Z', 'formation'}
        if not required_cols.issubset(set(df.columns)):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns: {missing}. Please check your file format.")

        store_update = store_data.copy()
        store_update['gempy_orientations'] = df.to_dict('records')
        columns = [{"name": i, "id": i} for i in df.columns]
        fig = px.scatter_3d(df, x="X", y="Y", z="Z", color="formation", title="Orientations Data") if all(col in df for col in ["X", "Y", "Z", "formation"]) else px.scatter()
        logging.info(f"Orientations file {filename} uploaded successfully.")
        return dbc.Alert(f"{filename} uploaded.", color="success"), store_update, df.to_dict('records'), columns, fig
    except Exception as e:
        store_update = store_data.copy()
        store_update['error'] = str(e)
        logging.error(f"Orientations upload error: {str(e)}")
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
        raise PreventUpdate
    df = pd.DataFrame(table_data)
    df = df.fillna(0)
    store_update = store_data.copy()
    store_update['gempy_surfaces'] = df.to_dict('records')
    logging.info("Surfaces data fixed.")
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
        raise PreventUpdate
    df = pd.DataFrame(table_data)
    df = df.fillna(0)
    store_update = store_data.copy()
    store_update['gempy_orientations'] = df.to_dict('records')
    logging.info("Orientations data fixed.")
    return dbc.Alert("Missing values filled with 0.", color="info"), store_update

@callback(
    [Output('gempy-output', 'children'), Output('global-store', 'data', allow_duplicate=True)],
    Input('run-gempy-btn', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def run_gempy(n_clicks, store_data):
    """
    Generate 3D geological model using GemPy

    FIXES APPLIED:
    - Bug #1: Changed solutions.to_dict() to store metadata only
    - Bug #2: Added try/finally for proper temp file cleanup
    """
    if not n_clicks:
        raise PreventUpdate

    store_update = store_data.copy()
    surf_path = None
    ori_path = None

    try:
        # Validate input data
        if 'gempy_surfaces' not in store_data or 'gempy_orientations' not in store_data:
            raise ValueError("Missing surfaces or orientations data. Please upload both files.")

        surfaces = pd.DataFrame(store_data['gempy_surfaces'])
        orientations = pd.DataFrame(store_data['gempy_orientations'])

        # FIX #2: Create temp files with proper cleanup
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w') as tmp_surf:
                surfaces.to_csv(tmp_surf.name, index=False)
                surf_path = tmp_surf.name
                logging.info(f"Created temp surfaces file: {surf_path}")

            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w') as tmp_ori:
                orientations.to_csv(tmp_ori.name, index=False)
                ori_path = tmp_ori.name
                logging.info(f"Created temp orientations file: {ori_path}")

            # Create importer
            importer = gp.data.ImporterHelper(
                path_to_surface_points=surf_path,
                path_to_orientations=ori_path
            )

            # Calculate extent
            extent = [
                surfaces.X.min(), surfaces.X.max(),
                surfaces.Y.min(), surfaces.Y.max(),
                surfaces.Z.min(), surfaces.Z.max()
            ]

            # Create geomodel
            geo_model = gp.create_geomodel(
                project_name='GemPy Model',
                extent=extent,
                refinement=4,
                importer_helper=importer
            )

            # Get formations
            if 'groundhog_profile' in store_data:  # Interop: Use Groundhog formations
                formations = pd.DataFrame(store_data['groundhog_profile'])['Soil type'].unique()
            else:
                formations = surfaces['formation'].unique()

            # Map formations
            gp.map_stack_to_surfaces(geo_model, {"Formations": formations})

            # Compute model
            gp.compute_model(geo_model)

            if geo_model.solutions is None:
                raise ValueError("Model computation failed. Check input data.")

            logging.info("GemPy model computed successfully")

            # Generate 3D visualization
            plot = gpv.plot_3d(geo_model, off_screen=True, plotter_type='basic', show=False)
            plot.p.render()

            export_path = os.path.join(PROJECT_DIR, 'assets', 'gempy_3d.html')
            plot.p.export_html(export_path)

            logging.info(f"3D visualization exported to: {export_path}")

            # Create output
            output = [
                dbc.Alert("GemPy model generated successfully!", color="success", className="mb-3"),
                html.H5("3D Geological Model"),
                html.Iframe(src='/assets/gempy_3d.html', style={"width": "100%", "height": "600px"}),
                html.Hr(),
                html.H6("Model Summary:"),
                html.Ul([
                    html.Li(f"Formations: {len(formations)}"),
                    html.Li(f"Surface points: {len(surfaces)}"),
                    html.Li(f"Orientations: {len(orientations)}"),
                    html.Li(f"Model extent: X=[{extent[0]:.1f}, {extent[1]:.1f}], Y=[{extent[2]:.1f}, {extent[3]:.1f}], Z=[{extent[4]:.1f}, {extent[5]:.1f}]"),
                ])
            ]

            # FIX #1: Store metadata only, not entire Solutions object
            # Solutions object doesn't have to_dict() method and would be too large anyway
            store_update['gempy_model'] = {
                'computed': True,
                'n_formations': len(formations),
                'formations': list(formations),
                'n_surfaces': len(surfaces),
                'n_orientations': len(orientations),
                'extent': extent,
                'export_path': export_path,
                'refinement': 4
            }

            logging.info("GemPy processing completed successfully.")
            return output, store_update

        finally:
            # FIX #2: Always cleanup temp files
            if surf_path and os.path.exists(surf_path):
                try:
                    os.unlink(surf_path)
                    logging.info(f"Cleaned up temp file: {surf_path}")
                except Exception as e:
                    logging.warning(f"Could not delete temp file {surf_path}: {e}")

            if ori_path and os.path.exists(ori_path):
                try:
                    os.unlink(ori_path)
                    logging.info(f"Cleaned up temp file: {ori_path}")
                except Exception as e:
                    logging.warning(f"Could not delete temp file {ori_path}: {e}")

    except Exception as e:
        store_update['error'] = str(e)
        logging.error(f"GemPy processing error: {str(e)}")
        import traceback
        traceback.print_exc()
        return [dbc.Alert(f"Error: {str(e)}", color="danger")], store_update

@callback(
    Output('download-component', 'data', allow_duplicate=True),
    Input('download-gempy-btn', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def download_gempy(n_clicks, store_data):
    """
    Download GemPy model metadata

    Note: Downloads metadata, not full Solutions object
    """
    if not n_clicks or 'gempy_model' not in store_data:
        raise PreventUpdate

    model_data = store_data.get('gempy_model')
    if model_data is None or not isinstance(model_data, dict):
        raise PreventUpdate

    # Convert metadata to JSON
    import json
    logging.info("GemPy model metadata downloaded.")
    return dcc.send_string(json.dumps(model_data, indent=2), 'gempy_model.json')
