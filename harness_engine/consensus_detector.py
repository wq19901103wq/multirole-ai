import json
import re
from typing import List, Optional, Dict
from core.message import Message


class ConsensusDetector:
    """
    共识检测器：分析一轮讨论后，判断参与者是否已达成一致。
    """

    def __init__(self, router):
        self.router = router

    def check(self, topic_text: str, messages: List[Message]) -> Dict:
        """
        判断本轮讨论后是否已达成共识。

        Returns:
            {
                "consensus_reached": bool,
                "consensus_summary": str,   # 如果达成，总结共识
                "disagreement_points": str, # 如果没达成，指出分歧
                "confidence": float,        # 0-1
            }
        """
        # 提取所有 debater 的发言
        debate_texts = []
        for m in messages:
            if m.is_moderation:
                continue
            debate_texts.append(f"{m.sender_name}: {m.content}")

        if len(debate_texts) < 2:
            return {
                "consensus_reached": False,
                "consensus_summary": "",
                "disagreement_points": "发言数量不足，无法判断共识",
                "confidence": 0.0,
            }

        transcript = "\n\n".join(debate_texts)

        prompt = f"""你是一位中立的讨论观察员。请分析下面这场圆桌讨论，判断4位参与者是否已经达成了实质性共识（即核心观点趋同，或者通过交锋收敛到了一致结论）。

话题：{topic_text}

讨论记录：
{transcript}

请严格按以下 JSON 格式输出（不要有多余内容）：
{{
  "consensus_reached": true/false,
  "consensus_summary": "如果达成，用一句话总结共识；如果没达成，写''",
  "disagreement_points": "如果没达成，指出核心分歧；如果达成，写''",
  "confidence": 0.0-1.0
}}
"""
        try:
            # Kimi Code 模型默认启用 thinking 模式
            # 需要确保 max_tokens 足够容纳 thinking + 正式回复
            raw = self.router.chat(
                messages=[{"role": "user", "content": prompt}],
                system="你是一个善于识别讨论共识和分歧的专家。",
                max_tokens=1200,
                temperature=0.2,
            )
            return self._parse(raw)
        except Exception:
            # fallback：本地规则判断
            return self._fallback_check(messages)

    @staticmethod
    def _parse(raw: str) -> Dict:
        """解析 LLM 返回的 JSON"""
        # 尝试从文本中提取 JSON 块
        raw = raw.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        try:
            data = json.loads(raw)
            return {
                "consensus_reached": bool(data.get("consensus_reached", False)),
                "consensus_summary": str(data.get("consensus_summary", "")),
                "disagreement_points": str(data.get("disagreement_points", "")),
                "confidence": float(data.get("confidence", 0.0)),
            }
        except Exception:
            # 如果 JSON 解析失败，尝试正则提取
            reached = bool(re.search(r'"consensus_reached"\s*:\s*true', raw, re.I))
            summary_match = re.search(r'"consensus_summary"\s*:\s*"([^"]*)"', raw)
            summary = summary_match.group(1) if summary_match else ""
            disagree_match = re.search(r'"disagreement_points"\s*:\s*"([^"]*)"', raw)
            disagree = disagree_match.group(1) if disagree_match else ""
            conf_match = re.search(r'"confidence"\s*:\s*([0-9.]+)', raw)
            confidence = float(conf_match.group(1)) if conf_match else 0.0
            return {
                "consensus_reached": reached,
                "consensus_summary": summary,
                "disagreement_points": disagree,
                "confidence": confidence,
            }

    @staticmethod
    def _fallback_check(messages: List[Message]) -> Dict:
        """无 LLM 时的本地 fallback：通过关键词简单判断"""
        texts = [m.content.lower() for m in messages if not m.is_moderation]
        if len(texts) < 2:
            return {
                "consensus_reached": False,
                "consensus_summary": "",
                "disagreement_points": "发言不足",
                "confidence": 0.0,
            }

        # 简单规则：如果有明显的反驳词，认为未达成共识
        conflict_signals = ["不同意", "不认同", "反驳", "质疑", "相反", "错误", "不对", "不能同意", "恰恰相反"]
        conflict_count = sum(1 for t in texts for s in conflict_signals if s in t)

        # 如果有赞同词且没有冲突词，认为达成共识
        agree_signals = ["同意", "认同", "赞同", "支持", "确实如此", "说得对", "我补充"]
        agree_count = sum(1 for t in texts for s in agree_signals if s in t)

        if conflict_count == 0 and agree_count >= len(texts) - 1:
            return {
                "consensus_reached": True,
                "consensus_summary": "讨论者们在核心观点上达成了一致",
                "disagreement_points": "",
                "confidence": 0.6,
            }

        return {
            "consensus_reached": False,
            "consensus_summary": "",
            "disagreement_points": "讨论中仍存在明显的分歧或反驳，需要继续交流",
            "confidence": 0.5,
        }
