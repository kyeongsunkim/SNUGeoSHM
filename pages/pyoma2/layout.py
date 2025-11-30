from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dash_table import DataTable as dash_table

def layout():
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
                                dash_table(id="pyoma2-data-table", editable=True, row_deletable=True, page_size=10),
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