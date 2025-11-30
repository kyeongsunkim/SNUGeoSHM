from dash import callback, Input, Output, State, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dash_table import DataTable as dash_table
import matplotlib.pyplot as plt
from groundhog.siteinvestigation.insitutests.pcpt_processing import PCPTProcessing
from groundhog.general.soilprofile import SoilProfile
import logging
import dash as dcc
from common.utils import process_uploaded_file, matplotlib_to_base64

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        if df is None:
            raise ValueError("No data uploaded.")
        store_update = store_data.copy()
        store_update['groundhog_cpt'] = df.to_dict('records')
        columns = [{"name": i, "id": i} for i in df.columns]
        fig = px.line(df, x="z [m]", y="qc [MPa]", title="CPT Data") if "z [m]" in df.columns and "qc [MPa]" in df.columns else px.scatter()
        logging.info(f"CPT file {filename} uploaded successfully.")
        return dbc.Alert(f"{filename} uploaded.", color="success"), store_update, df.to_dict('records'), columns, fig
    except Exception as e:
        store_update = store_data.copy()
        store_update['error'] = str(e)
        logging.error(f"CPT upload error: {str(e)}")
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
        if df is None:
            raise ValueError("No data uploaded.")
        store_update = store_data.copy()
        store_update['groundhog_layering'] = df.to_dict('records')
        columns = [{"name": i, "id": i} for i in df.columns]
        fig = px.bar(df, x="Soil type", y="Depth from [m]", title="Layering Data") if "Soil type" in df.columns and "Depth from [m]" in df.columns else px.scatter()
        logging.info(f"Layering file {filename} uploaded successfully.")
        return dbc.Alert(f"{filename} uploaded.", color="success"), store_update, df.to_dict('records'), columns, fig
    except Exception as e:
        store_update = store_data.copy()
        store_update['error'] = str(e)
        logging.error(f"Layering upload error: {str(e)}")
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
        raise PreventUpdate
    df = pd.DataFrame(table_data)
    df = df.fillna(0)
    store_update = store_data.copy()
    store_update['groundhog_cpt'] = df.to_dict('records')
    logging.info("CPT data fixed.")
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
        raise PreventUpdate
    df = pd.DataFrame(table_data)
    df = df.fillna(0)
    store_update = store_data.copy()
    store_update['groundhog_layering'] = df.to_dict('records')
    logging.info("Layering data fixed.")
    return dbc.Alert("Missing values filled with 0.", color="info"), store_update

@callback(
    [Output('groundhog-output', 'children'), Output('global-store', 'data', allow_duplicate=True)],
    Input('run-groundhog-btn', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def run_groundhog(n_clicks, store_data):
    if not n_clicks:
        raise PreventUpdate
    store_update = store_data.copy()
    try:
        if 'groundhog_cpt' not in store_data or 'groundhog_layering' not in store_data:
            raise ValueError("Missing CPT or layering data. Please upload both files.")
        cpt_df = pd.DataFrame(store_data['groundhog_cpt'])
        layering_df = pd.DataFrame(store_data['groundhog_layering'])
        cpt = PCPTProcessing(title='CPT Process')
        cpt.load_pandas(cpt_df, z_key='z [m]', qc_key='qc [MPa]', fs_key='fs [MPa]')
        if cpt.data is None:
            raise ValueError("CPT data loading failed. Check file columns and content.")
        cpt.normalise_pcpt()
        cpt.apply_correlation(name="relativedensity_ncsand_baldi", outputs={"Dr": "Dr [%]"}, apply_for_soiltypes=["Sand"])
        profile = SoilProfile(layering_df)
        if profile.layering is None:
            raise ValueError("Layering profile is empty. Check uploaded data.")
        # Plot example
        fig, ax = plt.subplots()
        cpt.plot_raw_pcpt(plot_rf=True, zlines=[0, 5, 10])
        if fig is None:
            raise ValueError("Plot generation failed.")
        img_src = matplotlib_to_base64(fig)
        output = [html.Img(src=img_src, style={'width': '100%'})]
        store_update['groundhog_cpt_processed'] = cpt.data.to_dict('records')
        store_update['groundhog_profile'] = profile.layering.to_dict('records')
        logging.info("Groundhog processing completed successfully.")
        return output, store_update
    except Exception as e:
        store_update['error'] = str(e)
        logging.error(f"Groundhog processing error: {str(e)}")
        return [dbc.Alert(str(e), color="danger")], store_update

@callback(
    Output('download-component', 'data', allow_duplicate=True),
    Input('download-groundhog-btn', 'n_clicks'),
    State('global-store', 'data'),
    prevent_initial_call=True
)
def download_groundhog(n_clicks, store_data):
    if not n_clicks or 'groundhog_cpt_processed' not in store_data:
        raise PreventUpdate
    processed_data = store_data.get('groundhog_cpt_processed')
    if processed_data is None:
        raise ValueError("No processed data available for download.")
    df = pd.DataFrame(processed_data)
    logging.info("Groundhog results downloaded.")
    return dcc.send_data_frame(df.to_csv, 'groundhog_results.csv', index=False)

