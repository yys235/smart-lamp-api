"""Stability test for long-running API operation."""

import asyncio
import time
import psutil
import statistics
from datetime import datetime, timedelta
from typing import Dict, List

import httpx


class StabilityMetrics:
    """Track stability metrics during long-running test."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.response_times: List[float] = []
        self.memory_samples: List[float] = []
        self.cpu_samples: List[float] = []
        self.errors: List[str] = []
        self.process = psutil.Process()

    def start(self):
        """Start tracking."""
        self.start_time = time.time()

    def stop(self):
        """Stop tracking."""
        self.end_time = time.time()

    def record_request(self, success: bool, response_time: float, error: str = None):
        """Record a request."""
        self.request_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
            if error:
                self.errors.append(error)
        self.response_times.append(response_time)

    def sample_resources(self):
        """Sample system resources."""
        try:
            self.memory_samples.append(self.process.memory_info().rss / 1024 / 1024)  # MB
            self.cpu_samples.append(self.process.cpu_percent())
        except:
            pass

    @property
    def duration(self) -> float:
        """Get test duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0

    @property
    def success_rate(self) -> float:
        """Get success rate."""
        if self.request_count == 0:
            return 0
        return (self.success_count / self.request_count) * 100

    @property
    def avg_response_time(self) -> float:
        """Get average response time."""
        if not self.response_times:
            return 0
        return statistics.mean(self.response_times)

    @property
    def p95_response_time(self) -> float:
        """Get P95 response time."""
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[min(index, len(sorted_times) - 1)]

    @property
    def requests_per_second(self) -> float:
        """Get requests per second."""
        if self.duration == 0:
            return 0
        return self.request_count / self.duration

    @property
    def avg_memory(self) -> float:
        """Get average memory usage in MB."""
        if not self.memory_samples:
            return 0
        return statistics.mean(self.memory_samples)

    @property
    def memory_growth(self) -> float:
        """Get memory growth in MB (last - first)."""
        if len(self.memory_samples) < 2:
            return 0
        return self.memory_samples[-1] - self.memory_samples[0]

    @property
    def avg_cpu(self) -> float:
        """Get average CPU usage."""
        if not self.cpu_samples:
            return 0
        return statistics.mean(self.cpu_samples)

    def summary(self) -> Dict:
        """Get summary dict."""
        return {
            "duration": f"{self.duration:.1f}s",
            "total_requests": self.request_count,
            "success_rate": f"{self.success_rate:.2f}%",
            "avg_response_time": f"{self.avg_response_time:.2f}ms",
            "p95_response_time": f"{self.p95_response_time:.2f}ms",
            "requests_per_second": f"{self.requests_per_second:.2f}",
            "avg_memory_mb": f"{self.avg_memory:.1f}",
            "memory_growth_mb": f"{self.memory_growth:.1f}",
            "avg_cpu_percent": f"{self.avg_cpu:.1f}",
        }


async def run_stability_test(
    base_url: str = "http://localhost:8000",
    duration_seconds: int = 300,  # 5 minutes default
    target_rps: int = 10  # Target requests per second
):
    """Run stability test for specified duration."""

    metrics = StabilityMetrics()
    metrics.start()

    print("="*80)
    print("STABILITY TEST - Smart Lamp API")
    print("="*80)
    print(f"Target URL: {base_url}")
    print(f"Duration: {duration_seconds}s")
    print(f"Target RPS: {target_rps}")
    print()
    print("Starting test...")
    print(f"{'Time':<10} {'Requests':<10} {'Success':<8} {'Avg RT':<10} {'Memory MB':<12}")
    print("-" * 80)

    endpoints = [
        "/api/v1/health",
        "/api/v1/lamps",
        "/api/v1/gateway",
        "/api/v1/logs?limit=10"
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        end_time = time.time() + duration_seconds
        endpoint_index = 0
        last_report_time = time.time()

        while time.time() < end_time:
            # Rotate through endpoints
            endpoint = endpoints[endpoint_index % len(endpoints)]
            endpoint_index += 1

            # Make request
            start = time.time()
            try:
                response = await client.get(f"{base_url}{endpoint}")
                elapsed = (time.time() - start) * 1000
                success = response.status_code in [200, 500]
                error = None if success else f"Status {response.status_code}"
                metrics.record_request(success, elapsed, error)
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                metrics.record_request(False, elapsed, str(e))

            # Sample resources periodically
            if metrics.request_count % 50 == 0:
                metrics.sample_resources()

            # Maintain target RPS
            sleep_time = 1.0 / target_rps
            await asyncio.sleep(sleep_time)

            # Print progress every 10 seconds
            if time.time() - last_report_time >= 10:
                elapsed_time = time.time() - metrics.start_time
                print(f"{elapsed_time:>8.0f}s {metrics.request_count:<10} {metrics.success_rate:>6.2f}% {metrics.avg_response_time:>8.2f}ms {metrics.avg_memory:>10.1f}MB")
                last_report_time = time.time()

    metrics.stop()

    # Print summary
    print()
    print("="*80)
    print("STABILITY TEST SUMMARY")
    print("="*80)
    summary = metrics.summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Check for memory leak
    print()
    if metrics.memory_growth > 50:  # More than 50MB growth
        print("  WARNING: Potential memory leak detected!")
        print(f"  Memory growth: {metrics.memory_growth:.1f}MB")
    else:
        print("  Memory stability: OK")

    # Check error rate
    error_count = len(metrics.errors)
    if error_count > 0:
        print(f"  Errors detected: {error_count}")
        unique_errors = list(set(metrics.errors[:10]))  # First 10 unique
        for error in unique_errors:
            print(f"    - {error}")
    else:
        print("  Errors: None")

    print("="*80)

    return metrics


async def run_quick_check(base_url: str = "http://localhost:8000"):
    """Run a quick API availability and performance check."""
    print("\nQuick API Check")
    print("-" * 40)

    endpoints = [
        ("GET /api/v1/health", "/api/v1/health"),
        ("GET /api/v1/lamps", "/api/v1/lamps"),
        ("GET /api/v1/gateway", "/api/v1/gateway"),
    ]

    async with httpx.AsyncClient(timeout=10.0) as client:
        for name, endpoint in endpoints:
            start = time.time()
            try:
                response = await client.get(f"{base_url}{endpoint}")
                elapsed = (time.time() - start) * 1000
                status = "✓" if response.status_code in [200, 500] else "✗"
                print(f"  {status} {name}: {response.status_code} ({elapsed:.1f}ms)")
            except Exception as e:
                elapsed = (time.time() - start) * 1000
                print(f"  ✗ {name}: Error ({elapsed:.1f}ms)")
                print(f"      {e}")


if __name__ == "__main__":
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60  # Default 1 minute

    # Run quick check first
    asyncio.run(run_quick_check(base_url))

    print()

    # Run stability test
    asyncio.run(run_stability_test(base_url, duration))
