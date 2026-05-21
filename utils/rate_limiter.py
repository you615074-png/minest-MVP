import time
import os


class RateLimiter:
    def __init__(self, calls_per_minute: int = 20):
        interval_ms = 60_000 / max(calls_per_minute, 1)
        self.interval = interval_ms / 1000
        self.last_call = 0.0

    def wait(self):
        elapsed = time.time() - self.last_call
        wait_time = self.interval - elapsed
        if wait_time > 0:
            time.sleep(wait_time)
        self.last_call = time.time()


def get_rate_limiter() -> RateLimiter:
    rpm = int(os.getenv("RATE_LIMIT_RPM", "20"))
    return RateLimiter(calls_per_minute=rpm)
