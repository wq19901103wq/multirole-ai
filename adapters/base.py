from abc import ABC, abstractmethod
from typing import List, Dict, Any
from core.event import DiscussionEvent


class BaseAdapter(ABC):
    """
    前端适配器基类。
    负责把底层事件流转为前端特定的消息格式。
    """

    @abstractmethod
    def render_events(self, events: List[DiscussionEvent]) -> Any:
        """把事件列表渲染为前端需要的格式"""
        raise NotImplementedError

    @abstractmethod
    def extract_user_message(self, payload: Any) -> str:
        """从前端请求中提取用户消息"""
        raise NotImplementedError

    @abstractmethod
    def extract_session_id(self, payload: Any) -> str:
        """从前端请求中提取 session_id"""
        raise NotImplementedError
