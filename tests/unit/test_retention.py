from __future__ import annotations

from datetime import datetime, timedelta, timezone

from news_ingestor.retention import prune_events


def test_retention_pruning() -> None:
    now = datetime.now(tz=timezone.utc)
    events = [
        {"published_at": now - timedelta(minutes=10)},
        {"published_at": now - timedelta(minutes=120)},
    ]
    kept = prune_events(events, max_age_minutes=60)
    assert len(kept) == 1
