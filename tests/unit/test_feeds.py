from __future__ import annotations

from pathlib import Path

from news_ingestor.feeds import parse_feed, stable_event_id

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_rss_parsing_fixture() -> None:
    items = parse_feed((FIXTURES / "sample_rss.xml").read_text(encoding="utf-8"))
    assert len(items) == 1
    assert items[0]["source"] == "VN Finance RSS"


def test_atom_parsing_fixture() -> None:
    items = parse_feed((FIXTURES / "sample_atom.xml").read_text(encoding="utf-8"))
    assert len(items) == 1
    assert items[0]["title"].startswith("Vingroup")


def test_event_id_stability() -> None:
    one = stable_event_id("S", "Title", "https://x", "2024-01-01")
    two = stable_event_id(" S ", "title", "https://x", "2024-01-01")
    assert one == two
