"""Bộ làm sạch dữ liệu text từ crawler."""

from __future__ import annotations

import logging
import re

from news_ingestor.utils.text_utils import chuan_hoa_khoang_trang, loai_bo_html

logger = logging.getLogger(__name__)

# Danh sách mẫu quảng cáo/nội dung không cần thiết thường gặp trong tin tài chính VN
MAU_QUANG_CAO = [
    r"(?i)xem thêm:?\s*http\S+",
    r"(?i)nguồn:?\s*http\S+",
    r"(?i)theo\s+dõi\s+.*twitter|facebook|youtube",
    r"(?i)đăng\s+ký\s+.*nhận\s+tin",
    r"(?i)bạn\s+đọc\s+gửi\s+bài",
    r"(?i)quảng\s+cáo",
    r"(?i)banner\s+\d+x\d+",
    r"(?i)click\s+(here|vào\s+đây)",
    r"(?i)tải\s+app\s+.*xuống",
    r"\[.*?\]\s*$",  # Các tag đóng
]

# Ký tự đặc biệt thường xuất hiện lỗi khi crawl
KY_TU_LOI = {
    "\u00a0": " ",      # Non-breaking space
    "\u200b": "",       # Zero-width space
    "\u200c": "",       # Zero-width non-joiner
    "\u200d": "",       # Zero-width joiner
    "\ufeff": "",       # BOM
    "\r\n": "\n",       # Windows newline
    "\r": "\n",         # Old Mac newline
}


class BoLamSach:
    """Làm sạch và chuẩn hóa nội dung bài báo từ crawler."""

    def lam_sach(self, text: str) -> str:
        """Thực hiện toàn bộ pipeline làm sạch."""
        if not text:
            return ""

        # 1. Loại bỏ HTML tags
        text = loai_bo_html(text)

        # 2. Sửa ký tự đặc biệt
        text = self._sua_ky_tu_dac_biet(text)

        # 3. Loại bỏ quảng cáo
        text = self._loai_quang_cao(text)

        # 4. Chuẩn hóa khoảng trắng
        text = chuan_hoa_khoang_trang(text)

        return text.strip()

    def lam_sach_tieu_de(self, tieu_de: str) -> str:
        """Làm sạch tiêu đề bài báo."""
        if not tieu_de:
            return ""

        tieu_de = loai_bo_html(tieu_de)
        tieu_de = self._sua_ky_tu_dac_biet(tieu_de)

        # Loại bỏ prefix nguồn tin thường thêm vào tiêu đề
        tieu_de = re.sub(r"^(CafeF|VnExpress|VietStock|Thanh Niên)\s*[-–|:]\s*", "", tieu_de)

        return chuan_hoa_khoang_trang(tieu_de).strip()

    def tom_tat(self, text: str, do_dai: int = 500) -> str:
        """Tạo tóm tắt từ nội dung đã làm sạch."""
        text = self.lam_sach(text)

        if len(text) <= do_dai:
            return text

        # Cắt tại ranh giới câu
        vi_tri = text.rfind(".", 0, do_dai)
        if vi_tri > do_dai // 2:
            return text[: vi_tri + 1]

        return text[:do_dai].rstrip() + "..."

    def _sua_ky_tu_dac_biet(self, text: str) -> str:
        """Thay thế các ký tự đặc biệt lỗi."""
        for ky_tu, thay_the in KY_TU_LOI.items():
            text = text.replace(ky_tu, thay_the)
        return text

    def _loai_quang_cao(self, text: str) -> str:
        """Loại bỏ các mẫu quảng cáo."""
        for mau in MAU_QUANG_CAO:
            text = re.sub(mau, "", text)
        return text
