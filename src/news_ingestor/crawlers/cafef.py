"""CafeF Crawler - Thu thập tin tức từ CafeF.vn."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from bs4 import BeautifulSoup

from news_ingestor.crawlers.base import BaseCrawler
from news_ingestor.models.article import BaiBaoTho
from news_ingestor.utils.text_utils import chuan_hoa_khoang_trang, loai_bo_html

logger = logging.getLogger(__name__)


class CafeFCrawler(BaseCrawler):
    """Bộ thu thập tin tức tài chính từ CafeF.vn.

    Thu thập từ các mục:
    - Chứng khoán
    - Vĩ mô - Đầu tư
    - Doanh nghiệp
    """

    # Các URL mục tin trên CafeF
    DANH_SACH_MUC = [
        {
            "ten": "CafeF - Chứng khoán",
            "url": "https://cafef.vn/thi-truong-chung-khoan.chn",
            "danh_muc": "MICRO",
        },
        {
            "ten": "CafeF - Vĩ mô",
            "url": "https://cafef.vn/vi-mo-dau-tu.chn",
            "danh_muc": "MACRO",
        },
        {
            "ten": "CafeF - Doanh nghiệp",
            "url": "https://cafef.vn/doanh-nghiep.chn",
            "danh_muc": "MICRO",
        },
    ]

    def __init__(self, timeout: int = 30):
        super().__init__(
            ten_nguon="CafeF",
            timeout=timeout,
            so_lan_thu_lai=3,
            do_tre_giua_request=2.0,  # Tôn trọng rate limit
        )

    def thu_thap(self) -> list[BaiBaoTho]:
        """Thu thập tin tức từ tất cả các mục trên CafeF."""
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
        """Thu thập tin tức từ một mục cụ thể trên CafeF."""
        html = self.gui_request(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        danh_sach = []

        # Tìm các thẻ bài viết trên CafeF
        # CafeF sử dụng class "tlitem" cho mỗi bài viết
        bai_viet_elements = soup.select("div.tlitem, li.tlitem, div.box-category-item")

        for element in bai_viet_elements:
            try:
                bai_bao = self._phan_tich_bai_viet(element, ten_nguon)
                if bai_bao:
                    danh_sach.append(bai_bao)
            except Exception as e:
                logger.debug(f"Bỏ qua bài viết lỗi: {e}")

        # Fallback: tìm theo thẻ h3 > a nếu không tìm thấy bằng class
        if not danh_sach:
            danh_sach = self._thu_thap_fallback(soup, ten_nguon)

        return danh_sach

    def _phan_tich_bai_viet(
        self, element: BeautifulSoup, ten_nguon: str
    ) -> Optional[BaiBaoTho]:
        """Phân tích một element HTML thành BaiBaoTho."""
        # Tìm tiêu đề
        tieu_de_el = element.select_one("h3 a, h2 a, a.title, a[title]")
        if not tieu_de_el:
            return None

        tieu_de = tieu_de_el.get_text(strip=True)
        if not tieu_de or len(tieu_de) < 10:
            return None

        # Lấy URL
        link = tieu_de_el.get("href", "")
        if link and not link.startswith("http"):
            link = f"https://cafef.vn{link}"
        if not link:
            return None

        # Lấy tóm tắt
        tom_tat_el = element.select_one("p.sapo, div.sapo, p.summary, span.summary")
        noi_dung = tom_tat_el.get_text(strip=True) if tom_tat_el else ""

        # Lấy thời gian
        thoi_gian_el = element.select_one("span.time, span.date, time")
        thoi_gian = self._phan_tich_thoi_gian_cafef(thoi_gian_el)

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
        """Phương thức dự phòng: tìm bài qua thẻ h3 > a."""
        danh_sach = []

        for link_el in soup.select("h3 a[href], h2 a[href]"):
            tieu_de = link_el.get_text(strip=True)
            href = link_el.get("href", "")

            if not tieu_de or len(tieu_de) < 10:
                continue
            if not href:
                continue
            if not href.startswith("http"):
                href = f"https://cafef.vn{href}"

            # Bỏ qua link không phải bài viết
            if any(skip in href for skip in ["/video/", "/photo/", "javascript:"]):
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
    def _phan_tich_thoi_gian_cafef(element) -> datetime:
        """Phân tích thời gian từ element HTML CafeF."""
        if not element:
            return datetime.now(tz=timezone.utc)

        text = element.get_text(strip=True)
        try:
            from dateutil.parser import parse as dateutil_parse
            dt = dateutil_parse(text, dayfirst=True)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone(offset=__import__("datetime").timedelta(hours=7)))
            return dt.astimezone(timezone.utc)
        except Exception:
            return datetime.now(tz=timezone.utc)
