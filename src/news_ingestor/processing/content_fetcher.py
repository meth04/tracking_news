"""Content Fetcher - Lấy nội dung đầy đủ từ URL bài báo.

Mỗi nguồn tin có cấu trúc HTML khác nhau, module này biết cách
trích xuất body content từ từng trang.
"""

from __future__ import annotations

import logging
import random
import re
import time

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# User-Agent pool
USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
]

# Tags to remove before extracting text
REMOVE_TAGS = {
    "script",
    "style",
    "iframe",
    "nav",
    "footer",
    "header",
    "aside",
    "form",
    "noscript",
    "svg",
}
REMOVE_CLASSES_EXACT = {
    "social-share",
    "share-news",
    "banner",
    "advertisement",
    "related-news",
    "box-comment",
    "comment",
    "tags",
    "tag-list",
    "breadcrumb",
    "author-info",
}
REMOVE_CLASSES_CONTAINS = {"ads-", "ad-slot", "adsbygoogle"}


class ContentFetcher:
    """Lấy nội dung đầy đủ bài báo từ URL gốc.

    Hỗ trợ:
    - VnExpress: article.fck_detail / p.Normal
    - CafeF: div.detail-content
    - VietStock: div.article-content
    - Thanh Niên: div.detail__content
    - Fallback: <article> hoặc largest text block
    """

    # Mapping domain → extraction config
    EXTRACTORS = {
        "vnexpress.net": {
            "body_selectors": ["article.fck_detail", "div.fck_detail"],
            "paragraph_selectors": ["p.Normal"],
            "description_selector": "p.description",
            "remove_selectors": ["div.box-tinlienquan", "div.social-share", "div.box-comment"],
        },
        "cafef.vn": {
            "body_selectors": ["div.detail-content", "div.contentdetail", "div#mainContent"],
            "paragraph_selectors": ["p.Normal"],
            "description_selector": "div.sapo, p.sapo",
            "remove_selectors": ["div.box-related", "div.social", "div.market-overview-detail",
                                 "div.box-ad", "div.link-source-wrapper"],
        },
        "vietstock.vn": {
            "body_selectors": ["div.article-content", "div#content-detail", "div.content-detail"],
            "paragraph_selectors": [],
            "description_selector": "div.article-sapo, p.sapo",
            "remove_selectors": ["div.box-related", "div.social", "div.tags"],
        },
        "thanhnien.vn": {
            "body_selectors": ["div.detail__content", "div.detail-content", "article"],
            "paragraph_selectors": [],
            "description_selector": "div.detail__summary, p.sapo",
            "remove_selectors": ["div.relate-article", "div.social", "div.tags"],
        },
    }

    def __init__(self, timeout: int = 20, delay: float = 1.0):
        self._timeout = timeout
        self._delay = delay
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(
                timeout=self._timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": random.choice(USER_AGENTS),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8",
                    "Connection": "keep-alive",
                },
            )
        return self._client

    def fetch_content(self, url: str) -> dict:
        """Lấy nội dung đầy đủ từ URL bài báo.

        Returns:
            dict with keys:
                - noi_dung_day_du: Full article body text
                - mo_ta: Article description/summary
                - success: Boolean
                - error: Error message if failed
                - char_count: Number of chars in full content
        """
        result = {
            "noi_dung_day_du": "",
            "mo_ta": "",
            "success": False,
            "error": "",
            "char_count": 0,
        }

        if not url or not url.startswith("http"):
            result["error"] = "URL không hợp lệ"
            return result

        try:
            # Rate limiting
            time.sleep(self._delay * random.uniform(0.5, 1.5))

            client = self._get_client()
            client.headers["User-Agent"] = random.choice(USER_AGENTS)
            response = client.get(url)
            response.raise_for_status()

            html = response.text
            soup = BeautifulSoup(html, "lxml")

            # Detect source domain
            domain = self._extract_domain(url)
            config = self._get_extractor_config(domain)

            # Clean: remove unwanted elements
            self._remove_unwanted(soup, config.get("remove_selectors", []))

            # Extract description
            desc_selector = config.get("description_selector", "")
            if desc_selector:
                for sel in desc_selector.split(","):
                    desc_el = soup.select_one(sel.strip())
                    if desc_el:
                        result["mo_ta"] = self._clean_text(desc_el.get_text())
                        break

            # Extract full body content
            body_text = self._extract_body(soup, config)

            if body_text and len(body_text) > 50:
                result["noi_dung_day_du"] = body_text
                result["success"] = True
                result["char_count"] = len(body_text)
            else:
                # Fallback: try generic extraction
                body_text = self._fallback_extract(soup)
                if body_text and len(body_text) > 50:
                    result["noi_dung_day_du"] = body_text
                    result["success"] = True
                    result["char_count"] = len(body_text)
                else:
                    result["error"] = f"Không tìm thấy nội dung (domain={domain})"

            logger.debug(
                f"Fetched {url}: {result['char_count']} chars, success={result['success']}"
            )

        except httpx.HTTPStatusError as e:
            result["error"] = f"HTTP {e.response.status_code}"
            logger.warning(f"HTTP Error fetching {url}: {e.response.status_code}")
        except httpx.TimeoutException:
            result["error"] = "Timeout"
            logger.warning(f"Timeout fetching {url}")
        except Exception as e:
            result["error"] = str(e)[:200]
            logger.error(f"Error fetching {url}: {e}")

        return result

    def _extract_domain(self, url: str) -> str:
        """Trích xuất domain từ URL."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        return domain

    def _get_extractor_config(self, domain: str) -> dict:
        """Lấy cấu hình extractor cho domain."""
        for key, config in self.EXTRACTORS.items():
            if key in domain:
                return config
        return {}

    def _extract_body(self, soup: BeautifulSoup, config: dict) -> str:
        """Trích xuất body content theo cấu hình."""
        # Try body selectors first
        for selector in config.get("body_selectors", []):
            body_el = soup.select_one(selector)
            if body_el:
                # Get text from all paragraphs within body
                paragraphs = body_el.find_all(["p", "h2", "h3", "blockquote"])
                if paragraphs:
                    texts = []
                    for p in paragraphs:
                        text = self._clean_text(p.get_text())
                        if text and len(text) > 10:
                            texts.append(text)
                    if texts:
                        return "\n\n".join(texts)

                # Fallback: get all text from body element
                text = self._clean_text(body_el.get_text())
                if text and len(text) > 50:
                    return text

        # Try paragraph selectors
        for selector in config.get("paragraph_selectors", []):
            paragraphs = soup.select(selector)
            if paragraphs:
                texts = [self._clean_text(p.get_text()) for p in paragraphs]
                texts = [t for t in texts if t and len(t) > 10]
                if texts:
                    return "\n\n".join(texts)

        return ""

    def _fallback_extract(self, soup: BeautifulSoup) -> str:
        """Fallback: trích xuất từ <article> hoặc largest text block."""
        # Try <article>
        article = soup.select_one("article")
        if article:
            text = self._clean_text(article.get_text())
            if len(text) > 100:
                return text

        # Try main content areas
        for selector in ["main", "[role='main']", "div.content", "div.article"]:
            el = soup.select_one(selector)
            if el:
                text = self._clean_text(el.get_text())
                if len(text) > 200:
                    return text

        return ""

    def _remove_unwanted(self, soup: BeautifulSoup, extra_selectors: list[str]) -> None:
        """Loại bỏ các element không cần thiết."""
        # Remove standard tags
        for tag_name in REMOVE_TAGS:
            for tag in soup.find_all(tag_name):
                try:
                    tag.decompose()
                except Exception:
                    pass

        # Remove by class (exact match or targeted substring)
        to_remove = []
        for el in soup.find_all(True):
            classes = el.get("class")
            if classes and isinstance(classes, list):
                class_set = set(c.lower() for c in classes)
                # Exact match
                if class_set & REMOVE_CLASSES_EXACT:
                    to_remove.append(el)
                    continue
                # Substring match for ad-related classes
                class_str = " ".join(classes).lower()
                if any(pat in class_str for pat in REMOVE_CLASSES_CONTAINS):
                    to_remove.append(el)
        for el in to_remove:
            try:
                el.decompose()
            except Exception:
                pass

        # Remove extra selectors
        for selector in extra_selectors:
            try:
                for el in soup.select(selector):
                    try:
                        el.decompose()
                    except Exception:
                        pass
            except Exception:
                pass

    def _clean_text(self, text: str) -> str:
        """Làm sạch text đã trích xuất."""
        if not text:
            return ""

        # Remove excess whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove common noise
        text = re.sub(r"(?i)(xem thêm|đọc thêm|tin liên quan|bạn đọc):\s*$", "", text)
        text = re.sub(r"(?i)^(tin mới|tin nổi bật)\s*", "", text)
        # Clean up
        text = text.strip()
        return text

    def close(self):
        if self._client and not self._client.is_closed:
            self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
