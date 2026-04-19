from __future__ import annotations

import pytest


@pytest.mark.anyio
async def test_repeat_shortcut_last_reuses_latest_action(client):
    first = await client.post(
        "/life/actions/log",
        json={
            "template_id": 1,
            "happened_at": "2026-04-20T10:00:00Z",
        },
    )
    assert first.status_code == 200

    second = await client.post(
        "/life/actions/log",
        json={
            "template_id": 3,
            "happened_at": "2026-04-20T11:00:00Z",
        },
    )
    assert second.status_code == 200

    repeated = await client.post(
        "/life/actions/repeat-shortcut",
        json={"mode": "last", "happened_at": "2026-04-20T12:00:00Z"},
    )
    assert repeated.status_code == 200
    body = repeated.json()
    assert body["delta_points"] == 3
    assert body["repeated_from_action_id"] == second.json()["user_action_id"]


@pytest.mark.anyio
async def test_repeat_shortcut_yesterday_uses_previous_day_action(client):
    yesterday = await client.post(
        "/life/actions/log",
        json={
            "template_id": 1,
            "happened_at": "2026-04-19T10:00:00Z",
        },
    )
    assert yesterday.status_code == 200

    repeated = await client.post(
        "/life/actions/repeat-shortcut",
        json={
            "mode": "yesterday",
            "reference_date": "2026-04-20",
            "happened_at": "2026-04-20T09:00:00Z",
        },
    )
    assert repeated.status_code == 200
    body = repeated.json()
    assert body["repeated_from_action_id"] == yesterday.json()["user_action_id"]


@pytest.mark.anyio
async def test_repeat_shortcut_validates_mode(client):
    invalid = await client.post(
        "/life/actions/repeat-shortcut",
        json={"mode": "weekly"},
    )
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "bad_request"
