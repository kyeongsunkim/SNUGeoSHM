from dash import dcc, html
import dash_bootstrap_components as dbc

def layout():
    return dbc.Card(
        dbc.CardBody(
            [
                html.H2("3D VTK Viewer"),
                dcc.Upload(id="upload-vtk", children=dbc.Button("Upload VTK File", className="mr-2"), multiple=False),
                html.Div(id="upload-vtk-status"),
                dbc.Button("View 3D Model", id="view-3d-btn"),
                dbc.Tooltip("Load and view uploaded VTK file in 3D", target="view-3d-btn"),
                dcc.Loading(html.Iframe(id="3d-content", style={"border": "none", "width": "100%", "height": "800px"}), type="circle"),
            ]
        )
    )