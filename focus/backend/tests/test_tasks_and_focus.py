# tests/test_tasks_and_focus.py
from datetime import datetime, timezone, timedelta

def test_tasks_crud_and_focus_today(client):
    # create a couple of tasks
    t1 = {"title": "Task A", "description": "A", "source": "manual", "tags": ["urgent"]}
    t2 = {"title": "Task B", "description": "B", "source": "manual", "deadline": (datetime.now(timezone.utc)+timedelta(hours=6)).isoformat(), "tags": []}

    r1 = client.post("/tasks/", json=t1)
    r2 = client.post("/tasks/", json=t2)
    assert r1.status_code == 201 and r2.status_code == 201

    # list tasks
    lst = client.get("/tasks/").json()
    assert len(lst) >= 2

    # build focus today
    fr = client.get("/focus/today")
    assert fr.status_code == 200
    data = fr.json()
    assert "items" in data
    # как минимум одна задача попала в список
    assert len(data["items"]) >= 1
