"""Base Crawler - Lớp trừu tượng cho tất cả bộ thu thập dữ liệu."""

from __future__ import annotations

import logging
import random
import time
from abc import ABC, abstractmethod
from typing import Optional

import httpx

from news_ingestor.models.article import BaiBaoTho

logger = logging.getLogger(__name__)

# Danh sách User-Agent luân phiên để tránh bị chặn
DANH_SACH_USER_AGENT = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
]


class BaseCrawler(ABC):
    """Lớp trừu tượng cơ sở cho bộ thu thập tin tức.

    Cung cấp:
    - HTTP client với retry và rate limiting
    - Luân phiên User-Agent
    - Xử lý lỗi thống nhất
    """

    def __init__(
        self,
        ten_nguon: str,
        timeout: int = 30,
        so_lan_thu_lai: int = 3,
        do_tre_giua_request: float = 1.0,
    ):
        self.ten_nguon = ten_nguon
        self._timeout = timeout
        self._so_lan_thu_lai = so_lan_thu_lai
        self._do_tre = do_tre_giua_request
        self._client: Optional[httpx.Client] = None

    def _tao_client(self) -> httpx.Client:
        """Tạo HTTP client với cấu hình phù hợp."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(
                timeout=self._timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": random.choice(DANH_SACH_USER_AGENT),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                },
            )
        return self._client

    def gui_request(self, url: str) -> Optional[str]:
        """Gửi HTTP GET request với retry logic.

        Returns:
            Nội dung response dạng text, hoặc None nếu thất bại.
        """
        client = self._tao_client()

        for lan_thu in range(1, self._so_lan_thu_lai + 1):
            try:
                # Luân phiên User-Agent mỗi lần thử
                client.headers["User-Agent"] = random.choice(DANH_SACH_USER_AGENT)

                response = client.get(url)
                response.raise_for_status()

                logger.debug(
                    f"Request thành công: {url}",
                    extra={"extra_fields": {"status_code": response.status_code}},
                )

                # Rate limiting: chờ ngẫu nhiên giữa các request
                time.sleep(self._do_tre * random.uniform(0.5, 1.5))

                return response.text

            except httpx.TimeoutException:
                logger.warning(
                    f"Timeout lần {lan_thu}/{self._so_lan_thu_lai}: {url}"
                )
            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"HTTP Error {e.response.status_code} lần {lan_thu}: {url}"
                )
                if e.response.status_code == 429:  # Rate limited
                    thoi_gian_cho = 2 ** lan_thu + random.uniform(0, 1)
                    logger.info(f"Rate limited, chờ {thoi_gian_cho:.1f}s...")
                    time.sleep(thoi_gian_cho)
            except Exception as e:
                logger.error(
                    f"Lỗi không xác định lần {lan_thu}: {e}"
                )

            if lan_thu < self._so_lan_thu_lai:
                thoi_gian_cho = lan_thu * 2 + random.uniform(0, 1)
                time.sleep(thoi_gian_cho)

        logger.error(f"Thất bại sau {self._so_lan_thu_lai} lần thử: {url}")
        return None

    @abstractmethod
    def thu_thap(self) -> list[BaiBaoTho]:
        """Thu thập tin tức từ nguồn. Phải được override bởi lớp con."""
        ...

    def dong(self) -> None:
        """Đóng HTTP client."""
        if self._client and not self._client.is_closed:
            self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.dong()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} nguon='{self.ten_nguon}'>"
