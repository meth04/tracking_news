"""Unit tests cho module cảnh báo Telegram."""

from __future__ import annotations

from datetime import datetime, timezone

from news_ingestor.models.article import BaiBao
from news_ingestor.utils.alerting import BoCanhBaoTelegram, tao_bo_canh_bao_tu_env


class TestAlerting:
    """Tests cho alert sender."""

    def test_tao_bo_canh_bao_tu_env(self):
        assert tao_bo_canh_bao_tu_env(False, "", "") is None
        assert tao_bo_canh_bao_tu_env(True, "", "123") is None
        assert tao_bo_canh_bao_tu_env(True, "token", "") is None
        assert tao_bo_canh_bao_tu_env(True, "token", "123") is not None

    def test_khong_gui_khi_khong_high_impact(self):
        bo = BoCanhBaoTelegram(bat_canh_bao=False, bot_token="", chat_id="")
        bai = BaiBao(
            tieu_de="Tin thường",
            url="https://example.com/1",
            nguon_tin="Test",
            thoi_gian_xuat_ban=datetime.now(tz=timezone.utc),
            is_high_impact=False,
        )
        assert bo.gui_canh_bao_bai_bao(bai) is False
