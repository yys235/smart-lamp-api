"""Performance tests for Smart Lamp API using Locust."""

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import time


class LampUser(HttpUser):
    """Simulated user interacting with lamp control endpoints."""

    # Wait time between tasks (1-3 seconds)
    wait_time = between(1, 3)

    def on_start(self):
        """Run when user starts."""
        # Check health endpoint
        self.client.get("/api/v1/health")

    @task(3)
    def get_all_lamps(self):
        """Get all lamps (most common operation)."""
        with self.client.get("/api/v1/lamps", catch_response=True, name="GET /api/v1/lamps") as response:
            # Accept 200 or 500 (no gateway)
            if response.status_code not in [200, 500]:
                response.failure(f"Got status {response.status_code}")

    @task(2)
    def get_gateway_status(self):
        """Get gateway status."""
        self.client.get("/api/v1/gateway")

    @task(1)
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/api/v1/health")

    @task(1)
    def get_logs(self):
        """Get operation logs."""
        self.client.get("/api/v1/logs?limit=10")


class AdminUser(HttpUser):
    """Admin user performing control operations."""

    wait_time = between(2, 5)

    def on_start(self):
        """Run when admin user starts."""
        self.device_id = 1  # Default test device ID

    @task(3)
    def turn_lamp_on(self):
        """Turn on a lamp."""
        self.client.post(
            f"/api/v1/lamps/{self.device_id}/on",
            json={"red": 255, "green": 200, "blue": 100, "intensity": 200}
        )

    @task(2)
    def turn_lamp_off(self):
        """Turn off a lamp."""
        self.client.post(f"/api/v1/lamps/{self.device_id}/off")

    @task(1)
    def get_lamp_status(self):
        """Get specific lamp status."""
        self.client.get(f"/api/v1/lamps/{self.device_id}")


# Event handlers for statistics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Custom request event handler."""
    if exception:
        print(f"Request failed: {name} - {exception}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Run when test stops."""
    print("\n" + "="*60)
    print("Performance Test Summary")
    print("="*60)

    if isinstance(environment.runner, MasterRunner):
        print("Master runner statistics:")
    else:
        print(f"Total requests: {environment.stats.total.num_requests}")
        print(f"Failures: {environment.stats.total.num_failures}")
        print(f"Success rate: {(environment.stats.total.num_requests - environment.stats.total.num_failures) / max(environment.stats.total.num_requests, 1) * 100:.1f}%")
