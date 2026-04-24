import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.server import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["status"] == "ok"


def test_discuss_endpoint(client):
    # 把默认 provider 换成 mock，避免调用真实 API
    from api.server import session_manager, router
    from tests.conftest import MockProvider

    mock = MockProvider()
    router.default_provider = mock
    # 也要更新 engine 的 router（因为 engine 已经实例化了）
    session_manager.engine.router = router

    payload = {"message": "测试问题", "session_id": "test-sess", "max_rounds": 1, "force_manual": True}
    resp = client.post("/v1/discuss", json=payload)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "events" in data
    assert data["session_id"] == "test-sess"
    # 4 debaters + 1 moderator
    assert len(data["events"]) == 5


def test_discuss_missing_message(client):
    resp = client.post("/v1/discuss", json={})
    assert resp.status_code == 400
    assert b"message is required" in resp.data
