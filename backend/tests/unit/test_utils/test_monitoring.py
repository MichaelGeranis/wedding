"""Unit tests for monitoring utilities."""

import asyncio
import time
from typing import Any

import pytest

from wedding_api.utils.monitoring import PerformanceMonitor, monitor_performance


def test_performance_monitor_initialization():
    """Test performance monitor initialization."""
    monitor = PerformanceMonitor()
    assert isinstance(monitor.metrics, dict)
    assert len(monitor.metrics) == 0


def test_record_metric_single_value():
    """Test recording a single metric value."""
    monitor = PerformanceMonitor()
    monitor.record_metric("test_metric", 1.5)

    assert "test_metric" in monitor.metrics
    assert len(monitor.metrics["test_metric"]) == 1
    assert monitor.metrics["test_metric"][0] == 1.5


def test_record_metric_multiple_values():
    """Test recording multiple metric values."""
    monitor = PerformanceMonitor()

    monitor.record_metric("test_metric", 1.0)
    monitor.record_metric("test_metric", 2.0)
    monitor.record_metric("test_metric", 3.0)

    assert len(monitor.metrics["test_metric"]) == 3
    assert monitor.metrics["test_metric"] == [1.0, 2.0, 3.0]


def test_record_metric_keeps_last_1000():
    """Test that recording metrics keeps only last 1000 values."""
    monitor = PerformanceMonitor()

    # Record 1500 values
    for i in range(1500):
        monitor.record_metric("test_metric", float(i))

    # Should only keep last 1000
    assert len(monitor.metrics["test_metric"]) == 1000
    assert monitor.metrics["test_metric"][0] == 500.0  # First value should be 500
    assert monitor.metrics["test_metric"][-1] == 1499.0  # Last value should be 1499


def test_record_metric_multiple_metrics():
    """Test recording values for multiple different metrics."""
    monitor = PerformanceMonitor()

    monitor.record_metric("metric_a", 1.0)
    monitor.record_metric("metric_b", 2.0)
    monitor.record_metric("metric_a", 3.0)

    assert len(monitor.metrics) == 2
    assert monitor.metrics["metric_a"] == [1.0, 3.0]
    assert monitor.metrics["metric_b"] == [2.0]


def test_get_average_single_value():
    """Test getting average for single value."""
    monitor = PerformanceMonitor()
    monitor.record_metric("test_metric", 5.0)

    avg = monitor.get_average("test_metric")
    assert avg == 5.0


def test_get_average_multiple_values():
    """Test getting average for multiple values."""
    monitor = PerformanceMonitor()

    monitor.record_metric("test_metric", 1.0)
    monitor.record_metric("test_metric", 2.0)
    monitor.record_metric("test_metric", 3.0)
    monitor.record_metric("test_metric", 4.0)

    avg = monitor.get_average("test_metric")
    assert avg == 2.5


def test_get_average_nonexistent_metric():
    """Test getting average for non-existent metric."""
    monitor = PerformanceMonitor()

    avg = monitor.get_average("nonexistent")
    assert avg is None


def test_get_average_empty_metric():
    """Test getting average for metric with no values."""
    monitor = PerformanceMonitor()
    monitor.metrics["empty_metric"] = []

    avg = monitor.get_average("empty_metric")
    assert avg is None


def test_get_percentile_single_value():
    """Test getting percentile for single value."""
    monitor = PerformanceMonitor()
    monitor.record_metric("test_metric", 5.0)

    p50 = monitor.get_percentile("test_metric", 50)
    assert p50 == 5.0


def test_get_percentile_multiple_values():
    """Test getting percentiles for multiple values."""
    monitor = PerformanceMonitor()

    # Record values 1-100
    for i in range(1, 101):
        monitor.record_metric("test_metric", float(i))

    p50 = monitor.get_percentile("test_metric", 50)
    p95 = monitor.get_percentile("test_metric", 95)
    p99 = monitor.get_percentile("test_metric", 99)

    # p50 should be around 50
    assert 45 <= p50 <= 55

    # p95 should be around 95
    assert 90 <= p95 <= 100

    # p99 should be around 99
    assert 95 <= p99 <= 100


