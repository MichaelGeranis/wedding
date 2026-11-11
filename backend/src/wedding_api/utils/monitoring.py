"""Application monitoring utilities."""

import inspect
import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor application performance metrics."""

    def __init__(self) -> None:
        """Initialize performance monitor."""
        self.metrics: dict[str, list[float]] = {}

    def record_metric(self, name: str, value: float) -> None:
        """Record a performance metric."""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(value)

        # Keep only last 1000 measurements to prevent memory issues
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-1000:]

    def get_average(self, name: str) -> float | None:
        """Get average value for a metric."""
        if name not in self.metrics or not self.metrics[name]:
            return None
        return sum(self.metrics[name]) / len(self.metrics[name])

    def get_percentile(self, name: str, percentile: float) -> float | None:
        """Get percentile value for a metric."""
        if name not in self.metrics or not self.metrics[name]:
            return None

        sorted_values = sorted(self.metrics[name])
        index = int(len(sorted_values) * (percentile / 100))
        return sorted_values[min(index, len(sorted_values) - 1)]

    def get_stats(self, name: str) -> dict[str, float] | None:
        """Get statistics for a metric."""
        if name not in self.metrics or not self.metrics[name]:
            return None

        values = self.metrics[name]
        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "p50": self.get_percentile(name, 50) or 0,
            "p95": self.get_percentile(name, 95) or 0,
            "p99": self.get_percentile(name, 99) or 0,
            "count": len(values),
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(metric_name: str) -> Callable:
    """Decorator to monitor function execution time."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                performance_monitor.record_metric(metric_name, duration)
                logger.debug(f"{metric_name} completed in {duration:.3f}s")

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                performance_monitor.record_metric(metric_name, duration)
                logger.debug(f"{metric_name} completed in {duration:.3f}s")

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
