from __future__ import annotations

import pytest


def _points_by_slug(categories: list[dict]) -> dict[str, int]:
    return {item["slug"]: item["points"] for item in categories}


@pytest.mark.anyio
async def test_life_dashboard_today_returns_category_points(client):
    first = await client.post(
        "/life/actions/log",
        json={
            "template_id": 1,  # health = 3
            "happened_at": "2026-04-20T10:00:00Z",
        },
    )
    assert first.status_code == 200

    second = await client.post(
        "/life/actions/log",
        json={
            "template_id": 3,  # work_money = 3
            "happened_at": "2026-04-20T11:00:00Z",
        },
    )
    assert second.status_code == 200

    resp = await client.get("/life/dashboard/today", params={"for_date": "2026-04-20"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["date"] == "2026-04-20"
    assert body["total_points"] == 6
    points = _points_by_slug(body["categories"])
    assert points["health"] == 3
    assert points["work_money"] == 3


@pytest.mark.anyio
async def test_life_dashboard_week_excludes_out_of_week_actions(client):
    in_week = await client.post(
        "/life/actions/log",
        json={
            "template_id": 1,  # health = 3
            "happened_at": "2026-04-20T10:00:00Z",  # monday
        },
    )
    assert in_week.status_code == 200

    out_week = await client.post(
        "/life/actions/log",
        json={
            "template_id": 2,  # health = 2
            "happened_at": "2026-04-27T10:00:00Z",  # next monday
        },
    )
    assert out_week.status_code == 200

    resp = await client.get("/life/dashboard/week", params={"for_date": "2026-04-22"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["week_start"] == "2026-04-20"
    assert body["week_end"] == "2026-04-26"
    assert body["total_points"] == 3
    points = _points_by_slug(body["categories"])
    assert points["health"] == 3
