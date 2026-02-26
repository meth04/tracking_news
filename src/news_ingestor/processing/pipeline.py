"""NLP Processing Pipeline - Luồng xử lý tổng hợp cho tin tức tài chính."""

from __future__ import annotations

import logging
from typing import Optional

from config.settings import lay_cau_hinh_nlp
from news_ingestor.models.article import BaiBao, BaiBaoTho
from news_ingestor.models.enums import TrangThai
from news_ingestor.processing.cleaner import BoLamSach
from news_ingestor.processing.content_fetcher import ContentFetcher
from news_ingestor.processing.embeddings import BoTaoEmbeddings
from news_ingestor.processing.entity_extractor import BoTrichXuatThucThe
from news_ingestor.processing.sentiment import BoPhanTichCamXuc
from news_ingestor.storage.repository import KhoTinTuc
from news_ingestor.storage.vector_store import KhoVector

logger = logging.getLogger(__name__)


class LuongXuLy:
    """Pipeline xử lý NLP tổng hợp cho tin tức tài chính.

    Luồng: BaiBaoTho → Fetch Full Content → Làm sạch → Entity Extraction
           → Sentiment Analysis → Embeddings → Lưu DB + Vector DB
    """

    def __init__(
        self,
        kho_tin_tuc: Optional[KhoTinTuc] = None,
        kho_vector: Optional[KhoVector] = None,
        tao_embedding: bool = True,
        fetch_content: bool = True,
    ):
        # Khởi tạo các module xử lý
        self._lam_sach = BoLamSach()
        self._trich_xuat = BoTrichXuatThucThe()

        # Content Fetcher — lấy nội dung đầy đủ từ URL gốc
        self._fetch_content = fetch_content
        self._content_fetcher: Optional[ContentFetcher] = None
        if fetch_content:
            self._content_fetcher = ContentFetcher(timeout=20, delay=0.8)

        # Sentiment analyzer: dùng Gemini nếu có API key
        cau_hinh_nlp = lay_cau_hinh_nlp()
        gemini_key = cau_hinh_nlp.gemini_api_key if cau_hinh_nlp.gemini_api_key else None
        self._cam_xuc = BoPhanTichCamXuc(gemini_api_key=gemini_key)

        # Embedding generator (lazy load)
        self._tao_embedding = tao_embedding
        self._embeddings: Optional[BoTaoEmbeddings] = None
        if tao_embedding:
            try:
                self._embeddings = BoTaoEmbeddings()
            except Exception as e:
                logger.warning(f"Không thể khởi tạo embedding model: {e}")
                self._tao_embedding = False

        # Storage
        self._kho_tin_tuc = kho_tin_tuc or KhoTinTuc()
        self._kho_vector = kho_vector

        logger.info(
            "Đã khởi tạo pipeline NLP",
            extra={"extra_fields": {
                "embedding": self._tao_embedding,
                "gemini": gemini_key is not None and gemini_key != "",
                "vector_db": kho_vector is not None,
                "content_fetch": fetch_content,
            }},
        )

    def xu_ly_mot_bai(self, bai_tho: BaiBaoTho) -> Optional[BaiBao]:
        """Xử lý một bài báo thô qua pipeline đầy đủ.

        Returns:
            BaiBao đã xử lý, hoặc None nếu lỗi.
        """
        try:
            # 0. Fetch nội dung đầy đủ từ URL gốc (nếu chưa có)
            noi_dung_goc = bai_tho.noi_dung
            noi_dung_day_du = ""

            if self._fetch_content and self._content_fetcher and bai_tho.url:
                try:
                    fetch_result = self._content_fetcher.fetch_content(bai_tho.url)
                    if fetch_result["success"] and fetch_result["noi_dung_day_du"]:
                        noi_dung_day_du = fetch_result["noi_dung_day_du"]
                        logger.debug(
                            f"Fetched full content: {fetch_result['char_count']} chars "
                            f"(was {len(noi_dung_goc)} chars) for: {bai_tho.tieu_de[:50]}"
                        )
                    else:
                        logger.debug(
                            f"Content fetch failed for {bai_tho.url}: {fetch_result.get('error', 'unknown')}"
                        )
                except Exception as e:
                    logger.warning(f"Content fetch error: {e}")

            # Sử dụng nội dung đầy đủ nếu có, nếu không dùng nội dung từ crawler
            noi_dung_phan_tich = noi_dung_day_du if noi_dung_day_du else noi_dung_goc

            # 1. Làm sạch nội dung
            tieu_de_sach = self._lam_sach.lam_sach_tieu_de(bai_tho.tieu_de)
            noi_dung_sach = self._lam_sach.lam_sach(noi_dung_phan_tich)
            tom_tat = self._lam_sach.tom_tat(noi_dung_goc if noi_dung_goc else noi_dung_sach)

            # 2. Trích xuất thực thể (dùng nội dung đầy đủ)
            van_ban_phan_tich = f"{tieu_de_sach} {noi_dung_sach}"
            ket_qua_ner = self._trich_xuat.phan_tich(van_ban_phan_tich)

            # 3. Phân tích cảm xúc (dùng nội dung đầy đủ)
            ket_qua_cam_xuc = self._cam_xuc.phan_tich(van_ban_phan_tich)

            # 4. Tạo đối tượng BaiBao
            bai_bao = BaiBao(
                tieu_de=tieu_de_sach,
                noi_dung_tom_tat=tom_tat,
                noi_dung_goc=noi_dung_sach,
                url=bai_tho.url,
                nguon_tin=bai_tho.nguon_tin,
                thoi_gian_xuat_ban=bai_tho.thoi_gian_xuat_ban,
                danh_muc=ket_qua_ner["danh_muc"],
                ma_chung_khoan_lien_quan=ket_qua_ner["ma_chung_khoan"],
                diem_cam_xuc=ket_qua_cam_xuc["diem"],
                nhan_cam_xuc=ket_qua_cam_xuc["nhan"],
                trang_thai=TrangThai.HOAN_THANH,
            )

            # 5. Tạo embedding và lưu Vector DB
            if self._tao_embedding and self._embeddings and self._kho_vector:
                try:
                    vector = self._embeddings.tao_embedding(van_ban_phan_tich)
                    vector_id = self._kho_vector.luu_vector(
                        vector=vector,
                        metadata={
                            "bai_bao_id": bai_bao.id,
                            "tieu_de": tieu_de_sach,
                            "nguon_tin": bai_bao.nguon_tin,
                            "danh_muc": str(bai_bao.danh_muc),
                            "diem_cam_xuc": bai_bao.diem_cam_xuc,
                            "ma_ck": bai_bao.ma_chung_khoan_lien_quan,
                        },
                    )
                    bai_bao.vector_id = vector_id
                except Exception as e:
                    logger.warning(f"Lỗi tạo embedding: {e}")

            # 6. Lưu vào database
            self._kho_tin_tuc.luu_bai_bao(bai_bao)

            return bai_bao

        except Exception as e:
            logger.error(
                f"Lỗi xử lý bài: {bai_tho.tieu_de[:50]}...",
                exc_info=True,
            )
            return None

    def xu_ly_hang_loat(self, danh_sach: list[BaiBaoTho]) -> list[BaiBao]:
        """Xử lý nhiều bài báo thô qua pipeline.

        Args:
            danh_sach: Danh sách bài báo thô từ crawler.

        Returns:
            Danh sách bài báo đã xử lý thành công.
        """
        ket_qua: list[BaiBao] = []
        loi = 0

        logger.info(f"Bắt đầu xử lý {len(danh_sach)} bài báo qua pipeline NLP")

        for i, bai_tho in enumerate(danh_sach, 1):
            bai_bao = self.xu_ly_mot_bai(bai_tho)
            if bai_bao:
                ket_qua.append(bai_bao)
            else:
                loi += 1

            # Báo cáo tiến trình mỗi 10 bài
            if i % 10 == 0:
                logger.info(
                    f"Tiến trình: {i}/{len(danh_sach)} "
                    f"(thành công: {len(ket_qua)}, lỗi: {loi})"
                )

        logger.info(
            f"Hoàn thành xử lý: {len(ket_qua)}/{len(danh_sach)} bài "
            f"(lỗi: {loi})",
            extra={"extra_fields": {
                "tong": len(danh_sach),
                "thanh_cong": len(ket_qua),
                "loi": loi,
            }},
        )

        return ket_qua
