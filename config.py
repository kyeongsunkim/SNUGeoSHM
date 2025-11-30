"""
Configuration management for SNUGeoSHM application.

This module provides centralized configuration using environment variables
with sensible defaults. All settings should be accessed through this module.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class SecurityConfig:
    """Security-related configuration."""
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DASH_USERNAME: str = os.getenv('DASH_USERNAME', 'admin')
    DASH_PASSWORD: str = os.getenv('DASH_PASSWORD', 'secret')
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv('SESSION_TIMEOUT_MINUTES', '30'))
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv('MAX_UPLOAD_SIZE_MB', '100'))
    ENABLE_CSRF_PROTECTION: bool = os.getenv('ENABLE_CSRF_PROTECTION', 'True').lower() == 'true'


@dataclass
class DatabaseConfig:
    """Database configuration."""
    DB_TYPE: str = os.getenv('DB_TYPE', 'file')  # 'file' or 'postgres'
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', '5432'))
    DB_NAME: str = os.getenv('DB_NAME', 'snugeoshm')
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    DB_POOL_SIZE: int = int(os.getenv('DB_POOL_SIZE', '5'))
    DB_MAX_OVERFLOW: int = int(os.getenv('DB_MAX_OVERFLOW', '10'))

    @property
    def connection_string(self) -> str:
        """Get database connection string."""
        if self.DB_TYPE == 'postgres':
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return ""


@dataclass
class CacheConfig:
    """Caching configuration."""
    CACHE_TYPE: str = os.getenv('CACHE_TYPE', 'simple')  # 'simple' or 'redis'
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB: int = int(os.getenv('REDIS_DB', '0'))
    REDIS_PASSWORD: Optional[str] = os.getenv('REDIS_PASSWORD')
    CACHE_DEFAULT_TIMEOUT: int = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))


@dataclass
class AppConfig:
    """Application configuration."""
    DEBUG: bool = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST: str = os.getenv('HOST', '0.0.0.0')
    PORT: int = int(os.getenv('PORT', '8050'))
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    DATA_REFRESH_INTERVAL_MS: int = int(os.getenv('DATA_REFRESH_INTERVAL_MS', '60000'))
    ENABLE_PROFILING: bool = os.getenv('ENABLE_PROFILING', 'False').lower() == 'true'


@dataclass
class DataConfig:
    """Data-related configuration."""
    PROJECT_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR: Path = PROJECT_DIR / 'data'
    ASSETS_DIR: Path = PROJECT_DIR / 'assets'
    OUTPUTS_DIR: Path = PROJECT_DIR / 'outputs'
    TEMP_DIR: Path = PROJECT_DIR / 'temp'

    # File size limits (in bytes)
    MAX_CSV_SIZE: int = int(os.getenv('MAX_CSV_SIZE', str(100 * 1024 * 1024)))  # 100MB
    MAX_NETCDF_SIZE: int = int(os.getenv('MAX_NETCDF_SIZE', str(500 * 1024 * 1024)))  # 500MB

    # Data validation
    ENABLE_DATA_VALIDATION: bool = os.getenv('ENABLE_DATA_VALIDATION', 'True').lower() == 'true'
    MAX_COORDINATE_BOUND: float = float(os.getenv('MAX_COORDINATE_BOUND', '1000'))
    MIN_QC_VALUE: float = float(os.getenv('MIN_QC_VALUE', '0'))
    MAX_QC_VALUE: float = float(os.getenv('MAX_QC_VALUE', '100'))


@dataclass
class PerformanceConfig:
    """Performance-related configuration."""
    MAX_WORKERS: int = int(os.getenv('MAX_WORKERS', '4'))
    ENABLE_ASYNC: bool = os.getenv('ENABLE_ASYNC', 'True').lower() == 'true'
    MAP_CLUSTER_THRESHOLD: int = int(os.getenv('MAP_CLUSTER_THRESHOLD', '100'))
    CHUNK_SIZE: int = int(os.getenv('CHUNK_SIZE', '10000'))


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    ENABLE_METRICS: bool = os.getenv('ENABLE_METRICS', 'False').lower() == 'true'
    METRICS_PORT: int = int(os.getenv('METRICS_PORT', '9090'))
    SENTRY_DSN: Optional[str] = os.getenv('SENTRY_DSN')
    ENABLE_REQUEST_LOGGING: bool = os.getenv('ENABLE_REQUEST_LOGGING', 'True').lower() == 'true'


class Config:
    """Main configuration class aggregating all config sections."""

    def __init__(self):
        self.security = SecurityConfig()
        self.database = DatabaseConfig()
        self.cache = CacheConfig()
        self.app = AppConfig()
        self.data = DataConfig()
        self.performance = PerformanceConfig()
        self.monitoring = MonitoringConfig()

        # Ensure directories exist
        self._create_directories()

    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        for dir_path in [
            self.data.DATA_DIR,
            self.data.ASSETS_DIR,
            self.data.OUTPUTS_DIR,
            self.data.TEMP_DIR
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def validate(self) -> list[str]:
        """
        Validate configuration settings.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate security
        if self.security.SECRET_KEY == 'dev-secret-key-change-in-production' and not self.app.DEBUG:
            errors.append("SECRET_KEY must be changed in production")

        if self.security.DASH_PASSWORD == 'secret' and not self.app.DEBUG:
            errors.append("DASH_PASSWORD must be changed in production")

        # Validate database
        if self.database.DB_TYPE == 'postgres' and not self.database.DB_PASSWORD:
            errors.append("DB_PASSWORD is required for PostgreSQL")

        # Validate paths
        if not self.data.PROJECT_DIR.exists():
            errors.append(f"Project directory does not exist: {self.data.PROJECT_DIR}")

        # Validate performance settings
        if self.performance.MAX_WORKERS < 1:
            errors.append("MAX_WORKERS must be at least 1")

        return errors


# Global configuration instance
config = Config()


# Validate on import in production
if not config.app.DEBUG:
    validation_errors = config.validate()
    if validation_errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {err}" for err in validation_errors))
