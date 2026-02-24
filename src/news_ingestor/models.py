from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NewsEvent:
    event_id: str
    source: str
    title: str
    link: str
    summary: str
    published_at: datetime
    companies: list[str]
    taxonomy: str
    score: float
    rumor: bool
