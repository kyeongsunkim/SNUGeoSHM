# Standalone example for Predictive Maintenance Dashboard: Estimates Remaining Useful Life (RUL).
# Uses synthetic data and a simple linear regression model.
# Extended with more sensors, data visualization, and input validation.
# Requires: pip install dash plotly pandas scikit-learn dash-bootstrap-components
# Run with `python predictive_maintenance_rul_dashboard.py`.

from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.express as px

# Generate extended synthetic data (more cycles and sensors for realism)
np.random.seed(42)
cycles = np.arange(1, 201)  # More data points
sensor1 = 100 - cycles * 0.5 + np.random.normal(0, 5, 200)  # Degradation trend
sensor2 = 50 + cycles * 0.3 + np.random.normal(0, 3, 200)
sensor3 = 20 - cycles * 0.1 + np.random.normal(0, 2, 200)  # Additional sensor
rul = 200 - cycles  # Linear RUL degradation

data = pd.DataFrame({'cycle': cycles, 'sensor1': sensor1, 'sensor2': sensor2, 'sensor3': sensor3, 'rul': rul})

# Train model on full data
X = data[['cycle', 'sensor1', 'sensor2', 'sensor3']]
y = data['rul']
model = LinearRegression().fit(X, y)

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("Predictive Maintenance RUL Dashboard"),
    html.P("Enter current engine state to estimate RUL. Model trained on synthetic degradation data."),
    dbc.Row([
        dbc.Col([
            html.H3("Input Current Cycle and Sensor Readings"),
            dbc.Label("Cycle"),
            dcc.Input(id='input-cycle', type='number', value=50, min=1),
            dbc.Label("Sensor 1 (e.g., Temperature)"),
            dcc.Input(id='input-sensor1', type='number', value=75.0),
            dbc.Label("Sensor 2 (e.g., Pressure)"),
            dcc.Input(id='input-sensor2', type='number', value=65.0),
            dbc.Label("Sensor 3 (e.g., Vibration)"),
            dcc.Input(id='input-sensor3', type='number', value=15.0),
            dbc.Button("Estimate RUL", id='estimate-button', color="primary"),
            html.Div(id='rul-output')
        ], md=4),
        dbc.Col(dcc.Graph(id='degradation-chart'), md=8)
    ])
], fluid=True)

@app.callback(
    Output('rul-output', 'children'),
    Input('estimate-button', 'n_clicks'),
    State('input-cycle', 'value'),
    State('input-sensor1', 'value'),
    State('input-sensor2', 'value'),
    State('input-sensor3', 'value'),
    prevent_initial_call=True
)
def estimate_rul(n_clicks, cycle, sensor1, sensor2, sensor3):
    # Validate inputs
    if n_clicks is None or any(v is None for v in [cycle, sensor1, sensor2, sensor3]):
        raise PreventUpdate
    if cycle < 1:
        return "Error: Cycle must be at least 1."
    input_data = np.array([[cycle, sensor1, sensor2, sensor3]])
    predicted_rul = max(0, model.predict(input_data)[0])  # Ensure non-negative RUL
    return f"Estimated Remaining Useful Life (RUL): {predicted_rul:.2f} cycles"

@app.callback(
    Output('degradation-chart', 'figure'),
    Input('rul-output', 'children')  # Trigger on RUL estimate
)
def update_chart(_):
    # Show RUL vs cycle with trendline
    fig = px.scatter(data, x='cycle', y='rul', title='Degradation Over Time (Training Data)',
                     trendline='ols')  # Ordinary least squares trend
    fig.update_layout(xaxis_title='Cycle', yaxis_title='RUL (cycles)')
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)