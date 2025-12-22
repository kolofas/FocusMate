from __future__ import annotations

from typing import Any, Dict

import httpx
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database.core import get_db
from ..settings import settings
from ..services import telegram_bot
from ..services.telegram_users import get_or_create_telegram_user

router = APIRouter()
log = logging.getLogger("telegram")


def _require_webhook_secret(provided: str) -> None:
    """
    Проверяет секрет в пути вебхука.
    Используем простой shared-secret для dev.
    """
    expected = settings.telegram_webhook_secret
    if not expected or provided != expected:
        # 403 по умолчанию, чтобы не раскрывать детали
        raise HTTPException(status_code=403, detail="invalid webhook secret")


def _get_bot_token_or_500() -> str:
    """
    Возвращает токен бота или падает 500, если он не сконфигурирован.
    Это удобнее, чем молчаливое поведение, для dev.
    """
    token = settings.telegram_bot_token
    if not token:
        raise HTTPException(
            status_code=500, detail="TELEGRAM_BOT_TOKEN is not configured"
        )

    return token


@router.post("/webhook/{secret}")
async def telegram_webhook(
    secret: str, request: Request, db: Session = Depends(get_db)
):
    """
    Точка входа для Telegram webhook.
    Делает только:
    -проверку секрета,
    -парсинг апдейта,
    -делегирование в сервис бота.
    """
    _require_webhook_secret(secret)

    update: Dict[str, Any] = await request.json()

    if settings.telegram_log_updates:
        log.info("tg.update: %s", update)

    text, chat_id, meta = telegram_bot.extract_text_and_chat_id(update)
    if not text:
        return {"ok": True, "skipped": True}

    telegram_user = None
    if chat_id is not None:
        telegram_user = get_or_create_telegram_user(
            db,
            chat_id=chat_id,
            username=meta.get("username"),
            first_name=meta.get("first_name"),
        )

    # команды обрабатываем только если знаем пользователя
    if telegram_user is not None:
        handled = await telegram_bot.try_handle_command(
            text,
            chat_id,
            db,
            telegram_user,
        )
        if handled:
            return {"ok": True, "command": True}

    # обычный инбокс
    result = telegram_bot.process_inbox_text(
        db,
        text,
        telegram_user=telegram_user,
    )

    if result.get("duplicate"):
        await telegram_bot.send_reply(chat_id, text="Это уже есть в инбоксе 👌")
    else:
        await telegram_bot.send_reply(chat_id, text=f"Добавил: {result.get('title')}")

    return result


@router.post("/set_webhook")
async def set_webhook(base_url: str):
    """
    Устанавливает webhook в Telegram:
    Telegram → {base_url}/telegram/webhook/{secret}
    Удобно вызывать в dev после запуска ngrok.
    """
    token = _get_bot_token_or_500()
    if not settings.telegram_webhook_secret:
        raise HTTPException(
            status_code=400, detail="TELEGRAM_WEBHOOK_SECRET is not configured"
        )

    hook_url = (
        f"{base_url.rstrip('/')}/telegram/webhook/{settings.telegram_webhook_secret}"
    )

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            url=f"https://api.telegram.org/bot{token}/setWebhook",
            json={
                "url": hook_url,
                "drop_pending_updates": True,
            },
        )

    return resp.json()
