"""Sentiment Analyzer - Phân tích cảm xúc tin tức tài chính."""

from __future__ import annotations

import logging

from news_ingestor.models.enums import CamXuc
from news_ingestor.utils.text_utils import bo_dau

logger = logging.getLogger(__name__)

# ============================================
# TỪ ĐIỂN CẢM XÚC TÀI CHÍNH TIẾNG VIỆT
# ============================================

TU_TICH_CUC = {
    # Tăng trưởng & lợi nhuận
    "tăng trưởng", "lợi nhuận", "tăng mạnh", "đột phá", "kỷ lục",
    "vượt kế hoạch", "tăng vốn", "chia cổ tức", "doanh thu tăng",
    "lãi lớn", "lãi ròng", "tích cực", "khởi sắc", "phục hồi",
    "bứt phá", "cải thiện", "thuận lợi", "lạc quan", "triển vọng tốt",
    # Thị trường
    "tăng điểm", "xanh sàn", "thanh khoản cao", "dòng tiền vào",
    "nâng hạng", "mua ròng", "khối ngoại mua", "VN-Index tăng",
    "bull", "uptrend", "breakout", "hỗ trợ",
    # Đầu tư
    "nâng mục tiêu giá", "khuyến nghị mua", "outperform",
    "overweight", "upgrade", "growth", "profit", "record",
}

TU_TIEU_CUC = {
    # Thua lỗ & sụt giảm
    "thua lỗ", "lỗ lũy kế", "giảm mạnh", "sụt giảm", "tụt dốc",
    "phá sản", "giải thể", "nợ xấu", "nợ quá hạn", "vi phạm",
    "bị phạt", "gian lận", "lừa đảo", "thao túng", "rủi ro",
    # Thị trường
    "giảm điểm", "đỏ sàn", "bán tháo", "cắt lỗ", "sàn chứng khoán đỏ",
    "khối ngoại bán", "bán ròng", "thanh khoản thấp", "VN-Index giảm",
    "bear", "downtrend", "breakdown", "kháng cự", "margin call",
    # Đầu tư
    "hạ mục tiêu giá", "khuyến nghị bán", "underperform",
    "underweight", "downgrade", "loss", "fraud", "bankrupt",
    # Vĩ mô tiêu cực
    "lạm phát tăng", "lãi suất tăng", "tỷ giá tăng", "thất nghiệp tăng",
    "suy thoái", "đình trệ", "khủng hoảng",
}

TU_TIN_DON = {
    "tin đồn", "chưa xác nhận", "nguồn tin giấu tên", "rò rỉ",
    "chưa kiểm chứng", "có thông tin", "nghe nói", "đồn đoán",
    "rumor", "unverified", "anonymous source",
}


