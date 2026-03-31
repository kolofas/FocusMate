from types import SimpleNamespace

import pytest

from focus.backend.services.telegram import callbacks as callbacks_module
from focus.backend.services.telegram.screens.today_screen import (
    resolve_screen_message_id,
)


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
