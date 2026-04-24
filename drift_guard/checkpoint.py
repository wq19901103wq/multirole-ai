from typing import List
from core.message import Message
from model_router.router import ModelRouter
from core.topic import Topic


class ModeratorCheckpoint:
    """
    对齐检查点：每轮结束后由 moderator 执行范围检查和摘要生成。
    """

    def __init__(self, router: ModelRouter):
        self.router = router

    def check(self, topic: Topic, round_messages: List[Message]) -> dict:
        """
        返回一个 dict：
        {
            "drift_detected": bool,
            "drift_report": str,
            "summary": str,
        }
        """
        # 构造 moderator 的输入
        lines = [f"核心议题：{topic.text}\n", "=== 本轮发言 ==="]
        for m in round_messages:
            rel = m.relevance_score if m.relevance_score is not None else "未评分"
            lines.append(f"{m.sender_name}（相关性 {rel}/10）：{m.content}")

        lines.append("\n请完成两个任务：")
        lines.append("1. 范围检查：如果有发言偏离议题（相关性<8），指出是谁、哪里偏了")
        lines.append("2. 摘要生成：把与议题直接相关的观点，压缩成2-3条核心论点")
        lines.append("输出格式：")
        lines.append("【范围检查】...")
        lines.append("【核心摘要】\n- ...\n- ...")

        system = (
            "你是主持人，严格把控讨论方向，不做价值判断，只做流程和范围控制。"
            "回复简洁，80字以内。"
        )
        prompt = "\n".join(lines)

        raw = self.router.chat(
            messages=[{"role": "user", "content": prompt}],
            system=system,
            max_tokens=4000,
            temperature=0.3,
        )

        drift_detected = "偏离" in raw or "漂移" in raw or "跑题" in raw
        return {
            "drift_detected": drift_detected,
            "drift_report": raw if drift_detected else "",
            "summary": raw,
        }
