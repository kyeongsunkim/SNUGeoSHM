from dash import callback, Input, Output, State, html, no_update, Dash
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash.dcc as dcc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash.dash_table import DataTable
from groundhog.siteinvestigation.insitutests.pcpt_processing import PCPTProcessing, DEFAULT_CONE_PROPERTIES, CORRELATIONS
from groundhog.general.soilprofile import SoilProfile, plot_fence_diagram
from groundhog.siteinvestigation.insitutests.pcpt_processing import plot_combined_longitudinal_profile
from groundhog.general.plotting import LogPlot
import logging
from common.utils import process_uploaded_file  # Assuming this is defined elsewhere

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the layout for the Groundhog page
layout = dbc.Container(
    fluid=True,
    children=[
        dbc.Row(
            justify="center",
            children=[
                dbc.Col(
                    html.H1("Groundhog CPT Processing Report", className="text-center mb-4"),
                    width=12
                )
            ]
        ),
        dbc.Row(
            className="mb-4",
            children=[
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Upload CPT Data", className="font-weight-bold"),
                            dbc.CardBody(
                                [
                                    dcc.Upload(
                                        id="upload-groundhog-cpt",
                                        children=html.Div(["Drag and Drop or ", html.A("Select CPT File")]),
                                        style={
                                            "width": "100%",
                                            "height": "60px",
                                            "lineHeight": "60px",
                                            "borderWidth": "1px",
                                            "borderStyle": "dashed",
                                            "borderRadius": "5px",
                                            "textAlign": "center",
                                            "margin": "10px",
                                        },
                                        multiple=False,
                                    ),
                                    html.Div(id="upload-groundhog-cpt-status"),
                                    html.Hr(),
                                    html.H5("CPT Data Preview", className="mt-3"),
                                    DataTable(
                                        id="groundhog-cpt-data-table",
                                        editable=True,
                                        page_size=10,
                                        style_table={"overflowX": "auto"},
                                    ),
                                    dcc.Graph(id="groundhog-cpt-data-viz"),
                                    dbc.Button("Fix Missing Values in CPT", id="fix-groundhog-cpt-btn", color="primary", className="mt-3"),
                                    html.Div(id="groundhog-cpt-fix-status"),
                                ]
                            ),
                        ],
                        outline=True,
                    ),
                    md=6,
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Upload Layering Data", className="font-weight-bold"),
                            dbc.CardBody(
                                [
                                    dcc.Upload(
                                        id="upload-groundhog-layering",
                                        children=html.Div(["Drag and Drop or ", html.A("Select Layering File")]),
                                        style={
                                            "width": "100%",
                                            "height": "60px",
                                            "lineHeight": "60px",
                                            "borderWidth": "1px",
                                            "borderStyle": "dashed",
                                            "borderRadius": "5px",
                                            "textAlign": "center",
                                            "margin": "10px",
                                        },
                                        multiple=False,
                                    ),
                                    html.Div(id="upload-groundhog-layering-status"),
                                    html.Hr(),
                                    html.H5("Layering Data Preview", className="mt-3"),
                                    DataTable(
                                        id="groundhog-layering-data-table",
                                        editable=True,
                                        page_size=10,
                                        style_table={"overflowX": "auto"},
                                    ),
                                    dcc.Graph(id="groundhog-layering-data-viz"),
                                    dbc.Button("Fix Missing Values in Layering", id="fix-groundhog-layering-btn", color="primary", className="mt-3"),
                                    html.Div(id="groundhog-layering-fix-status"),
                                ]
                            ),
                        ],
                        outline=True,
                    ),
                    md=6,
                ),
            ],
        ),
        dbc.Row(
            justify="center",
            className="mb-4",
            children=[
                dbc.Button("Run Groundhog Processing", id="run-groundhog-btn", color="success", size="lg"),
            ],
        ),
        dbc.Row(
            children=[
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Processing Results Report", className="font-weight-bold"),
                            dbc.CardBody(id="groundhog-output"),
                        ],
                        outline=True,
                    ),
                    width=12,
                ),
            ],
        ),
        dbc.Row(
            justify="center",
            className="mt-4",
            children=[
                dbc.Button("Download Processed Results", id="download-groundhog-btn", color="info", size="lg"),
            ],
        ),
        dcc.Download(id="download-component"),
        dcc.Store(id="global-store", data={}),
    ],
    style={"padding": "20px"},
)

