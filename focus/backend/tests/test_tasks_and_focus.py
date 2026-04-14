# tests/test_tasks_and_focus.py
import pytest
from datetime import datetime, timezone, timedelta


@pytest.mark.anyio
async def test_tasks_crud_and_focus_today(client):
    # create a couple of tasks
    t1 = {"title": "Task A", "description": "A", "source": "manual", "tags": ["urgent"]}
    t2 = {
        "title": "Task B",
        "description": "B",
        "source": "manual",
        "deadline": (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat(),
        "tags": [],
    }

    r1 = await client.post("/tasks/", json=t1)
    r2 = await client.post("/tasks/", json=t2)
    assert r1.status_code == 201 and r2.status_code == 201

    # list tasks
    resp = await client.get("/tasks/")
    lst = resp.json()
    assert len(lst) >= 2

    # build focus today
    fr = await client.get("/focus/today")
    assert fr.status_code == 200
    data = fr.json()
    assert "items" in data
    # как минимум одна задача попала в список
    assert len(data["items"]) >= 1


@pytest.mark.anyio
async def test_focus_today_updates_after_snoozed_to_planned_status_change(client):
    # create one task
    payload = {"title": "Replan candidate", "description": "x", "source": "manual"}
    created = await client.post("/tasks/", json=payload)
    assert created.status_code == 201
    task_id = created.json()["id"]

    # build today's focus and ensure the task is there
    first_today = await client.get("/focus/today")
    assert first_today.status_code == 200
    first_ids = [item["task"]["id"] for item in first_today.json()["items"]]
    assert task_id in first_ids

    # move task out of planner candidates
    r1 = await client.post(f"/tasks/{task_id}/status", json={"status": "snoozed"})
    assert r1.status_code == 200

    second_today = await client.get("/focus/today")
    assert second_today.status_code == 200
    second_ids = [item["task"]["id"] for item in second_today.json()["items"]]
    assert task_id not in second_ids

    # move task back to planner candidates and ensure it appears again
    r2 = await client.post(f"/tasks/{task_id}/status", json={"status": "planned"})
    assert r2.status_code == 200

    third_today = await client.get("/focus/today")
    assert third_today.status_code == 200
    third_ids = [item["task"]["id"] for item in third_today.json()["items"]]
    assert task_id in third_ids


@pytest.mark.anyio
async def test_create_task_accepts_reminder_at(client):
    reminder_dt = datetime(2026, 4, 20, 10, 30, tzinfo=timezone.utc)
    reminder_at = reminder_dt.isoformat()
    payload = {
        "title": "Task with reminder",
        "description": "x",
        "source": "manual",
        "reminder_at": reminder_at,
    }

    created = await client.post("/tasks/", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "Task with reminder"
    returned = datetime.fromisoformat(body["reminder_at"].replace("Z", "+00:00"))
    assert returned == reminder_dt


@pytest.mark.anyio
async def test_patch_task_sets_and_clears_reminder_at(client):
    created = await client.post(
        "/tasks/",
        json={"title": "Patch reminder", "description": "x", "source": "manual"},
    )
    assert created.status_code == 201
    task_id = created.json()["id"]

    set_dt = datetime(2026, 4, 21, 9, 15, tzinfo=timezone.utc)
    set_value = set_dt.isoformat()
    patched_set = await client.patch(
        f"/tasks/{task_id}", json={"reminder_at": set_value}
    )
    assert patched_set.status_code == 200
    returned = datetime.fromisoformat(
        patched_set.json()["reminder_at"].replace("Z", "+00:00")
    )
    assert returned == set_dt

    patched_clear = await client.patch(f"/tasks/{task_id}", json={"reminder_at": None})
    assert patched_clear.status_code == 200
    assert patched_clear.json()["reminder_at"] is None
