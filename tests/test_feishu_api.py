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


def test_feishu_discuss_endpoint(client):
    from api.server import session_manager, router
    from tests.conftest import MockProvider

    mock = MockProvider()
    router.default_provider = mock
    session_manager.engine.router = router

    payload = {
        "event": {
            "message": {
                "content": json.dumps({"text": "飞书测试问题"}),
                "message_id": "msg-feishu-1",
            },
            "sender": {
                "sender_id": {"open_id": "ou_123"},
            },
        },
        "force_manual": True,
    }
    resp = client.post("/v1/feishu/discuss", json=payload)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data.get("msg_type") == "interactive"
    assert "card" in data
    elements = data["card"]["elements"]
    assert len(elements) > 0


def test_feishu_discuss_missing_message(client):
    payload = {
        "event": {
            "message": {
                "content": json.dumps({"text": ""}),
                "message_id": "msg-feishu-2",
            },
            "sender": {
                "sender_id": {"open_id": "ou_123"},
            },
        }
    }
    resp = client.post("/v1/feishu/discuss", json=payload)
    assert resp.status_code == 400
    assert b"message is required" in resp.data
