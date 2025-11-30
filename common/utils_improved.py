"""
Improved utility functions with validation, error handling, and type hints.

This module replaces common/utils.py with enhanced functionality including:
- Type hints for all functions
- Comprehensive validation
- Error handling with retry logic
- Better logging
- Performance optimizations
"""

import base64
from io import BytesIO
from typing import Optional, Tuple, List
import functools
import pandas as pd
import numpy as np
import xarray as xr
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
from pathlib import Path

from config import config
from common.logging_config import get_logger
from common.validation import validate_soil_data, validate_sensor_data, validate_uploaded_file, ValidationError
from common.error_handling import retry, ErrorContext, format_error_message

logger = get_logger(__name__)


@retry(max_attempts=3, delay=1.0, exceptions=(FileNotFoundError, IOError))
@functools.lru_cache(maxsize=128)
def load_sensor_data_sync() -> xr.Dataset:
    """
    Load and validate sensor data from NetCDF file.

    Returns:
        xarray Dataset with validated sensor data

    Raises:
        FileNotFoundError: If sensor data file not found
        ValidationError: If data validation fails
        IOError: If file cannot be read
    """
    file_path = config.data.DATA_DIR / 'sensor_data.nc'

    with ErrorContext("loading sensor data"):
        if not file_path.exists():
            raise FileNotFoundError(
                f"Sensor data not found at {file_path}. "
                "Please place 'sensor_data.nc' in the data directory."
            )

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > config.data.MAX_NETCDF_SIZE:
            logger.warning(
                f"Sensor data file is large ({file_size / 1024 / 1024:.2f} MB), "
                "loading may take time"
            )

        ds = xr.open_dataset(file_path)

        # Validate data
        if config.data.ENABLE_DATA_VALIDATION:
            ds = validate_sensor_data(ds)

        logger.info(
            f"Sensor data loaded successfully: "
            f"{len(ds.time)} timestamps, {len(ds.channel)} channels"
        )

        return ds


@retry(max_attempts=3, delay=1.0, exceptions=(FileNotFoundError, IOError))
@functools.lru_cache(maxsize=128)
def load_soil_data_sync() -> pd.DataFrame:
    """
    Load and validate soil data from CSV file.

    Returns:
        DataFrame with validated soil data

    Raises:
        FileNotFoundError: If soil data file not found
        ValidationError: If data validation fails
        IOError: If file cannot be read
    """
    file_path = config.data.DATA_DIR / 'soil_data.csv'

    with ErrorContext("loading soil data"):
        if not file_path.exists():
            raise FileNotFoundError(
                f"Soil data not found at {file_path}. "
                "Please place 'soil_data.csv' in the data directory."
            )

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > config.data.MAX_CSV_SIZE:
            logger.warning(
                f"Soil data file is large ({file_size / 1024 / 1024:.2f} MB), "
                "loading may take time"
            )

        df = pd.read_csv(file_path)

        # Validate data
        if config.data.ENABLE_DATA_VALIDATION:
            df = validate_soil_data(df)

        logger.info(f"Soil data loaded successfully: {len(df)} records")

        return df


def init_data() -> None:
    """
    Initialize data directories and create sample data if needed.

    Creates:
    - Data directory with sample sensor and soil data
    - Assets directory for generated files
    - Outputs directory for exports
    - Temp directory for temporary files
    """
    with ErrorContext("initializing data directories"):
        # Directories are created by config initialization
        data_dir = config.data.DATA_DIR
        assets_dir = config.data.ASSETS_DIR

        # Create sample sensor data if doesn't exist
        sensor_file = data_dir / 'sensor_data.nc'
        if not sensor_file.exists():
            logger.info("Creating sample sensor data...")
            time = pd.date_range('2023-01-01', periods=1000, freq='S')
            channel = [1, 2]
            ds = xr.Dataset(
                {'value': (['time', 'channel'], np.random.randn(1000, 2) * 10)},
                coords={'time': time, 'channel': channel}
            )
            ds.to_netcdf(sensor_file)
            logger.info(f"Sample sensor data created at {sensor_file}")

        # Create sample soil data if doesn't exist
        soil_file = data_dir / 'soil_data.csv'
        if not soil_file.exists():
            logger.info("Creating sample soil data...")
            soil_df = pd.DataFrame({
                'x': np.random.uniform(0, 10, 100),
                'y': np.random.uniform(0, 10, 100),
                'z': np.random.uniform(-50, 0, 100),
                'formation': np.random.choice(['Sand', 'Clay'], 100),
                'qc': np.random.uniform(1, 10, 100),
                'fs': np.random.uniform(0.1, 1, 100)
            })
            soil_df.to_csv(soil_file, index=False)
            logger.info(f"Sample soil data created at {soil_file}")

        logger.info("Data initialization complete")


def simulate_optumgx(
    material_strength: float,
    strain: Optional[np.ndarray] = None
) -> pd.DataFrame:
    """
    Simulate OptumGX stress-strain response.

    Args:
        material_strength: Material strength parameter (MPa)
        strain: Optional strain values array (defaults to linspace(0, 0.1, 100))

    Returns:
        DataFrame with 'strain' and 'stress' columns

    Raises:
        ValueError: If material_strength is invalid
    """
    if material_strength <= 0:
        raise ValueError(f"Material strength must be positive, got {material_strength}")

    if strain is None:
        strain = np.linspace(0, 0.1, 100)

    # Simple parabolic stress-strain model
    epsilon_f = 0.05  # Failure strain
    stress = material_strength * strain * (1 - strain / epsilon_f)

    # Ensure stress doesn't go negative
    stress = np.maximum(stress, 0)

    logger.debug(
        f"OptumGX simulation: material_strength={material_strength}, "
        f"max_stress={stress.max():.2f}"
    )

    return pd.DataFrame({'strain': strain, 'stress': stress})


