"""Load test configuration and runner for Smart Lamp API."""

import asyncio
import time
import statistics
from contextlib import asynccontextmanager
from typing import List, Dict, Any

import httpx


class LoadTestResult:
    """Load test result data."""

    def __init__(self):
        self.response_times: List[float] = []
        self.success_count = 0
        self.failure_count = 0
        self.errors: List[str] = []

    def add_response(self, response_time: float, success: bool, error: str = None):
        """Add a response time to the results."""
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
            if error:
                self.errors.append(error)

    @property
    def total_requests(self) -> int:
        return self.success_count + self.failure_count

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.success_count / self.total_requests) * 100

    @property
    def avg_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)

    @property
    def p50_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return statistics.median(self.response_times)

    @property
    def p95_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[min(index, len(sorted_times) - 1)]

    @property
    def p99_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.99)
        return sorted_times[min(index, len(sorted_times) - 1)]

    def summary(self) -> Dict[str, Any]:
        """Get test summary as dict."""
        return {
            "total_requests": self.total_requests,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": f"{self.success_rate:.2f}%",
            "avg_response_time": f"{self.avg_response_time:.2f}ms",
            "p50_response_time": f"{self.p50_response_time:.2f}ms",
            "p95_response_time": f"{self.p95_response_time:.2f}ms",
            "p99_response_time": f"{self.p99_response_time:.2f}ms",
            "min_response_time": f"{min(self.response_times):.2f}ms" if self.response_times else "N/A",
            "max_response_time": f"{max(self.response_times):.2f}ms" if self.response_times else "N/A",
        }


class LoadTester:
    """Load tester for API endpoints."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: Dict[str, LoadTestResult] = {}

    def get_result(self, endpoint: str) -> LoadTestResult:
        """Get or create result for endpoint."""
        if endpoint not in self.results:
            self.results[endpoint] = LoadTestResult()
        return self.results[endpoint]

    async def test_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        num_requests: int = 100,
        concurrency: int = 10,
        **kwargs
    ) -> LoadTestResult:
        """Run load test on an endpoint."""
        result = self.get_result(endpoint)
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            semaphore = asyncio.Semaphore(concurrency)

            async def make_request():
                async with semaphore:
                    start = time.time()
                    try:
                        if method.upper() == "GET":
                            response = await client.get(url, **kwargs)
                        elif method.upper() == "POST":
                            response = await client.post(url, **kwargs)
                        else:
                            raise ValueError(f"Unsupported method: {method}")

                        elapsed = (time.time() - start) * 1000  # Convert to ms
                        is_success = response.status_code in [200, 500]  # 500 OK for no gateway
                        error = None if is_success else f"Status {response.status_code}"

                        result.add_response(elapsed, is_success, error)
                    except Exception as e:
                        elapsed = (time.time() - start) * 1000
                        result.add_response(elapsed, False, str(e))

            # Create tasks
            tasks = [make_request() for _ in range(num_requests)]
            await asyncio.gather(*tasks)

        return result

    async def run_concurrent_test(
        self,
        endpoints: List[Dict[str, Any]],
        total_users: int = 100,
        spawn_rate: int = 10,
        run_time: int = 60
    ) -> Dict[str, LoadTestResult]:
        """Run concurrent test with multiple endpoints."""
        start_time = time.time()
        tasks_remaining = total_users

        while tasks_remaining > 0 and (time.time() - start_time) < run_time:
            # Spawn batch of users
            batch_size = min(spawn_rate, tasks_remaining)

            for endpoint_config in endpoints:
                endpoint = endpoint_config["endpoint"]
                method = endpoint_config.get("method", "GET")
                num_requests = batch_size // len(endpoints)

                asyncio.create_task(
                    self.test_endpoint(
                        endpoint,
                        method,
                        num_requests=num_requests,
                        **endpoint_config.get("kwargs", {})
                    )
                )

            tasks_remaining -= batch_size
            await asyncio.sleep(1.0)  # Wait before next batch

        # Wait for all tasks to complete
        await asyncio.sleep(2)

        return self.results

    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*80)
        print("LOAD TEST SUMMARY")
        print("="*80)

        for endpoint, result in self.results.items():
            print(f"\nEndpoint: {endpoint}")
            print("-" * 60)
            summary = result.summary()
            for key, value in summary.items():
                print(f"  {key}: {value}")

        print("\n" + "="*80)


async def run_performance_tests(base_url: str = "http://localhost:8000"):
    """Run all performance tests."""
    tester = LoadTester(base_url)

    print("="*80)
    print("PERFORMANCE TESTS - Smart Lamp API")
    print("="*80)
    print(f"Target URL: {base_url}")
    print()

    # Test 1: Health endpoint (should be fastest)
    print("Test 1: Health endpoint (100 requests)")
    await tester.test_endpoint("/api/v1/health", "GET", num_requests=100)

    # Test 2: Get all lamps
    print("\nTest 2: Get all lamps (100 requests)")
    await tester.test_endpoint("/api/v1/lamps", "GET", num_requests=100)

    # Test 3: Get gateway status
    print("\nTest 3: Get gateway status (100 requests)")
    await tester.test_endpoint("/api/v1/gateway", "GET", num_requests=100)

    # Test 4: Turn lamp on (POST)
    print("\nTest 4: Turn lamp on (50 requests)")
    await tester.test_endpoint(
        "/api/v1/lamps/1/on",
        "POST",
        num_requests=50,
        json={"red": 255, "green": 200, "blue": 100, "intensity": 200}
    )

    # Print summary
    tester.print_summary()

    return tester.results


if __name__ == "__main__":
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    asyncio.run(run_performance_tests(base_url))
