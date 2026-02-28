"""Unit tests cho Repository và Database."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest

from news_ingestor.models.article import BaiBao
from news_ingestor.models.enums import CamXuc, DanhMuc, TrangThai
from news_ingestor.storage.database import QuanLyDatabase
from news_ingestor.storage.repository import KhoTinTuc


@pytest.fixture
def kho() -> KhoTinTuc:
    """Tạo repository với SQLite in-memory cho testing."""
    import news_ingestor.storage.database as db_module
    db_module._quan_ly = None

    # Dùng unique DB path cho mỗi test session
    db_name = f"test_{uuid.uuid4().hex[:8]}.db"
    os.makedirs("./data", exist_ok=True)
    db_url = f"sqlite:///./data/{db_name}"

    db = QuanLyDatabase(database_url=db_url)
    db_module._quan_ly = db
    db.khoi_tao_bang()

    kho = KhoTinTuc(database_url=db_url)
    yield kho

    # Cleanup
    db.dong_ket_noi()
    db_module._quan_ly = None
    try:
        os.remove(f"./data/{db_name}")
    except Exception:
        pass


@pytest.fixture
def bai_bao_mau() -> BaiBao:
    """Tạo bài báo mẫu cho test."""
    return BaiBao(
        id=str(uuid.uuid4()),
        tieu_de="FPT báo lãi kỷ lục quý 3",
        noi_dung_tom_tat="Lợi nhuận thuần tăng 30% so với cùng kỳ",
        url=f"https://example.com/fpt-lai-ky-luc-{uuid.uuid4().hex[:6]}",
        nguon_tin="CafeF",
        thoi_gian_xuat_ban=datetime.now(tz=timezone.utc),
        danh_muc=DanhMuc.DOANH_NGHIEP,
        ma_chung_khoan_lien_quan=["FPT"],
        diem_cam_xuc=0.65,
        nhan_cam_xuc=CamXuc.TICH_CUC,
        trang_thai=TrangThai.HOAN_THANH,
    )


class TestKhoTinTuc:
    """Tests cho KhoTinTuc repository."""

    def test_luu_va_dem(self, kho: KhoTinTuc, bai_bao_mau: BaiBao):
        ket_qua = kho.luu_bai_bao(bai_bao_mau)
        assert ket_qua is True
        assert kho.dem_bai_bao() >= 1

    def test_khong_trung_lap(self, kho: KhoTinTuc, bai_bao_mau: BaiBao):
        kho.luu_bai_bao(bai_bao_mau)
        ket_qua_2 = kho.luu_bai_bao(bai_bao_mau)  # Lưu lại lần 2
        assert ket_qua_2 is False  # Đã tồn tại

    def test_khong_trung_lap_theo_url_chuan_hoa(self, kho: KhoTinTuc):
        bai_1 = BaiBao(
            id=str(uuid.uuid4()),
            tieu_de="FPT tăng trưởng quý 4",
            url="https://example.com/news?id=1&utm_source=abc",
            nguon_tin="Test",
            thoi_gian_xuat_ban=datetime.now(tz=timezone.utc),
        )
        bai_2 = BaiBao(
            id=str(uuid.uuid4()),
            tieu_de="Tiêu đề khác",
            url="https://example.com/news?id=1",
            nguon_tin="Test",
            thoi_gian_xuat_ban=datetime.now(tz=timezone.utc),
        )

        assert kho.luu_bai_bao(bai_1) is True
        assert kho.luu_bai_bao(bai_2) is False

    def test_khong_trung_lap_theo_hash_tieu_de(self, kho: KhoTinTuc):
        bai_1 = BaiBao(
            id=str(uuid.uuid4()),
            tieu_de="VN-Index tăng mạnh nhờ nhóm ngân hàng",
            url="https://example.com/a",
            nguon_tin="Test",
            thoi_gian_xuat_ban=datetime.now(tz=timezone.utc),
        )
        bai_2 = BaiBao(
            id=str(uuid.uuid4()),
            tieu_de="VN-Index tăng mạnh nhờ nhóm ngân hàng",
            url="https://example.com/b",
            nguon_tin="Test",
            thoi_gian_xuat_ban=datetime.now(tz=timezone.utc),
        )

        assert kho.luu_bai_bao(bai_1) is True
        assert kho.luu_bai_bao(bai_2) is False

    def test_tim_theo_ma_ck(self, kho: KhoTinTuc, bai_bao_mau: BaiBao):
        kho.luu_bai_bao(bai_bao_mau)
        ket_qua = kho.tim_theo_ma_ck("FPT")
        assert len(ket_qua) >= 1
        assert any(b.tieu_de == bai_bao_mau.tieu_de for b in ket_qua)

    def test_lay_cam_xuc_thi_truong(self, kho: KhoTinTuc, bai_bao_mau: BaiBao):
        kho.luu_bai_bao(bai_bao_mau)
        thong_ke = kho.lay_cam_xuc_thi_truong(ma_ck="FPT", so_ngay=30)
        assert thong_ke.tong_so_tin >= 1
        assert thong_ke.ma_chung_khoan == "FPT"

    def test_lay_tin_tac_dong_cao(self, kho: KhoTinTuc):
        bai_cao = BaiBao(
            id=str(uuid.uuid4()),
            tieu_de="NHNN điều chỉnh lãi suất điều hành",
            url=f"https://example.com/high-{uuid.uuid4().hex[:6]}",
            nguon_tin="Test",
            thoi_gian_xuat_ban=datetime.now(tz=timezone.utc),
            impact_score=10,
            impact_level="HIGH",
            impact_tags=["lai_suat", "ngan_hang"],
            is_high_impact=True,
        )
        bai_thap = BaiBao(
            id=str(uuid.uuid4()),
            tieu_de="Bản tin thị trường thường nhật",
            url=f"https://example.com/low-{uuid.uuid4().hex[:6]}",
            nguon_tin="Test",
            thoi_gian_xuat_ban=datetime.now(tz=timezone.utc),
            impact_score=1,
            impact_level="LOW",
            impact_tags=[],
            is_high_impact=False,
        )

        kho.luu_bai_bao(bai_cao)
        kho.luu_bai_bao(bai_thap)

        ket_qua = kho.lay_tin_tac_dong_cao(so_ngay=7, gioi_han=10)
        assert len(ket_qua) >= 1
        assert all(b.is_high_impact for b in ket_qua)

    def test_phan_tich_khung_thoi_gian(self, kho: KhoTinTuc):
        assert kho._phan_tich_khung_thoi_gian("7d") is not None
        assert kho._phan_tich_khung_thoi_gian("1m") is not None
        assert kho._phan_tich_khung_thoi_gian("invalid") is None