class BoPhanTichCamXuc:
    """Phân tích cảm xúc tin tức tài chính.

    Hỗ trợ 2 chế độ:
    1. Gemini AI (chính xác hơn, cần API key)
    2. Keyword-based (fallback, hoạt động offline)
    """

    def __init__(self, gemini_api_key: str | None = None):
        self._gemini_key = gemini_api_key
        self._gemini_client = None

        if gemini_api_key:
            self._khoi_tao_gemini(gemini_api_key)

    def _khoi_tao_gemini(self, api_key: str) -> None:
        """Khởi tạo Gemini client."""
        try:
            from google import genai

            self._gemini_client = genai.Client(api_key=api_key)
            logger.info("Đã khởi tạo Gemini AI cho phân tích cảm xúc")
        except Exception as e:
            logger.warning(f"Không thể khởi tạo Gemini: {e}. Dùng keyword-based.")
            self._gemini_client = None

    def phan_tich(self, text: str) -> dict:
        """Phân tích cảm xúc của văn bản.

        Returns:
            Dict: {'nhan': CamXuc, 'diem': float(-1.0 → 1.0), 'tin_don': bool}
        """
        if not text:
            return {
                "nhan": CamXuc.TRUNG_TINH,
                "diem": 0.0,
                "tin_don": False,
            }

        # Thử Gemini trước
        if self._gemini_client:
            ket_qua = self._phan_tich_gemini(text)
            if ket_qua:
                return ket_qua

        # Fallback: keyword-based
        return self._phan_tich_keyword(text)

    def _phan_tich_gemini(self, text: str) -> dict | None:
        """Phân tích cảm xúc bằng Gemini AI."""
        try:
            prompt = f"""Bạn là chuyên gia phân tích cảm xúc tin tức tài chính Việt Nam.

Phân tích bài báo sau và trả lời CHÍNH XÁC theo format:
NHAN: POSITIVE hoặc NEGATIVE hoặc NEUTRAL
DIEM: (số thực từ -1.0 đến 1.0)
TIN_DON: TRUE hoặc FALSE

Bài báo:
{text[:1000]}"""

            response = self._gemini_client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt,
            )

            return self._parse_gemini_response(response.text)

        except Exception as e:
            logger.debug(f"Gemini sentiment lỗi: {e}")
            return None

    def _parse_gemini_response(self, response_text: str) -> dict | None:
        """Parse kết quả từ Gemini response."""
        try:
            lines = response_text.strip().split("\n")
            result = {}

            for line in lines:
                line = line.strip()
                if line.startswith("NHAN:"):
                    nhan_str = line.split(":", 1)[1].strip().upper()
                    if "POSITIVE" in nhan_str:
                        result["nhan"] = CamXuc.TICH_CUC
                    elif "NEGATIVE" in nhan_str:
                        result["nhan"] = CamXuc.TIEU_CUC
                    else:
                        result["nhan"] = CamXuc.TRUNG_TINH

                elif line.startswith("DIEM:"):
                    diem_str = line.split(":", 1)[1].strip()
                    diem = float(diem_str)
                    result["diem"] = max(-1.0, min(1.0, diem))

                elif line.startswith("TIN_DON:"):
                    td_str = line.split(":", 1)[1].strip().upper()
                    result["tin_don"] = td_str == "TRUE"

            if "nhan" in result and "diem" in result:
                result.setdefault("tin_don", False)
                return result

        except Exception as e:
            logger.debug(f"Parse Gemini response lỗi: {e}")

        return None

    def _phan_tich_keyword(self, text: str) -> dict:
        """Phân tích cảm xúc bằng từ điển keyword."""
        text_lower = text.lower()
        text_no_dau = bo_dau(text_lower)

        diem_tich_cuc = 0
        diem_tieu_cuc = 0

        # Đếm từ tích cực
        for tu in TU_TICH_CUC:
            tu_lower = tu.lower()
            if tu_lower in text_lower or bo_dau(tu_lower) in text_no_dau:
                diem_tich_cuc += 1

        # Đếm từ tiêu cực
        for tu in TU_TIEU_CUC:
            tu_lower = tu.lower()
            if tu_lower in text_lower or bo_dau(tu_lower) in text_no_dau:
                diem_tieu_cuc += 1

        # Kiểm tra tin đồn
        tin_don = any(
            tu.lower() in text_lower or bo_dau(tu.lower()) in text_no_dau
            for tu in TU_TIN_DON
        )

        # Tính điểm tổng
        tong = diem_tich_cuc + diem_tieu_cuc
        if tong == 0:
            nhan = CamXuc.TRUNG_TINH
            diem = 0.0
        elif diem_tich_cuc > diem_tieu_cuc:
            nhan = CamXuc.TICH_CUC
            diem = min((diem_tich_cuc - diem_tieu_cuc) / max(tong, 1), 1.0)
        elif diem_tieu_cuc > diem_tich_cuc:
            nhan = CamXuc.TIEU_CUC
            diem = max((diem_tich_cuc - diem_tieu_cuc) / max(tong, 1), -1.0)
        else:
            nhan = CamXuc.TRUNG_TINH
            diem = 0.0

        # Giảm độ tin cậy nếu là tin đồn
        if tin_don:
            diem *= 0.5

        return {
            "nhan": nhan,
            "diem": round(diem, 4),
            "tin_don": tin_don,
        }
