"""Unit tests cho Bộ Làm Sạch dữ liệu."""

from __future__ import annotations

from news_ingestor.processing.cleaner import BoLamSach


class TestBoLamSach:
    """Tests cho BoLamSach."""

    def setup_method(self):
        self.lam_sach = BoLamSach()

    def test_loai_html_tags(self):
        text = "<p>Lợi nhuận <strong>tăng mạnh</strong></p>"
        ket_qua = self.lam_sach.lam_sach(text)
        assert "<" not in ket_qua
        assert ">" not in ket_qua
        assert "Lợi nhuận" in ket_qua
        assert "tăng mạnh" in ket_qua

    def test_loai_html_entities(self):
        text = "FPT &amp; VIC &lt;tốt&gt;"
        ket_qua = self.lam_sach.lam_sach(text)
        assert "&amp;" not in ket_qua
        assert "&lt;" not in ket_qua

    def test_chuan_hoa_khoang_trang(self):
        text = "Nhiều    khoảng   trắng   dư   thừa"
        ket_qua = self.lam_sach.lam_sach(text)
        assert "    " not in ket_qua

    def test_text_rong(self):
        assert self.lam_sach.lam_sach("") == ""

    def test_loai_quang_cao(self):
        text = "Tin tốt cho FPT. Click vào đây để xem thêm."
        ket_qua = self.lam_sach.lam_sach(text)
        assert "Tin tốt cho FPT" in ket_qua

    def test_lam_sach_tieu_de(self):
        tieu_de = "  FPT báo lãi kỷ lục   quý 3  "
        ket_qua = self.lam_sach.lam_sach_tieu_de(tieu_de)
        assert ket_qua == "FPT báo lãi kỷ lục quý 3"

    def test_tom_tat_ngan(self):
        text = "Đoạn văn ngắn."
        ket_qua = self.lam_sach.tom_tat(text, do_dai=100)
        assert ket_qua == "Đoạn văn ngắn."

    def test_tom_tat_dai(self):
        text = "A" * 600 + ". Phần dư."
        ket_qua = self.lam_sach.tom_tat(text, do_dai=500)
        assert len(ket_qua) <= 510  # Sai số nhỏ do cắt tại dấu chấm
