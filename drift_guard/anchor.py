import re
from typing import Optional
from core.topic import Topic


class TopicAnchor:
    """
    议题锚定器：给每个 agent 的 system prompt 注入硬约束，
    并在回复后提取锚定指标（如相关性评分）。
    """

    FORBIDDEN_PREFIXES = [
        "此外",
        "值得一提的是",
        "这让我想到",
        "更广泛地说",
        "另一个相关的角度是",
    ]

    def __init__(self, topic: Topic):
        self.topic = topic

    def inject_prompt(self, role_name: str, role_personality: str, role_style: str) -> str:
        """为某个角色生成带议题锚定的 system prompt"""
        forbidden_lines = "\n   - ".join([f'"{w}..."' for w in self.FORBIDDEN_PREFIXES])
        return f"""你是{role_name}，{role_personality}。

你的说话风格：{role_style}

## 议题锚定规则（必须遵守）
{self.topic.anchor_prompt}

1. 每次发言的第一句话必须是："关于'{self.topic.text}'，我的观点是："
2. 你的每一个论点都必须直接回应该议题
3. 禁止使用的扩展性词汇（这些词是跑题的高发信号）：
   - {forbidden_lines}
4. 每次发言的最后，必须用独立一行写出：
   "以上观点与核心议题的相关性：X/10"
   如果相关性低于8，必须同时说"此观点偏离议题，跳过。"
5. 回复要简洁（80字以内），只讲最核心的1-2个点

## 角色适配约束（重要）
- 如果你的专业背景与当前议题关联不大，请不要强行套用专业术语或硬找角度。
- 此时应从"普通人视角"、"通用逻辑"或"实际生活经验"切入，保持对核心议题的相关性。
- 目标不是"炫技"，而是让讨论抓住重点。

示例格式：
关于'{self.topic.text}'，我的观点是：[你的核心论点]

以上观点与核心议题的相关性：9/10
"""

    @staticmethod
    def extract_relevance(text: str) -> Optional[float]:
        match = re.search(r'相关性[:：]\s*(\d+(?:\.\d+)?)\s*/\s*10', text)
        if match:
            return float(match.group(1))
        return None

    @staticmethod
    def clean_response(text: str) -> str:
        """移除锚定模板，返回展示用内容"""
        text = re.sub(r'^关于[\"\'].*?[\"\']，我的(?:观点|看法|意见)是[：:]\s*', '', text, flags=re.MULTILINE)
        text = re.split(r'\n?以上(?:观点|内容|发言)与核心议题的相关性[:：]', text)[0]
        return text.strip()
