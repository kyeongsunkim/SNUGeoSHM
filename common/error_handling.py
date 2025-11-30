"""
Error handling and retry utilities for SNUGeoSHM.

This module provides decorators and utilities for handling errors gracefully,
implementing retry logic, and circuit breaker patterns.
"""

import functools
import time
import logging
from typing import Callable, Type, Tuple, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RetryExhaustedError(Exception):
    """Raised when all retry attempts have been exhausted."""
    pass


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""
    pass


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorator to retry a function on failure with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function called before each retry

    Example:
        @retry(max_attempts=3, delay=1.0, backoff=2.0)
        def fetch_data():
            # This will retry up to 3 times with exponential backoff
            return requests.get(url)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts",
                            exc_info=True,
                            extra={'attempts': max_attempts, 'function': func.__name__}
                        )
                        raise RetryExhaustedError(
                            f"Failed after {max_attempts} attempts"
                        ) from e

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}), "
                        f"retrying in {current_delay:.1f}s: {str(e)}",
                        extra={'attempt': attempt, 'delay': current_delay, 'function': func.__name__}
                    )

                    if on_retry:
                        on_retry(attempt, e)

                    time.sleep(current_delay)
                    current_delay *= backoff

            # This should never be reached, but just in case
            raise last_exception

        return wrapper
    return decorator


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Async version of retry decorator.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional async callback function called before each retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            import asyncio

            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts",
                            exc_info=True,
                            extra={'attempts': max_attempts, 'function': func.__name__}
                        )
                        raise RetryExhaustedError(
                            f"Failed after {max_attempts} attempts"
                        ) from e

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}), "
                        f"retrying in {current_delay:.1f}s: {str(e)}",
                        extra={'attempt': attempt, 'delay': current_delay, 'function': func.__name__}
                    )

                    if on_retry:
                        if asyncio.iscoroutinefunction(on_retry):
                            await on_retry(attempt, e)
                        else:
                            on_retry(attempt, e)

                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

            raise last_exception

        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by failing fast when error rate is high.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail immediately
    - HALF_OPEN: Testing if service has recovered

    Example:
        circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

        @circuit_breaker
        def call_external_service():
            return requests.get(url)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exceptions: Exceptions that count as failures
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions

        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = 'CLOSED'

    def __call__(self, func: Callable) -> Callable:
        """Make circuit breaker work as a decorator."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if self._should_attempt_reset():
                    self.state = 'HALF_OPEN'
                    logger.info(
                        f"Circuit breaker for {func.__name__} entering HALF_OPEN state",
                        extra={'function': func.__name__}
                    )
                else:
                    raise CircuitBreakerOpen(
                        f"Circuit breaker is OPEN for {func.__name__}"
                    )

            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result

            except self.expected_exceptions as e:
                self._on_failure()
                raise

        return wrapper

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return True

        return datetime.now() - self.last_failure_time >= timedelta(seconds=self.recovery_timeout)

    def _on_success(self):
        """Handle successful call."""
        if self.state == 'HALF_OPEN':
            logger.info("Circuit breaker reset to CLOSED")
        self.failure_count = 0
        self.state = 'CLOSED'

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.error(
                f"Circuit breaker opened after {self.failure_count} failures",
                extra={'failure_count': self.failure_count}
            )


def safe_execute(func: Callable, default: Any = None, log_errors: bool = True) -> Any:
    """
    Execute a function safely, returning default value on error.

    Args:
        func: Function to execute
        default: Default value to return on error
        log_errors: Whether to log errors

    Returns:
        Function result or default value

    Example:
        result = safe_execute(lambda: risky_operation(), default=[])
    """
    try:
        return func()
    except Exception as e:
        if log_errors:
            logger.error(f"Error in safe_execute: {str(e)}", exc_info=True)
        return default


def handle_exceptions(*exceptions: Type[Exception], default: Any = None):
    """
    Decorator to handle specific exceptions and return default value.

    Args:
        *exceptions: Exception types to catch
        default: Default value to return on exception

    Example:
        @handle_exceptions(ValueError, KeyError, default=[])
        def get_data():
            return potentially_failing_operation()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                logger.error(
                    f"Exception in {func.__name__}: {str(e)}",
                    exc_info=True,
                    extra={'function': func.__name__}
                )
                return default
        return wrapper
    return decorator


class ErrorContext:
    """
    Context manager for error handling with cleanup.

    Example:
        with ErrorContext("loading data", cleanup=close_connection):
            data = load_data()
    """

    def __init__(
        self,
        operation_name: str,
        cleanup: Optional[Callable] = None,
        raise_error: bool = True
    ):
        """
        Initialize error context.

        Args:
            operation_name: Name of operation for logging
            cleanup: Optional cleanup function
            raise_error: Whether to re-raise errors
        """
        self.operation_name = operation_name
        self.cleanup = cleanup
        self.raise_error = raise_error

    def __enter__(self):
        """Enter context."""
        logger.debug(f"Starting: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context with error handling."""
        if exc_type is not None:
            logger.error(
                f"Error during {self.operation_name}: {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb),
                extra={'operation': self.operation_name}
            )

        # Always run cleanup
        if self.cleanup:
            try:
                self.cleanup()
            except Exception as e:
                logger.error(
                    f"Error during cleanup of {self.operation_name}: {str(e)}",
                    exc_info=True
                )

        # Suppress exception if raise_error is False
        return not self.raise_error


def format_error_message(error: Exception, context: Optional[str] = None) -> str:
    """
    Format error message with context for user display.

    Args:
        error: Exception instance
        context: Optional context description

    Returns:
        Formatted error message
    """
    error_type = type(error).__name__
    error_msg = str(error)

    if context:
        return f"{context}: {error_type} - {error_msg}"
    else:
        return f"{error_type}: {error_msg}"
