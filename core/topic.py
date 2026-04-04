from dataclasses import dataclass
from typing import Optional


@dataclass
class Topic:
    text: str
    scope_inner: Optional[str] = None    # 核心圆
    scope_middle: Optional[str] = None   # 中间圆
    scope_outer: Optional[str] = None    # 外层圆（禁止主动讨论）
    
    @property
    def anchor_prompt(self) -> str:
        prompt = f'核心议题："{self.text}"'
        if self.scope_inner:
            prompt += f"\n必须讨论：{self.scope_inner}"
        if self.scope_middle:
            prompt += f"\n可以触及：{self.scope_middle}"
        if self.scope_outer:
            prompt += f"\n禁止主动讨论：{self.scope_outer}"
        return prompt
