from __future__ import annotations

import pytest
from sqlalchemy import text


@pytest.mark.anyio
async def test_recent_actions_returns_latest_first_with_limit(client):
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

    resp = await client.get("/life/actions/recent", params={"limit": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["title"] == "30 min project work"
    assert body[0]["category_slug"] == "work_money"


@pytest.mark.anyio
async def test_recent_actions_can_filter_by_user_id(client, db_session):
    await db_session.execute(
        text(
            """
            INSERT INTO telegram_users (id, chat_id, username, first_name)
            VALUES
                (10, 'test_u10', 'u10', 'User10'),
                (20, 'test_u20', 'u20', 'User20')
            """
        )
    )
    await db_session.commit()

    categories_10 = await client.get("/life/categories", params={"user_id": 10})
    assert categories_10.status_code == 200
    category_10_id = categories_10.json()[0]["id"]

    categories_20 = await client.get("/life/categories", params={"user_id": 20})
    assert categories_20.status_code == 200
    category_20_id = categories_20.json()[0]["id"]

    r1 = await client.post(
        "/life/actions/log",
        json={
            "user_id": 10,
            "category_id": category_10_id,
            "title": "u10 action",
        },
    )
    assert r1.status_code == 200

    r2 = await client.post(
        "/life/actions/log",
        json={
            "user_id": 20,
            "category_id": category_20_id,
            "title": "u20 action",
        },
    )
    assert r2.status_code == 200

    filtered = await client.get("/life/actions/recent", params={"user_id": 10})
    assert filtered.status_code == 200
    body = filtered.json()
    assert len(body) == 1
    assert body[0]["user_id"] == 10
