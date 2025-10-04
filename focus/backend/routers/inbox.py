# backend/routers/inbox.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from focus.backend.database.core import get_db
from ..schemas import InboxTelegram, TaskRead
from focus.backend.database.enums import TaskSource, TaskStatus
from ..services import InboxParser, create_task_from_parsed, make_dedup, is_duplicate_inbox, save_inbox_event

router = APIRouter()

# создаём один инстанс парсера (можно держать на уровне модуля)
_parser = InboxParser(tz=ZoneInfo("Europe/Amsterdam"))

@router.post("/telegram", response_model=TaskRead, status_code=201)
def accept_from_telegram(payload: InboxTelegram, db: Session = Depends(get_db)):
    """
    Приём задачи из Telegram:
      1. считаем dedup-ключ → проверяем дубль,
      2. парсим текст,
      3. создаём Task,
      4. сохраняем событие инбокса,
      5. коммитим транзакцию.
    """
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(400, detail="empty inbox message")

    source = TaskSource.TELEGRAM
    dedup_key = make_dedup(text)

    if is_duplicate_inbox(db, source.value, dedup_key):
        raise HTTPException(409, "Duplicate inbox message")

    parsed = _parser.parse(text)

    try:
        task = create_task_from_parsed(
            db,
            parsed,
            source=source,
            status=TaskStatus.INBOX,
            raw_text=text,
        )
        save_inbox_event(db, source.value, dedup_key)
        db.commit()
        db.refresh(task)
        return task

    except Exception:
        db.rollback()
        raise


