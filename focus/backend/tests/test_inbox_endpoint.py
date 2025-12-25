# tests/test_inbox_endpoint.py
import pytest


@pytest.mark.anyio
async def test_inbox_telegram_creates_task_and_dedups(client):
    payload = {"text": "Купить хлеб #urgent 2025-12-31 12:00"}
    r1 = await client.post("/inbox/telegram", json=payload)
    assert r1.status_code == 201, r1.text
    r2 = await client.post("/inbox/telegram", json=payload)
    assert r2.status_code == 409, r2.text
