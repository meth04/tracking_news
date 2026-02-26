"""Cấu hình tập trung cho toàn bộ hệ thống thu thập tin tức tài chính."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field


# Thư mục gốc dự án
THU_MUC_GOC = Path(__file__).resolve().parent.parent


class CauHinhDatabase(BaseSettings):
    """Cấu hình kết nối cơ sở dữ liệu."""

    url: str = Field(
        default="sqlite+aiosqlite:///./data/tin_tuc.db",
        alias="DATABASE_URL",
        description="Chuỗi kết nối database (PostgreSQL hoặc SQLite)",
    )

    class Config:
        env_file = ".env"
        extra = "ignore"


class CauHinhQdrant(BaseSettings):
    """Cấu hình Vector Database Qdrant."""

    url: str = Field(
        default="http://localhost:6333",
        alias="QDRANT_URL",
        description="URL kết nối Qdrant",
    )
    ten_collection: str = Field(
        default="tin_tuc_tai_chinh",
        alias="QDRANT_COLLECTION",
        description="Tên collection trong Qdrant",
    )

    class Config:
        env_file = ".env"
        extra = "ignore"


class CauHinhNLP(BaseSettings):
    """Cấu hình mô hình NLP và AI."""

    gemini_api_key: str = Field(
        default="",
        alias="GEMINI_API_KEY",
        description="API key cho Google Gemini",
    )
    embedding_model: str = Field(
        default="paraphrase-multilingual-MiniLM-L12-v2",
        alias="EMBEDDING_MODEL",
        description="Tên model sentence-transformers",
    )

    class Config:
        env_file = ".env"
        extra = "ignore"


class CauHinhCrawler(BaseSettings):
    """Cấu hình cho bộ thu thập dữ liệu."""

    khoang_cach_phut: int = Field(
        default=15,
        alias="CRAWL_INTERVAL_MINUTES",
        description="Khoảng cách giữa các lần thu thập (phút)",
    )
    timeout_giay: int = Field(
        default=30,
        alias="REQUEST_TIMEOUT",
        description="Timeout cho mỗi request HTTP (giây)",
    )
    so_lan_thu_lai: int = Field(
        default=3,
        alias="MAX_RETRIES",
        description="Số lần thử lại khi request thất bại",
    )
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        alias="USER_AGENT",
        description="User-Agent header cho HTTP requests",
    )

    class Config:
        env_file = ".env"
        extra = "ignore"


class CauHinhHeThong(BaseSettings):
    """Cấu hình tổng hợp cho toàn hệ thống."""

    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Cấp độ log (DEBUG, INFO, WARNING, ERROR)",
    )

    class Config:
        env_file = ".env"
        extra = "ignore"


# Singleton instances
_database: CauHinhDatabase | None = None
_qdrant: CauHinhQdrant | None = None
_nlp: CauHinhNLP | None = None
_crawler: CauHinhCrawler | None = None
_he_thong: CauHinhHeThong | None = None


def lay_cau_hinh_database() -> CauHinhDatabase:
    """Lấy cấu hình database (singleton)."""
    global _database
    if _database is None:
        _database = CauHinhDatabase()
    return _database


def lay_cau_hinh_qdrant() -> CauHinhQdrant:
    """Lấy cấu hình Qdrant (singleton)."""
    global _qdrant
    if _qdrant is None:
        _qdrant = CauHinhQdrant()
    return _qdrant


def lay_cau_hinh_nlp() -> CauHinhNLP:
    """Lấy cấu hình NLP (singleton)."""
    global _nlp
    if _nlp is None:
        _nlp = CauHinhNLP()
    return _nlp


def lay_cau_hinh_crawler() -> CauHinhCrawler:
    """Lấy cấu hình crawler (singleton)."""
    global _crawler
    if _crawler is None:
        _crawler = CauHinhCrawler()
    return _crawler


def lay_cau_hinh_he_thong() -> CauHinhHeThong:
    """Lấy cấu hình hệ thống (singleton)."""
    global _he_thong
    if _he_thong is None:
        _he_thong = CauHinhHeThong()
    return _he_thong
