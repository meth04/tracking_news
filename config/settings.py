"""Cấu hình tập trung cho toàn bộ hệ thống thu thập tin tức tài chính."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Thư mục gốc dự án
THU_MUC_GOC = Path(__file__).resolve().parent.parent


class CauHinhDatabase(BaseSettings):
    """Cấu hình kết nối cơ sở dữ liệu."""

    url: str = Field(
        default="sqlite+aiosqlite:///./data/tin_tuc.db",
        alias="DATABASE_URL",
        description="Chuỗi kết nối database (PostgreSQL hoặc SQLite)",
    )

    @field_validator("url")
    @classmethod
    def _kiem_tra_database_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("DATABASE_URL không được để trống")
        if not (
            value.startswith("sqlite+")
            or value.startswith("postgresql+")
            or value.startswith("postgresql://")
        ):
            raise ValueError("DATABASE_URL phải là sqlite hoặc postgresql")
        return value

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


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

    @field_validator("url")
    @classmethod
    def _kiem_tra_qdrant_url(cls, value: str) -> str:
        value = value.strip()
        if not (value.startswith("http://") or value.startswith("https://")):
            raise ValueError("QDRANT_URL phải bắt đầu bằng http:// hoặc https://")
        return value

    @field_validator("ten_collection")
    @classmethod
    def _kiem_tra_collection(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QDRANT_COLLECTION không được để trống")
        return value

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


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

    @field_validator("gemini_api_key")
    @classmethod
    def _chuan_hoa_api_key(cls, value: str) -> str:
        return value.strip()

    @field_validator("embedding_model")
    @classmethod
    def _kiem_tra_embedding_model(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("EMBEDDING_MODEL không được để trống")
        return value

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class CauHinhCrawler(BaseSettings):
    """Cấu hình cho bộ thu thập dữ liệu."""

    khoang_cach_phut: int = Field(
        default=15,
        alias="CRAWL_INTERVAL_MINUTES",
        description="Khoảng cách giữa các lần thu thập (phút)",
        ge=1,
        le=1440,
    )
    timeout_giay: int = Field(
        default=30,
        alias="REQUEST_TIMEOUT",
        description="Timeout cho mỗi request HTTP (giây)",
        ge=5,
        le=300,
    )
    so_lan_thu_lai: int = Field(
        default=3,
        alias="MAX_RETRIES",
        description="Số lần thử lại khi request thất bại",
        ge=0,
        le=10,
    )
    user_agent: str = Field(
        default=(
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        alias="USER_AGENT",
        description="User-Agent header cho HTTP requests",
    )

    @field_validator("user_agent")
    @classmethod
    def _kiem_tra_user_agent(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("USER_AGENT không được để trống")
        return value

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class CauHinhHeThong(BaseSettings):
    """Cấu hình tổng hợp cho toàn hệ thống."""

    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Cấp độ log (DEBUG, INFO, WARNING, ERROR)",
    )
    telemetry_enabled: bool = Field(
        default=True,
        alias="METRICS_ENABLED",
        description="Bật ghi nhận metrics trong process",
    )
    telegram_alert_enabled: bool = Field(
        default=False,
        alias="TELEGRAM_ALERT_ENABLED",
        description="Bật/tắt gửi cảnh báo Telegram",
    )
    telegram_bot_token: str = Field(
        default="",
        alias="TELEGRAM_BOT_TOKEN",
        description="Telegram bot token",
    )
    telegram_chat_id: str = Field(
        default="",
        alias="TELEGRAM_CHAT_ID",
        description="Telegram chat id nhận cảnh báo",
    )

    @field_validator("log_level")
    @classmethod
    def _kiem_tra_log_level(cls, value: str) -> str:
        value = value.strip().upper()
        hop_le = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if value not in hop_le:
            raise ValueError(f"LOG_LEVEL không hợp lệ: {value}")
        return value

    @field_validator("telegram_bot_token", "telegram_chat_id")
    @classmethod
    def _chuan_hoa_telegram_fields(cls, value: str) -> str:
        return value.strip()

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


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

        if _he_thong.telegram_alert_enabled and (
            not _he_thong.telegram_bot_token or not _he_thong.telegram_chat_id
        ):
            raise ValueError(
                "TELEGRAM_ALERT_ENABLED=true nhưng thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID"
            )

    return _he_thong
