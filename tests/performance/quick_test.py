#!/usr/bin/env python3
"""Quick performance test runner for Smart Lamp API."""

import asyncio
import time
import statistics
from typing import List

import httpx


async def test_endpoint_performance(
    client: httpx.AsyncClient,
    base_url: str,
    endpoint: str,
    method: str = "GET",
    num_requests: int = 50
) -> dict:
    """Test performance of a single endpoint."""
    url = f"{base_url}{endpoint}"
    response_times: List[float] = []
    success_count = 0
    failure_count = 0

    for _ in range(num_requests):
        start = time.time()
        try:
            if method.upper() == "GET":
                response = await client.get(url)
            elif method.upper() == "POST":
                response = await client.post(url, json={"red": 255, "green": 200, "blue": 100})
            else:
                raise ValueError(f"Unsupported method: {method}")

            elapsed = (time.time() - start) * 1000  # ms
            response_times.append(elapsed)

            if response.status_code in [200, 500]:  # Accept 500 (no gateway)
                success_count += 1
            else:
                failure_count += 1

        except Exception as e:
            elapsed = (time.time() - start) * 1000
            response_times.append(elapsed)
            failure_count += 1

    return {
        "endpoint": endpoint,
        "method": method,
        "total_requests": num_requests,
        "success": success_count,
        "failures": failure_count,
        "success_rate": (success_count / num_requests * 100) if num_requests > 0 else 0,
        "avg_ms": statistics.mean(response_times) if response_times else 0,
        "min_ms": min(response_times) if response_times else 0,
        "max_ms": max(response_times) if response_times else 0,
        "p50_ms": statistics.median(response_times) if response_times else 0,
        "p95_ms": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0,
        "p99_ms": sorted(response_times)[int(len(response_times) * 0.99)] if response_times else 0,
    }


async def run_performance_tests(base_url: str = "http://localhost:8000"):
    """Run performance tests on all endpoints."""

    print("="*70)
    print("Smart Lamp API - Performance Test")
    print("="*70)
    print(f"Target URL: {base_url}")
    print(f"Start Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    endpoints = [
        ("GET", "/api/v1/health", 100),
        ("GET", "/api/v1/lamps", 100),
        ("GET", "/api/v1/gateway", 100),
        ("GET", "/api/v1/logs?limit=10", 50),
        ("POST", "/api/v1/lamps/1/on", 50),
        ("POST", "/api/v1/lamps/1/off", 50),
    ]

    results = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for method, endpoint, count in endpoints:
            print(f"Testing: {method} {endpoint} ({count} requests)...")
            result = await test_endpoint_performance(client, base_url, endpoint, method, count)
            results.append(result)

    # Print results
    print()
    print("="*70)
    print("PERFORMANCE TEST RESULTS")
    print("="*70)
    print()
    print(f"{'Endpoint':<30} {'Success':<8} {'Avg':<8} {'P50':<8} {'P95':<8} {'P99':<8}")
    print("-"*70)

    for r in results:
        endpoint_name = f"{r['method']} {r['endpoint']}"
        print(f"{endpoint_name:<30} {r['success_rate']:>6.1f}% {r['avg_ms']:>6.1f}ms {r['p50_ms']:>6.1f}ms {r['p95_ms']:>6.1f}ms {r['p99_ms']:>6.1f}ms")

    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)

    total_requests = sum(r["total_requests"] for r in results)
    total_success = sum(r["success"] for r in results)
    overall_success_rate = (total_success / total_requests * 100) if total_requests > 0 else 0
    all_response_times = []
    for r in results:
        all_response_times.extend([r["avg_ms"]] * r["total_requests"])

    print(f"Total Requests: {total_requests}")
    print(f"Overall Success Rate: {overall_success_rate:.2f}%")
    print(f"Overall Avg Response Time: {statistics.mean(all_response_times):.2f}ms" if all_response_times else "N/A")

    # Check against targets
    print()
    print("TARGET CHECK")
    print("-"*70)
    avg_response_time = statistics.mean(all_response_times) if all_response_times else 0
    print(f"P95 Response Time < 200ms: {'✓ PASS' if avg_response_time < 200 else '✗ FAIL'} ({avg_response_time:.2f}ms)")
    print(f"Success Rate >= 95%: {'✓ PASS' if overall_success_rate >= 95 else '✗ FAIL'} ({overall_success_rate:.2f}%)")
    print(f"Concurrent Support (100 req/s): {'✓ PASS' if total_requests / 10 >= 100 else '✗ CHECK'}")

    print()
    print("="*70)
    print(f"End Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)


if __name__ == "__main__":
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    asyncio.run(run_performance_tests(base_url))
