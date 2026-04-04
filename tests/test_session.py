import pytest
from core.topic import Topic
from harness_engine import HarnessEngine
from session import SessionManager, MemorySessionStore, DiscussionSession


def test_session_manager_create_and_run(router):
    engine = HarnessEngine(router)
    manager = SessionManager(engine=engine, store=MemorySessionStore())

    session = manager.create_session("sess-1", "测试问题")
    assert session.session_id == "sess-1"
    assert session.topic_text == "测试问题"

    events = manager.run_discussion("sess-1", "测试问题", max_rounds=1, force_manual=True)
    assert len(events) == 5  # 4 debaters + 1 moderator

    retrieved = manager.store.get("sess-1")
    assert retrieved is not None
    assert len(retrieved.turn_results) == 1


def test_session_manager_latest_summary(router):
    engine = HarnessEngine(router)
    manager = SessionManager(engine=engine)
    manager.run_discussion("sess-2", "测试", max_rounds=1, force_manual=True)
    session = manager.store.get("sess-2")
    assert session.latest_summary != ""
