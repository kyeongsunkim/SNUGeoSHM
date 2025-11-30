# Wind Turbine Generator (WTG) Viewer

## Overview

The WTG Viewer is an interactive component integrated into the SNUGeoSHM home page that provides real-time monitoring and analysis of offshore wind turbines.

## Features

### 1. Interactive Map View
- **GeoJSON-based Markers**: Each turbine is represented as a point on the map
- **Color-coded Status**: Turbines are colored by operational status
  - 🟢 Green: Operational
  - 🟡 Yellow: Maintenance
  - ⚪ Gray: Idle
- **Click Interaction**: Click any turbine marker to view detailed time-series data
- **Popup Information**: Hover over markers to see quick stats

### 2. View Modes
- **Map View**: Shows only the turbine map
- **Charts View**: Shows only the performance charts
- **Combined View**: Shows both map and charts (default)

### 3. Performance Charts

#### Power Output Chart
- **Overview Mode**: Bar chart showing power output for all turbines
- **Detail Mode**: 24-hour time series for selected turbine
- Color-coded by operational status

#### Wind Speed Chart
- **Overview Mode**: Scatter plot showing wind speed vs power output relationship
- **Detail Mode**: 24-hour wind speed time series
- Bubble size represents efficiency

#### Status Distribution Chart
- **Overview Mode**: Pie chart showing turbine status distribution
- **Detail Mode**: Vibration monitoring with warning levels
- Alert threshold at 2.0 mm/s

#### Efficiency Chart
- **Overview Mode**: Bar chart comparing all turbine efficiencies
- **Detail Mode**: Performance metrics (Efficiency, Availability, Capacity Factor)

## Data Structure

### Turbine Data Fields

```python
{
    'id': int,                    # Unique turbine ID
    'name': str,                  # Turbine name (e.g., 'WTG-01')
    'lat': float,                 # Latitude
    'lon': float,                 # Longitude
    'power_output': float,        # Current power (kW)
    'wind_speed': float,          # Wind speed (m/s)
    'rotor_speed': float,         # Rotor RPM
    'nacelle_direction': float,   # Direction (degrees)
    'blade_pitch': float,         # Pitch angle (degrees)
    'temperature': float,         # Temperature (°C)
    'vibration': float,           # Vibration (mm/s)
    'status': str,                # 'Operational', 'Maintenance', 'Idle'
    'availability': float,        # Availability (%)
    'capacity_factor': float,     # Capacity factor (%)
    'efficiency': float,          # Calculated efficiency (%)
    'last_maintenance': str,      # Last maintenance date
}
```

### Time Series Data

Generated dynamically for 24-hour historical data:
- `timestamp`: Hourly timestamps
- `turbine_id`: Turbine identifier
- `wind_speed`: Historical wind speed
- `power_output`: Historical power output
- `rotor_speed`: Historical rotor speed
- `vibration`: Historical vibration levels

## Components

### Files

1. **`wtg_data.py`** - Data generation and utilities
   - `generate_wtg_sample_data()`: Generate sample turbine data
   - `get_wtg_time_series()`: Generate time series data
   - `get_status_color()`: Get color for status
   - `get_marker_color()`: Get marker color for map

2. **`wtg_callbacks.py`** - Interactive callbacks
   - `toggle_wtg_view()`: Toggle between view modes
   - `update_wtg_geojson()`: Update map markers
   - `update_wtg_power_chart()`: Update power chart
   - `update_wtg_wind_chart()`: Update wind chart
   - `update_wtg_status_chart()`: Update status chart
   - `update_wtg_efficiency_chart()`: Update efficiency chart

3. **`layout.py`** - UI layout
   - WTG viewer section integrated into home page
   - View mode selector
   - Map container
   - Chart containers

## Usage

### Basic Usage

1. **Open the application** and navigate to the home page
2. **Scroll down** to the "Wind Turbine Generator Monitor" section
3. **Select view mode** using the radio buttons
4. **Interact with the map**:
   - Click turbine markers to see detailed charts
   - Hover over markers for quick info
5. **Analyze charts**:
   - Overview mode shows all turbines
   - Click a turbine to see 24-hour trends

### Customization

#### Change Number of Turbines

Edit `wtg_data.py`:
```python
# Generate 20 turbines instead of 10
WTG_DATA = generate_wtg_sample_data(20)
```

#### Change Map Center Location

Edit `layout.py`:
```python
dlf.Map(
    id='wtg-map',
    center=[YOUR_LAT, YOUR_LON],  # Change coordinates
    zoom=12,
    # ...
)
```

#### Customize Time Series Length

Edit callback calls in `wtg_callbacks.py`:
```python
# Show 48 hours instead of 24
ts_data = get_wtg_time_series(tid, hours=48)
```

## Integration with Real Data

To integrate with real turbine data:

### 1. Replace Sample Data Generator

In `wtg_data.py`, replace `generate_wtg_sample_data()`:

