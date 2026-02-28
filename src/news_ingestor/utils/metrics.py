"""In-process metrics counters for observability."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from threading import Lock
from typing import Any


class BoDemMetrics:
    """Lightweight thread-safe metrics registry."""

    def __init__(self):
        self._lock = Lock()
        self._counter = Counter()
        self._started_at = datetime.now(tz=timezone.utc)

    def tang(self, ten: str, gia_tri: int = 1) -> None:
        with self._lock:
            self._counter[ten] += gia_tri

    def gan(self, ten: str, gia_tri: int) -> None:
        with self._lock:
            self._counter[ten] = gia_tri

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "started_at": self._started_at.isoformat(),
                "counters": dict(self._counter),
            }


_metrics = BoDemMetrics()


def lay_metrics() -> BoDemMetrics:
    """Get singleton metrics registry."""
    return _metrics
