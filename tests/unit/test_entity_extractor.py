"""Unit tests cho Bộ Trích Xuất Thực Thể."""

from __future__ import annotations

import pytest

from news_ingestor.models.enums import DanhMuc
from news_ingestor.processing.entity_extractor import BoTrichXuatThucThe


class TestBoTrichXuatThucThe:
    """Tests cho trích xuất mã CK và phân loại danh mục."""

    def setup_method(self):
        self.trich_xuat = BoTrichXuatThucThe()

    def test_nhan_dien_ma_ck_trong_tieu_de(self):
        text = "FPT báo lãi kỷ lục quý 3, vượt kế hoạch năm"
        ket_qua = self.trich_xuat.trich_xuat_ma_ck(text)
        assert "FPT" in ket_qua

    def test_nhan_dien_ten_cong_ty(self):
        text = "Vietcombank mở rộng tín dụng tiêu dùng"
        ket_qua = self.trich_xuat.trich_xuat_ma_ck(text)
        assert "VCB" in ket_qua

    def test_nhan_dien_nhieu_ma(self):
        text = "Vingroup và FPT dẫn đầu tăng trưởng"
        ket_qua = self.trich_xuat.trich_xuat_ma_ck(text)
        assert "FPT" in ket_qua
        assert "VIC" in ket_qua

    def test_khong_co_ma_ck(self):
        text = "Thời tiết hôm nay đẹp"
        ket_qua = self.trich_xuat.trich_xuat_ma_ck(text)
        assert ket_qua == []

    def test_text_rong(self):
        assert self.trich_xuat.trich_xuat_ma_ck("") == []

    def test_phan_loai_doanh_nghiep(self):
        text = "FPT công bố kết quả kinh doanh"
        danh_muc = self.trich_xuat.phan_loai_danh_muc(text, ["FPT"])
        assert danh_muc == DanhMuc.DOANH_NGHIEP

    def test_phan_loai_vi_mo(self):
        text = "GDP tăng trưởng kinh tế vĩ mô lãi suất tỷ giá CPI lạm phát"
        danh_muc = self.trich_xuat.phan_loai_danh_muc(text, [])
        assert danh_muc == DanhMuc.VI_MO

    def test_phan_tich_day_du(self):
        text = "HPG Hòa Phát tăng trưởng nhờ giá thép phục hồi"
        ket_qua = self.trich_xuat.phan_tich(text)
        assert "ma_chung_khoan" in ket_qua
        assert "danh_muc" in ket_qua
        assert "HPG" in ket_qua["ma_chung_khoan"]
