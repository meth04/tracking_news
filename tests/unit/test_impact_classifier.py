"""Unit tests cho bộ phân loại tác động tài chính Việt Nam."""

from __future__ import annotations

from news_ingestor.processing.impact_classifier import BoPhanLoaiTacDong


class TestBoPhanLoaiTacDong:
    """Tests cho classifier rule-based v1."""

    def setup_method(self):
        self.classifier = BoPhanLoaiTacDong()

    def test_tin_tac_dong_cao(self):
        ket_qua = self.classifier.phan_loai(
            tieu_de="NHNN điều chỉnh lãi suất điều hành",
            noi_dung="Lạm phát và tỷ giá là trọng tâm điều hành chính sách tiền tệ.",
            ma_ck=["VCB", "BID"],
        )
        assert ket_qua["impact_level"] == "HIGH"
        assert ket_qua["is_high_impact"] is True
        assert ket_qua["impact_score"] >= 8
        assert "lai_suat" in ket_qua["impact_tags"]

    def test_tin_tac_dong_thap(self):
        ket_qua = self.classifier.phan_loai(
            tieu_de="Doanh nghiệp tổ chức họp cổ đông thường niên",
            noi_dung="Thông tin lịch họp định kỳ.",
            ma_ck=[],
        )
        assert ket_qua["impact_level"] in {"LOW", "MEDIUM"}
        assert ket_qua["impact_score"] >= 0

    def test_tin_tac_dong_trung_binh(self):
        ket_qua = self.classifier.phan_loai(
            tieu_de="Doanh nghiệp công bố lợi nhuận và kế hoạch chia cổ tức",
            noi_dung="Thị trường chứng khoán ghi nhận khối ngoại mua ròng nhẹ trong phiên.",
            ma_ck=["FPT"],
        )
        assert ket_qua["impact_level"] in {"MEDIUM", "HIGH"}
        assert ket_qua["impact_score"] >= 4
        assert "co_phieu" in ket_qua["impact_tags"]
