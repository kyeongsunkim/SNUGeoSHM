"""
Wind Turbine Generator (WTG) sample data and utilities.

This module provides sample WTG data and helper functions for the WTG viewer.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_wtg_sample_data(num_turbines=10):
    """
    Generate sample wind turbine data.

    Args:
        num_turbines: Number of turbines to generate

    Returns:
        DataFrame with WTG data
    """
    # Generate turbines in a grid pattern around a central location
    # Using offshore locations near San Francisco as example
    base_lat = 37.7749
    base_lon = -122.4194

    data = []
    for i in range(num_turbines):
        # Create a grid pattern
        row = i // 5
        col = i % 5

        turbine = {
            'id': i + 1,
            'name': f'WTG-{i+1:02d}',
            'lat': base_lat + (row * 0.01),
            'lon': base_lon + (col * 0.01),
            'power_output': np.random.uniform(150, 250),  # kW
            'wind_speed': np.random.uniform(4.5, 7.5),  # m/s
            'rotor_speed': np.random.uniform(10, 15),  # RPM
            'nacelle_direction': np.random.uniform(0, 360),  # degrees
            'blade_pitch': np.random.uniform(0, 20),  # degrees
            'temperature': np.random.uniform(15, 25),  # °C
            'vibration': np.random.uniform(0.5, 2.5),  # mm/s
            'status': np.random.choice(['Operational', 'Maintenance', 'Idle'], p=[0.7, 0.2, 0.1]),
            'availability': np.random.uniform(92, 99),  # %
            'capacity_factor': np.random.uniform(25, 45),  # %
            'last_maintenance': (datetime.now() - timedelta(days=np.random.randint(1, 90))).strftime('%Y-%m-%d'),
        }

        # Calculate efficiency based on wind speed and power output
        theoretical_max = (turbine['wind_speed'] ** 3) * 0.5  # Simplified
        turbine['efficiency'] = min((turbine['power_output'] / theoretical_max) * 100, 100) if theoretical_max > 0 else 0

        data.append(turbine)

    return pd.DataFrame(data)


def get_wtg_time_series(turbine_id, hours=24):
    """
    Generate time series data for a specific turbine.

    Args:
        turbine_id: Turbine ID
        hours: Number of hours of data to generate

    Returns:
        DataFrame with time series data
    """
    timestamps = pd.date_range(end=datetime.now(), periods=hours, freq='H')

    # Generate realistic patterns
    base_wind = 6.0
    base_power = 200.0

    data = []
    for ts in timestamps:
        # Add daily pattern (higher wind during day)
        hour_factor = 1 + 0.3 * np.sin((ts.hour - 6) * np.pi / 12)

        # Add random variation
        wind_variation = np.random.normal(0, 0.5)
        wind_speed = base_wind * hour_factor + wind_variation

        # Power is proportional to wind speed cubed (simplified)
        power_output = min(base_power * (wind_speed / base_wind) ** 3, 250)

        data.append({
            'timestamp': ts,
            'turbine_id': turbine_id,
            'wind_speed': max(0, wind_speed),
            'power_output': max(0, power_output),
            'rotor_speed': max(0, wind_speed * 2),
            'vibration': np.random.uniform(0.5, 2.0),
        })

    return pd.DataFrame(data)


def get_status_color(status):
    """
    Get color code for turbine status.

    Args:
        status: Status string

    Returns:
        Color code
    """
    colors = {
        'Operational': '#28a745',  # Green
        'Maintenance': '#ffc107',  # Yellow
        'Idle': '#6c757d',  # Gray
        'Offline': '#dc3545',  # Red
    }
    return colors.get(status, '#6c757d')


def get_marker_icon(status):
    """
    Get marker icon configuration for turbine status.

    Args:
        status: Status string

    Returns:
        Icon configuration dict
    """
    return {
        'iconUrl': f'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-{get_marker_color(status)}.png',
        'shadowUrl': 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
        'iconSize': [25, 41],
        'iconAnchor': [12, 41],
        'popupAnchor': [1, -34],
        'shadowSize': [41, 41]
    }


def get_marker_color(status):
    """
    Get marker color name for turbine status.

    Args:
        status: Status string

    Returns:
        Color name
    """
    colors = {
        'Operational': 'green',
        'Maintenance': 'yellow',
        'Idle': 'grey',
        'Offline': 'red',
    }
    return colors.get(status, 'grey')


# Generate global WTG data on module load
WTG_DATA = generate_wtg_sample_data(10)
