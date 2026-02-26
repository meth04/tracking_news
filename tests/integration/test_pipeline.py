"""Integration test cho Pipeline xử lý NLP."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from news_ingestor.models.article import BaiBaoTho
from news_ingestor.processing.pipeline import LuongXuLy
from news_ingestor.storage.database import lay_quan_ly_db
from news_ingestor.storage.repository import KhoTinTuc


@pytest.fixture
def pipeline() -> LuongXuLy:
    """Tạo pipeline test không dùng embedding/vector DB."""
    import news_ingestor.storage.database as db_module
    db_module._quan_ly = None

    db = lay_quan_ly_db("sqlite:///./data/test_pipeline.db")
    db.khoi_tao_bang()

    return LuongXuLy(
        kho_tin_tuc=KhoTinTuc("sqlite:///./data/test_pipeline.db"),
        kho_vector=None,
        tao_embedding=False,
    )


class TestLuongXuLy:
    """Tests cho pipeline NLP tổng hợp."""

    def test_xu_ly_mot_bai_tich_cuc(self, pipeline: LuongXuLy):
        bai_tho = BaiBaoTho(
            tieu_de="FPT báo lãi kỷ lục, lợi nhuận tăng trưởng vượt kế hoạch",
            noi_dung="Tập đoàn FPT công bố kết quả kinh doanh quý 3 với lợi nhuận tăng 30%",
            url="https://test.com/fpt-pipeline-test",
            nguon_tin="Test CafeF",
            thoi_gian_xuat_ban=datetime.now(tz=timezone.utc),
        )

        bai_bao = pipeline.xu_ly_mot_bai(bai_tho)
        assert bai_bao is not None
        assert bai_bao.tieu_de != ""
        assert "FPT" in bai_bao.ma_chung_khoan_lien_quan
        assert bai_bao.diem_cam_xuc > 0  # Tích cực

    def test_xu_ly_mot_bai_tieu_cuc(self, pipeline: LuongXuLy):
        bai_tho = BaiBaoTho(
            tieu_de="Công ty X thua lỗ nặng, nguy cơ phá sản",
            noi_dung="Doanh nghiệp ghi nhận khoản lỗ lũy kế lớn",
            url="https://test.com/x-thua-lo-test",
            nguon_tin="Test VnExpress",
            thoi_gian_xuat_ban=datetime.now(tz=timezone.utc),
        )

        bai_bao = pipeline.xu_ly_mot_bai(bai_tho)
        assert bai_bao is not None
        assert bai_bao.diem_cam_xuc < 0  # Tiêu cực

    def test_xu_ly_hang_loat(self, pipeline: LuongXuLy):
        danh_sach = [
            BaiBaoTho(
                tieu_de=f"Tin tức tài chính số {i}",
                noi_dung=f"Nội dung bài {i}",
                url=f"https://test.com/tin-{i}-pipeline",
                nguon_tin="Test",
                thoi_gian_xuat_ban=datetime.now(tz=timezone.utc),
            )
            for i in range(5)
        ]

        ket_qua = pipeline.xu_ly_hang_loat(danh_sach)
        assert len(ket_qua) == 5
