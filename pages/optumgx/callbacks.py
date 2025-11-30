from dash import callback, Input, Output, State, clientside_callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dash_table import DataTable as dash_table
import logging
import asyncio

from common.utils import process_uploaded_file, simulate_optumgx

# TODO: Add data validation for OptumGX-specific formats
# TODO: Implement real OptumGX API integration
# TODO: Add support for batch processing multiple files
# TODO: Add export to OptumGX native format
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        logging.info(f"Uploaded {filename}")
        return dbc.Alert(f"{filename} uploaded successfully.", color="success"), store_update, df.to_dict('records'), columns, fig
    except Exception as e:
        store_update = store_data.copy()
        store_update['error'] = str(e)
        logging.error(str(e))
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
        raise PreventUpdate
    df = pd.DataFrame(table_data)
    df = df.fillna(0)
    store_update = store_data.copy()
    store_update['optumgx_data'] = df.to_dict('records')
    logging.info("OptumGX data fixed.")
    return dbc.Alert("Missing values filled with 0.", color="info"), store_update

@callback(
    [Output('optumgx-output', 'children'), Output('global-store', 'data', allow_duplicate=True)],
    Input('run-optumgx-btn', 'n_clicks'),
    State('material-input', 'value'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
async def run_optumgx(n_clicks, material, store_data):
    if not n_clicks:
        raise PreventUpdate
    try:
        if 'optumgx_data' in store_data:
            df = pd.DataFrame(store_data['optumgx_data'])
            if 'qt [MPa]' in df.columns:
                material = df['qt [MPa]'].mean()
        if 'groundhog_cpt_processed' in store_data:
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
        logging.info("OptumGX simulation ran.")
        return output, store_update
    except Exception as e:
        store_update = store_data.copy()
        store_update['error'] = str(e)
        logging.error(str(e))
        return [dbc.Alert(str(e), color="danger")], store_update

@callback(
    Output('download-component', 'data', allow_duplicate=True),
    Input('download-optumgx-btn', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def download_optumgx(n_clicks, store_data):
    if not n_clicks or 'optumgx_result' not in store_data:
        raise PreventUpdate
    df = pd.DataFrame(store_data['optumgx_result'])
    logging.info("OptumGX results downloaded.")
    return dcc.send_data_frame(df.to_csv, 'optumgx_results.csv', index=False)

# Clientside callbacks remain the same
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