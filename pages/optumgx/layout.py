from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dash_table import DataTable as dash_table

def layout():
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
                                dash_table(id="optumgx-data-table", editable=True, row_deletable=True, page_size=10),
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