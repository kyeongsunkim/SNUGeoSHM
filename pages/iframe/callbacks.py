from dash import callback, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import pyvista as pv
import os
import tempfile

from common.utils import process_vtk_file
from common.constants import PROJECT_DIR

@callback(
    [
        Output("upload-vtk-status", "children"),
        Output('global-store', 'data', allow_duplicate=True),
    ],
    Input("upload-vtk", "contents"),
    State("upload-vtk", "filename"),
    State("global-store", "data"),
    prevent_initial_call=True,
)
def handle_vtk_upload(contents, filename, store_data):
    try:
        decoded = process_vtk_file(contents, filename)
        store_update = store_data.copy()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.vtk') as tmp:
            tmp.write(decoded)
            tmp_path = tmp.name
        mesh = pv.read(tmp_path)
        plotter = pv.Plotter(off_screen=True)
        plotter.add_mesh(mesh)
        export_path = os.path.join(PROJECT_DIR, 'assets', 'uploaded_3d.html')
        plotter.export_html(export_path)
        store_update['vtk_html'] = '/assets/uploaded_3d.html'
        os.unlink(tmp_path)
        return dbc.Alert(f"{filename} uploaded.", color="success"), store_update
    except Exception as e:
        store_update = store_data.copy()
        store_update['error'] = str(e)
        return dbc.Alert(str(e), color="danger"), store_update

@callback(
    Output("3d-content", "src"),
    Input("view-3d-btn", "n_clicks"),
    State("global-store", "data"),
    prevent_initial_call=True
)
def view_3d(n, store_data):
    if 'vtk_html' in store_data:
        return store_data['vtk_html']
    raise PreventUpdate