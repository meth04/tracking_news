"""Bộ phân loại mức độ tác động đến tài chính Việt Nam (rule-based v1)."""

from __future__ import annotations

from news_ingestor.utils.text_utils import bo_dau


class BoPhanLoaiTacDong:
    """Classifier v1 dựa trên từ khóa + mã chứng khoán + chủ đề."""

    TU_KHOA_TAC_DONG_CAO = {
        "ngan hang nha nuoc",
        "nhnn",
        "lai suat",
        "ty gia",
        "lam phat",
        "gdp",
        "cpi",
        "fed",
        "chinh sach tien te",
        "trai phieu chinh phu",
        "room tin dung",
        "thue",
        "thuong mai",
        "xuat khau",
        "nhap khau",
        "gia xang",
        "gia dau",
        "vn-index",
        "vnindex",
        "thi truong chung khoan",
        "bat dong san",
        "khung hoang",
        "suy thoai",
        "thao tung",
        "pha san",
        "vo no",
        "giai ngan dau tu cong",
    }

    TU_KHOA_TAC_DONG_TRUNG_BINH = {
        "doanh thu",
        "loi nhuan",
        "co tuc",
        "mua lai co phieu",
        "chia co tuc",
        "phat hanh",
        "trai phieu doanh nghiep",
        "m&a",
        "sap nhap",
        "hop tac chien luoc",
        "nang hang",
        "ha hang",
        "khoi ngoai",
        "mua rong",
        "ban rong",
        "thanh khoan",
    }

    TAG_THEO_CHU_DE = {
        "lai_suat": {"lai suat", "nhnn", "fed", "chinh sach tien te"},
        "ty_gia": {"ty gia", "usd", "ngoai hoi"},
        "lam_phat": {"lam phat", "cpi"},
        "tang_truong": {"gdp", "tang truong kinh te"},
        "co_phieu": {"vn-index", "vnindex", "thi truong chung khoan", "co phieu"},
        "ngan_hang": {"ngan hang", "tin dung", "room tin dung"},
        "bat_dong_san": {"bat dong san", "nha o", "du an"},
        "nang_luong": {"gia xang", "gia dau", "nang luong"},
        "thuong_mai": {"xuat khau", "nhap khau", "thuong mai"},
    }

    def phan_loai(self, tieu_de: str, noi_dung: str, ma_ck: list[str] | None = None) -> dict:
        """Trả về điểm, mức tác động, và tags."""
        text = f"{tieu_de} {noi_dung}".strip().lower()
        text_khong_dau = bo_dau(text)

        diem = 0

        for tu in self.TU_KHOA_TAC_DONG_CAO:
            if tu in text_khong_dau:
                diem += 3

        for tu in self.TU_KHOA_TAC_DONG_TRUNG_BINH:
            if tu in text_khong_dau:
                diem += 1

        if ma_ck:
            diem += min(len(ma_ck), 5)

        tags = self._gan_tags(text_khong_dau)

        if diem >= 8:
            muc = "HIGH"
        elif diem >= 4:
            muc = "MEDIUM"
        else:
            muc = "LOW"

        return {
            "impact_score": diem,
            "impact_level": muc,
            "impact_tags": tags,
            "is_high_impact": muc == "HIGH",
        }

    def _gan_tags(self, text_khong_dau: str) -> list[str]:
        tags: list[str] = []
        for tag, tu_khoa_set in self.TAG_THEO_CHU_DE.items():
            if any(tu in text_khong_dau for tu in tu_khoa_set):
                tags.append(tag)
        return tags
