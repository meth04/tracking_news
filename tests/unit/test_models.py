"""Unit tests cho Models."""

from __future__ import annotations

from news_ingestor.models.article import BaiBao, BaiBaoTho, ThongKeCamXuc
from news_ingestor.models.enums import CamXuc, DanhMuc, TrangThai


class TestEnums:
    """Tests cho các Enum."""

    def test_danh_muc_gia_tri(self):
        assert DanhMuc.VI_MO.value == "MACRO"
        assert DanhMuc.DOANH_NGHIEP.value == "MICRO"
        assert DanhMuc.NGANH.value == "INDUSTRY"

    def test_cam_xuc_gia_tri(self):
        assert CamXuc.TICH_CUC.value == "POSITIVE"
        assert CamXuc.TIEU_CUC.value == "NEGATIVE"
        assert CamXuc.TRUNG_TINH.value == "NEUTRAL"

    def test_trang_thai_gia_tri(self):
        assert TrangThai.CHO_XU_LY.value == "PENDING"
        assert TrangThai.HOAN_THANH.value == "COMPLETED"


class TestBaiBaoTho:
    """Tests cho model BaiBaoTho."""

    def test_tao_bai_bao_tho(self):
        bai = BaiBaoTho(
            tieu_de="FPT báo lãi kỷ lục quý 3",
            noi_dung="Lợi nhuận sau thuế tăng 30%",
            url="https://example.com/fpt-lai-ky-luc",
            nguon_tin="CafeF",
        )
        assert bai.tieu_de == "FPT báo lãi kỷ lục quý 3"
        assert bai.nguon_tin == "CafeF"
        assert bai.url_chuan_hoa == "https://example.com/fpt-lai-ky-luc"
        assert len(bai.tieu_de_hash) == 64
        assert bai.thoi_gian_xuat_ban is not None

    def test_thoi_gian_mac_dinh(self):
        bai = BaiBaoTho(
            tieu_de="Test",
            url="https://test.com",
            nguon_tin="Test",
        )
        assert bai.thoi_gian_xuat_ban.tzinfo is not None


class TestBaiBao:
    """Tests cho model BaiBao."""

    def test_tao_bai_bao_day_du(self):
        bai = BaiBao(
            tieu_de="VCB tăng trưởng tín dụng",
            noi_dung_tom_tat="Vietcombank mở rộng...",
            url="https://example.com/vcb?utm_source=abc",
            nguon_tin="VnExpress",
            danh_muc=DanhMuc.DOANH_NGHIEP,
            ma_chung_khoan_lien_quan=["VCB"],
            diem_cam_xuc=0.5,
            nhan_cam_xuc=CamXuc.TICH_CUC,
            impact_score=9,
            impact_level="HIGH",
            impact_tags=["ngan_hang", "lai_suat"],
            is_high_impact=True,
        )
        assert bai.id is not None
        assert bai.ma_chung_khoan_lien_quan == ["VCB"]
        assert bai.diem_cam_xuc == 0.5
        assert bai.url_chuan_hoa == "https://example.com/vcb"
        assert len(bai.tieu_de_hash) == 64
        assert bai.impact_level == "HIGH"
        assert bai.is_high_impact is True
        assert bai.trang_thai == TrangThai.CHO_XU_LY

    def test_diem_cam_xuc_rang_buoc(self):
        bai = BaiBao(
            tieu_de="Test",
            url="https://test.com",
            nguon_tin="Test",
            diem_cam_xuc=0.8,
        )
        assert -1.0 <= bai.diem_cam_xuc <= 1.0

    def test_mac_dinh(self):
        bai = BaiBao(
            tieu_de="Test",
            url="https://test.com",
            nguon_tin="Test",
        )
        assert bai.danh_muc == DanhMuc.VI_MO
        assert bai.nhan_cam_xuc == CamXuc.TRUNG_TINH
        assert bai.ma_chung_khoan_lien_quan == []


class TestThongKeCamXuc:
    """Tests cho model ThongKeCamXuc."""

    def test_thong_ke_mac_dinh(self):
        tk = ThongKeCamXuc()
        assert tk.ma_chung_khoan == "VNINDEX"
        assert tk.tong_so_tin == 0
        assert tk.xu_huong == "TRUNG_TINH"

    def test_thong_ke_co_du_lieu(self):
        tk = ThongKeCamXuc(
            ma_chung_khoan="FPT",
            diem_trung_binh=0.35,
            so_tin_tich_cuc=10,
            so_tin_tieu_cuc=3,
            so_tin_trung_tinh=5,
            tong_so_tin=18,
            xu_huong="TÍCH CỰC",
        )
        assert tk.tong_so_tin == 18
        assert tk.xu_huong == "TÍCH CỰC"
