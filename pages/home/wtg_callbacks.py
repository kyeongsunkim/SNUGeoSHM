"""
Wind Turbine Generator (WTG) Viewer Callbacks.

This module contains all callbacks for the WTG viewer component on the home page.
"""

from dash import callback, Input, Output
import plotly.graph_objects as go
import plotly.express as px

from pages.home.wtg_data import WTG_DATA, get_wtg_time_series


@callback(
    [Output('wtg-map-container', 'style'),
     Output('wtg-charts-container', 'style')],
    Input('wtg-view-mode', 'value')
)
def toggle_wtg_view(view_mode):
    """
    Toggle visibility of WTG map and charts based on view mode.

    Args:
        view_mode: Selected view mode ('map', 'charts', or 'combined')

    Returns:
        Tuple of style dicts for map and charts containers
    """
    if view_mode == 'map':
        return {'display': 'block'}, {'display': 'none'}
    elif view_mode == 'charts':
        return {'display': 'none'}, {'display': 'block'}
    else:  # combined
        return {'display': 'block'}, {'display': 'block'}


@callback(
    Output('wtg-geojson', 'data'),
    Input('wtg-map', 'bounds')
)
def update_wtg_geojson(bounds):
    """
    Generate GeoJSON features for wind turbines.

    Args:
        bounds: Map bounds (used to trigger update)

    Returns:
        GeoJSON FeatureCollection with turbine markers
    """
    features = []
    for _, row in WTG_DATA.iterrows():
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [row['lon'], row['lat']]
            },
            'properties': {
                'id': int(row['id']),
                'name': row['name'],
                'status': row['status'],
                'power_output': float(row['power_output']),
                'wind_speed': float(row['wind_speed']),
                'efficiency': float(row['efficiency']),
                'popup': f"<b>{row['name']}</b><br>"
                         f"Status: {row['status']}<br>"
                         f"Power: {row['power_output']:.1f} kW<br>"
                         f"Wind: {row['wind_speed']:.1f} m/s<br>"
                         f"Efficiency: {row['efficiency']:.1f}%"
            }
        })
    return {'type': 'FeatureCollection', 'features': features}


@callback(
    Output('wtg-power-chart', 'figure'),
    Input('wtg-geojson', 'click_feature')
)
def update_wtg_power_chart(feature):
    """
    Update power output chart.

    Args:
        feature: Clicked turbine feature (None if no selection)

    Returns:
        Plotly figure with power output data
    """
    if feature is None:
        # Show all turbines
        fig = px.bar(
            WTG_DATA,
            x='name',
            y='power_output',
            color='status',
            title='Power Output by Turbine',
            labels={'power_output': 'Power (kW)', 'name': 'Turbine'},
            color_discrete_map={
                'Operational': '#28a745',
                'Maintenance': '#ffc107',
                'Idle': '#6c757d'
            }
        )
    else:
        # Show selected turbine with time series
        tid = feature['properties']['id']
        ts_data = get_wtg_time_series(tid, hours=24)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ts_data['timestamp'],
            y=ts_data['power_output'],
            mode='lines+markers',
            name='Power Output',
            line=dict(color='#28a745', width=2)
        ))
        fig.update_layout(
            title=f"Power Output - {feature['properties']['name']} (24h)",
            xaxis_title='Time',
            yaxis_title='Power (kW)',
            hovermode='x unified'
        )

    fig.update_layout(
        template='plotly_white',
        height=300
    )
    return fig