def process_uploaded_file(
    contents: Optional[str],
    filename: str
) -> Optional[pd.DataFrame]:
    """
    Process uploaded CSV or Excel file with validation.

    Args:
        contents: Base64 encoded file contents
        filename: Original filename

    Returns:
        DataFrame with file data, or None if contents is None

    Raises:
        ValidationError: If file validation fails
        ValueError: If file format is unsupported
    """
    if contents is None:
        return None

    with ErrorContext("processing uploaded file"):
        # Determine file type
        if filename.endswith('.csv'):
            file_type = 'csv'
        elif filename.endswith(('.xlsx', '.xls')):
            file_type = 'excel'
        else:
            raise ValueError(f"Unsupported file type: {filename}")

        # Validate upload
        validate_uploaded_file(contents, filename, file_type)

        # Decode and parse
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        if file_type == 'csv':
            # Try different encodings
            try:
                df = pd.read_csv(BytesIO(decoded))
            except UnicodeDecodeError:
                df = pd.read_csv(BytesIO(decoded), encoding='latin1')
        else:
            df = pd.read_excel(BytesIO(decoded))

        logger.info(
            f"File '{filename}' processed successfully: "
            f"{len(df)} rows, {len(df.columns)} columns"
        )

        return df


def process_vtk_file(
    contents: Optional[str],
    filename: str
) -> Optional[bytes]:
    """
    Process uploaded VTK file.

    Args:
        contents: Base64 encoded file contents
        filename: Original filename

    Returns:
        Decoded VTK file bytes, or None if contents is None

    Raises:
        ValueError: If file is not VTK format
    """
    if contents is None:
        return None

    if not filename.endswith('.vtk'):
        raise ValueError(f"File must be VTK format, got: {filename}")

    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    logger.info(f"VTK file '{filename}' processed: {len(decoded)} bytes")

    return decoded


def simulate_pyoma2(data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simulate PyOMA2 frequency analysis using FFT.

    Args:
        data: Time series data array

    Returns:
        Tuple of (frequencies, amplitudes)

    Raises:
        ValueError: If data is empty or invalid
    """
    if len(data) == 0:
        raise ValueError("Input data cannot be empty")

    # Compute FFT
    freqs = np.fft.fftfreq(len(data), d=1/100)[:len(data)//2]
    amps = np.abs(np.fft.fft(data))[:len(data)//2]

    logger.debug(
        f"PyOMA2 simulation: {len(data)} samples, "
        f"dominant freq={freqs[amps.argmax()]:.2f} Hz"
    )

    return freqs, amps


def matplotlib_to_base64(fig: plt.Figure) -> str:
    """
    Convert matplotlib figure to base64 encoded image.

    Args:
        fig: Matplotlib figure instance

    Returns:
        Base64 encoded image string with data URI

    Raises:
        ValueError: If figure is invalid
    """
    if fig is None:
        raise ValueError("Figure cannot be None")

    buf = BytesIO()
    try:
        fig.savefig(buf, format="png", bbox_inches='tight', dpi=150)
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"
    finally:
        buf.close()
        plt.close(fig)


def create_bullet_chart(
    value: float,
    title: str = "Average Sensor Value",
    ranges: List[float] = None,
    colors: List[str] = None
) -> go.Figure:
    """
    Create a bullet chart for KPI visualization.

    Args:
        value: Current value to display
        title: Chart title
        ranges: List of range boundaries [min, target1, target2, max]
        colors: List of colors for each range

    Returns:
        Plotly Figure object
    """
    if ranges is None:
        ranges = [0, 60, 80, 100]

    if colors is None:
        colors = ["lightgray", "gray"]

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title},
            delta={'reference': ranges[1]},
            gauge={
                'shape': "bullet",
                'axis': {'range': [ranges[0], ranges[-1]]},
                'threshold': {
                    'line': {'color': "red", 'width': 2},
                    'thickness': 0.75,
                    'value': ranges[-2]
                },
                'steps': [
                    {'range': [ranges[i], ranges[i+1]], 'color': colors[i % len(colors)]}
                    for i in range(len(ranges)-1)
                ]
            }
        )
    )
    fig.update_layout(height=250)

    return fig


def create_gauge_chart(
    value: float,
    title: str = "Max Sensor Value",
    min_val: float = 0,
    max_val: float = 100,
    colors: List[str] = None,
    ranges: List[float] = None
) -> go.Figure:
    """
    Create a gauge chart for monitoring metrics.

    Args:
        value: Current value to display
        title: Chart title
        min_val: Minimum value on gauge
        max_val: Maximum value on gauge
        colors: List of colors for gauge ranges
        ranges: List of range boundaries

    Returns:
        Plotly Figure object
    """
    if colors is None:
        colors = ["green", "yellow", "red"]

    if ranges is None:
        ranges = [0, 60, 80, 100]

    steps = [
        {'range': [ranges[i], ranges[i+1]], 'color': colors[i]}
        for i in range(len(ranges)-1)
    ]

    fig = go.Figure(
        go.Indicator(
            domain={'x': [0, 1], 'y': [0, 1]},
            value=value,
            mode="gauge+number+delta",
            title={'text': title},
            delta={'reference': (min_val + max_val)/2},
            gauge={
                'axis': {'range': [min_val, max_val]},
                'steps': steps,
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_val * 0.9
                }
            }
        )
    )

    return fig
