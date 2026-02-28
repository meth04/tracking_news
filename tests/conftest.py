"""Fixtures dùng chung cho tất cả tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Thêm src và root vào path
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SRC))
