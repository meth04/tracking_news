from __future__ import annotations

from news_ingestor.feeds import strip_diacritics


def match_companies(text: str, companies: list[str]) -> list[str]:
    haystack = strip_diacritics(text).lower()
    matches: list[str] = []
    for company in companies:
        if strip_diacritics(company).lower() in haystack:
            matches.append(company)
    return sorted(set(matches))