# Callbacks remain similar, but updated for better UX and fixed processing

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
        store_update = store_data.copy() if store_data else {}
        store_update['groundhog_cpt'] = df.to_dict('records')
        columns = [{"name": i, "id": i} for i in df.columns]
        fig = px.line(df, x="z [m]", y="qc [MPa]", title="CPT Data Preview") if "z [m]" in df.columns and "qc [MPa]" in df.columns else go.Figure()
        fig.update_layout(template="plotly_white")
        logging.info(f"CPT file {filename} uploaded successfully.")
        return dbc.Alert(f"{filename} uploaded successfully.", color="success"), store_update, df.to_dict('records'), columns, fig
    except Exception as e:
        store_update = store_data.copy() if store_data else {}
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
        store_update = store_data.copy() if store_data else {}
        store_update['groundhog_layering'] = df.to_dict('records')
        columns = [{"name": i, "id": i} for i in df.columns]
        fig = px.bar(df, x="Soil type", y="Depth from [m]", title="Layering Preview", color="Soil type") if "Soil type" in df.columns and "Depth from [m]" in df.columns else go.Figure()
        fig.update_layout(template="plotly_white")
        logging.info(f"Layering file {filename} uploaded successfully.")
        return dbc.Alert(f"{filename} uploaded successfully.", color="success"), store_update, df.to_dict('records'), columns, fig
    except Exception as e:
        store_update = store_data.copy() if store_data else {}
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
    return dbc.Alert("Missing values filled with 0 in CPT data.", color="info"), store_update

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
    return dbc.Alert("Missing values filled with 0 in layering data.", color="info"), store_update

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

        # Initialize PCPTProcessing from uploaded CPT data
        pcpt = PCPTProcessing(title="Uploaded CPT")
        pcpt.load_pandas(
            df=cpt_df,
            z_key="z [m]",
            qc_key="qc [MPa]",
            fs_key="fs [kPa]" if "fs [kPa]" in cpt_df.columns else None,
            u2_key="u [kPa]" if "u [kPa]" in cpt_df.columns else None,
        )
        

        # Initialize SoilProfile from layering data
        layering = SoilProfile(layering_df)  # Assumes columns: 'Depth from [m]', 'Depth to [m]', 'Soil type', etc.
        layering.title = 'Uploaded Profile'
        

        color_dict = {
            'SAND': '#ffe300',  # Yellow
            'Silty SAND': '#fff5a3',  # Light yellow
            'Clayey SAND': '#c2ae0c',  # Dark yellow
            'Gravelly SAND': '#868a44',  # Yellow with a shade of grey
            'CLAY': '#af7337'  # Brown
        }

        # Map properties
        pcpt.map_properties(layer_profile=layering, cone_profile=DEFAULT_CONE_PROPERTIES)

        # Generate plots
        raw_fig = pcpt.plot_raw_pcpt(return_fig=True)
        raw_fig.update_layout(template="plotly_white", title="Raw CPT Data")

        pcpt.normalise_pcpt()
        norm_fig = pcpt.plot_normalised_pcpt(return_fig=True)
        norm_fig.update_layout(template="plotly_white", title="Normalised CPT Data")

        rob_fig = pcpt.plot_robertson_chart(return_fig=True)
        rob_fig.update_layout(template="plotly_white", title="Robertson Soil Classification Chart")

        # Apply correlations
        pcpt.apply_correlation('Ic Robertson and Wride (1998)', outputs={'Ic [-]': 'Ic [-]'})
        pcpt.apply_correlation(
            'Gmax Rix and Stokoe (1991)', outputs={'Gmax [kPa]': 'Gmax sand [kPa]'},
            apply_for_soiltypes=['SAND',]
        )
        pcpt.apply_correlation(
            'Gmax Mayne and Rix (1993)', outputs={'Gmax [kPa]': 'Gmax clay [kPa]'},
            apply_for_soiltypes=['CLAY',]
        )

        # Processed plot
        cpt_processed_plot = LogPlot(layering, no_panels=3, fillcolordict={'SAND': 'yellow', 'CLAY': 'brown'})
        cpt_processed_plot.add_trace(
            x=pcpt.data['qc [MPa]'],
            z=pcpt.data['z [m]'],
            name='qc',
            showlegend=False,
            panel_no=1
        )
        cpt_processed_plot.add_trace(
            x=pcpt.data['Ic [-]'],
            z=pcpt.data['z [m]'],
            name='Ic',
            showlegend=False,
            panel_no=2
        )
        cpt_processed_plot.add_trace(
            x=pcpt.data['Gmax sand [kPa]'],
            z=pcpt.data['z [m]'],
            name='Gmax SAND',
            showlegend=True,
            panel_no=3
        )
        cpt_processed_plot.add_trace(
            x=pcpt.data['Gmax clay [kPa]'],
            z=pcpt.data['z [m]'],
            name='Gmax CLAY',
            showlegend=True,
            panel_no=3
        )
        cpt_processed_plot.set_xaxis(title=r'$ q_c \ \text{[MPa]} $', panel_no=1)
        cpt_processed_plot.set_xaxis(title=r'$ I_c \ \text{[-]} $', panel_no=2, range=(1, 3.5))
        cpt_processed_plot.set_xaxis(title=r'$ G_{max} \ \text{[kPa]} $', panel_no=3, range=(0, 200e3))
        cpt_processed_plot.set_zaxis(title=r'$ z \ \text{[m]} $', range=(20, 0))
        processed_fig = cpt_processed_plot.fig
        processed_fig.update_layout(template="plotly_white", title="Processed CPT with Correlations")

        # Fence diagram
        profile_fig = plot_fence_diagram(
            profiles=[layering],
            band=2000,
            fillcolordict=color_dict,
            opacity=0.8, logwidth=250
        )
        profile_fig.update_layout(template="plotly_white", title="Soil Profile Fence Diagram")

        # Combined longitudinal profile
        cpt_profile_fig = plot_combined_longitudinal_profile(
            cpts=[pcpt],
            profiles=[layering],
            band=1000,
            fillcolordict=color_dict,
            opacity=0.8, logwidth=250, scale_factor=10
        )
        cpt_profile_fig.update_layout(template="plotly_white", title="Combined Longitudinal CPT Profile")

        # Processed data for storage and download
        processed_df = pcpt.data
        store_update['groundhog_cpt_processed'] = processed_df.to_dict('records')
        store_update['groundhog_profile'] = layering_df.to_dict('records')  # Or layering.to_pandas() if needed

        # Build the report UI
        report = [
            html.H3("Groundhog Processing Report", className="mb-3"),
            html.P("This report presents the processed CPT data, soil layering, and applied correlations. Visualizations are provided for easy understanding."),
            html.H4("1. Input Data Summary", className="mt-4"),
            html.H5("CPT Data Table"),
            DataTable(
                data=cpt_df.head(10).to_dict('records'),  # Preview top rows
                columns=[{"name": i, "id": i} for i in cpt_df.columns],
                page_size=5,
                style_table={"overflowX": "auto"},
            ),
            html.P("Full CPT data is available in the preview section above."),
            html.H5("Layering Data Table"),
            DataTable(
                data=layering_df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in layering_df.columns],
                style_table={"overflowX": "auto"},
            ),
            html.H4("2. Raw CPT Visualization", className="mt-4"),
            dcc.Graph(figure=raw_fig),
            html.P("The raw cone penetration test data plotted against depth."),
            html.H4("3. Normalized CPT Visualization", className="mt-4"),
            dcc.Graph(figure=norm_fig),
            html.P("Normalized resistance and friction ratio for soil behavior analysis."),
            html.H4("4. Robertson Soil Classification Chart", className="mt-4"),
            dcc.Graph(figure=rob_fig),
            html.P("Soil type classification based on normalized CPT parameters."),
            html.H4("5. Applied Correlations", className="mt-4"),
            html.P("Correlations applied: Ic (Robertson and Wride 1998), Gmax for sand (Rix and Stokoe 1991), Gmax for clay (Mayne and Rix 1993)."),
            html.H4("6. Processed CPT with Correlations", className="mt-4"),
            dcc.Graph(figure=processed_fig),
            html.P("Log plot showing qc, Ic, and Gmax values across depth, overlaid with soil layers."),
            html.H4("7. Soil Profile Fence Diagram", className="mt-4"),
            dcc.Graph(figure=profile_fig),
            html.P("Visual representation of soil layers in a fence diagram format."),
            html.H4("8. Combined Longitudinal CPT Profile", className="mt-4"),
            dcc.Graph(figure=cpt_profile_fig),
            html.P("Integrated view of CPT data and soil profile along a longitudinal section."),
            html.H4("9. Processed Data Table (Preview)", className="mt-4"),
            DataTable(
                data=processed_df.head(10).to_dict('records'),
                columns=[{"name": i, "id": i} for i in processed_df.columns],
                page_size=5,
                style_table={"overflowX": "auto"},
            ),
            html.P("Download the full processed data using the button below."),
        ]

        logging.info("Groundhog processing completed successfully.")
        return report, store_update
    except Exception as e:
        store_update['error'] = str(e)
        logging.error(f"Groundhog processing error: {str(e)}")
        return [dbc.Alert(f"Error: {str(e)}", color="danger")], store_update

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
    return dcc.send_data_frame(df.to_csv, 'groundhog_processed_results.csv', index=False)