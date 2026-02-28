"""Các kiểu liệt kê (Enum) dùng trong hệ thống tin tức tài chính."""

from __future__ import annotations

from enum import StrEnum


class DanhMuc(StrEnum):
    """Danh mục phân loại tin tức."""

    VI_MO = "MACRO"          # Tin tức vĩ mô (lãi suất, tỷ giá, GDP...)
    DOANH_NGHIEP = "MICRO"   # Tin tức doanh nghiệp cụ thể
    NGANH = "INDUSTRY"       # Tin tức theo ngành

    def __str__(self) -> str:
        return self.value


class CamXuc(StrEnum):
    """Kết quả phân tích cảm xúc bài báo."""

    TICH_CUC = "POSITIVE"    # Tin tích cực
    TIEU_CUC = "NEGATIVE"    # Tin tiêu cực
    TRUNG_TINH = "NEUTRAL"   # Tin trung tính

    def __str__(self) -> str:
        return self.value


class TrangThai(StrEnum):
    """Trạng thái xử lý của bài báo trong pipeline."""

    CHO_XU_LY = "PENDING"         # Chờ xử lý NLP
    DANG_XU_LY = "PROCESSING"     # Đang xử lý
    HOAN_THANH = "COMPLETED"      # Đã xử lý xong
    LOI = "ERROR"                 # Xử lý lỗi

    def __str__(self) -> str:
        return self.value
