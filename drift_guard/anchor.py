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
        """为某个角色生成简洁的 system prompt，仅保留议题提示"""
        return f"""你是{role_name}，{role_personality}。

{role_style}

讨论议题：{self.topic.text}

请围绕上述议题发表你的观点。可以自由赞同、补充、质疑或反驳其他发言者的观点。"""

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