def test_get_percentile_edge_values():
    """Test getting edge percentiles (0 and 100)."""
    monitor = PerformanceMonitor()

    for i in range(1, 11):
        monitor.record_metric("test_metric", float(i))

    p0 = monitor.get_percentile("test_metric", 0)
    p100 = monitor.get_percentile("test_metric", 100)

    assert p0 == 1.0  # Minimum value
    assert p100 == 10.0  # Maximum value


def test_get_percentile_nonexistent_metric():
    """Test getting percentile for non-existent metric."""
    monitor = PerformanceMonitor()

    percentile = monitor.get_percentile("nonexistent", 50)
    assert percentile is None


def test_get_percentile_empty_metric():
    """Test getting percentile for metric with no values."""
    monitor = PerformanceMonitor()
    monitor.metrics["empty_metric"] = []

    percentile = monitor.get_percentile("empty_metric", 50)
    assert percentile is None


def test_get_stats_comprehensive():
    """Test getting comprehensive statistics."""
    monitor = PerformanceMonitor()

    # Record values: 1, 2, 3, 4, 5
    for i in range(1, 6):
        monitor.record_metric("test_metric", float(i))

    stats = monitor.get_stats("test_metric")

    assert stats is not None
    assert stats["min"] == 1.0
    assert stats["max"] == 5.0
    assert stats["avg"] == 3.0
    assert stats["count"] == 5
    assert stats["p50"] == 3.0
    # p95 and p99 should be high values (4 or 5)
    assert stats["p95"] >= 4.0
    assert stats["p99"] >= 4.0


def test_get_stats_single_value():
    """Test getting statistics for single value."""
    monitor = PerformanceMonitor()
    monitor.record_metric("test_metric", 7.5)

    stats = monitor.get_stats("test_metric")

    assert stats is not None
    assert stats["min"] == 7.5
    assert stats["max"] == 7.5
    assert stats["avg"] == 7.5
    assert stats["count"] == 1
    assert stats["p50"] == 7.5
    assert stats["p95"] == 7.5
    assert stats["p99"] == 7.5


def test_get_stats_nonexistent_metric():
    """Test getting statistics for non-existent metric."""
    monitor = PerformanceMonitor()

    stats = monitor.get_stats("nonexistent")
    assert stats is None


def test_get_stats_empty_metric():
    """Test getting statistics for metric with no values."""
    monitor = PerformanceMonitor()
    monitor.metrics["empty_metric"] = []

    stats = monitor.get_stats("empty_metric")
    assert stats is None


def test_get_stats_large_dataset():
    """Test getting statistics for large dataset."""
    monitor = PerformanceMonitor()

    # Record 1000 values
    for i in range(1000):
        monitor.record_metric("test_metric", float(i))

    stats = monitor.get_stats("test_metric")

    assert stats is not None
    assert stats["min"] == 0.0
    assert stats["max"] == 999.0
    assert 400 <= stats["avg"] <= 600  # Should be around 499.5
    assert stats["count"] == 1000


@pytest.mark.asyncio
async def test_monitor_performance_async_function():
    """Test monitoring performance of async function."""
    monitor = PerformanceMonitor()

    @monitor_performance("test_async")
    async def async_function(duration: float) -> str:
        """Test async function."""
        await asyncio.sleep(duration)
        return "completed"

    # Manually set the monitor for testing
    import wedding_api.utils.monitoring

    original_monitor = wedding_api.utils.monitoring.performance_monitor
    wedding_api.utils.monitoring.performance_monitor = monitor

    try:
        result = await async_function(0.1)

        assert result == "completed"
        assert "test_async" in monitor.metrics
        assert len(monitor.metrics["test_async"]) == 1
        # Duration should be at least 0.1 seconds
        assert monitor.metrics["test_async"][0] >= 0.1
    finally:
        wedding_api.utils.monitoring.performance_monitor = original_monitor


def test_monitor_performance_sync_function():
    """Test monitoring performance of sync function."""
    monitor = PerformanceMonitor()

    @monitor_performance("test_sync")
    def sync_function(duration: float) -> str:
        """Test sync function."""
        time.sleep(duration)
        return "completed"

    # Manually set the monitor for testing
    import wedding_api.utils.monitoring

    original_monitor = wedding_api.utils.monitoring.performance_monitor
    wedding_api.utils.monitoring.performance_monitor = monitor

    try:
        result = sync_function(0.1)

        assert result == "completed"
        assert "test_sync" in monitor.metrics
        assert len(monitor.metrics["test_sync"]) == 1
        # Duration should be at least 0.1 seconds
        assert monitor.metrics["test_sync"][0] >= 0.1
    finally:
        wedding_api.utils.monitoring.performance_monitor = original_monitor


