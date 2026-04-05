#!/usr/bin/env python3
"""
真实端到端多代理辩论示例。

本脚本演示如何使用实际的 HarnessEngine 和 KimiProvider 运行一场多轮讨论。
它会从环境变量读取 KIMI_API_KEY，初始化 ModelRouter 和引擎，
然后围绕指定话题运行 2 轮受控辩论，并格式化输出每位参与者的发言内容及相关性评分。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_router.providers.kimi import KimiProvider
from model_router.router import ModelRouter
from harness_engine.engine import HarnessEngine
from core.topic import Topic


def main():
    api_key = os.environ.get("KIMI_API_KEY")
    if not api_key:
        print("错误：未设置 KIMI_API_KEY 环境变量。")
        print("请先执行：export KIMI_API_KEY='your_api_key'，然后重新运行本脚本。")
        sys.exit(1)

    provider = KimiProvider(api_key=api_key)
    router = ModelRouter(default_provider=provider)
    engine = HarnessEngine(router)

    topic = Topic(
        text="人工智能是否会取代程序员？",
        scope_inner="技术发展趋势和职业替代风险",
        scope_middle="教育转型、政策支持、社会接受度",
        scope_outer="宏观经济、科幻设想、伦理哲学",
    )

    print(f"\n▶ 开始讨论话题：{topic.text}\n")
    results = engine.run(topic=topic, max_rounds=2, force_manual=True)

    for turn in results:
        round_num = turn.metadata.get("round", "?")
        print(f"\n{'=' * 50}")
        print(f"  第 {round_num} 轮")
        print(f"{'=' * 50}")

        for msg in turn.messages:
            if msg.is_moderation:
                icon = "🛡️ "
                label = "主持人"
            else:
                icon = "💬 "
                label = msg.sender_name or msg.sender_id or "未知"

            rel = ""
            if msg.relevance_score is not None:
                rel = f" (相关性: {msg.relevance_score}/10)"

            print(f"\n{icon}[{label}]{rel}")
            print("-" * 40)
            print(msg.content)

        if turn.drift_detected:
            print(f"\n⚠️  漂移警告：{turn.drift_report}")

    print(f"\n{'=' * 50}")
    print("  讨论结束")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    main()
