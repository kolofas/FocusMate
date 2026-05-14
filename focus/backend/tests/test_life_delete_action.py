from __future__ import annotations

import pytest
from sqlalchemy import text


pytestmark = pytest.mark.anyio


@pytest.mark.anyio
async def test_delete_life_action_removes_recent_and_dashboard_points(client):
    create_resp = await client.post(
        "/life/actions/log",
        json={
            "template_id": 1,
            "happened_at": "2026-05-14T10:00:00Z",
        },
    )
    assert create_resp.status_code == 200, create_resp.text
    created_action_id = create_resp.json()["user_action_id"]

    delete_resp = await client.delete(f"/life/actions/{created_action_id}")
    assert delete_resp.status_code == 204, delete_resp.text

    recent_resp = await client.get("/life/actions/recent")
    assert recent_resp.status_code == 200
    assert recent_resp.json() == []

    dashboard_resp = await client.get("/life/dashboard/today", params={"for_date": "2026-05-14"})
    assert dashboard_resp.status_code == 200, dashboard_resp.text
    body = dashboard_resp.json()
    assert body["total_points"] == 0
    points_by_slug = {item["slug"]: item["points"] for item in body["categories"]}
    assert points_by_slug["health"] == 0


@pytest.mark.anyio
async def test_delete_life_action_is_user_scoped(client, db_session):
    await db_session.execute(
        text(
            """
            INSERT INTO telegram_users (id, chat_id, username, first_name)
            VALUES
                (10, 'life_u10', 'life10', 'Life10'),
                (20, 'life_u20', 'life20', 'Life20')
            """
        )
    )
    await db_session.commit()

    categories_10 = await client.get("/life/categories", params={"user_id": 10})
    assert categories_10.status_code == 200
    category_10_id = categories_10.json()[0]["id"]

    create_resp = await client.post(
        "/life/actions/log",
        json={
            "user_id": 10,
            "category_id": category_10_id,
            "title": "u10 action",
            "points": 3,
            "happened_at": "2026-05-14T10:00:00Z",
        },
    )
    assert create_resp.status_code == 200, create_resp.text
    created_action_id = create_resp.json()["user_action_id"]

    wrong_scope_delete = await client.delete(
        f"/life/actions/{created_action_id}",
        params={"user_id": 20},
    )
    assert wrong_scope_delete.status_code == 404

    recent_u10 = await client.get("/life/actions/recent", params={"user_id": 10})
    assert recent_u10.status_code == 200
    body = recent_u10.json()
    assert len(body) == 1
    assert body[0]["id"] == created_action_id

