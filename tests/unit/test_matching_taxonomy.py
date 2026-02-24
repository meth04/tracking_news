from __future__ import annotations

from news_ingestor.matching import match_companies
from news_ingestor.taxonomy import classify


def test_company_matching_vietnamese_diacritics() -> None:
    text = "Cong ty co phan FPT va Ngan hang Vietcombank"
    companies = ["FPT", "Vietcombank", "Vinamilk"]
    assert match_companies(text, companies) == ["FPT", "Vietcombank"]


def test_taxonomy_scoring_determinism() -> None:
    text = "record profit growth"
    assert classify(text) == classify(text)


def test_rumor_heuristic() -> None:
    result = classify("This is a rumor from anonymous source about loss")
    assert result.rumor is True
    assert result.score <= 0
