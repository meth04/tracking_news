"""Tiện ích xử lý văn bản tiếng Việt."""

from __future__ import annotations

import re
import unicodedata


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
