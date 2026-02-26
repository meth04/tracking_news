"""Pydantic models cho dữ liệu tin tức tài chính."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from news_ingestor.models.enums import CamXuc, DanhMuc, TrangThai


class BaiBaoTho(BaseModel):
    """Bài báo thô - dữ liệu trực tiếp từ crawler, chưa qua xử lý NLP."""

    tieu_de: str = Field(..., description="Tiêu đề bài báo")
    noi_dung: str = Field(default="", description="Nội dung đầy đủ hoặc tóm tắt")
    url: str = Field(..., description="Đường dẫn gốc bài báo")
    nguon_tin: str = Field(..., description="Tên nguồn tin (VD: CafeF, VnExpress)")
    thoi_gian_xuat_ban: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="Thời gian xuất bản bài báo",
    )


class BaiBao(BaseModel):
    """Bài báo đã qua xử lý - model chính lưu vào database."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Mã định danh duy nhất (UUID)",
    )
    tieu_de: str = Field(..., description="Tiêu đề bài báo")
    noi_dung_tom_tat: str = Field(default="", description="Tóm tắt nội dung")
    noi_dung_goc: str = Field(default="", description="Nội dung gốc đầy đủ")
    url: str = Field(..., description="Đường dẫn gốc bài báo")
    nguon_tin: str = Field(..., description="Tên nguồn tin")
    thoi_gian_xuat_ban: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="Thời gian xuất bản",
    )
    danh_muc: DanhMuc = Field(
        default=DanhMuc.VI_MO,
        description="Danh mục: MACRO / MICRO / INDUSTRY",
    )
    ma_chung_khoan_lien_quan: list[str] = Field(
        default_factory=list,
        description="Danh sách mã CK liên quan (VD: ['FPT', 'VIC'])",
    )
    diem_cam_xuc: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Điểm cảm xúc từ -1.0 (rất tiêu cực) đến 1.0 (rất tích cực)",
    )
    nhan_cam_xuc: CamXuc = Field(
        default=CamXuc.TRUNG_TINH,
        description="Nhãn cảm xúc: POSITIVE / NEGATIVE / NEUTRAL",
    )
    vector_id: Optional[str] = Field(
        default=None,
        description="Khóa ngoại liên kết tới Vector DB",
    )
    trang_thai: TrangThai = Field(
        default=TrangThai.CHO_XU_LY,
        description="Trạng thái xử lý trong pipeline",
    )
    thoi_gian_tao: datetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        description="Thời gian tạo bản ghi",
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class KetQuaTimKiem(BaseModel):
    """Kết quả trả về từ MCP tools."""

    bai_bao: BaiBao
    diem_tuong_dong: float = Field(
        default=0.0,
        description="Điểm tương đồng ngữ nghĩa (cosine similarity)",
    )


class ThongKeCamXuc(BaseModel):
    """Thống kê cảm xúc tổng hợp cho một mã CK hoặc thị trường."""

    ma_chung_khoan: str = Field(default="VNINDEX", description="Mã chứng khoán")
    diem_trung_binh: float = Field(default=0.0, description="Điểm cảm xúc trung bình")
    so_tin_tich_cuc: int = Field(default=0, description="Số tin tích cực")
    so_tin_tieu_cuc: int = Field(default=0, description="Số tin tiêu cực")
    so_tin_trung_tinh: int = Field(default=0, description="Số tin trung tính")
    tong_so_tin: int = Field(default=0, description="Tổng số tin")
    xu_huong: str = Field(default="TRUNG_TINH", description="Xu hướng chung")
