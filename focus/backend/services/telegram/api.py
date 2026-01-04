import logging

from typing import Optional, Any
import httpx
from focus.backend.settings import settings

log = logging.getLogger(__name__)


async def send_reply(
    chat_id: Optional[int],
    text: str,
    *,
    parse_mode: Optional[str] = None,
    reply_markup: Optional[dict[str, Any]] = None,
    disable_web_page_preview: bool = True,
) -> None:
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
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": disable_web_page_preview,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(url, json=payload)
    except Exception:
        log.exception("Failed to send telegram message to chat_id=%s", chat_id)


async def answer_callback_query(
    callback_query_id: Optional[str],
    *,
    text: Optional[str] = None,
    show_alert: bool = False,
) -> None:
    if not callback_query_id:
        return

    token = settings.telegram_bot_token
    if not token:
        return

    url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
    payload: dict[str, Any] = {
        "callback_query_id": callback_query_id,
        "show_alert": show_alert,
    }
    if text:
        payload["text"] = text

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(url, json=payload)
    except Exception:
        log.exception("Failed to answer callback_query_id=%s", callback_query_id)


async def edit_message_text(
    chat_id: Optional[int],
    message_id: Optional[int],
    text: str,
    *,
    parse_mode: Optional[str] = None,
    reply_markup: Optional[dict[str, Any]] = None,
    disable_web_page_preview: bool = True,
) -> bool:
    if not chat_id or not message_id:
        return False

    token = settings.telegram_bot_token
    if not token:
        return False

    url = f"https://api.telegram.org/bot{token}/editMessageText"
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "disable_web_page_preview": disable_web_page_preview,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(url, json=payload)

            if resp.status_code == 400:
                # Важно увидеть причину всех 400, не только "not modified"
                if "message is not modified" in resp.text:
                    return False
                log.warning("editMessageText 400: %s", resp.text)
                return False

            if resp.status_code >= 400:
                log.error("editMessageText failed: %s %s", resp.status_code, resp.text)
                return False

            return True
    except Exception:
        log.exception(
            "Failed to edit telegram message chat_id=%s message_id=%s",
            chat_id,
            message_id,
        )
        return False
