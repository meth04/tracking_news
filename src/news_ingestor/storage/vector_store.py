"""Kết nối và thao tác với Vector Database (Qdrant)."""

from __future__ import annotations

import logging
import uuid

from config.settings import lay_cau_hinh_qdrant

logger = logging.getLogger(__name__)


class KhoVector:
    """Quản lý lưu trữ và tìm kiếm vector embeddings qua Qdrant.

    Tự động fallback sang chế độ in-memory nếu không kết nối được Qdrant.
    """

    def __init__(self, url: str | None = None, ten_collection: str | None = None):
        cau_hinh = lay_cau_hinh_qdrant()
        self._url = url or cau_hinh.url
        self._ten_collection = ten_collection or cau_hinh.ten_collection
        self._client = None
        self._in_memory: list[dict] = []  # Fallback in-memory storage
        self._kich_thuoc_vector = 384  # paraphrase-multilingual-MiniLM-L12-v2
        self._da_ket_noi = False

    def ket_noi(self) -> bool:
        """Kết nối tới Qdrant server. Trả về True nếu thành công."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams

            self._client = QdrantClient(url=self._url, timeout=10)

            # Kiểm tra và tạo collection nếu chưa có
            collections = self._client.get_collections().collections
            ten_hien_co = [c.name for c in collections]

            if self._ten_collection not in ten_hien_co:
                self._client.create_collection(
                    collection_name=self._ten_collection,
                    vectors_config=VectorParams(
                        size=self._kich_thuoc_vector,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Đã tạo collection mới: {self._ten_collection}")

            self._da_ket_noi = True
            logger.info(f"Kết nối Qdrant thành công: {self._url}")
            return True

        except Exception as e:
            logger.warning(
                f"Không thể kết nối Qdrant ({e}). Sử dụng chế độ in-memory."
            )
            self._da_ket_noi = False
            return False

    def luu_vector(
        self,
        vector: list[float],
        metadata: dict,
        vector_id: str | None = None,
    ) -> str:
        """Lưu một vector embedding cùng metadata. Trả về vector_id."""
        if vector_id is None:
            vector_id = str(uuid.uuid4())

        if self._da_ket_noi and self._client:
            try:
                from qdrant_client.models import PointStruct

                self._client.upsert(
                    collection_name=self._ten_collection,
                    points=[
                        PointStruct(
                            id=vector_id,
                            vector=vector,
                            payload=metadata,
                        )
                    ],
                )
                logger.debug(f"Đã lưu vector: {vector_id}")
            except Exception as e:
                logger.error(f"Lỗi lưu vector vào Qdrant: {e}")
                # Fallback in-memory
                self._luu_in_memory(vector_id, vector, metadata)
        else:
            self._luu_in_memory(vector_id, vector, metadata)

        return vector_id

    def tim_kiem_ngu_nghia(
        self,
        vector_truy_van: list[float],
        gioi_han: int = 10,
        diem_toi_thieu: float = 0.3,
    ) -> list[dict]:
        """Tìm kiếm ngữ nghĩa - trả về danh sách kết quả với metadata và điểm."""
        if self._da_ket_noi and self._client:
            try:
                ket_qua = self._client.search(
                    collection_name=self._ten_collection,
                    query_vector=vector_truy_van,
                    limit=gioi_han,
                    score_threshold=diem_toi_thieu,
                )
                return [
                    {
                        "vector_id": str(hit.id),
                        "diem_tuong_dong": round(hit.score, 4),
                        **hit.payload,
                    }
                    for hit in ket_qua
                ]
            except Exception as e:
                logger.error(f"Lỗi tìm kiếm Qdrant: {e}")
                return self._tim_in_memory(vector_truy_van, gioi_han)
        else:
            return self._tim_in_memory(vector_truy_van, gioi_han)

    def dem_vectors(self) -> int:
        """Đếm số lượng vector trong collection."""
        if self._da_ket_noi and self._client:
            try:
                info = self._client.get_collection(self._ten_collection)
                return info.points_count
            except Exception:
                return len(self._in_memory)
        return len(self._in_memory)

    # --- Phương thức in-memory fallback ---

    def _luu_in_memory(self, vector_id: str, vector: list[float], metadata: dict) -> None:
        """Lưu vector vào bộ nhớ khi không có Qdrant."""
        self._in_memory.append({
            "id": vector_id,
            "vector": vector,
            "metadata": metadata,
        })

    def _tim_in_memory(self, vector_truy_van: list[float], gioi_han: int) -> list[dict]:
        """Tìm kiếm cosine similarity trong bộ nhớ."""
        if not self._in_memory:
            return []

        ket_qua = []
        for item in self._in_memory:
            diem = self._cosine_similarity(vector_truy_van, item["vector"])
            ket_qua.append({
                "vector_id": item["id"],
                "diem_tuong_dong": round(diem, 4),
                **item["metadata"],
            })

        ket_qua.sort(key=lambda x: x["diem_tuong_dong"], reverse=True)
        return ket_qua[:gioi_han]

    @staticmethod
    def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        """Tính cosine similarity giữa hai vector."""
        if len(vec_a) != len(vec_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b, strict=False))
        norm_a = sum(a * a for a in vec_a) ** 0.5
        norm_b = sum(b * b for b in vec_b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)
