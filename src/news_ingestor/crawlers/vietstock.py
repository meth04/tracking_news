"""VietStock Crawler - Thu thập tin tức từ VietStock.vn."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from bs4 import BeautifulSoup

from news_ingestor.crawlers.base import BaseCrawler
from news_ingestor.models.article import BaiBaoTho
from news_ingestor.utils.text_utils import chuan_hoa_khoang_trang, loai_bo_html

logger = logging.getLogger(__name__)


class VietStockCrawler(BaseCrawler):
    """Bộ thu thập tin tức từ VietStock.vn."""

    DANH_SACH_MUC = [
        {
            "ten": "VietStock - Chứng khoán",
            "url": "https://vietstock.vn/chung-khoan.htm",
            "danh_muc": "MICRO",
        },
        {
            "ten": "VietStock - Doanh nghiệp",
            "url": "https://vietstock.vn/doanh-nghiep.htm",
            "danh_muc": "MICRO",
        },
        {
            "ten": "VietStock - Tài chính",
            "url": "https://vietstock.vn/tai-chinh.htm",
            "danh_muc": "MACRO",
        },
    ]

    def __init__(self, timeout: int = 30):
        super().__init__(
            ten_nguon="VietStock",
            timeout=timeout,
            so_lan_thu_lai=3,
            do_tre_giua_request=2.0,
        )

    def thu_thap(self) -> list[BaiBaoTho]:
        """Thu thập tin tức từ VietStock."""
        tat_ca_tin = []

        for muc in self.DANH_SACH_MUC:
            try:
                logger.info(f"Thu thập: {muc['ten']}")
                tin = self._thu_thap_muc(muc["url"], muc["ten"])
                tat_ca_tin.extend(tin)
                logger.info(f"  → {len(tin)} bài từ {muc['ten']}")
            except Exception as e:
                logger.error(f"Lỗi thu thập {muc['ten']}: {e}")

        return tat_ca_tin

    def _thu_thap_muc(self, url: str, ten_nguon: str) -> list[BaiBaoTho]:
        """Thu thập từ một mục."""
        html = self.gui_request(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        danh_sach = []

        # VietStock sử dụng class "item" hoặc "news-item"
        bai_viet_elements = soup.select(
            "div.item-news, div.news-item, article.item, div.m-b-15"
        )

        for element in bai_viet_elements:
            try:
                bai_bao = self._phan_tich_bai_viet(element, ten_nguon)
                if bai_bao:
                    danh_sach.append(bai_bao)
            except Exception as e:
                logger.debug(f"Bỏ qua bài VietStock lỗi: {e}")

        # Fallback
        if not danh_sach:
            danh_sach = self._thu_thap_fallback(soup, ten_nguon)

        return danh_sach

    def _phan_tich_bai_viet(
        self, element: BeautifulSoup, ten_nguon: str
    ) -> Optional[BaiBaoTho]:
        """Phân tích element HTML VietStock."""
        tieu_de_el = element.select_one("h3 a, h2 a, a.title, a[title]")
        if not tieu_de_el:
            return None

        tieu_de = tieu_de_el.get_text(strip=True)
        if not tieu_de or len(tieu_de) < 10:
            return None

        link = tieu_de_el.get("href", "")
        if link and not link.startswith("http"):
            link = f"https://vietstock.vn{link}"
        if not link:
            return None

        tom_tat_el = element.select_one("p.summary, div.summary, p.sapo, p.description")
        noi_dung = tom_tat_el.get_text(strip=True) if tom_tat_el else ""

        thoi_gian_el = element.select_one("span.time, span.date, time")
        thoi_gian = self._phan_tich_thoi_gian(thoi_gian_el)

        return BaiBaoTho(
            tieu_de=chuan_hoa_khoang_trang(tieu_de),
            noi_dung=chuan_hoa_khoang_trang(loai_bo_html(noi_dung)),
            url=link,
            nguon_tin=ten_nguon,
            thoi_gian_xuat_ban=thoi_gian,
        )

    def _thu_thap_fallback(
        self, soup: BeautifulSoup, ten_nguon: str
    ) -> list[BaiBaoTho]:
        """Fallback: tìm bài qua h3 > a."""
        danh_sach = []

        for link_el in soup.select("h3 a[href], h2 a[href]"):
            tieu_de = link_el.get_text(strip=True)
            href = link_el.get("href", "")

            if not tieu_de or len(tieu_de) < 10 or not href:
                continue
            if not href.startswith("http"):
                href = f"https://vietstock.vn{href}"
            if any(skip in href for skip in ["/video/", "javascript:", "#"]):
                continue

            danh_sach.append(
                BaiBaoTho(
                    tieu_de=chuan_hoa_khoang_trang(tieu_de),
                    noi_dung="",
                    url=href,
                    nguon_tin=ten_nguon,
                    thoi_gian_xuat_ban=datetime.now(tz=timezone.utc),
                )
            )

        return danh_sach

    @staticmethod
    def _phan_tich_thoi_gian(element) -> datetime:
        """Parse thời gian từ element."""
        if not element:
            return datetime.now(tz=timezone.utc)

        text = element.get_text(strip=True)
        try:
            from dateutil.parser import parse as dateutil_parse
            dt = dateutil_parse(text, dayfirst=True)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return datetime.now(tz=timezone.utc)
