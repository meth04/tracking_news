"""Kết nối và quản lý cơ sở dữ liệu (PostgreSQL / SQLite)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config.settings import lay_cau_hinh_database

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class cho tất cả SQLAlchemy models."""
    pass


class BangTinTuc(Base):
    """ORM model cho bảng tin_tuc_tai_chinh."""

    __tablename__ = "tin_tuc_tai_chinh"

    id = Column(String(36), primary_key=True)
    tieu_de = Column(String(500), nullable=False)
    noi_dung_tom_tat = Column(Text, default="")
    noi_dung_goc = Column(Text, default="")
    url = Column(String(2000), nullable=False, unique=True)
    nguon_tin = Column(String(100), nullable=False)
    thoi_gian_xuat_ban = Column(DateTime(timezone=True), nullable=False)
    danh_muc = Column(String(20), nullable=False, default="MACRO")
    ma_chung_khoan_lien_quan = Column(Text, default="")  # JSON string cho SQLite
    diem_cam_xuc = Column(Float, default=0.0)
    nhan_cam_xuc = Column(String(20), default="NEUTRAL")
    vector_id = Column(String(36), nullable=True)
    trang_thai = Column(String(20), default="PENDING")
    thoi_gian_tao = Column(DateTime(timezone=True))


class BangNhatKy(Base):
    """ORM model cho bảng nhat_ky_thu_thap."""

    __tablename__ = "nhat_ky_thu_thap"

    id = Column(String(36), primary_key=True)
    nguon_tin = Column(String(100), nullable=False)
    thoi_gian_bat_dau = Column(DateTime(timezone=True), nullable=False)
    thoi_gian_ket_thuc = Column(DateTime(timezone=True), nullable=True)
    so_bai_thu_thap = Column(Integer, default=0)
    so_bai_moi = Column(Integer, default=0)
    trang_thai = Column(String(20), default="RUNNING")
    thong_bao_loi = Column(Text, nullable=True)


class QuanLyDatabase:
    """Quản lý kết nối và phiên làm việc với database."""

    def __init__(self, database_url: Optional[str] = None):
        if database_url is None:
            cau_hinh = lay_cau_hinh_database()
            database_url = cau_hinh.url

        # Chuyển async URL sang sync cho SQLAlchemy sync engine
        sync_url = database_url
        if "asyncpg" in sync_url:
            sync_url = sync_url.replace("postgresql+asyncpg", "postgresql")
        elif "aiosqlite" in sync_url:
            sync_url = sync_url.replace("sqlite+aiosqlite", "sqlite")

        # Tạo thư mục data nếu dùng SQLite
        if sync_url.startswith("sqlite"):
            db_path = sync_url.replace("sqlite:///", "")
            if db_path and db_path != ":memory:":
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self._engine = create_engine(
            sync_url,
            echo=False,
            pool_pre_ping=True if "postgresql" in sync_url else False,
        )
        self._session_factory = sessionmaker(bind=self._engine)
        logger.info(
            "Kết nối database thành công",
            extra={"extra_fields": {"url": sync_url.split("@")[-1] if "@" in sync_url else sync_url}},
        )

    def khoi_tao_bang(self) -> None:
        """Tạo tất cả bảng nếu chưa tồn tại."""
        Base.metadata.create_all(self._engine)
        logger.info("Đã khởi tạo cấu trúc database")

    def tao_phien(self) -> Session:
        """Tạo một phiên làm việc mới."""
        return self._session_factory()

    def dong_ket_noi(self) -> None:
        """Đóng engine database."""
        self._engine.dispose()
        logger.info("Đã đóng kết nối database")


# Singleton instance
_quan_ly: Optional[QuanLyDatabase] = None


def lay_quan_ly_db(database_url: Optional[str] = None) -> QuanLyDatabase:
    """Lấy hoặc tạo QuanLyDatabase singleton."""
    global _quan_ly
    if _quan_ly is None:
        _quan_ly = QuanLyDatabase(database_url)
    return _quan_ly
