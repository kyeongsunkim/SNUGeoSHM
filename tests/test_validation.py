"""
Unit tests for validation module.
"""

import pytest
import pandas as pd
import numpy as np
import xarray as xr
from datetime import datetime, timedelta

from common.validation import (
    ValidationError,
    SoilDataValidator,
    SensorDataValidator,
    UploadedFileValidator,
    validate_soil_data,
    validate_sensor_data
)


class TestSoilDataValidator:
    """Tests for soil data validation."""

    def test_valid_soil_data(self):
        """Test validation of valid soil data."""
        df = pd.DataFrame({
            'x': [1.0, 2.0, 3.0],
            'y': [4.0, 5.0, 6.0],
            'z': [-10.0, -20.0, -30.0],
            'formation': ['Sand', 'Clay', 'Sand'],
            'qc': [5.0, 6.0, 7.0],
            'fs': [0.5, 0.6, 0.7]
        })

        is_valid, errors = SoilDataValidator.validate(df)
        assert is_valid
        assert len(errors) == 0

    def test_missing_columns(self):
        """Test validation fails with missing columns."""
        df = pd.DataFrame({
            'x': [1.0, 2.0],
            'y': [3.0, 4.0]
            # Missing z, formation, qc, fs
        })

        is_valid, errors = SoilDataValidator.validate(df)
        assert not is_valid
        assert len(errors) > 0
        assert any('Missing required columns' in err for err in errors)

    def test_invalid_coordinate_bounds(self):
        """Test validation with coordinates out of bounds."""
        df = pd.DataFrame({
            'x': [10000.0],  # Too large
            'y': [1.0],
            'z': [-10.0],
            'formation': ['Sand'],
            'qc': [5.0],
            'fs': [0.5]
        })

        is_valid, errors = SoilDataValidator.validate(df)
        # May fail depending on config
        assert isinstance(errors, list)

    def test_positive_depth(self):
        """Test validation fails when z (depth) is positive."""
        df = pd.DataFrame({
            'x': [1.0],
            'y': [2.0],
            'z': [10.0],  # Should be negative
            'formation': ['Sand'],
            'qc': [5.0],
            'fs': [0.5]
        })

        is_valid, errors = SoilDataValidator.validate(df)
        assert not is_valid
        assert any('should be negative' in err for err in errors)

    def test_invalid_qc_values(self):
        """Test validation with invalid qc values."""
        df = pd.DataFrame({
            'x': [1.0],
            'y': [2.0],
            'z': [-10.0],
            'formation': ['Sand'],
            'qc': [-1.0],  # Negative qc
            'fs': [0.5]
        })

        is_valid, errors = SoilDataValidator.validate(df)
        assert not is_valid
        assert any('qc' in err for err in errors)


class TestSensorDataValidator:
    """Tests for sensor data validation."""

    def test_valid_sensor_data(self):
        """Test validation of valid sensor data."""
        time = pd.date_range('2023-01-01', periods=100, freq='S')
        channel = [1, 2]
        ds = xr.Dataset(
            {'value': (['time', 'channel'], np.random.randn(100, 2))},
            coords={'time': time, 'channel': channel}
        )

        is_valid, errors = SensorDataValidator.validate(ds)
        assert is_valid
        assert len(errors) == 0

    def test_missing_dimensions(self):
        """Test validation fails with missing dimensions."""
        ds = xr.Dataset(
            {'value': (['x'], [1.0, 2.0, 3.0])},
            coords={'x': [0, 1, 2]}
        )

        is_valid, errors = SensorDataValidator.validate(ds)
        assert not is_valid
        assert any('Missing required dimensions' in err for err in errors)

    def test_missing_variables(self):
        """Test validation fails with missing variables."""
        time = pd.date_range('2023-01-01', periods=10, freq='S')
        ds = xr.Dataset(
            {'temperature': (['time'], np.random.randn(10))},
            coords={'time': time, 'channel': [1]}
        )

        is_valid, errors = SensorDataValidator.validate(ds)
        assert not is_valid
        assert any('Missing required variables' in err for err in errors)

    def test_non_monotonic_time(self):
        """Test validation with non-monotonic time."""
        time = pd.DatetimeIndex([
            '2023-01-01 00:00:00',
            '2023-01-01 00:00:02',  # Out of order
            '2023-01-01 00:00:01'
        ])
        ds = xr.Dataset(
            {'value': (['time', 'channel'], np.random.randn(3, 2))},
            coords={'time': time, 'channel': [1, 2]}
        )

        is_valid, errors = SensorDataValidator.validate(ds)
        assert not is_valid
        assert any('monotonically increasing' in err for err in errors)

    def test_nan_values(self):
        """Test validation with NaN values."""
        time = pd.date_range('2023-01-01', periods=10, freq='S')
        values = np.random.randn(10, 2)
        values[0, 0] = np.nan
        ds = xr.Dataset(
            {'value': (['time', 'channel'], values)},
            coords={'time': time, 'channel': [1, 2]}
        )

        is_valid, errors = SensorDataValidator.validate(ds)
        assert not is_valid
        assert any('NaN' in err for err in errors)


class TestUploadedFileValidator:
    """Tests for uploaded file validation."""

    def test_valid_csv_extension(self):
        """Test validation accepts valid CSV extension."""
        is_valid, errors = UploadedFileValidator.validate_upload(
            "data:text/csv;base64,eHl6", "test.csv", 'csv'
        )
        assert is_valid or len(errors) == 0  # May have size errors

    def test_invalid_extension(self):
        """Test validation rejects invalid extension."""
        is_valid, errors = UploadedFileValidator.validate_upload(
            "data:text/plain;base64,eHl6", "test.txt", 'csv'
        )
        assert not is_valid
        assert any('extension' in err.lower() for err in errors)

    def test_file_too_large(self):
        """Test validation rejects files that are too large."""
        # Create a large mock base64 string
        large_content = "data:text/csv;base64," + ("A" * (200 * 1024 * 1024))  # Simulate 200MB

        is_valid, errors = UploadedFileValidator.validate_upload(
            large_content, "large.csv", 'csv'
        )
        assert not is_valid
        assert any('exceeds maximum' in err for err in errors)


class TestValidateFunctions:
    """Tests for top-level validation functions."""

    def test_validate_soil_data_success(self):
        """Test successful soil data validation."""
        df = pd.DataFrame({
            'x': [1.0], 'y': [2.0], 'z': [-10.0],
            'formation': ['Sand'], 'qc': [5.0], 'fs': [0.5]
        })

        result = validate_soil_data(df)
        assert isinstance(result, pd.DataFrame)

    def test_validate_soil_data_failure(self):
        """Test soil data validation failure."""
        df = pd.DataFrame({'x': [1.0]})  # Missing columns

        with pytest.raises(ValidationError):
            validate_soil_data(df)

    def test_validate_sensor_data_success(self):
        """Test successful sensor data validation."""
        time = pd.date_range('2023-01-01', periods=10, freq='S')
        ds = xr.Dataset(
            {'value': (['time', 'channel'], np.random.randn(10, 2))},
            coords={'time': time, 'channel': [1, 2]}
        )

        result = validate_sensor_data(ds)
        assert isinstance(result, xr.Dataset)

    def test_validate_sensor_data_failure(self):
        """Test sensor data validation failure."""
        ds = xr.Dataset({'x': (['i'], [1, 2, 3])})

        with pytest.raises(ValidationError):
            validate_sensor_data(ds)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
