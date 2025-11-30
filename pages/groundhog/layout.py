from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dash_table import DataTable as dash_table

def layout():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H2("Soil/CPT Processing with Groundhog"),

                # CPT Data Upload Section
                html.H4("1. Upload CPT Data", className="mt-3"),
                dcc.Upload(
                    id="upload-groundhog-cpt",
                    children=dbc.Button(
                        ["📁 Upload excel_example_cpt.xlsx"],
                        className="mr-2",
                        color="primary"
                    ),
                    multiple=False
                ),
                html.Div(id="upload-groundhog-cpt-status", className="mt-2"),

                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                html.P("Edit the CPT data table below. Required columns: z [m], qc [MPa], fs [MPa], u [kPa]"),
                                dash_table(
                                    id="groundhog-cpt-data-table",
                                    editable=True,
                                    row_deletable=True,
                                    page_size=10,
                                    style_table={'overflowX': 'auto'},
                                    style_cell={
                                        'textAlign': 'left',
                                        'padding': '10px'
                                    },
                                    style_header={
                                        'backgroundColor': 'rgb(230, 230, 230)',
                                        'fontWeight': 'bold'
                                    }
                                ),
                                dbc.Button("Fix Missing Values", id="fix-groundhog-cpt-btn", className="mt-2", color="warning"),
                                html.Div(id="groundhog-cpt-fix-status", className="mt-2"),
                            ],
                            title="📊 View/Edit CPT Data",
                        ),
                        dbc.AccordionItem(
                            dcc.Graph(id="groundhog-cpt-data-viz"),
                            title="📈 Visualize CPT Data",
                        ),
                    ],
                    start_collapsed=True,
                    className="mt-3"
                ),

                # Layering Data Upload Section
                html.H4("2. Upload Soil Layering Data", className="mt-4"),
                dcc.Upload(
                    id="upload-groundhog-layering",
                    children=dbc.Button(
                        ["📁 Upload excel_example_layering.xlsx"],
                        className="mr-2",
                        color="primary"
                    ),
                    multiple=False
                ),
                html.Div(id="upload-groundhog-layering-status", className="mt-2"),

                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                html.P("Edit the soil layering data. Required columns: Depth from [m], Depth to [m], Soil type"),
                                dash_table(
                                    id="groundhog-layering-data-table",
                                    editable=True,
                                    row_deletable=True,
                                    page_size=10,
                                    style_table={'overflowX': 'auto'},
                                    style_cell={
                                        'textAlign': 'left',
                                        'padding': '10px'
                                    },
                                    style_header={
                                        'backgroundColor': 'rgb(230, 230, 230)',
                                        'fontWeight': 'bold'
                                    }
                                ),
                                dbc.Button("Fix Missing Values", id="fix-groundhog-layering-btn", className="mt-2", color="warning"),
                                html.Div(id="groundhog-layering-fix-status", className="mt-2"),
                            ],
                            title="📊 View/Edit Layering Data",
                        ),
                        dbc.AccordionItem(
                            dcc.Graph(id="groundhog-layering-data-viz"),
                            title="📈 Visualize Layering Data",
                        ),
                    ],
                    start_collapsed=True,
                    className="mt-3"
                ),

                # Processing Section
                html.H4("3. Process CPT Data", className="mt-4"),
                html.P("Process the uploaded CPT and layering data using Groundhog library."),
                dbc.Button(
                    "▶ Process CPT",
                    id="run-groundhog-btn",
                    color="success",
                    size="lg",
                    className="mt-2"
                ),
                dbc.Tooltip(
                    "Process uploaded CPT and layering data to generate soil profile analysis",
                    target="run-groundhog-btn"
                ),

                # Results Section
                html.Hr(className="mt-4"),
                dcc.Loading(
                    html.Div(id="groundhog-output", className="mt-3"),
                    type="circle"
                ),

                # Download Section
                html.Div([
                    dbc.Button(
                        "⬇ Download Results",
                        id="download-groundhog-btn",
                        color="info",
                        className="mt-3"
                    ),
                    # FIXED: Add the missing download component
                    dcc.Download(id="download-component"),
                ]),

                # Help Section
                dbc.Accordion(
                    [
                        dbc.AccordionItem(
                            [
                                html.H6("Expected File Formats:"),
                                html.P("CPT Data (Excel/CSV):"),
                                html.Ul([
                                    html.Li("z [m] - Depth in meters"),
                                    html.Li("qc [MPa] - Cone resistance in MPa"),
                                    html.Li("fs [MPa] - Sleeve friction in MPa"),
                                    html.Li("u [kPa] - Pore pressure in kPa (optional)"),
                                    html.Li("Rf [%] - Friction ratio in % (optional)"),
                                ]),
                                html.P("Soil Layering Data (Excel/CSV):"),
                                html.Ul([
                                    html.Li("Depth from [m] - Top depth of layer"),
                                    html.Li("Depth to [m] - Bottom depth of layer"),
                                    html.Li("Soil type - Type of soil (e.g., SAND, CLAY)"),
                                    html.Li("Total unit weight [kN/m3] - Unit weight (optional)"),
                                ]),
                                html.Hr(),
                                html.H6("Known Limitations:"),
                                html.Ul([
                                    html.Li("Normalization requires vertical stress calculation (currently disabled)"),
                                    html.Li("Soil type correlations require proper soil profile mapping"),
                                    html.Li("Only basic CPT visualization is available in this version"),
                                ]),
                            ],
                            title="❓ Help & File Format Guide",
                        ),
                    ],
                    start_collapsed=True,
                    className="mt-4"
                ),
            ]
        )
    )
