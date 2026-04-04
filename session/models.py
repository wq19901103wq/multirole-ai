from dataclasses import dataclass, field
from typing import List, Dict, Any
from core.event import TurnResult


@dataclass
class DiscussionSession:
    session_id: str
    topic_text: str = ""
    turn_results: List[TurnResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def latest_summary(self) -> str:
        if self.turn_results:
            return self.turn_results[-1].summary
        return ""
