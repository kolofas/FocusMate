from types import SimpleNamespace
from datetime import datetime, timezone

import pytest

from focus.backend.services.telegram import callbacks as callbacks_module
from focus.backend.services.telegram import next_actions as next_actions_module
from focus.backend.services.telegram.screens.today_screen import (
    render_today,
    resolve_screen_message_id,
)
from focus.backend.services.telegram import time_badges as time_badges_module


def test_resolve_screen_message_id_prefers_callback_message_id():
    ctx = SimpleNamespace(telegram_user=SimpleNamespace(screen_message_id=321))
    assert resolve_screen_message_id(ctx, callback_message_id=555) == 555


def test_resolve_screen_message_id_falls_back_to_saved_screen_message_id():
    ctx = SimpleNamespace(telegram_user=SimpleNamespace(screen_message_id=321))
    assert resolve_screen_message_id(ctx, callback_message_id=None) == 321


@pytest.mark.anyio
async def test_handle_callback_routes_del_no(monkeypatch):
    calls: dict[str, object] = {}

    async def fake_handle_delete_no(ctx, *, callback_query_id, message_id):
        calls["ctx"] = ctx
        calls["callback_query_id"] = callback_query_id
        calls["message_id"] = message_id

    async def fake_answer_callback_query(
        callback_query_id, *, text=None, show_alert=False
    ):
        calls["answer_called"] = True

    monkeypatch.setattr(callbacks_module, "handle_delete_no", fake_handle_delete_no)
    monkeypatch.setattr(
        callbacks_module, "answer_callback_query", fake_answer_callback_query
    )

    ctx = SimpleNamespace()
    handled = await callbacks_module.handle_callback(
        data="del_no",
        ctx=ctx,
        callback_query_id="cq_1",
        message_id=77,
    )

    assert handled is True
    assert calls["ctx"] is ctx
    assert calls["callback_query_id"] == "cq_1"
    assert calls["message_id"] == 77
    assert "answer_called" not in calls


@pytest.mark.anyio
async def test_handle_callback_routes_today_replan_with_action(monkeypatch):
    calls: dict[str, object] = {}

    async def fake_handle_today_refresh_or_replan(ctx, *, action, message_id):
        calls["ctx"] = ctx
        calls["action"] = action
        calls["message_id"] = message_id
        return True

    async def fake_answer_callback_query(
        callback_query_id, *, text=None, show_alert=False
    ):
        calls["callback_query_id"] = callback_query_id
        calls["answer_text"] = text

    monkeypatch.setattr(
        callbacks_module,
        "handle_today_refresh_or_replan",
        fake_handle_today_refresh_or_replan,
    )
    monkeypatch.setattr(
        callbacks_module, "answer_callback_query", fake_answer_callback_query
    )

    ctx = SimpleNamespace()
    handled = await callbacks_module.handle_callback(
        data="today_replan",
        ctx=ctx,
        callback_query_id="cq_2",
        message_id=88,
    )

    assert handled is True
    assert calls["ctx"] is ctx
    assert calls["action"] == "today_replan"
    assert calls["message_id"] == 88
    assert calls["callback_query_id"] == "cq_2"


def test_format_task_time_badges_renders_deadline_and_reminder(monkeypatch):
    monkeypatch.setattr(time_badges_module.settings, "app_timezone", "UTC")
    fixed_now = datetime(2026, 4, 10, 8, 0, tzinfo=timezone.utc)

    class _FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now if tz else fixed_now.replace(tzinfo=None)

    monkeypatch.setattr(time_badges_module, "datetime", _FixedDateTime)

    task = SimpleNamespace(
        deadline=datetime(2026, 4, 10, 10, 30, tzinfo=timezone.utc),
        reminder_at=datetime(2026, 4, 10, 9, 0, tzinfo=timezone.utc),
    )

    rendered = time_badges_module.format_task_time_badges(task)

    assert "⏳ сегодня 10:30" in rendered
    assert "⏰ сегодня 09:00" in rendered


@pytest.mark.anyio
async def test_render_today_and_next_action_include_time_badges(monkeypatch):
    monkeypatch.setattr(time_badges_module.settings, "app_timezone", "UTC")
    fixed_now = datetime(2026, 4, 10, 8, 0, tzinfo=timezone.utc)

    class _FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now if tz else fixed_now.replace(tzinfo=None)

    monkeypatch.setattr(time_badges_module, "datetime", _FixedDateTime)

    task = SimpleNamespace(
        id=23,
        title="Reminder task",
        status="planned",
        tags=["focusmate"],
        deadline=datetime(2026, 4, 10, 10, 30, tzinfo=timezone.utc),
        reminder_at=datetime(2026, 4, 10, 9, 0, tzinfo=timezone.utc),
    )
    plan = SimpleNamespace(
        date="2026-04-10", items=[SimpleNamespace(rank=1, score=40, task=task)]
    )
    ctx = SimpleNamespace(db=object(), telegram_user=SimpleNamespace(id=1))

    async def fake_get_plan_today(
        db, *, user_id, ensure_build=True, force_rebuild=False
    ):
        return plan

    monkeypatch.setattr(
        "focus.backend.services.telegram.screens.today_screen.get_plan_today",
        fake_get_plan_today,
    )
    monkeypatch.setattr(
        "focus.backend.services.telegram.next_actions.get_plan_today",
        fake_get_plan_today,
    )

    text, _ = await render_today(ctx, args=[])
    next_line = await next_actions_module.suggest_next_action_line(ctx)

    assert "⏳ сегодня 10:30" in text
    assert "⏰ сегодня 09:00" in text
    assert "⏳ сегодня 10:30" in next_line
    assert "⏰ сегодня 09:00" in next_line
