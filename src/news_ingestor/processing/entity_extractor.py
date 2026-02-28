"""Entity Extractor - Trích xuất mã chứng khoán và phân loại danh mục."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from news_ingestor.models.enums import DanhMuc
from news_ingestor.utils.text_utils import bo_dau

logger = logging.getLogger(__name__)


class BoTrichXuatThucThe:
    """Nhận diện mã chứng khoán (NER) và phân loại danh mục tin tức.

    Sử dụng từ điển từ config/tickers.json để matching.
    """

    def __init__(self, duong_dan_tickers: str = "config/tickers.json"):
        self._ma_ck: dict[str, dict] = {}
        self._tu_khoa_vi_mo: list[str] = []
        self._tu_khoa_nganh: dict[str, list[str]] = {}
        self._tai_cau_hinh(duong_dan_tickers)

    def _tai_cau_hinh(self, duong_dan: str) -> None:
        """Tải cấu hình từ file tickers.json."""
        try:
            path = Path(duong_dan)
            if not path.exists():
                logger.warning(f"Không tìm thấy file tickers: {duong_dan}")
                return

            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            self._ma_ck = data.get("ma_chung_khoan", {})
            self._tu_khoa_vi_mo = data.get("tu_khoa_vi_mo", [])
            self._tu_khoa_nganh = data.get("tu_khoa_nganh", {})

            logger.info(
                f"Đã tải {len(self._ma_ck)} mã CK, "
                f"{len(self._tu_khoa_vi_mo)} từ khóa vĩ mô, "
                f"{len(self._tu_khoa_nganh)} ngành"
            )
        except Exception as e:
            logger.error(f"Lỗi tải cấu hình tickers: {e}")

    def trich_xuat_ma_ck(self, text: str) -> list[str]:
        """Trích xuất danh sách mã chứng khoán từ văn bản.

        Sử dụng matching cả mã CK lẫn tên công ty/từ khóa.
        """
        if not text:
            return []

        text_lower = text.lower()
        text_no_dau = bo_dau(text_lower)
        ma_tim_thay: set[str] = set()

        for ma, thong_tin in self._ma_ck.items():
            tu_khoa = thong_tin.get("tu_khoa", [])

            for tk in tu_khoa:
                tk_lower = tk.lower()
                tk_no_dau = bo_dau(tk_lower)

                # Kiểm tra cả có dấu và không dấu
                if tk_lower in text_lower or tk_no_dau in text_no_dau:
                    ma_tim_thay.add(ma)
                    break

        # Bổ sung: tìm mã CK 3 ký tự viết hoa (VD: FPT, VIC, VCB)
        ma_regex = re.findall(r"\b([A-Z]{3})\b", text)
        for ma in ma_regex:
            if ma in self._ma_ck:
                ma_tim_thay.add(ma)

        return sorted(ma_tim_thay)

    def phan_loai_danh_muc(self, text: str, ma_ck_da_tim: list[str] | None = None) -> DanhMuc:
        """Phân loại bài báo vào danh mục: MACRO, MICRO, hoặc INDUSTRY.

        Logic phân loại:
        1. Nếu có mã chứng khoán cụ thể → MICRO (tin doanh nghiệp)
        2. Nếu chứa từ khóa ngành → INDUSTRY
        3. Nếu chứa từ khóa vĩ mô → MACRO
        4. Mặc định → MACRO
        """
        # Nếu có mã CK cụ thể → tin doanh nghiệp
        if ma_ck_da_tim:
            return DanhMuc.DOANH_NGHIEP

        text_lower = text.lower()
        text_no_dau = bo_dau(text_lower)

        # Kiểm tra từ khóa ngành
        diem_nganh = 0
        for _nganh, tu_khoa_list in self._tu_khoa_nganh.items():
            for tk in tu_khoa_list:
                if tk.lower() in text_lower or bo_dau(tk.lower()) in text_no_dau:
                    diem_nganh += 1

        # Kiểm tra từ khóa vĩ mô
        diem_vi_mo = 0
        for tk in self._tu_khoa_vi_mo:
            if tk.lower() in text_lower or bo_dau(tk.lower()) in text_no_dau:
                diem_vi_mo += 1

        # Quyết định dựa trên điểm
        if diem_vi_mo > diem_nganh and diem_vi_mo > 0:
            return DanhMuc.VI_MO
        elif diem_nganh > 0:
            return DanhMuc.NGANH

        return DanhMuc.VI_MO  # Mặc định

    def phan_tich(self, text: str) -> dict:
        """Phân tích đầy đủ: trích xuất mã CK + phân loại danh mục.

        Returns:
            Dict với keys: 'ma_chung_khoan', 'danh_muc'
        """
        ma_ck = self.trich_xuat_ma_ck(text)
        danh_muc = self.phan_loai_danh_muc(text, ma_ck)

        return {
            "ma_chung_khoan": ma_ck,
            "danh_muc": danh_muc,
        }
