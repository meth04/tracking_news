"""Embeddings Generator - Tạo vector embeddings cho tìm kiếm ngữ nghĩa."""

from __future__ import annotations

import logging

from config.settings import lay_cau_hinh_nlp

logger = logging.getLogger(__name__)


class BoTaoEmbeddings:
    """Tạo vector embeddings từ văn bản sử dụng sentence-transformers.

    Model mặc định: paraphrase-multilingual-MiniLM-L12-v2
    (hỗ trợ 50+ ngôn ngữ bao gồm tiếng Việt)
    """

    def __init__(self, ten_model: str | None = None):
        cau_hinh = lay_cau_hinh_nlp()
        self._ten_model = ten_model or cau_hinh.embedding_model
        self._model = None
        self._kich_thuoc: int = 384  # Mặc định cho MiniLM

    def _tai_model(self) -> None:
        """Lazy loading - tải model khi cần lần đầu."""
        if self._model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Đang tải model embedding: {self._ten_model}...")
            self._model = SentenceTransformer(self._ten_model)
            self._kich_thuoc = self._model.get_sentence_embedding_dimension()
            logger.info(
                f"Đã tải model embedding thành công "
                f"(kích thước vector: {self._kich_thuoc})"
            )
        except Exception as e:
            logger.error(f"Không thể tải model embedding: {e}")
            raise

    def tao_embedding(self, text: str) -> list[float]:
        """Tạo vector embedding cho một văn bản.

        Args:
            text: Văn bản cần tạo embedding.

        Returns:
            List[float]: Vector embedding.
        """
        self._tai_model()

        if not text:
            return [0.0] * self._kich_thuoc

        try:
            # Giới hạn độ dài input để tối ưu hiệu suất
            text_clean = text[:512]
            embedding = self._model.encode(text_clean, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Lỗi tạo embedding: {e}")
            return [0.0] * self._kich_thuoc

    def tao_nhieu_embedding(self, danh_sach_text: list[str]) -> list[list[float]]:
        """Tạo embeddings cho nhiều văn bản (batch processing).

        Args:
            danh_sach_text: Danh sách văn bản.

        Returns:
            List vectors tương ứng.
        """
        self._tai_model()

        if not danh_sach_text:
            return []

        try:
            # Giới hạn độ dài mỗi text
            texts_clean = [t[:512] if t else "" for t in danh_sach_text]
            embeddings = self._model.encode(
                texts_clean,
                normalize_embeddings=True,
                batch_size=32,
                show_progress_bar=len(texts_clean) > 10,
            )
            return [e.tolist() for e in embeddings]
        except Exception as e:
            logger.error(f"Lỗi tạo batch embeddings: {e}")
            return [[0.0] * self._kich_thuoc] * len(danh_sach_text)

    @property
    def kich_thuoc_vector(self) -> int:
        """Kích thước vector embedding."""
        return self._kich_thuoc
