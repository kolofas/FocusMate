from __future__ import annotations

import pytest


@pytest.mark.anyio
async def test_repeat_action_creates_new_progress_entry(client):
    created = await client.post(
        "/life/actions/log",
        json={
            "template_id": 1,  # health = 3
            "happened_at": "2026-04-20T10:00:00Z",
        },
    )
    assert created.status_code == 200
    source_id = created.json()["user_action_id"]

    repeated = await client.post(
        "/life/actions/repeat",
        json={
            "user_action_id": source_id,
            "happened_at": "2026-04-20T12:00:00Z",
        },
    )
    assert repeated.status_code == 200
    body = repeated.json()
    assert body["repeated_from_action_id"] == source_id
    assert body["delta_points"] == 3

    dashboard = await client.get(
        "/life/dashboard/today",
        params={"for_date": "2026-04-20"},
    )
    assert dashboard.status_code == 200
    assert dashboard.json()["total_points"] == 6


@pytest.mark.anyio
async def test_repeat_action_returns_not_found_for_unknown_source(client):
    repeated = await client.post(
        "/life/actions/repeat",
        json={
            "user_action_id": 999999,
        },
    )
    assert repeated.status_code == 404
    body = repeated.json()
    assert body["error"]["code"] == "not_found"
