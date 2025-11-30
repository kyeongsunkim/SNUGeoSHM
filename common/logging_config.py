"""
Centralized logging configuration for SNUGeoSHM.

This module provides structured logging with rotation, filtering,
and different handlers for development and production.
"""

import logging
import logging.handlers
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict
from config import config


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""

    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging() -> None:
    """
    Setup application logging with appropriate handlers.

    Configures:
    - Console handler (colored in dev, plain in prod)
    - File handler with rotation
    - JSON handler for structured logs (production)
    - Error file handler for errors only
    """
    # Create logs directory
    log_dir = config.data.PROJECT_DIR / 'logs'
    log_dir.mkdir(exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.app.LOG_LEVEL.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if config.app.DEBUG:
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO if not config.app.DEBUG else logging.DEBUG)
    root_logger.addHandler(console_handler)

    # File handler with rotation (all logs)
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'app.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    # Error file handler (errors only)
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'errors.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setFormatter(file_formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)

    # JSON handler for structured logs (production only)
    if not config.app.DEBUG:
        json_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'app.json',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        json_handler.setFormatter(JSONFormatter())
        json_handler.setLevel(logging.INFO)
        root_logger.addHandler(json_handler)

    # Suppress noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)

    root_logger.info(f"Logging configured - Level: {config.app.LOG_LEVEL}, Debug: {config.app.DEBUG}")


class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter for adding context."""

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add extra context to log messages."""
        extra = kwargs.get('extra', {})

        # Add any context from the adapter
        for key, value in self.extra.items():
            if key not in extra:
                extra[key] = value

        kwargs['extra'] = extra
        return msg, kwargs


def get_logger(name: str, **context) -> logging.Logger:
    """
    Get a logger with optional context.

    Args:
        name: Logger name (usually __name__)
        **context: Additional context to include in all logs

    Returns:
        Logger instance or LoggerAdapter with context
    """
    logger = logging.getLogger(name)

    if context:
        return LoggerAdapter(logger, context)

    return logger


# Performance logging decorator
def log_performance(logger: logging.Logger):
    """
    Decorator to log function performance.

    Args:
        logger: Logger instance to use

    Usage:
        @log_performance(logger)
        def my_function():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                logger.info(
                    f"{func.__name__} completed in {duration_ms:.2f}ms",
                    extra={'duration_ms': duration_ms, 'function': func.__name__}
                )

                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"{func.__name__} failed after {duration_ms:.2f}ms: {str(e)}",
                    extra={'duration_ms': duration_ms, 'function': func.__name__},
                    exc_info=True
                )
                raise

        return wrapper
    return decorator


# Initialize logging when module is imported
setup_logging()
