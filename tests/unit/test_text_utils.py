"""Unit tests cho tiện ích chuẩn hóa URL và hash tiêu đề."""

from __future__ import annotations

from news_ingestor.utils.text_utils import chuan_hoa_url, tao_hash_tieu_de


class TestTextUtilsDedup:
    """Tests cho dedup helpers."""

    def test_chuan_hoa_url_bo_utm(self):
        url = "https://Example.com/news?id=1&utm_source=abc&utm_medium=x"
        assert chuan_hoa_url(url) == "https://example.com/news?id=1"

    def test_chuan_hoa_url_bo_fragment(self):
        url = "https://example.com/news/abc/#section"
        assert chuan_hoa_url(url) == "https://example.com/news/abc"

    def test_hash_tieu_de_on_dinh(self):
        h1 = tao_hash_tieu_de("FPT báo lãi kỷ lục")
        h2 = tao_hash_tieu_de("  fpt báo lãi kỷ lục  ")
        assert h1 == h2
        assert len(h1) == 64