@callback(
    Output('wtg-wind-chart', 'figure'),
    Input('wtg-geojson', 'click_feature')
)
def update_wtg_wind_chart(feature):
    """
    Update wind speed chart.

    Args:
        feature: Clicked turbine feature (None if no selection)

    Returns:
        Plotly figure with wind speed data
    """
    if feature is None:
        # Show all turbines - scatter plot
        fig = px.scatter(
            WTG_DATA,
            x='wind_speed',
            y='power_output',
            color='status',
            size='efficiency',
            hover_data=['name', 'rotor_speed'],
            title='Wind Speed vs Power Output',
            labels={'wind_speed': 'Wind Speed (m/s)', 'power_output': 'Power (kW)'},
            color_discrete_map={
                'Operational': '#28a745',
                'Maintenance': '#ffc107',
                'Idle': '#6c757d'
            }
        )
    else:
        # Show selected turbine with time series
        tid = feature['properties']['id']
        ts_data = get_wtg_time_series(tid, hours=24)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ts_data['timestamp'],
            y=ts_data['wind_speed'],
            mode='lines+markers',
            name='Wind Speed',
            line=dict(color='#007bff', width=2)
        ))
        fig.update_layout(
            title=f"Wind Speed - {feature['properties']['name']} (24h)",
            xaxis_title='Time',
            yaxis_title='Wind Speed (m/s)',
            hovermode='x unified'
        )

    fig.update_layout(
        template='plotly_white',
        height=300
    )
    return fig


@callback(
    Output('wtg-status-chart', 'figure'),
    Input('wtg-geojson', 'click_feature')
)
def update_wtg_status_chart(feature):
    """
    Update status distribution or vibration chart.

    Args:
        feature: Clicked turbine feature (None if no selection)

    Returns:
        Plotly figure with status or vibration data
    """
    if feature is None:
        # Show status distribution
        status_counts = WTG_DATA['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']

        fig = px.pie(
            status_counts,
            values='Count',
            names='Status',
            title='Turbine Status Distribution',
            color='Status',
            color_discrete_map={
                'Operational': '#28a745',
                'Maintenance': '#ffc107',
                'Idle': '#6c757d'
            }
        )
    else:
        # Show selected turbine vibration over time
        tid = feature['properties']['id']
        ts_data = get_wtg_time_series(tid, hours=24)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ts_data['timestamp'],
            y=ts_data['vibration'],
            mode='lines',
            name='Vibration',
            fill='tozeroy',
            line=dict(color='#dc3545', width=2)
        ))
        fig.add_hline(
            y=2.0,
            line_dash="dash",
            line_color="red",
            annotation_text="Warning Level"
        )
        fig.update_layout(
            title=f"Vibration - {feature['properties']['name']} (24h)",
            xaxis_title='Time',
            yaxis_title='Vibration (mm/s)',
            hovermode='x unified'
        )

    fig.update_layout(
        template='plotly_white',
        height=300
    )
    return fig


@callback(
    Output('wtg-efficiency-chart', 'figure'),
    Input('wtg-geojson', 'click_feature')
)
def update_wtg_efficiency_chart(feature):
    """
    Update efficiency chart.

    Args:
        feature: Clicked turbine feature (None if no selection)

    Returns:
        Plotly figure with efficiency data
    """
    if feature is None:
        # Show efficiency comparison
        fig = px.bar(
            WTG_DATA.sort_values('efficiency', ascending=False),
            x='name',
            y='efficiency',
            color='efficiency',
            title='Turbine Efficiency Comparison',
            labels={'efficiency': 'Efficiency (%)', 'name': 'Turbine'},
            color_continuous_scale='RdYlGn'
        )
    else:
        # Show selected turbine metrics
        tid = feature['properties']['id']
        turbine = WTG_DATA[WTG_DATA['id'] == tid].iloc[0]

        metrics = {
            'Efficiency': turbine['efficiency'],
            'Availability': turbine['availability'],
            'Capacity Factor': turbine['capacity_factor']
        }

        fig = go.Figure(data=[
            go.Bar(
                x=list(metrics.keys()),
                y=list(metrics.values()),
                marker_color=['#28a745', '#007bff', '#ffc107']
            )
        ])
        fig.update_layout(
            title=f"Performance Metrics - {feature['properties']['name']}",
            yaxis_title='Percentage (%)',
            showlegend=False
        )

    fig.update_layout(
        template='plotly_white',
        height=300
    )
    return fig
