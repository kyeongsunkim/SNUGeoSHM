import dash_bootstrap_components as dbc
import dash_daq as daq
from dash_iconify import DashIconify
from dash import dcc

def create_navbar():
    navbar = dbc.Navbar(
        children=[
            dbc.NavbarBrand("Offshore Wind Turbine Monitoring Dashboard", style={"color": "white"}),
            daq.BooleanSwitch(id="theme-switch", on=True, label="Dark Mode", className="ms-auto"),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavItem(
                            dcc.Link(
                                [DashIconify(icon="fa-solid:house", width=20, className="me-2"), "Home"],
                                href="/",
                                style={"color": "white"},
                            )
                        ),
                        dbc.NavItem(
                            className="dropdown",
                            children=dbc.DropdownMenu(
                                children=[
                                    dbc.DropdownMenuItem(
                                        dcc.Link(
                                            [DashIconify(icon="mdi:chart-bell-curve-cumulative", width=20, className="me-2"), "OptumGX"],
                                            href="/optumgx",
                                        )
                                    ),
                                    dbc.DropdownMenuItem(
                                        dcc.Link(
                                            [DashIconify(icon="mdi:excavator", width=20, className="me-2"), "Groundhog"],
                                            href="/groundhog",
                                        )
                                    ),
                                    dbc.DropdownMenuItem(
                                        dcc.Link(
                                            [DashIconify(icon="mdi:layers-triple", width=20, className="me-2"), "Gempy"],
                                            href="/gempy",
                                        )
                                    ),
                                    dbc.DropdownMenuItem(
                                        dcc.Link(
                                            [DashIconify(icon="mdi:bridge", width=20, className="me-2"), "OpenSeesPy"],
                                            href="/openseespy",
                                        )
                                    ),
                                    dbc.DropdownMenuItem(
                                        dcc.Link(
                                            [DashIconify(icon="mdi:cube-scan", width=20, className="me-2"), "3D Viewer"],
                                            href="/3d-viewer",
                                        )
                                    ),
                                ],
                                label=[DashIconify(icon="fa-solid:cubes", width=20, className="me-2"), "FEM"],
                                nav=True,
                            ),
                        ),
                        dbc.NavItem(
                            className="dropdown",
                            children=dbc.DropdownMenu(
                                children=[
                                    dbc.DropdownMenuItem(
                                        dcc.Link(
                                            [DashIconify(icon="mdi:database-cog", width=20, className="me-2"), "Preprocessing"],
                                            href="/preprocessing",
                                        )
                                    ),
                                    dbc.DropdownMenuItem(
                                        dcc.Link(
                                            [DashIconify(icon="mdi:waveform", width=20, className="me-2"), "PyOMA2"],
                                            href="/pyoma2",
                                        )
                                    ),
                                    dbc.DropdownMenuItem(
                                        dcc.Link(
                                            [DashIconify(icon="fa-solid:location-crosshairs", width=20, className="me-2"), "Tracker"],
                                            href="/tracker",
                                        )
                                    ),
                                ],
                                label=[DashIconify(icon="fa-solid:database", width=20, className="me-2"), "Data"],
                                nav=True,
                            ),
                        ),
                    ],
                    className="ms-auto",
                    navbar=True,
                ),
                id="navbar-collapse",
                is_open=False,
                navbar=True,
            ),
        ],
        id="navbar",
        color="#1a1a1a",
        dark=True,
        sticky="top",
    )
    return navbar