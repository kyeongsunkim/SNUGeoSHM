from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dash_table import DataTable as dash_table

def layout():
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
                                dash_table(id="gempy-surfaces-data-table", editable=True, row_deletable=True, page_size=10),
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
                                dash_table(id="gempy-orientations-data-table", editable=True, row_deletable=True, page_size=10),
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