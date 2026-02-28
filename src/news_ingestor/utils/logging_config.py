"""Cấu hình structured logging dạng JSON."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from config.settings import lay_cau_hinh_he_thong


class JsonFormatter(logging.Formatter):
    """Formatter xuất log dạng JSON có cấu trúc."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Thêm extra fields nếu có
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload["extra"] = extra

        # Thêm exception info nếu có
        if record.exc_info and record.exc_info[1]:
            payload["error"] = str(record.exc_info[1])

        return json.dumps(payload, ensure_ascii=False, default=str)


class ConsoleFormatter(logging.Formatter):
    """Formatter đẹp cho terminal với màu sắc."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        thoi_gian = datetime.now(tz=timezone.utc).strftime("%H:%M:%S")

        prefix = f"{color}{self.BOLD}[{thoi_gian}] {record.levelname:>8}{self.RESET}"
        message = f"{prefix} │ {record.name}: {record.getMessage()}"

        if record.exc_info and record.exc_info[1]:
            message += f"\n{'':>22}└─ error: {record.exc_info[1]}"

        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            for key, value in extra.items():
                message += f"\n{'':>22}├─ {key}: {value}"

        return message


def cau_hinh_logging(
    cap_do: str | None = None,
    json_mode: bool = False,
) -> None:
    """Thiết lập logging cho toàn hệ thống.

    Args:
        cap_do: Cấp độ log (DEBUG, INFO, WARNING, ERROR). Mặc định từ .env.
        json_mode: True = JSON output (production), False = Console output (dev).
    """
    if cap_do is None:
        cau_hinh = lay_cau_hinh_he_thong()
        cap_do = cau_hinh.log_level

    handler = logging.StreamHandler(sys.stdout)

    if json_mode:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(ConsoleFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(cap_do.upper())

    logging.raiseExceptions = False

    # Giảm noise từ thư viện bên ngoài
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
