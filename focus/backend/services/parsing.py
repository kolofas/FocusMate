# parsing.py
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo
from ..settings import settings


@dataclass(frozen=True)
class ParsedInbox:
    """
    Результат разбора входного текста:
    - raw: исходный текст
    - title: заголовок без тегов (первая строка, обрезанная по длине)
    - tags: список найденных тегов без '#', в исходном регистре (нормализацию делаем на уровне сервисов)
    - deadline_local: локальный дедлайн (tz-aware, Europe/Amsterdam) или None
    """

    raw: str
    title: str
    tags: list[str]
    deadline_local: Optional[datetime]  # tz-aware локальное время


class InboxParser:
    """
    Парсер входного текста из инбокса.
    Выделяет #tags, ISO-дедлайн и формирует заголовок без тегов.
    """

    ISO_DT = re.compile(
        r"\b(?P<date>\d{4}-\d{2}-\d{2})(?:[ T](?P<time>\d{2}:\d{2}))?\b"
    )
    TAGS = re.compile(r"#(?P<tag>[A-Za-z0-9_]+)")

    def __init__(self, tz: ZoneInfo | None = None, title_limit: int = 300) -> None:
        self.tz = tz or ZoneInfo("Europe/Amsterdam")
        self.title_limit = title_limit or settings.max_title_length

    def parse(self, text: str) -> ParsedInbox:
        raw = text or ""
        tags = self._extract_tags(raw)
        title = self._build_title_without_tags(raw)
        deadline = self._parse_iso_deadline(raw)

        return ParsedInbox(raw=raw, title=title, tags=tags, deadline_local=deadline)

    def _extract_tags(self, text: str) -> list[str]:
        """
        Возвращает теги без символа '#', в исходном регистре.
        Нормализация (нижний регистр, trim, dedup) — на уровне сервисов.
        """
        return [m.group("tag") for m in self.TAGS.finditer(text)]

    def _build_title_without_tags(self, text: str) -> str:
        """
        Убирает теги из текста и берёт первую строку, обрезая до title_limit.
        """
        no_tags = self.TAGS.sub("", text).strip()
        first_line = no_tags.splitlines()[0] if no_tags else ""
        title = " ".join(first_line.split())
        return title[: self.title_limit]

    def _parse_iso_deadline(self, text: str) -> Optional[datetime]:
        """
        Ищет первую ISO-дату в тексте и возвращает tz-aware datetime в Europe/Amsterdam.
        Правила:
          - если указана только дата → дедлайн = 23:59 этого дня;
          - если указана дата и время → используем указанное время.
        """
        m = self.ISO_DT.search(text)
        if not m:
            return None

        date_part = m.group("date")  # YYYY-MM-DD
        time_part = m.group("time")  # HH:MM | None

        try:
            if time_part:
                yyyy, mm, dd = (int(p) for p in date_part.split("-"))
                hh, mn = (int(p) for p in time_part.split(":"))
                dt = datetime(yyyy, mm, dd, hh, mn, tzinfo=self.tz)
            else:
                yyyy, mm, dd = (int(p) for p in date_part.split("-"))
                dt = datetime(yyyy, mm, dd, 23, 59, tzinfo=self.tz)
            return dt
        except ValueError:
            # Невалидная дата/время → дедлайн отсутствует
            return None
