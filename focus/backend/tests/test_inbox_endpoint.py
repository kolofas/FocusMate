# tests/test_inbox_endpoint.py
def test_inbox_telegram_creates_task_and_dedups(client):
    payload = {"text": "Купить хлеб #urgent 2025-12-31 12:00"}
    r1 = client.post("/inbox/telegram", json=payload)
    assert r1.status_code == 201, r1.text
    # task_id = (
    #     r1.json()["id"]
    #     if "id" in r1.json()
    #     else r1.json().get("task", {}).get("id", None)
    # )

    # повтор — должен дать 409 в окне дедупа
    r2 = client.post("/inbox/telegram", json=payload)
    assert r2.status_code == 409, r2.text
