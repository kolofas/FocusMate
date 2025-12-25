from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class TaskListQuery(BaseModel):
    user_id: int | None = Field(
        None, description="Filter by user_id; None = common tasks"
    )

    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)

    status: Optional[str] = Field(None, description="Task status")
    q: Optional[str] = Field(None, description="Case-insensitive substring in title")
    tag: Optional[str] = Field(None, description="Filter by tag (without #)")

    order_by: str = Field("created_at")
    direction: str = Field("desc")

    def normalized(self) -> "TaskListQuery":
        """
        Нормализация пользовательского ввода.
        Здесь — всё, что относится к *данным запроса*, а не к БД.
        """
        data = self.model_dump()

        if data["tag"]:
            data["tag"] = data["tag"].lower()

        if data["q"]:
            data["q"] = data["q"].strip()

        return TaskListQuery(**data)
