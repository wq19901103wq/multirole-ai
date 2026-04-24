import pytest
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from session.store_redis import RedisSessionStore
from session.models import DiscussionSession
from session.manager import SessionManager
from core.topic import Topic
from harness_engine.engine import HarnessEngine
from model_router.router import ModelRouter
from tests.conftest import MockProvider


@pytest.fixture
def redis_store():
    """真实的 Redis 存储，使用 db=15 避免污染默认数据。"""
    store = RedisSessionStore(host="localhost", port=6379, db=15, key_prefix="test:multirole:")
    # 清理测试数据
    for key in store.client.scan_iter(match=f"{store.key_prefix}*"):
        store.client.delete(key)
    yield store
    # teardown
    for key in store.client.scan_iter(match=f"{store.key_prefix}*"):
        store.client.delete(key)


def test_redis_store_save_and_get(redis_store):
    session = DiscussionSession(session_id="redis-sess-1", topic_text="测试话题")
    redis_store.save(session)

    loaded = redis_store.get("redis-sess-1")
    assert loaded is not None
    assert loaded.session_id == "redis-sess-1"
    assert loaded.topic_text == "测试话题"


def test_redis_store_delete(redis_store):
    session = DiscussionSession(session_id="redis-sess-2", topic_text="测试话题")
    redis_store.save(session)
    assert redis_store.get("redis-sess-2") is not None

    redis_store.delete("redis-sess-2")
    assert redis_store.get("redis-sess-2") is None


def test_redis_store_ttl(redis_store):
    session = DiscussionSession(session_id="redis-sess-3", topic_text="测试话题")
    redis_store.save(session)
    ttl = redis_store.client.ttl(redis_store._key("redis-sess-3"))
    assert ttl > 0


def test_session_manager_with_redis(redis_store):
    router = ModelRouter(default_provider=MockProvider())
    engine = HarnessEngine(router=router)
    manager = SessionManager(engine=engine, store=redis_store)

    events = manager.run_discussion(
        session_id="redis-sess-4",
        user_message="Redis 测试问题",
        max_rounds=1,
        force_manual=True,
    )
    assert len(events) == 5  # 4 debaters + 1 moderator

    # 验证 session 已持久化到 Redis
    loaded = redis_store.get("redis-sess-4")
    assert loaded is not None
    assert loaded.topic_text == "Redis 测试问题"
    assert len(loaded.turn_results) == 1


def test_api_with_redis_env(redis_store):
    """通过环境变量 MULTIROLE_REDIS_URL 启动 API 并使用 Redis。"""
    from api.server import app, session_manager as global_sm

    # 备份原 store
    original_store = global_sm.store

    # 切换到 Redis
    global_sm.store = redis_store

    try:
        app.config["TESTING"] = True
        with app.test_client() as client:
            payload = {
                "message": "Redis API 测试",
                "session_id": "redis-api-sess",
                "max_rounds": 1,
                "force_manual": True,
            }
            resp = client.post("/v1/discuss", json=payload)
            assert resp.status_code == 200
            data = json.loads(resp.data)
            assert data["session_id"] == "redis-api-sess"
            assert len(data["events"]) == 5

        # 验证 Redis 中确实存了数据
        loaded = redis_store.get("redis-api-sess")
        assert loaded is not None
        assert loaded.topic_text == "Redis API 测试"
    finally:
        # 恢复
        global_sm.store = original_store
