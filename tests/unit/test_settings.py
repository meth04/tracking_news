"""Unit tests cho validation của config settings."""

from __future__ import annotations

import pytest

from config.settings import (
    CauHinhCrawler,
    CauHinhDatabase,
    CauHinhHeThong,
    CauHinhNLP,
    CauHinhQdrant,
)


class TestSettingsValidation:
    """Kiểm tra các ràng buộc và default an toàn."""

    def test_database_url_hop_le(self):
        cfg = CauHinhDatabase(DATABASE_URL="sqlite+aiosqlite:///./data/test.db")
        assert cfg.url.startswith("sqlite+")

    def test_database_url_khong_hop_le(self):
        with pytest.raises(ValueError):
            CauHinhDatabase(DATABASE_URL="mysql://localhost/db")

    def test_qdrant_url_phai_http(self):
        with pytest.raises(ValueError):
            CauHinhQdrant(QDRANT_URL="localhost:6333")

    def test_embedding_model_khong_rong(self):
        with pytest.raises(ValueError):
            CauHinhNLP(EMBEDDING_MODEL="")

    def test_crawler_ranges(self):
        with pytest.raises(ValueError):
            CauHinhCrawler(CRAWL_INTERVAL_MINUTES=0)
        with pytest.raises(ValueError):
            CauHinhCrawler(REQUEST_TIMEOUT=1)
        with pytest.raises(ValueError):
            CauHinhCrawler(MAX_RETRIES=11)

    def test_log_level_validate(self):
        cfg = CauHinhHeThong(LOG_LEVEL="warning")
        assert cfg.log_level == "WARNING"

        with pytest.raises(ValueError):
            CauHinhHeThong(LOG_LEVEL="TRACE")
