"""Repository pattern - CRUD operations cho tin tức tài chính."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import desc, or_

from news_ingestor.models.article import BaiBao, ThongKeCamXuc
from news_ingestor.models.enums import CamXuc, DanhMuc
from news_ingestor.storage.database import BangNhatKy, BangTinTuc, lay_quan_ly_db

logger = logging.getLogger(__name__)


class KhoTinTuc:
    """Repository cho bảng tin_tuc_tai_chinh - thao tác CRUD chính."""

    def __init__(self, database_url: Optional[str] = None):
        self._db = lay_quan_ly_db(database_url)

    def luu_bai_bao(self, bai_bao: BaiBao) -> bool:
        """Lưu một bài báo vào database. Trả về True nếu là bài mới."""
        session = self._db.tao_phien()
        try:
            # Kiểm tra trùng lặp theo URL
            ton_tai = session.query(BangTinTuc).filter_by(url=bai_bao.url).first()
            if ton_tai:
                logger.debug(f"Bài báo đã tồn tại: {bai_bao.url}")
                return False

            ban_ghi = BangTinTuc(
                id=bai_bao.id,
                tieu_de=bai_bao.tieu_de,
                noi_dung_tom_tat=bai_bao.noi_dung_tom_tat,
                noi_dung_goc=bai_bao.noi_dung_goc,
                url=bai_bao.url,
                nguon_tin=bai_bao.nguon_tin,
                thoi_gian_xuat_ban=bai_bao.thoi_gian_xuat_ban,
                danh_muc=str(bai_bao.danh_muc),
                ma_chung_khoan_lien_quan=json.dumps(
                    bai_bao.ma_chung_khoan_lien_quan, ensure_ascii=False
                ),
                diem_cam_xuc=bai_bao.diem_cam_xuc,
                nhan_cam_xuc=str(bai_bao.nhan_cam_xuc),
                vector_id=bai_bao.vector_id,
                trang_thai=str(bai_bao.trang_thai),
                thoi_gian_tao=bai_bao.thoi_gian_tao,
            )
            session.add(ban_ghi)
            session.commit()
            logger.info(f"Đã lưu bài báo mới: {bai_bao.tieu_de[:50]}...")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Lỗi khi lưu bài báo: {e}")
            return False
        finally:
            session.close()

    def luu_nhieu_bai_bao(self, danh_sach: list[BaiBao]) -> int:
        """Lưu nhiều bài báo, trả về số bài mới được lưu."""
        so_moi = 0
        for bai_bao in danh_sach:
            if self.luu_bai_bao(bai_bao):
                so_moi += 1
        logger.info(f"Đã lưu {so_moi}/{len(danh_sach)} bài báo mới")
        return so_moi

    def tim_theo_ma_ck(
        self,
        ma_ck: str,
        ngay_bat_dau: Optional[datetime] = None,
        ngay_ket_thuc: Optional[datetime] = None,
        gioi_han: int = 50,
    ) -> list[BaiBao]:
        """Tìm tin tức theo mã chứng khoán và khoảng thời gian."""
        session = self._db.tao_phien()
        try:
            query = session.query(BangTinTuc).filter(
                BangTinTuc.ma_chung_khoan_lien_quan.contains(ma_ck)
            )

            if ngay_bat_dau:
                query = query.filter(BangTinTuc.thoi_gian_xuat_ban >= ngay_bat_dau)
            if ngay_ket_thuc:
                query = query.filter(BangTinTuc.thoi_gian_xuat_ban <= ngay_ket_thuc)

            ket_qua = (
                query.order_by(desc(BangTinTuc.thoi_gian_xuat_ban))
                .limit(gioi_han)
                .all()
            )
            return [self._chuyen_doi(r) for r in ket_qua]
        finally:
            session.close()

    def tim_tin_vi_mo(
        self,
        khung_thoi_gian: Optional[str] = None,
        chu_de: Optional[str] = None,
        gioi_han: int = 50,
    ) -> list[BaiBao]:
        """Tìm tin tức vĩ mô theo thời gian và chủ đề."""
        session = self._db.tao_phien()
        try:
            query = session.query(BangTinTuc).filter(
                BangTinTuc.danh_muc == "MACRO"
            )

            # Xử lý khung thời gian
            if khung_thoi_gian:
                ngay_bat_dau = self._phan_tich_khung_thoi_gian(khung_thoi_gian)
                if ngay_bat_dau:
                    query = query.filter(
                        BangTinTuc.thoi_gian_xuat_ban >= ngay_bat_dau
                    )

            # Tìm theo chủ đề (trong tiêu đề và tóm tắt)
            if chu_de:
                query = query.filter(
                    or_(
                        BangTinTuc.tieu_de.contains(chu_de),
                        BangTinTuc.noi_dung_tom_tat.contains(chu_de),
                    )
                )

            ket_qua = (
                query.order_by(desc(BangTinTuc.thoi_gian_xuat_ban))
                .limit(gioi_han)
                .all()
            )
            return [self._chuyen_doi(r) for r in ket_qua]
        finally:
            session.close()

    def lay_cam_xuc_thi_truong(
        self,
        ma_ck: Optional[str] = None,
        so_ngay: int = 7,
    ) -> ThongKeCamXuc:
        """Tổng hợp thống kê cảm xúc cho một mã CK hoặc toàn thị trường."""
        session = self._db.tao_phien()
        try:
            ngay_bat_dau = datetime.now(tz=timezone.utc) - timedelta(days=so_ngay)
            query = session.query(BangTinTuc).filter(
                BangTinTuc.thoi_gian_xuat_ban >= ngay_bat_dau
            )

            if ma_ck:
                query = query.filter(
                    BangTinTuc.ma_chung_khoan_lien_quan.contains(ma_ck)
                )

            ket_qua = query.all()

            if not ket_qua:
                return ThongKeCamXuc(
                    ma_chung_khoan=ma_ck or "VNINDEX",
                    tong_so_tin=0,
                )

            diem_tong = 0.0
            tich_cuc = 0
            tieu_cuc = 0
            trung_tinh = 0

            for r in ket_qua:
                diem_tong += r.diem_cam_xuc or 0.0
                nhan = r.nhan_cam_xuc or "NEUTRAL"
                if nhan == "POSITIVE":
                    tich_cuc += 1
                elif nhan == "NEGATIVE":
                    tieu_cuc += 1
                else:
                    trung_tinh += 1

            tong = len(ket_qua)
            trung_binh = round(diem_tong / tong, 4) if tong > 0 else 0.0

            if trung_binh > 0.1:
                xu_huong = "TÍCH CỰC"
            elif trung_binh < -0.1:
                xu_huong = "TIÊU CỰC"
            else:
                xu_huong = "TRUNG TÍNH"

            return ThongKeCamXuc(
                ma_chung_khoan=ma_ck or "VNINDEX",
                diem_trung_binh=trung_binh,
                so_tin_tich_cuc=tich_cuc,
                so_tin_tieu_cuc=tieu_cuc,
                so_tin_trung_tinh=trung_tinh,
                tong_so_tin=tong,
                xu_huong=xu_huong,
            )
        finally:
            session.close()

    def lay_tat_ca(self, gioi_han: int = 100) -> list[BaiBao]:
        """Lấy tất cả bài báo mới nhất."""
        session = self._db.tao_phien()
        try:
            ket_qua = (
                session.query(BangTinTuc)
                .order_by(desc(BangTinTuc.thoi_gian_xuat_ban))
                .limit(gioi_han)
                .all()
            )
            return [self._chuyen_doi(r) for r in ket_qua]
        finally:
            session.close()

    def dem_bai_bao(self) -> int:
        """Đếm tổng số bài báo trong database."""
        session = self._db.tao_phien()
        try:
            return session.query(BangTinTuc).count()
        finally:
            session.close()

    # --- Nhật ký thu thập ---

    def tao_nhat_ky(self, nguon_tin: str) -> str:
        """Tạo bản ghi nhật ký thu thập mới, trả về ID."""
        session = self._db.tao_phien()
        try:
            nhat_ky_id = str(uuid.uuid4())
            nhat_ky = BangNhatKy(
                id=nhat_ky_id,
                nguon_tin=nguon_tin,
                thoi_gian_bat_dau=datetime.now(tz=timezone.utc),
                trang_thai="RUNNING",
            )
            session.add(nhat_ky)
            session.commit()
            return nhat_ky_id
        except Exception as e:
            session.rollback()
            logger.error(f"Lỗi tạo nhật ký: {e}")
            return ""
        finally:
            session.close()

    def cap_nhat_nhat_ky(
        self,
        nhat_ky_id: str,
        so_bai_thu_thap: int = 0,
        so_bai_moi: int = 0,
        trang_thai: str = "SUCCESS",
        loi: Optional[str] = None,
    ) -> None:
        """Cập nhật nhật ký thu thập khi hoàn thành."""
        session = self._db.tao_phien()
        try:
            nhat_ky = session.query(BangNhatKy).filter_by(id=nhat_ky_id).first()
            if nhat_ky:
                nhat_ky.thoi_gian_ket_thuc = datetime.now(tz=timezone.utc)
                nhat_ky.so_bai_thu_thap = so_bai_thu_thap
                nhat_ky.so_bai_moi = so_bai_moi
                nhat_ky.trang_thai = trang_thai
                nhat_ky.thong_bao_loi = loi
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Lỗi cập nhật nhật ký: {e}")
        finally:
            session.close()

    # --- Phương thức nội bộ ---

    def _chuyen_doi(self, ban_ghi: BangTinTuc) -> BaiBao:
        """Chuyển đổi từ ORM model sang Pydantic model."""
        ma_ck = []
        if ban_ghi.ma_chung_khoan_lien_quan:
            try:
                ma_ck = json.loads(ban_ghi.ma_chung_khoan_lien_quan)
            except (json.JSONDecodeError, TypeError):
                ma_ck = []

        return BaiBao(
            id=ban_ghi.id,
            tieu_de=ban_ghi.tieu_de,
            noi_dung_tom_tat=ban_ghi.noi_dung_tom_tat or "",
            noi_dung_goc=ban_ghi.noi_dung_goc or "",
            url=ban_ghi.url,
            nguon_tin=ban_ghi.nguon_tin,
            thoi_gian_xuat_ban=ban_ghi.thoi_gian_xuat_ban,
            danh_muc=DanhMuc(ban_ghi.danh_muc) if ban_ghi.danh_muc else DanhMuc.VI_MO,
            ma_chung_khoan_lien_quan=ma_ck,
            diem_cam_xuc=ban_ghi.diem_cam_xuc or 0.0,
            nhan_cam_xuc=CamXuc(ban_ghi.nhan_cam_xuc) if ban_ghi.nhan_cam_xuc else CamXuc.TRUNG_TINH,
            vector_id=ban_ghi.vector_id,
            trang_thai=ban_ghi.trang_thai,
            thoi_gian_tao=ban_ghi.thoi_gian_tao,
        )

    @staticmethod
    def _phan_tich_khung_thoi_gian(khung: str) -> Optional[datetime]:
        """Phân tích chuỗi khung thời gian thành datetime.

        Hỗ trợ: '1d' (1 ngày), '7d' (7 ngày), '1w' (1 tuần),
                 '1m' (1 tháng), '3m' (3 tháng)
        """
        khung = khung.strip().lower()
        now = datetime.now(tz=timezone.utc)

        mapping = {
            "1d": timedelta(days=1),
            "3d": timedelta(days=3),
            "7d": timedelta(days=7),
            "1w": timedelta(weeks=1),
            "2w": timedelta(weeks=2),
            "1m": timedelta(days=30),
            "3m": timedelta(days=90),
            "6m": timedelta(days=180),
            "1y": timedelta(days=365),
        }

        delta = mapping.get(khung)
        if delta:
            return now - delta

        # Thử parse số + đơn vị
        try:
            if khung.endswith("d"):
                return now - timedelta(days=int(khung[:-1]))
            elif khung.endswith("w"):
                return now - timedelta(weeks=int(khung[:-1]))
            elif khung.endswith("m"):
                return now - timedelta(days=int(khung[:-1]) * 30)
        except ValueError:
            pass

        return None
