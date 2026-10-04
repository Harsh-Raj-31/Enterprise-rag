import time
from collections import defaultdict
from threading import Lock


class RateLimiter:
    """
    Simple in-memory fixed-window rate limiter.

    This is suitable for a single application instance.
    A distributed deployment should use Redis instead.
    """

    def __init__(
        self,
        max_requests: int = 60,
        window_seconds: int = 60,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds

        self._requests = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, client_key: str) -> bool:
        now = time.monotonic()
        window_start = now - self.window_seconds

        with self._lock:
            timestamps = self._requests[client_key]

            # Remove requests outside the current window.
            self._requests[client_key] = [
                timestamp
                for timestamp in timestamps
                if timestamp > window_start
            ]

            timestamps = self._requests[client_key]

            if len(timestamps) >= self.max_requests:
                return False

            timestamps.append(now)
            return True