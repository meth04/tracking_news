"""Tiện ích xử lý văn bản tiếng Việt."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def bo_dau(text: str) -> str:
    """Loại bỏ dấu tiếng Việt để so sánh không phân biệt dấu."""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def chuan_hoa_khoang_trang(text: str) -> str:
    """Chuẩn hóa khoảng trắng: nhiều space → 1 space, trim."""
    return " ".join(text.split())


def loai_bo_html(text: str) -> str:
    """Loại bỏ tất cả HTML tags khỏi chuỗi."""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"&[a-zA-Z]+;", " ", clean)  # HTML entities
    clean = re.sub(r"&#\d+;", " ", clean)  # Numeric entities
    return chuan_hoa_khoang_trang(clean)


def rut_gon_noi_dung(text: str, do_dai_toi_da: int = 500) -> str:
    """Rút gọn nội dung về số ký tự tối đa, cắt ở ranh giới câu."""
    if len(text) <= do_dai_toi_da:
        return text

    # Cắt tại dấu chấm gần nhất trước giới hạn
    vi_tri_cat = text.rfind(".", 0, do_dai_toi_da)
    if vi_tri_cat > do_dai_toi_da // 2:
        return text[: vi_tri_cat + 1]

    return text[:do_dai_toi_da].rstrip() + "..."


def kiem_tra_tieng_viet(text: str) -> bool:
    """Kiểm tra xem chuỗi có chứa ký tự tiếng Việt không."""
    viet_chars = "àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ"
    return any(ch in viet_chars for ch in text.lower())


def chuan_hoa_url(url: str) -> str:
    """Chuẩn hóa URL để hỗ trợ so khớp trùng lặp ổn định."""
    if not url:
        return ""

    url = url.strip()
    if not url:
        return ""

    try:
        parsed = urlsplit(url)
    except Exception:
        return url

    scheme = (parsed.scheme or "https").lower()
    netloc = parsed.netloc.lower()

    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]

    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")

    bo_qua_params = {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "utm_id",
        "gclid",
        "fbclid",
        "mc_cid",
        "mc_eid",
    }

    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in bo_qua_params
    ]
    query = urlencode(sorted(query_pairs), doseq=True)

    return urlunsplit((scheme, netloc, path, query, ""))


def tao_hash_tieu_de(tieu_de: str) -> str:
    """Tạo hash tiêu đề sau chuẩn hóa nhẹ để hỗ trợ dedup."""
    tieu_de_chuan = chuan_hoa_khoang_trang((tieu_de or "").lower())
    return hashlib.sha256(tieu_de_chuan.encode("utf-8")).hexdigest()
