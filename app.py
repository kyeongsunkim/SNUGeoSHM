import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import dash
from dash import html, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
import dash_auth
from dash.exceptions import PreventUpdate
from dash import dcc
from common.utils import init_data, load_sensor_data_sync, load_soil_data_sync
from common.navbar import create_navbar
from common.constants import PROJECT_DIR

# TODO: Add structured logging with file rotation for production
# TODO: Consider using environment-based log levels (DEBUG for dev, INFO for prod)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

init_data()

app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP], use_pages=True)

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Security upgrade: Use environment variables for auth
# TODO: Implement JWT-based authentication for better security
# TODO: Add session management and timeout functionality
# TODO: Consider adding OAuth2 integration for enterprise use
# TODO: Add rate limiting to prevent brute force attacks
DASH_USERNAME = os.getenv('DASH_USERNAME', 'admin')
DASH_PASSWORD = os.getenv('DASH_PASSWORD', 'secret')
dash_auth.BasicAuth(app, {DASH_USERNAME: DASH_PASSWORD})

navbar = create_navbar()

app.layout = dbc.Container(
    fluid=True,
    children=[
        html.Link(id="theme-sheet", rel="stylesheet", href=dbc.themes.DARKLY),
        navbar,
        dash.page_container,
        dcc.Store(id='global-store', data={}),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Error")),
                dbc.ModalBody(html.Div(id="error-message")),
            ],
            id="error-modal",
            is_open=False,
        ),
        # TODO: Make interval configurable via settings page
        # TODO: Add pause/resume functionality for data refresh
        dcc.Interval(id='digital-twin-interval', interval=60*1000, n_intervals=0),
        html.Div(id="dummy-export", style={"display": "none"}),
        # TODO: Add progress indicator for downloads
        dcc.Download(id='download-component'),
    ],
    style={"padding": 0},
)

@callback(
    Output("navbar-collapse", "is_open"),
    Input("navbar-toggler", "n_clicks"),
    State("navbar-collapse", "is_open"),
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@callback(
    [
        Output("theme-sheet", "href"),
        Output("navbar", "color"),
        Output("navbar", "dark"),
    ],
    Input("theme-switch", "on"),
)
def switch_theme(on):
    if on:
        return dbc.themes.DARKLY, "#1a1a1a", True
    return dbc.themes.BOOTSTRAP, "light", False

@callback(
    [Output('error-modal', 'is_open'), Output('error-message', 'children')],
    Input('global-store', 'data')
)
def show_error(store_data):
    if 'error' in store_data:
        logging.error(store_data['error'])
        return True, store_data['error']
    return False, no_update

@callback(
    Output('global-store', 'data', allow_duplicate=True),
    Input('digital-twin-interval', 'n_intervals'),
    prevent_initial_call=True
)
async def auto_load_data(n):
    # TODO: Add error handling for data loading failures
    # TODO: Implement retry logic with exponential backoff
    # TODO: Add data validation before storing
    # TODO: Consider incremental loading for large datasets
    # TODO: Add monitoring/alerting for data loading performance
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as executor:
        soil_data = await loop.run_in_executor(executor, load_soil_data_sync)
        sensor_data = await loop.run_in_executor(executor, load_sensor_data_sync)
    data = {'soil': soil_data.to_dict('records'), 'sensor': sensor_data.to_dict()}
    logging.info("Data auto-loaded successfully.")
    return data

if __name__ == '__main__':
    # TODO: Set debug=False for production deployment
    # TODO: Make port configurable via environment variable
    # TODO: Add HTTPS support for production
    # TODO: Add WSGI server configuration (gunicorn/waitress) for production
    app.run(debug=True, port=8050)