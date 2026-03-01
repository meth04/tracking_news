"""Unit tests cho module evaluation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from news_ingestor.models.article import BaiBao
from news_ingestor.models.enums import CamXuc
from news_ingestor.utils.evaluation import (
    danh_gia_impact_classifier,
    tao_bao_cao_pipeline,
)


class TestDanhGiaImpactClassifier:
    def test_accuracy_va_confusion(self):
        du_doan = [
            {"impact_level": "HIGH"},
            {"impact_level": "MEDIUM"},
            {"impact_level": "LOW"},
            {"impact_level": "LOW"},
        ]
        nhan = ["HIGH", "LOW", "LOW", "MEDIUM"]

        kq = danh_gia_impact_classifier(du_doan, nhan)

        assert kq.so_mau == 4
        assert kq.dung == 2
        assert kq.accuracy == 0.5
        assert kq.confusion["HIGH"]["HIGH"] == 1
        assert kq.confusion["LOW"]["MEDIUM"] == 1


class TestBaoCaoPipeline:
    def test_bao_cao_co_du_lieu(self):
        now = datetime.now(tz=timezone.utc)
        ds = [
            BaiBao(
                tieu_de="A",
                url="https://example.com/a",
                nguon_tin="CafeF",
                thoi_gian_xuat_ban=now - timedelta(days=1),
                noi_dung_goc="noi dung day du",
                noi_dung_tom_tat="tom tat",
                ma_chung_khoan_lien_quan=["VCB"],
                diem_cam_xuc=0.2,
                nhan_cam_xuc=CamXuc.TICH_CUC,
                impact_level="HIGH",
                is_high_impact=True,
                vector_id="vec-1",
            ),
            BaiBao(
                tieu_de="B",
                url="https://example.com/b",
                nguon_tin="VnExpress",
                thoi_gian_xuat_ban=now - timedelta(days=2),
                noi_dung_goc="",
                noi_dung_tom_tat="",
                ma_chung_khoan_lien_quan=[],
                diem_cam_xuc=0.0,
                impact_level="LOW",
                is_high_impact=False,
                vector_id=None,
            ),
        ]

        bc = tao_bao_cao_pipeline(ds, so_ngay=7)

        assert bc.total_articles == 2
        assert bc.unique_sources == 2
        assert bc.coverage["has_content_ratio"] == 0.5
        assert bc.coverage["has_summary_ratio"] == 0.5
        assert bc.coverage["has_tickers_ratio"] == 0.5
        assert bc.coverage["has_vector_ratio"] == 0.5
        assert bc.sentiment_distribution["POSITIVE"] == 1
        assert bc.impact_distribution["HIGH"] == 1
        assert bc.high_impact_ratio == 0.5

    def test_bao_cao_khong_du_lieu(self):
        bc = tao_bao_cao_pipeline([], so_ngay=3)

        assert bc.total_articles == 0
        assert bc.high_impact_ratio == 0.0
        assert bc.coverage["has_content_ratio"] == 0.0
