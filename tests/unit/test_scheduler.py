"""Unit tests cho scheduler và dedup/backoff."""

from __future__ import annotations

from datetime import datetime, timezone

from news_ingestor.crawlers.scheduler import BoLichThuThap
from news_ingestor.models.article import BaiBaoTho


class TestBoLichThuThap:
    """Tests cho cơ chế scheduler."""

    def test_backoff(self):
        assert BoLichThuThap._tinh_backoff_giay(900, 0) == 900
        assert BoLichThuThap._tinh_backoff_giay(900, 1) == 1800
        assert BoLichThuThap._tinh_backoff_giay(900, 2) == 3600
        assert BoLichThuThap._tinh_backoff_giay(900, 5) <= 7200

    def test_dedup_url_or_title(self):
        scheduler = BoLichThuThap()

        class CrawlerGia:
            ten_nguon = "gia"

            def thu_thap(self):
                return [
                    BaiBaoTho(
                        tieu_de="Tin A",
                        noi_dung="",
                        url="https://example.com/a?utm_source=x",
                        nguon_tin="T1",
                        thoi_gian_xuat_ban=datetime.now(tz=timezone.utc),
                    ),
                    BaiBaoTho(
                        tieu_de="Tin B",
                        noi_dung="",
                        url="https://example.com/a",
                        nguon_tin="T2",
                        thoi_gian_xuat_ban=datetime.now(tz=timezone.utc),
                    ),
                    BaiBaoTho(
                        tieu_de="Tin A",
                        noi_dung="",
                        url="https://example.com/c",
                        nguon_tin="T3",
                        thoi_gian_xuat_ban=datetime.now(tz=timezone.utc),
                    ),
                ]

            def dong(self):
                return None

        scheduler.dang_ky_crawler(CrawlerGia())
        ket_qua = scheduler.chay_mot_lan()
        assert len(ket_qua) == 1
