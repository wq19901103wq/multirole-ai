from typing import Dict, Optional
from .models import DiscussionSession


class MemorySessionStore:
    """内存中的 session 存储，后续可替换为 Redis / DB"""

    def __init__(self):
        self._data: Dict[str, DiscussionSession] = {}

    def get(self, session_id: str) -> Optional[DiscussionSession]:
        return self._data.get(session_id)

    def save(self, session: DiscussionSession):
        self._data[session.session_id] = session

    def delete(self, session_id: str):
        self._data.pop(session_id, None)
