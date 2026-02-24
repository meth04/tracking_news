from __future__ import annotations

from datetime import datetime, timedelta, timezone


def prune_events(events: list[dict[str, object]], max_age_minutes: int) -> list[dict[str, object]]:
    cutoff = datetime.now(tz=timezone.utc) - timedelta(minutes=max_age_minutes)
    kept: list[dict[str, object]] = []
    for event in events:
        published = event.get("published_at")
        if isinstance(published, datetime) and published >= cutoff:
            kept.append(event)
    return kept
