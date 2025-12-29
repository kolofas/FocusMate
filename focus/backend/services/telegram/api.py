import logging

from typing import Optional
import httpx
from focus.backend.settings import settings

log = logging.getLogger(__name__)


async def send_reply(chat_id: Optional[int], text: str) -> None:
    """
    Отправляет ответ пользователю.
    Ошибки доставки не пробрасываем — вебхук важнее.
    """
    if not chat_id:
        return

    token = settings.telegram_bot_token
    if not token:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(url, json=payload)
    except Exception:
        log.exception("Failed to send telegram message to chat_id=%s", chat_id)
