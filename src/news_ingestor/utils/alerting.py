"""Gửi cảnh báo tùy chọn qua Telegram dựa trên env flags."""

from __future__ import annotations

import logging

import httpx

from news_ingestor.models.article import BaiBao

logger = logging.getLogger(__name__)


class BoCanhBaoTelegram:
    """Alert sender cho Telegram với cơ chế bật/tắt qua env."""

    def __init__(
        self,
        bat_canh_bao: bool = False,
        bot_token: str = "",
        chat_id: str = "",
        timeout: int = 10,
    ):
        self._bat_canh_bao = bat_canh_bao
        self._bot_token = bot_token.strip()
        self._chat_id = chat_id.strip()
        self._timeout = timeout

    @property
    def kha_dung(self) -> bool:
        return self._bat_canh_bao and bool(self._bot_token) and bool(self._chat_id)

    def gui_canh_bao_bai_bao(self, bai_bao: BaiBao) -> bool:
        """Gửi cảnh báo cho bài báo tác động cao."""
        if not self.kha_dung:
            return False

        if not bai_bao.is_high_impact:
            return False

        thong_diep = self._tao_thong_diep(bai_bao)
        return self._gui_telegram(thong_diep)

    def _tao_thong_diep(self, bai_bao: BaiBao) -> str:
        tags = ", ".join(bai_bao.impact_tags[:5]) if bai_bao.impact_tags else "-"
        return (
            "📣 <b>Tin tác động cao</b>\n"
            f"• Mức: <b>{bai_bao.impact_level}</b> (score={bai_bao.impact_score})\n"
            f"• Nguồn: {bai_bao.nguon_tin}\n"
            f"• Tiêu đề: {bai_bao.tieu_de}\n"
            f"• Tags: {tags}\n"
            f"• URL: {bai_bao.url}"
        )

    def _gui_telegram(self, thong_diep: str) -> bool:
        url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": thong_diep,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"Gửi cảnh báo Telegram thất bại: {e}")
            return False


def tao_bo_canh_bao_tu_env(
    telegram_enabled: bool,
    telegram_bot_token: str,
    telegram_chat_id: str,
) -> BoCanhBaoTelegram | None:
    """Khởi tạo alert sender từ cấu hình env đã đọc sẵn."""
    bo = BoCanhBaoTelegram(
        bat_canh_bao=telegram_enabled,
        bot_token=telegram_bot_token,
        chat_id=telegram_chat_id,
    )
    if bo.kha_dung:
        return bo
    return None
