"""Unit tests cho Bộ Phân Tích Cảm Xúc."""

from __future__ import annotations

from news_ingestor.models.enums import CamXuc
from news_ingestor.processing.sentiment import BoPhanTichCamXuc


class TestBoPhanTichCamXuc:
    """Tests cho phân tích cảm xúc keyword-based."""

    def setup_method(self):
        # Không dùng Gemini API cho unit tests
        self.phan_tich = BoPhanTichCamXuc(gemini_api_key=None)

    def test_tin_tich_cuc(self):
        text = "FPT báo lãi kỷ lục, lợi nhuận tăng trưởng mạnh mẽ"
        ket_qua = self.phan_tich.phan_tich(text)
        assert ket_qua["nhan"] == CamXuc.TICH_CUC
        assert ket_qua["diem"] > 0

    def test_tin_tieu_cuc(self):
        text = "Công ty thua lỗ nặng nề, nguy cơ phá sản, gian lận tài chính"
        ket_qua = self.phan_tich.phan_tich(text)
        assert ket_qua["nhan"] == CamXuc.TIEU_CUC
        assert ket_qua["diem"] < 0

    def test_tin_trung_tinh(self):
        text = "Họp báo thường niên của công ty vào ngày mai"
        ket_qua = self.phan_tich.phan_tich(text)
        assert ket_qua["nhan"] == CamXuc.TRUNG_TINH
        assert ket_qua["diem"] == 0.0

    def test_tin_co_tin_don(self):
        text = "Tin đồn FPT sẽ chia cổ tức đặc biệt, chưa xác nhận"
        ket_qua = self.phan_tich.phan_tich(text)
        assert ket_qua["tin_don"] is True
        # Điểm bị giảm 50% do tin đồn
        assert abs(ket_qua["diem"]) < 1.0

    def test_text_rong(self):
        ket_qua = self.phan_tich.phan_tich("")
        assert ket_qua["nhan"] == CamXuc.TRUNG_TINH
        assert ket_qua["diem"] == 0.0
        assert ket_qua["tin_don"] is False

    def test_diem_nam_trong_khoang(self):
        text = "Tăng trưởng tích cực lãi lớn lợi nhuận kỷ lục"
        ket_qua = self.phan_tich.phan_tich(text)
        assert -1.0 <= ket_qua["diem"] <= 1.0

    def test_tu_khoa_thi_truong(self):
        text = "VN-Index tăng điểm mạnh, thanh khoản cao, khối ngoại mua ròng"
        ket_qua = self.phan_tich.phan_tich(text)
        assert ket_qua["nhan"] == CamXuc.TICH_CUC

    def test_vi_mo_tieu_cuc(self):
        text = "Lạm phát tăng cao, suy thoái kinh tế, thất nghiệp tăng"
        ket_qua = self.phan_tich.phan_tich(text)
        assert ket_qua["nhan"] == CamXuc.TIEU_CUC
