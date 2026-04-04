from typing import Optional
from model_router.router import ModelRouter


class RelevanceScorer:
    """
    LLM-as-a-Judge 风格的相关性评分器。
    如果 agent 自己没有打出可靠分数，由 scorer 二次判定。
    """

    def __init__(self, router: ModelRouter):
        self.router = router

    def score(self, topic_text: str, response_text: str) -> float:
        system = (
            "你是一个严格的议题相关性评分器。"
            "只返回 0-10 之间的一个数字，10 表示完全相关，0 表示完全无关。"
        )
        prompt = (
            f"核心议题：{topic_text}\n\n"
            f"待评分内容：{response_text}\n\n"
            "请只返回一个 0-10 的数字，不要解释。"
        )
        raw = self.router.chat(
            messages=[{"role": "user", "content": prompt}],
            system=system,
            max_tokens=10,
            temperature=0.0,
        )
        try:
            # 尝试提取第一个数字
            import re
            nums = re.findall(r"\d+(?:\.\d+)?", raw)
            if nums:
                score = float(nums[0])
                return max(0.0, min(10.0, score))
        except Exception:
            pass
        return 5.0  # 失败时返回中性的 5 分
