"""Minimal in-process sliding-window rate limiter.

Per-process only (no Redis). Documented limitation: in multi-replica deployments,
platform-level or API-provider limits should be used instead. See DECISIONS.md.
"""

import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._windows: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, limit: int, window_seconds: float = 60.0) -> bool:
        now = time.monotonic()
        window = self._windows[key]
        while window and now - window[0] > window_seconds:
            window.popleft()
        if len(window) >= limit:
            return False
        window.append(now)
        return True


limiter = SlidingWindowLimiter()