@pytest.mark.asyncio
async def test_monitor_performance_async_with_exception():
    """Test monitoring performance when async function raises exception."""
    monitor = PerformanceMonitor()

    @monitor_performance("test_async_error")
    async def async_function_with_error() -> None:
        """Test async function that raises error."""
        await asyncio.sleep(0.05)
        raise ValueError("Test error")

    # Manually set the monitor for testing
    import wedding_api.utils.monitoring

    original_monitor = wedding_api.utils.monitoring.performance_monitor
    wedding_api.utils.monitoring.performance_monitor = monitor

    try:
        with pytest.raises(ValueError, match="Test error"):
            await async_function_with_error()

        # Metric should still be recorded even when exception occurs
        assert "test_async_error" in monitor.metrics
        assert len(monitor.metrics["test_async_error"]) == 1
        assert monitor.metrics["test_async_error"][0] >= 0.05
    finally:
        wedding_api.utils.monitoring.performance_monitor = original_monitor


def test_monitor_performance_sync_with_exception():
    """Test monitoring performance when sync function raises exception."""
    monitor = PerformanceMonitor()

    @monitor_performance("test_sync_error")
    def sync_function_with_error() -> None:
        """Test sync function that raises error."""
        time.sleep(0.05)
        raise ValueError("Test error")

    # Manually set the monitor for testing
    import wedding_api.utils.monitoring

    original_monitor = wedding_api.utils.monitoring.performance_monitor
    wedding_api.utils.monitoring.performance_monitor = monitor

    try:
        with pytest.raises(ValueError, match="Test error"):
            sync_function_with_error()

        # Metric should still be recorded even when exception occurs
        assert "test_sync_error" in monitor.metrics
        assert len(monitor.metrics["test_sync_error"]) == 1
        assert monitor.metrics["test_sync_error"][0] >= 0.05
    finally:
        wedding_api.utils.monitoring.performance_monitor = original_monitor


@pytest.mark.asyncio
async def test_monitor_performance_multiple_calls():
    """Test monitoring performance with multiple function calls."""
    monitor = PerformanceMonitor()

    @monitor_performance("test_multiple")
    async def async_function(duration: float) -> int:
        """Test async function."""
        await asyncio.sleep(duration)
        return 1

    # Manually set the monitor for testing
    import wedding_api.utils.monitoring

    original_monitor = wedding_api.utils.monitoring.performance_monitor
    wedding_api.utils.monitoring.performance_monitor = monitor

    try:
        # Call function 5 times
        for _ in range(5):
            await async_function(0.01)

        assert "test_multiple" in monitor.metrics
        assert len(monitor.metrics["test_multiple"]) == 5
        # All durations should be at least 0.01 seconds
        for duration in monitor.metrics["test_multiple"]:
            assert duration >= 0.01
    finally:
        wedding_api.utils.monitoring.performance_monitor = original_monitor


def test_monitor_performance_preserves_function_metadata():
    """Test that decorator preserves function metadata."""

    @monitor_performance("test_metadata")
    def test_function() -> str:
        """Test function docstring."""
        return "test"

    assert test_function.__name__ == "test_function"
    assert test_function.__doc__ == "Test function docstring."


@pytest.mark.asyncio
async def test_monitor_performance_async_preserves_metadata():
    """Test that decorator preserves async function metadata."""

    @monitor_performance("test_async_metadata")
    async def test_async_function() -> str:
        """Test async function docstring."""
        return "test"

    assert test_async_function.__name__ == "test_async_function"
    assert test_async_function.__doc__ == "Test async function docstring."


def test_monitor_performance_with_arguments():
    """Test monitoring performance of function with arguments."""
    monitor = PerformanceMonitor()

    @monitor_performance("test_with_args")
    def function_with_args(a: int, b: int, c: str = "default") -> str:
        """Test function with arguments."""
        return f"{a + b} {c}"

    # Manually set the monitor for testing
    import wedding_api.utils.monitoring

    original_monitor = wedding_api.utils.monitoring.performance_monitor
    wedding_api.utils.monitoring.performance_monitor = monitor

    try:
        result = function_with_args(1, 2, c="custom")

        assert result == "3 custom"
        assert "test_with_args" in monitor.metrics
        assert len(monitor.metrics["test_with_args"]) == 1
    finally:
        wedding_api.utils.monitoring.performance_monitor = original_monitor