```python
def load_real_wtg_data():
    """Load real turbine data from database or API."""
    # Connect to your data source
    import requests
    response = requests.get('your-api-endpoint/turbines')
    data = response.json()

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Ensure required columns exist
    required_cols = ['id', 'name', 'lat', 'lon', 'power_output',
                     'wind_speed', 'status']
    assert all(col in df.columns for col in required_cols)

    return df

# Use real data
WTG_DATA = load_real_wtg_data()
```

### 2. Implement Real-Time Updates

Add a callback to refresh data periodically:

```python
@callback(
    Output('wtg-data-store', 'data'),
    Input('interval-component', 'n_intervals')
)
def update_wtg_data(n):
    """Fetch latest turbine data."""
    return load_real_wtg_data().to_dict('records')
```

### 3. Connect to Time Series Database

For historical data, connect to a time-series database:

```python
def get_wtg_time_series_real(turbine_id, hours=24):
    """Get real time series data from database."""
    from datetime import datetime, timedelta
    import psycopg2

    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)

    conn = psycopg2.connect(config.database.connection_string)
    query = """
        SELECT timestamp, wind_speed, power_output, vibration
        FROM turbine_timeseries
        WHERE turbine_id = %s
        AND timestamp BETWEEN %s AND %s
        ORDER BY timestamp
    """
    df = pd.read_sql(query, conn, params=(turbine_id, start_time, end_time))
    conn.close()

    return df
```

## Performance Optimization

### For Large Datasets (>100 turbines)

1. **Implement Marker Clustering**:
```python
from dash_leaflet import MarkerClusterGroup

# In layout.py
MarkerClusterGroup(id='wtg-cluster', children=markers)
```

2. **Use Server-Side Filtering**:
```python
@callback(
    Output('wtg-geojson', 'data'),
    Input('wtg-map', 'bounds'),
    Input('wtg-map', 'zoom')
)
def update_wtg_geojson(bounds, zoom):
    """Only show turbines in current viewport."""
    if bounds:
        # Filter turbines by map bounds
        in_view = WTG_DATA[
            (WTG_DATA['lat'] >= bounds[0][0]) &
            (WTG_DATA['lat'] <= bounds[1][0]) &
            (WTG_DATA['lon'] >= bounds[0][1]) &
            (WTG_DATA['lon'] <= bounds[1][1])
        ]
        return create_geojson(in_view)
    return create_geojson(WTG_DATA)
```

3. **Cache Time Series Data**:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_wtg_time_series_cached(turbine_id, hours):
    """Cached version of time series fetch."""
    return get_wtg_time_series(turbine_id, hours)
```

## Troubleshooting

### Issue: Map not displaying

**Solution**: Ensure dash-leaflet is installed:
```bash
pip install dash-leaflet
```

### Issue: GeoJSON markers not showing

**Solution**: Check that coordinates are in [lon, lat] order:
```python
'coordinates': [row['lon'], row['lat']]  # Correct
'coordinates': [row['lat'], row['lon']]  # Wrong!
```

### Issue: Charts not updating on click

**Solution**: Verify callback inputs/outputs match component IDs:
```python
@callback(
    Output('wtg-power-chart', 'figure'),  # Must match graph ID
    Input('wtg-geojson', 'click_feature')  # Must match GeoJSON ID
)
```

### Issue: Time series data looks unrealistic

**Solution**: Adjust generation parameters in `get_wtg_time_series()`:
```python
# More realistic wind variation
wind_variation = np.random.normal(0, 1.0)  # Increase std dev

# Add more daily pattern variation
hour_factor = 1 + 0.5 * np.sin((ts.hour - 6) * np.pi / 12)
```

## Future Enhancements

### Planned Features
- [ ] Real-time WebSocket updates
- [ ] Alert notifications for abnormal conditions
- [ ] Historical data export (CSV, Excel)
- [ ] Predictive maintenance indicators
- [ ] Wind rose diagrams
- [ ] Power curve analysis
- [ ] Comparison with forecast data
- [ ] Mobile-responsive view
- [ ] 3D turbine visualization
- [ ] SCADA system integration

### API Endpoints (Future)
```python
GET /api/turbines - List all turbines
GET /api/turbines/{id} - Get turbine details
GET /api/turbines/{id}/timeseries - Get historical data
POST /api/turbines/{id}/maintenance - Schedule maintenance
GET /api/alerts - Get active alerts
```

## References

- [Dash Leaflet Documentation](https://dash-leaflet.herokuapp.com/)
- [Plotly Express Documentation](https://plotly.com/python/plotly-express/)
- [GeoJSON Specification](https://geojson.org/)
- [Wind Turbine Monitoring Best Practices](https://www.energy.gov/eere/wind/wind-turbine-condition-monitoring)

## Support

For issues or questions:
- Check the main [README.md](../../README.md)
- Review [claude.md](../../claude.md) for architecture details
- Contact the development team

---

**Last Updated**: 2024-11-30
**Version**: 1.0.0
