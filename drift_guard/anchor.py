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

1. 你的每一个论点都必须直接回应该议题
2. 禁止使用的扩展性词汇（这些词是跑题的高发信号）：
   - {forbidden_lines}
3. 每次发言的最后，必须用独立一行写出：
   "以上观点与核心议题的相关性：X/10"
   如果相关性低于8，必须同时说"此观点偏离议题，跳过。"
4. 你可以赞同、补充、质疑或反驳前面发言者的观点。这是一个真实的讨论，不是各自独白。你的目标是推动讨论向更深入、更正确的方向发展。
5. 每次发言请进行充分论述，尽量从多个层面展开深入分析，避免蜻蜓点水。字数建议在300字以上。

示例格式：
[你的核心论点或对他人的回应]

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
