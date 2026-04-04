from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class Role(Enum):
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"
    MODERATOR = "moderator"


@dataclass
class Message:
    role: Role
    content: str
    sender_id: Optional[str] = None      # 哪个 agent / 用户发的
    sender_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def relevance_score(self) -> Optional[float]:
        return self.metadata.get("relevance_score")
    
    @property
    def is_moderation(self) -> bool:
        return self.metadata.get("type") == "moderation"
