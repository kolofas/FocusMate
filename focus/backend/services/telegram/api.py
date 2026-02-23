import logging

from typing import Optional, Any
import httpx
from focus.backend.settings import settings

log = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}"


async def send_reply(
    chat_id: Optional[int],
    text: str,
    *,
    parse_mode: Optional[str] = None,
    reply_markup: Optional[dict[str, Any]] = None,
    disable_web_page_preview: bool = True,
) -> Optional[int]:
    """
    Отправляет ответ пользователю и возвращает message_id отправленного сообщения.
    Ошибки доставки не пробрасываем — вебхук важнее.
    """
    if not chat_id:
        return

    token = settings.telegram_bot_token
    if not token:
        return None

    url = f"{TELEGRAM_API_BASE.format(token=token)}/sendMessage"
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
            resp = await client.post(url, json=payload)

            if resp.status_code >= 400:
                log.error("sendMessage failed: %s %s", resp.status_code, resp.text)
                return None

            data = resp.json()
            if not data.get("ok"):
                log.error("sendMessage returned ok=false: %s", data)
                return None

            result = data.get("result") or {}
            message_id = result.get("message_id")
            if isinstance(message_id, int):
                return message_id

            log.warning("sendMessage: no message_id in result: %s", result)
            return None
    except Exception:
        log.exception("Failed to send telegram message to chat_id=%s", chat_id)
        return None


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

    url = f"{TELEGRAM_API_BASE.format(token=token)}/answerCallbackQuery"
    payload: dict[str, Any] = {
        "callback_query_id": callback_query_id,
        "show_alert": show_alert,
    }
    if text:
        payload["text"] = text

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code >= 400:
                log.error(
                    "answerCallbackQuery failed: %s %s", resp.status_code, resp.text
                )
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

    url = f"{TELEGRAM_API_BASE.format(token=token)}/editMessageText"
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

            data = resp.json()
            if not data.get("ok"):
                log.error("editMessageText returned ok=false: %s", data)
                return False

            return True
    except Exception:
        log.exception(
            "Failed to edit telegram message chat_id=%s message_id=%s",
            chat_id,
            message_id,
        )
        return False


async def send_or_edit(
    chat_id: Optional[int],
    message_id: Optional[int],
    text: str,
    *,
    parse_mode: Optional[str] = None,
    reply_markup: Optional[dict[str, Any]] = None,
    disable_web_page_preview: bool = True,
) -> Optional[int]:
    """
    Универсальный ответ:
    - если message_id есть и edit прошел - возвращаем message_id
    - иначе отправляем новое сообщение и возвращаем новый message_id
    """
    edited = False
    if chat_id and message_id:
        edited = await edit_message_text(
            chat_id,
            message_id,
            text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview,
        )
        if edited:
            return message_id

    # fallback: отправляем новое сообщение
    return await send_reply(
        chat_id,
        text,
        parse_mode=parse_mode,
        reply_markup=reply_markup,
        disable_web_page_preview=disable_web_page_preview,
    )
