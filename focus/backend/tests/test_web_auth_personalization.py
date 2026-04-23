from __future__ import annotations

import pytest


pytestmark = pytest.mark.anyio


async def _register(client, email: str, password: str) -> None:
    resp = await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 201, resp.text


async def _login(client, email: str, password: str) -> str:
    resp = await client.post(
        "/auth/jwt/login",
        data={"username": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    return body["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_web_auth_personalized_life_scope(client):
    email = "web-user@example.com"
    password = "verysecret123"

    await _register(client, email=email, password=password)
    token = await _login(client, email=email, password=password)

    me_resp = await client.get("/users/me", headers=_auth_headers(token))
    assert me_resp.status_code == 200
    me = me_resp.json()
    assert me["email"] == email
    assert me["telegram_user_id"] is not None

    log_resp = await client.post(
        "/life/actions/log",
        json={"template_id": 1},
        headers=_auth_headers(token),
    )
    assert log_resp.status_code == 200, log_resp.text

    recent_resp = await client.get(
        "/life/actions/recent",
        params={"limit": 1},
        headers=_auth_headers(token),
    )
    assert recent_resp.status_code == 200, recent_resp.text
    recent = recent_resp.json()
    assert len(recent) == 1
    assert recent[0]["user_id"] == me["telegram_user_id"]
