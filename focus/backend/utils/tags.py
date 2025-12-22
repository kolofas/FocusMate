from __future__ import annotations

from collections.abc import Sequence

__all__ = ["canonicalize_tags"]


def canonicalize_tags(tags: Sequence[str] | None) -> list[str]:
    """
    Возвращает приведённые к канону теги:
    - без ведущего '#'
    - без лишних пробелов
    - в нижнем регистре
    - без пустых значений и дублей
    - отсортированные (стабильный порядок на выходе)
    """
    if not tags:
        return []

    cleaned = (clean_tag(t) for t in tags)
    unique = {t for t in cleaned if t}  # set убирает дубли
    return sorted(unique)


def clean_tag(tag: str) -> str | None:
    """
    Приводит одиночный тег к канону. Пустые строки → None
    """
    if tag is None:
        return None
    t = tag.strip().lstrip("#").strip().lower()
    return t or None
