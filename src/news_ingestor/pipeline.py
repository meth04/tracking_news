from __future__ import annotations

import json
import logging
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Protocol, cast

from news_ingestor.feeds import parse_feed
from news_ingestor.matching import match_companies
from news_ingestor.retention import prune_events
from news_ingestor.taxonomy import classify

logger = logging.getLogger(__name__)


class Output(Protocol):
    def send(self, event: dict[str, object]) -> None: ...
    def flush(self, timeout: float = 5.0) -> None: ...


def fetch_feed(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310
        return cast(bytes, response.read()).decode("utf-8")


def enrich_events(events: list[dict[str, object]], companies: list[str]) -> list[dict[str, object]]:
    enriched: list[dict[str, object]] = []
    for event in events:
        text = f"{event['title']} {event['summary']}"
        taxonomy = classify(text)
        event["companies"] = match_companies(text, companies)
        event["taxonomy"] = taxonomy.label
        event["score"] = taxonomy.score
        event["rumor"] = taxonomy.rumor
        enriched.append(event)
    return enriched


def run_once(feed_urls: list[str], companies: list[str], output: Output) -> int:
    total = 0
    for url in feed_urls:
        raw = fetch_feed(url)
        events = enrich_events(parse_feed(raw), companies)
        for event in events:
            output.send(event)
            total += 1
    output.flush()
    logger.info("published events", extra={"extra_fields": {"count": total}})
    return total


def run_backfill(feed_urls: list[str], companies: list[str], output: Output, minutes: int) -> int:
    total = 0
    cutoff = datetime.now(tz=timezone.utc) - timedelta(minutes=minutes)
    for url in feed_urls:
        raw = fetch_feed(url)
        events = enrich_events(parse_feed(raw), companies)
        for event in events:
            published = event["published_at"]
            if isinstance(published, datetime) and published >= cutoff:
                output.send(event)
                total += 1
    output.flush()
    return total


def run_daemon(
    feed_urls: list[str], companies: list[str], output: Output, interval_seconds: int
) -> None:
    while True:
        run_once(feed_urls, companies, output)
        time.sleep(interval_seconds)


def load_companies(path: str) -> list[str]:
    with open(path, encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def load_feed_urls(path: str) -> list[str]:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    urls = data.get("feed_urls", [])
    return [str(url) for url in urls]


def apply_retention(events: list[dict[str, object]], minutes: int) -> list[dict[str, object]]:
    return prune_events(events, minutes)
