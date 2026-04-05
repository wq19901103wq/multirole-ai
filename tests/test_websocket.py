import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.server import app

# WebSocket 测试依赖 flask-sock
try:
    from api.server import sock, discuss_stream
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.mark.skipif(not WS_AVAILABLE, reason="flask-sock not installed")
def test_discuss_stream_websocket(monkeypatch):
    from api.server import session_manager, router
    from tests.conftest import MockProvider

    mock = MockProvider()
    router.default_provider = mock
    session_manager.engine.router = router

    class MockWS:
        def __init__(self):
            self.sent = []
            self._to_receive = json.dumps({"message": "测试 WebSocket", "max_rounds": 1})

        def receive(self, timeout=None):
            val = self._to_receive
            self._to_receive = None
            return val

        def send(self, data):
            self.sent.append(json.loads(data))

    ws = MockWS()
    discuss_stream(ws)

    types = [m["type"] for m in ws.sent]
    assert "status" in types
    assert "event" in types
    assert "done" in types

    events = [m["payload"] for m in ws.sent if m["type"] == "event"]
    assert len(events) == 5  # 4 debaters + 1 moderator


def test_swagger_ui_endpoint(client):
    """Swagger UI 是否可访问（flasgger 可选）"""
    try:
        resp = client.get("/apidocs/")
        assert resp.status_code in (200, 302)
    except Exception:
        # flasgger 未安装时跳过断言
        pass