@pytest.mark.asyncio
async def test_monitor_performance_async_with_return_value():
    """Test monitoring performance with complex return value."""
    monitor = PerformanceMonitor()

    @monitor_performance("test_return_value")
    async def async_function_with_return() -> dict[str, Any]:
        """Test async function with return value."""
        await asyncio.sleep(0.01)
        return {"status": "success", "data": [1, 2, 3]}

    # Manually set the monitor for testing
    import wedding_api.utils.monitoring

    original_monitor = wedding_api.utils.monitoring.performance_monitor
    wedding_api.utils.monitoring.performance_monitor = monitor

    try:
        result = await async_function_with_return()

        assert result == {"status": "success", "data": [1, 2, 3]}
        assert "test_return_value" in monitor.metrics
        assert len(monitor.metrics["test_return_value"]) == 1
    finally:
        wedding_api.utils.monitoring.performance_monitor = original_monitor


def test_percentile_boundary_conditions():
    """Test percentile calculation with boundary conditions."""
    monitor = PerformanceMonitor()

    # Record exactly 2 values
    monitor.record_metric("two_values", 1.0)
    monitor.record_metric("two_values", 100.0)

    p50 = monitor.get_percentile("two_values", 50)
    p100 = monitor.get_percentile("two_values", 100)

    # With 2 values, p50 should be one of them
    assert p50 in [1.0, 100.0]
    # p100 should be the maximum
    assert p100 == 100.0


def test_get_stats_with_negative_values():
    """Test getting statistics with negative values."""
    monitor = PerformanceMonitor()

    monitor.record_metric("negative_metric", -5.0)
    monitor.record_metric("negative_metric", -2.0)
    monitor.record_metric("negative_metric", 3.0)
    monitor.record_metric("negative_metric", 10.0)

    stats = monitor.get_stats("negative_metric")

    assert stats is not None
    assert stats["min"] == -5.0
    assert stats["max"] == 10.0
    assert stats["avg"] == 1.5  # (-5 + -2 + 3 + 10) / 4
    assert stats["count"] == 4


def test_get_stats_with_zero_values():
    """Test getting statistics with zero values."""
    monitor = PerformanceMonitor()

    monitor.record_metric("zero_metric", 0.0)
    monitor.record_metric("zero_metric", 0.0)
    monitor.record_metric("zero_metric", 0.0)

    stats = monitor.get_stats("zero_metric")

    assert stats is not None
    assert stats["min"] == 0.0
    assert stats["max"] == 0.0
    assert stats["avg"] == 0.0
    assert stats["count"] == 3
    assert stats["p50"] == 0.0


def test_get_stats_with_very_small_values():
    """Test getting statistics with very small float values."""
    monitor = PerformanceMonitor()

    monitor.record_metric("small_metric", 0.001)
    monitor.record_metric("small_metric", 0.002)
    monitor.record_metric("small_metric", 0.003)

    stats = monitor.get_stats("small_metric")

    assert stats is not None
    assert stats["min"] == 0.001
    assert stats["max"] == 0.003
    assert abs(stats["avg"] - 0.002) < 0.0001  # Float comparison with tolerance
    assert stats["count"] == 3


def test_record_metric_at_exactly_1000():
    """Test that recording exactly 1000 values works correctly."""
    monitor = PerformanceMonitor()

    # Record exactly 1000 values
    for i in range(1000):
        monitor.record_metric("test_metric", float(i))

    # Should have exactly 1000 values
    assert len(monitor.metrics["test_metric"]) == 1000
    assert monitor.metrics["test_metric"][0] == 0.0
    assert monitor.metrics["test_metric"][-1] == 999.0


def test_record_metric_at_1001():
    """Test that recording 1001 values triggers cleanup."""
    monitor = PerformanceMonitor()

    # Record 1001 values
    for i in range(1001):
        monitor.record_metric("test_metric", float(i))

    # Should keep only last 1000
    assert len(monitor.metrics["test_metric"]) == 1000
    assert monitor.metrics["test_metric"][0] == 1.0  # First value should be 1 (0 was dropped)
    assert monitor.metrics["test_metric"][-1] == 1000.0  # Last value should be 1000
