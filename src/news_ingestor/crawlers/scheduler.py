"""Scheduler - Bộ lập lịch tự động chạy crawlers theo chu kỳ."""

from __future__ import annotations

import logging
from collections.abc import Callable

from news_ingestor.crawlers.base import BaseCrawler
from news_ingestor.crawlers.cafef import CafeFCrawler
from news_ingestor.crawlers.rss_crawler import RSSCrawler
from news_ingestor.crawlers.vietstock import VietStockCrawler
from news_ingestor.crawlers.vnexpress import VnExpressCrawler
from news_ingestor.models.article import BaiBaoTho

logger = logging.getLogger(__name__)


class BoLichThuThap:
    """Quản lý và điều phối các bộ thu thập dữ liệu.

    Hỗ trợ:
    - Chạy tất cả crawlers một lần (run_once)
    - Chạy daemon với khoảng cách có thể cấu hình
    - Callback sau mỗi lần thu thập
    """

    def __init__(self):
        self._crawlers: list[BaseCrawler] = []
        self._callback: Callable[[list[BaiBaoTho]], None] | None = None

    def dang_ky_tat_ca(self) -> None:
        """Đăng ký tất cả crawlers mặc định."""
        self._crawlers = [
            RSSCrawler(),
            CafeFCrawler(),
            VnExpressCrawler(),
            VietStockCrawler(),
        ]
        logger.info(
            f"Đã đăng ký {len(self._crawlers)} bộ thu thập",
            extra={"extra_fields": {
                "crawlers": [c.ten_nguon for c in self._crawlers]
            }},
        )

    def dang_ky_crawler(self, crawler: BaseCrawler) -> None:
        """Thêm một crawler vào danh sách."""
        self._crawlers.append(crawler)

    def dat_callback(self, callback: Callable[[list[BaiBaoTho]], None]) -> None:
        """Đặt hàm callback được gọi sau mỗi lần thu thập.

        Callback nhận danh sách bài báo thô để xử lý tiếp.
        """
        self._callback = callback

    def chay_mot_lan(self) -> list[BaiBaoTho]:
        """Chạy tất cả crawlers một lần và trả về kết quả tổng hợp."""
        tat_ca_tin: list[BaiBaoTho] = []

        for crawler in self._crawlers:
            try:
                logger.info(f"═══ Bắt đầu thu thập: {crawler.ten_nguon} ═══")
                tin = crawler.thu_thap()
                tat_ca_tin.extend(tin)
                logger.info(
                    f"═══ Hoàn thành {crawler.ten_nguon}: {len(tin)} bài ═══"
                )
            except Exception as e:
                logger.error(
                    f"Lỗi crawler {crawler.ten_nguon}: {e}",
                    exc_info=True,
                )

        # Loại bỏ trùng lặp theo URL chuẩn hóa hoặc hash tiêu đề
        da_thay_url: set[str] = set()
        da_thay_tieu_de: set[str] = set()
        khong_trung: list[BaiBaoTho] = []
        for bai in tat_ca_tin:
            if bai.url_chuan_hoa in da_thay_url or bai.tieu_de_hash in da_thay_tieu_de:
                continue
            da_thay_url.add(bai.url_chuan_hoa)
            da_thay_tieu_de.add(bai.tieu_de_hash)
            khong_trung.append(bai)

        da_loai = len(tat_ca_tin) - len(khong_trung)
        logger.info(
            f"Tổng kết thu thập: {len(khong_trung)} bài "
            f"(đã loại {da_loai} trùng lặp)",
            extra={"extra_fields": {
                "tong_thu_thap": len(tat_ca_tin),
                "sau_loai_trung": len(khong_trung),
            }},
        )

        # Gọi callback nếu có
        if self._callback and khong_trung:
            try:
                self._callback(khong_trung)
            except Exception as e:
                logger.error(f"Lỗi callback: {e}", exc_info=True)

        return khong_trung

    def chay_daemon(self, khoang_cach_giay: int = 900) -> None:
        """Chạy thu thập theo chu kỳ (blocking) với retry/backoff.

        Args:
            khoang_cach_giay: Khoảng cách giữa các lần chạy (mặc định 15 phút).
        """
        import time

        logger.info(
            f"Khởi động chế độ daemon - chu kỳ {khoang_cach_giay}s "
            f"({khoang_cach_giay // 60} phút)"
        )

        so_lan_loi_lien_tiep = 0

        while True:
            try:
                self.chay_mot_lan()
                so_lan_loi_lien_tiep = 0
            except KeyboardInterrupt:
                logger.info("Nhận tín hiệu dừng, đang thoát...")
                break
            except Exception as e:
                so_lan_loi_lien_tiep += 1
                logger.error(f"Lỗi trong chu kỳ daemon: {e}", exc_info=True)

            thoi_gian_cho = self._tinh_backoff_giay(
                khoang_cach_co_so=khoang_cach_giay,
                so_lan_loi_lien_tiep=so_lan_loi_lien_tiep,
            )

            if so_lan_loi_lien_tiep > 0:
                logger.warning(
                    f"Đang backoff do lỗi liên tiếp ({so_lan_loi_lien_tiep}): chờ {thoi_gian_cho}s"
                )
            else:
                logger.info(f"Chờ {thoi_gian_cho}s đến chu kỳ tiếp theo...")

            try:
                time.sleep(thoi_gian_cho)
            except KeyboardInterrupt:
                logger.info("Nhận tín hiệu dừng, đang thoát...")
                break

    @staticmethod
    def _tinh_backoff_giay(khoang_cach_co_so: int, so_lan_loi_lien_tiep: int) -> int:
        """Tính thời gian chờ chu kỳ kế tiếp với exponential backoff có giới hạn."""
        if so_lan_loi_lien_tiep <= 0:
            return khoang_cach_co_so

        he_so = min(2 ** min(so_lan_loi_lien_tiep, 5), 32)
        return min(khoang_cach_co_so * he_so, 7200)

    def dong_tat_ca(self) -> None:
        """Đóng tất cả crawlers."""
        for crawler in self._crawlers:
            try:
                crawler.dong()
            except Exception:
                pass
