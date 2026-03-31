from types import SimpleNamespace

import pytest

from focus.backend.services.telegram.commands import COMMAND_HANDLERS
from focus.backend.services.telegram.commands import today as today_module


def test_refresh_alias_points_to_today_handler():
    assert COMMAND_HANDLERS["/refresh"] is COMMAND_HANDLERS["/today"]


@pytest.mark.anyio
async def test_command_today_forces_new_message(monkeypatch):
    calls: dict[str, object] = {}

    async def fake_refresh_today_screen(
        ctx,
        args=(),
        *,
        preferred_message_id=None,
        rebuild_plan=False,
        notice=None,
        force_new_message=False,
    ):
        calls["ctx"] = ctx
        calls["args"] = list(args)
        calls["force_new_message"] = force_new_message

    monkeypatch.setattr(today_module, "refresh_today_screen", fake_refresh_today_screen)

    ctx = SimpleNamespace()
    await today_module.command_today(ctx, args=["planned"])

    assert calls["ctx"] is ctx
    assert calls["args"] == ["planned"]
    assert calls["force_new_message"] is True
