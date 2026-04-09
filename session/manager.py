from typing import List, Optional
from core.topic import Topic
from core.event import TurnResult, DiscussionEvent
from core.message import Message, Role
from harness_engine.engine import HarnessEngine
from .store import MemorySessionStore
from .store_redis import RedisSessionStore
from .models import DiscussionSession


class SessionManager:
    """
    会话层：桥接前端适配器与 Harness Engine。
    
    - 维护 Session 生命周期
    - 把用户输入翻译为 Topic
    - 调用 Harness Engine 生成 TurnResult
    - 把 TurnResult 翻译为前端可消费的事件序列
    """

    def __init__(self, engine: HarnessEngine, store=None):
        self.engine = engine
        self.store = store or MemorySessionStore()

    def create_session(self, session_id: str, user_message: str) -> DiscussionSession:
        session = DiscussionSession(
            session_id=session_id,
            topic_text=user_message,
        )
        self.store.save(session)
        return session

    def run_discussion(
        self,
        session_id: str,
        user_message: str,
        max_rounds: int = 2,
        force_manual: bool = False,
    ) -> List[DiscussionEvent]:
        session = self.store.get(session_id)
        if session is None:
            session = self.create_session(session_id, user_message)

        topic = Topic(text=user_message)
        turn_results = self.engine.run(topic, max_rounds=max_rounds, force_manual=force_manual)

        session.turn_results.extend(turn_results)
        self.store.save(session)

        return self._turns_to_events(turn_results)

    def run_discussion_consensus(
        self,
        session_id: str,
        user_message: str,
        max_rounds: int = 10,
        force_manual: bool = False,
    ) -> List[DiscussionEvent]:
        session = self.store.get(session_id)
        if session is None:
            session = self.create_session(session_id, user_message)

        topic = Topic(text=user_message)
        turn_results = self.engine.run_until_consensus(
            topic=topic,
            max_rounds=max_rounds,
            force_manual=force_manual,
        )

        session.turn_results.extend(turn_results)
        self.store.save(session)

        return self._turns_to_events(turn_results)

    @staticmethod
    def _turns_to_events(turn_results: List[TurnResult]) -> List[DiscussionEvent]:
        events: List[DiscussionEvent] = []
        for turn in turn_results:
            for msg in turn.messages:
                if msg.metadata.get("type") == "consensus":
                    evt_type = "consensus"
                elif msg.is_moderation:
                    evt_type = "moderation"
                else:
                    evt_type = "message"
                events.append(DiscussionEvent(
                    event_type=evt_type,
                    payload=msg,
                    round_num=msg.metadata.get("round", 0),
                ))
        return events
