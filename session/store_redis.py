import pickle
from typing import Optional
import redis
from .models import DiscussionSession


class RedisSessionStore:
    """Redis 中的 session 存储"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        key_prefix: str = "multirole:session:",
        ttl_seconds: int = 3600 * 24,  # 1天
    ):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=False,
        )
        self.key_prefix = key_prefix
        self.ttl_seconds = ttl_seconds

    def _key(self, session_id: str) -> str:
        return f"{self.key_prefix}{session_id}"

    def get(self, session_id: str) -> Optional[DiscussionSession]:
        data = self.client.get(self._key(session_id))
        if data is None:
            return None
        try:
            return pickle.loads(data)
        except Exception:
            return None

    def save(self, session: DiscussionSession):
        key = self._key(session.session_id)
        self.client.setex(key, self.ttl_seconds, pickle.dumps(session))

    def delete(self, session_id: str):
        self.client.delete(self._key(session_id))
