"""RSS/Atom Feed Crawler - Bộ thu thập tin tức qua nguồn RSS."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import feedparser

from news_ingestor.crawlers.base import BaseCrawler
from news_ingestor.models.article import BaiBaoTho
from news_ingestor.utils.text_utils import chuan_hoa_khoang_trang, loai_bo_html

logger = logging.getLogger(__name__)


class RSSCrawler(BaseCrawler):
    """Crawler tổng quát cho nguồn RSS/Atom feed.

    Đọc danh sách nguồn từ config/feeds.json và thu thập tin từ tất cả.
    """

    def __init__(
        self,
        duong_dan_config: str = "config/feeds.json",
        timeout: int = 30,
    ):
        super().__init__(
            ten_nguon="RSS Tổng hợp",
            timeout=timeout,
            do_tre_giua_request=0.5,
        )
        self._duong_dan_config = duong_dan_config
        self._nguon_feeds = self._doc_cau_hinh()

    def _doc_cau_hinh(self) -> list[dict]:
        """Đọc danh sách nguồn RSS từ file config."""
        try:
            duong_dan = Path(self._duong_dan_config)
            if not duong_dan.exists():
                logger.warning(f"Không tìm thấy file cấu hình: {self._duong_dan_config}")
                return []

            with open(duong_dan, encoding="utf-8") as f:
                data = json.load(f)

            nguon = data.get("nguon_rss", [])
            logger.info(f"Đã tải {len(nguon)} nguồn RSS từ cấu hình")
            return nguon
        except Exception as e:
            logger.error(f"Lỗi đọc cấu hình RSS: {e}")
            return []

    def thu_thap(self) -> list[BaiBaoTho]:
        """Thu thập tin tức từ tất cả nguồn RSS đã cấu hình."""
        tat_ca_tin = []

        for nguon in self._nguon_feeds:
            try:
                ten = nguon.get("ten", "Không rõ")
                url = nguon.get("url", "")
                danh_muc = nguon.get("danh_muc", "MACRO")

                if not url:
                    continue

                logger.info(f"Thu thập RSS: {ten}")
                tin_moi = self._thu_thap_feed(url, ten, danh_muc)
                tat_ca_tin.extend(tin_moi)
                logger.info(
                    f"  → Thu được {len(tin_moi)} bài từ {ten}",
                    extra={"extra_fields": {"nguon": ten, "so_bai": len(tin_moi)}},
                )

            except Exception as e:
                logger.error(f"Lỗi thu thập từ {nguon.get('ten', '?')}: {e}")

        logger.info(f"Tổng cộng: {len(tat_ca_tin)} bài từ {len(self._nguon_feeds)} nguồn RSS")
        return tat_ca_tin

    def _thu_thap_feed(self, url: str, ten_nguon: str, danh_muc: str) -> list[BaiBaoTho]:
        """Thu thập tin từ một feed RSS/Atom cụ thể."""
        noi_dung = self.gui_request(url)
        if not noi_dung:
            return []

        feed = feedparser.parse(noi_dung)
        danh_sach = []

        for entry in feed.entries:
            try:
                bai_bao = self._phan_tich_entry(entry, ten_nguon)
                if bai_bao:
                    danh_sach.append(bai_bao)
            except Exception as e:
                logger.debug(f"Bỏ qua entry lỗi: {e}")

        return danh_sach

    def _phan_tich_entry(
        self, entry: dict, ten_nguon: str
    ) -> BaiBaoTho | None:
        """Phân tích một entry RSS thành BaiBaoTho."""
        tieu_de = getattr(entry, "title", "")
        if not tieu_de:
            return None

        # Lấy nội dung tóm tắt
        noi_dung = ""
        if hasattr(entry, "summary"):
            noi_dung = entry.summary
        elif hasattr(entry, "description"):
            noi_dung = entry.description
        elif hasattr(entry, "content") and entry.content:
            noi_dung = entry.content[0].get("value", "")

        # Làm sạch HTML
        tieu_de = loai_bo_html(tieu_de)
        noi_dung = loai_bo_html(noi_dung)

        # Lấy URL
        link = getattr(entry, "link", "")
        if not link:
            return None

        # Phân tích thời gian
        thoi_gian = self._phan_tich_thoi_gian(entry)

        return BaiBaoTho(
            tieu_de=chuan_hoa_khoang_trang(tieu_de),
            noi_dung=chuan_hoa_khoang_trang(noi_dung),
            url=link,
            nguon_tin=ten_nguon,
            thoi_gian_xuat_ban=thoi_gian,
        )

    @staticmethod
    def _phan_tich_thoi_gian(entry: dict) -> datetime:
        """Trích xuất và chuẩn hóa thời gian từ RSS entry."""
        for field in ("published_parsed", "updated_parsed"):
            parsed = getattr(entry, field, None)
            if parsed:
                try:
                    from calendar import timegm
                    timestamp = timegm(parsed)
                    return datetime.fromtimestamp(timestamp, tz=timezone.utc)
                except Exception:
                    pass

        # Thử parse chuỗi thô
        for field in ("published", "updated"):
            raw = getattr(entry, field, None)
            if raw:
                try:
                    from dateutil.parser import parse as dateutil_parse
                    dt = dateutil_parse(raw)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt.astimezone(timezone.utc)
                except Exception:
                    pass

        return datetime.now(tz=timezone.utc)
