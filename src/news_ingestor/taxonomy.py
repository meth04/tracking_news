from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaxonomyResult:
    label: str
    score: float
    rumor: bool


POSITIVE = {"profit", "growth", "record", "upgrade"}
NEGATIVE = {"loss", "fraud", "downgrade", "bankrupt"}
RUMOR = {"rumor", "unverified", "anonymous source", "tin don"}


def classify(text: str) -> TaxonomyResult:
    lowered = text.lower()
    pos = sum(1 for token in POSITIVE if token in lowered)
    neg = sum(1 for token in NEGATIVE if token in lowered)
    rumor = any(token in lowered for token in RUMOR)

    if pos > neg:
        label = "positive"
    elif neg > pos:
        label = "negative"
    else:
        label = "neutral"

    score = max(min((pos - neg) / 4, 1.0), -1.0)
    if rumor:
        score *= 0.5
    return TaxonomyResult(label=label, score=round(score, 4), rumor=rumor)
