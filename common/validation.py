"""
Data validation utilities for SNUGeoSHM.

This module provides comprehensive validation functions for all data types
used in the application, including sensor data, soil data, and uploaded files.
"""

from typing import Optional, Tuple, List, Dict, Any
import pandas as pd
import numpy as np
import xarray as xr
from pathlib import Path
import logging
from datetime import datetime, timedelta

from config import config

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class DataValidator:
    """Base class for data validators."""

    @staticmethod
    def validate_file_size(file_size: int, max_size: int, file_type: str = "file") -> None:
        """
        Validate file size.

        Args:
            file_size: Size of file in bytes
            max_size: Maximum allowed size in bytes
            file_type: Type of file for error message

        Raises:
            ValidationError: If file is too large
        """
        if file_size > max_size:
            max_mb = max_size / (1024 * 1024)
            actual_mb = file_size / (1024 * 1024)
            raise ValidationError(
                f"{file_type} size ({actual_mb:.2f} MB) exceeds maximum allowed size ({max_mb:.2f} MB)"
            )

    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> None:
        """
        Validate file extension.

        Args:
            filename: Name of file
            allowed_extensions: List of allowed extensions (e.g., ['.csv', '.xlsx'])

        Raises:
            ValidationError: If extension not allowed
        """
        ext = Path(filename).suffix.lower()
        if ext not in allowed_extensions:
            raise ValidationError(
                f"File extension '{ext}' not allowed. Allowed: {', '.join(allowed_extensions)}"
            )

    @staticmethod
    def validate_dataframe_columns(
        df: pd.DataFrame,
        required_columns: set,
        optional_columns: Optional[set] = None
    ) -> None:
        """
        Validate DataFrame has required columns.

        Args:
            df: DataFrame to validate
            required_columns: Set of required column names
            optional_columns: Set of optional column names

        Raises:
            ValidationError: If required columns are missing
        """
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise ValidationError(f"Missing required columns: {', '.join(missing)}")

    @staticmethod
    def validate_no_null_values(
        df: pd.DataFrame,
        columns: Optional[List[str]] = None
    ) -> None:
        """
        Validate DataFrame has no null values in specified columns.

        Args:
            df: DataFrame to validate
            columns: List of columns to check (None = all columns)

        Raises:
            ValidationError: If null values found
        """
        check_cols = columns if columns else df.columns
        null_cols = [col for col in check_cols if df[col].isnull().any()]

        if null_cols:
            null_counts = {col: df[col].isnull().sum() for col in null_cols}
            error_msg = "Null values found in columns: " + ", ".join(
                f"{col} ({count} nulls)" for col, count in null_counts.items()
            )
            raise ValidationError(error_msg)

    @staticmethod
    def validate_numeric_range(
        df: pd.DataFrame,
        column: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> None:
        """
        Validate numeric column values are within range.

        Args:
            df: DataFrame to validate
            column: Column name
            min_value: Minimum allowed value
            max_value: Maximum allowed value

        Raises:
            ValidationError: If values outside range
        """
        if column not in df.columns:
            raise ValidationError(f"Column '{column}' not found in DataFrame")

        if not pd.api.types.is_numeric_dtype(df[column]):
            raise ValidationError(f"Column '{column}' is not numeric")

        if min_value is not None:
            below_min = (df[column] < min_value).sum()
            if below_min > 0:
                raise ValidationError(
                    f"{below_min} values in '{column}' are below minimum ({min_value})"
                )

        if max_value is not None:
            above_max = (df[column] > max_value).sum()
            if above_max > 0:
                raise ValidationError(
                    f"{above_max} values in '{column}' are above maximum ({max_value})"
                )


class SoilDataValidator(DataValidator):
    """Validator for soil data."""

    REQUIRED_COLUMNS = {'x', 'y', 'z', 'formation', 'qc', 'fs'}
    NUMERIC_COLUMNS = {'x', 'y', 'z', 'qc', 'fs'}

    @classmethod
    def validate(cls, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate soil data DataFrame.

        Args:
            df: DataFrame with soil data

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        try:
            # Check required columns
            cls.validate_dataframe_columns(df, cls.REQUIRED_COLUMNS)
        except ValidationError as e:
            errors.append(str(e))
            return False, errors

        # Validate numeric columns
        for col in cls.NUMERIC_COLUMNS:
            if col not in df.columns:
                continue

            if not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Column '{col}' must be numeric")

        # Validate coordinate bounds
        if config.data.ENABLE_DATA_VALIDATION:
            try:
                for coord in ['x', 'y']:
                    cls.validate_numeric_range(
                        df, coord,
                        -config.data.MAX_COORDINATE_BOUND,
                        config.data.MAX_COORDINATE_BOUND
                    )
            except ValidationError as e:
                errors.append(str(e))

            # Validate z is negative (depth below surface)
            if 'z' in df.columns:
                if (df['z'] > 0).any():
                    errors.append("Depth values (z) should be negative (below surface)")

            # Validate qc and fs are positive
            try:
                cls.validate_numeric_range(
                    df, 'qc',
                    config.data.MIN_QC_VALUE,
                    config.data.MAX_QC_VALUE
                )
            except ValidationError as e:
                errors.append(str(e))

            try:
                cls.validate_numeric_range(df, 'fs', 0, None)
            except ValidationError as e:
                errors.append(str(e))

        # Check for outliers using IQR method
        outlier_info = cls._detect_outliers(df)
        if outlier_info:
            logger.warning(f"Potential outliers detected: {outlier_info}")

        return len(errors) == 0, errors

    @staticmethod
    def _detect_outliers(df: pd.DataFrame) -> Dict[str, int]:
        """
        Detect outliers using IQR method.

        Args:
            df: DataFrame to check

        Returns:
            Dictionary of column names and outlier counts
        """
        outliers = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR

            outlier_count = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
            if outlier_count > 0:
                outliers[col] = outlier_count

        return outliers


class SensorDataValidator(DataValidator):
    """Validator for sensor data."""

    REQUIRED_DIMS = {'time', 'channel'}
    REQUIRED_VARS = {'value'}

    @classmethod
    def validate(cls, ds: xr.Dataset) -> Tuple[bool, List[str]]:
        """
        Validate sensor data Dataset.

        Args:
            ds: xarray Dataset with sensor data

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Check required dimensions
        if not cls.REQUIRED_DIMS.issubset(ds.dims):
            missing = cls.REQUIRED_DIMS - set(ds.dims)
            errors.append(f"Missing required dimensions: {', '.join(missing)}")

        # Check required variables
        if not cls.REQUIRED_VARS.issubset(ds.variables):
            missing = cls.REQUIRED_VARS - set(ds.variables)
            errors.append(f"Missing required variables: {', '.join(missing)}")

        if errors:
            return False, errors

        # Validate time dimension
        if 'time' in ds.dims:
            time_errors = cls._validate_time_dimension(ds['time'])
            errors.extend(time_errors)

        # Validate data values
        if 'value' in ds.variables:
            value_errors = cls._validate_values(ds['value'])
            errors.extend(value_errors)

        return len(errors) == 0, errors

    @staticmethod
    def _validate_time_dimension(time_coord: xr.DataArray) -> List[str]:
        """Validate time dimension."""
        errors = []

        # Check monotonic increase
        if not time_coord.to_index().is_monotonic_increasing:
            errors.append("Time coordinate must be monotonically increasing")

        # Check for duplicates
        if time_coord.to_index().has_duplicates:
            errors.append("Time coordinate contains duplicate values")

        # Check time range is reasonable (not in far future/past)
        try:
            time_values = pd.to_datetime(time_coord.values)
            now = pd.Timestamp.now()
            future_limit = now + timedelta(days=365)
            past_limit = now - timedelta(days=365 * 10)

            if (time_values > future_limit).any():
                errors.append("Some timestamps are too far in the future")

            if (time_values < past_limit).any():
                errors.append("Some timestamps are too far in the past")

        except Exception as e:
            errors.append(f"Error validating time values: {str(e)}")

        return errors

    @staticmethod
    def _validate_values(value_var: xr.DataArray) -> List[str]:
        """Validate sensor values."""
        errors = []

        # Check for NaN/Inf values
        if np.isnan(value_var.values).any():
            nan_count = np.isnan(value_var.values).sum()
            errors.append(f"Dataset contains {nan_count} NaN values")

        if np.isinf(value_var.values).any():
            inf_count = np.isinf(value_var.values).sum()
            errors.append(f"Dataset contains {inf_count} infinite values")

        # Check value range is reasonable
        if len(value_var.values) > 0:
            min_val = float(np.nanmin(value_var.values))
            max_val = float(np.nanmax(value_var.values))

            # Very basic sanity check - adjust based on your sensor specs
            if abs(min_val) > 1e6 or abs(max_val) > 1e6:
                logger.warning(
                    f"Sensor values have very large magnitude: min={min_val}, max={max_val}"
                )

        return errors


class UploadedFileValidator(DataValidator):
    """Validator for uploaded files."""

    ALLOWED_EXTENSIONS = {
        'csv': ['.csv'],
        'excel': ['.xlsx', '.xls'],
        'netcdf': ['.nc', '.nc4', '.netcdf'],
        'vtk': ['.vtk'],
        'geojson': ['.geojson', '.json']
    }

    @classmethod
    def validate_upload(
        cls,
        contents: str,
        filename: str,
        file_type: str = 'csv'
    ) -> Tuple[bool, List[str]]:
        """
        Validate uploaded file.

        Args:
            contents: Base64 encoded file contents
            filename: Original filename
            file_type: Expected file type

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        # Validate extension
        try:
            allowed = cls.ALLOWED_EXTENSIONS.get(file_type, ['.csv'])
            cls.validate_file_extension(filename, allowed)
        except ValidationError as e:
            errors.append(str(e))

        # Estimate file size from base64 content
        if contents:
            # Base64 adds ~33% overhead
            estimated_size = len(contents) * 3 / 4
            max_size = config.security.MAX_UPLOAD_SIZE_MB * 1024 * 1024

            try:
                cls.validate_file_size(int(estimated_size), max_size, file_type)
            except ValidationError as e:
                errors.append(str(e))

        return len(errors) == 0, errors


def validate_soil_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and clean soil data DataFrame.

    Args:
        df: DataFrame with soil data

    Returns:
        Validated DataFrame

    Raises:
        ValidationError: If validation fails
    """
    is_valid, errors = SoilDataValidator.validate(df)

    if not is_valid:
        error_msg = "Soil data validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
        logger.error(error_msg)
        raise ValidationError(error_msg)

    logger.info(f"Soil data validated successfully ({len(df)} records)")
    return df


def validate_sensor_data(ds: xr.Dataset) -> xr.Dataset:
    """
    Validate and clean sensor data Dataset.

    Args:
        ds: xarray Dataset with sensor data

    Returns:
        Validated Dataset

    Raises:
        ValidationError: If validation fails
    """
    is_valid, errors = SensorDataValidator.validate(ds)

    if not is_valid:
        error_msg = "Sensor data validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
        logger.error(error_msg)
        raise ValidationError(error_msg)

    logger.info(f"Sensor data validated successfully")
    return ds


def validate_uploaded_file(
    contents: str,
    filename: str,
    file_type: str = 'csv'
) -> None:
    """
    Validate uploaded file before processing.

    Args:
        contents: Base64 encoded file contents
        filename: Original filename
        file_type: Expected file type

    Raises:
        ValidationError: If validation fails
    """
    is_valid, errors = UploadedFileValidator.validate_upload(contents, filename, file_type)

    if not is_valid:
        error_msg = "File upload validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
        logger.error(error_msg)
        raise ValidationError(error_msg)

    logger.info(f"File '{filename}' validated successfully")
