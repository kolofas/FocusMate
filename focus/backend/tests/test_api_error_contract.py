import pytest


@pytest.mark.anyio
async def test_error_contract_for_bad_request(client):
    resp = await client.get("/tasks/", params={"status": "wrong_status"})
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"] == "Invalid status"


@pytest.mark.anyio
async def test_error_contract_for_not_found(client):
    resp = await client.get("/tasks/999999")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "Task not found"


@pytest.mark.anyio
async def test_error_contract_for_validation_error(client):
    resp = await client.post(
        "/tasks/",
        json={"description": "missing title"},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == "Validation failed"
    assert isinstance(body["error"]["details"], list)
    assert body["error"]["details"]
