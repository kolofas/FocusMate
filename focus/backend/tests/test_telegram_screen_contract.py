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
