from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request, status


@dataclass
class RateWindow:
    count: int
    reset_at: float


class InMemoryRateLimiter:
    """Fixed-window protection for a single API instance."""

    def __init__(
        self,
        clock: Callable[[], float] = monotonic,
        window_seconds: int = 60,
        max_keys: int = 10_000,
    ) -> None:
        self._clock = clock
        self._window_seconds = window_seconds
        self._max_keys = max_keys
        self._windows: dict[tuple[str, str], RateWindow] = {}
        self._lock = Lock()

    def consume(self, category: str, subject: str, limit: int) -> int | None:
        now = self._clock()
        key = (category, subject)
        with self._lock:
            window = self._windows.get(key)
            if window is None or now >= window.reset_at:
                self._prune(now)
                self._windows[key] = RateWindow(1, now + self._window_seconds)
                return None
            if window.count >= limit:
                return max(1, int(window.reset_at - now) + 1)
            window.count += 1
            return None

    def clear(self) -> None:
        with self._lock:
            self._windows.clear()

    def _prune(self, now: float) -> None:
        if len(self._windows) < self._max_keys:
            return
        expired = [key for key, window in self._windows.items() if now >= window.reset_at]
        for key in expired:
            self._windows.pop(key, None)
        if len(self._windows) >= self._max_keys:
            oldest = min(self._windows, key=lambda key: self._windows[key].reset_at)
            self._windows.pop(oldest, None)


rate_limiter = InMemoryRateLimiter()


def client_ip(request: Request) -> str:
    return request.client.host if request.client is not None else "unknown"


def enforce_rate_limit(request: Request, category: str, subject: str, limit: int) -> None:
    retry_after = rate_limiter.consume(category, subject, limit)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Request rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )
