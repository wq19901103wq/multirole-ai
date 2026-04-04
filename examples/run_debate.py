#!/usr/bin/env python3
"""
命令行示例：直接运行 Harness Engine，不经过 Web 层。
用于本地调试和验证防漂移效果。
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_router.providers.kimi import KimiProvider
from model_router.router import ModelRouter
from harness_engine.engine import HarnessEngine
from core.topic import Topic


def main():
    provider = KimiProvider()
    router = ModelRouter(default_provider=provider)
    engine = HarnessEngine(router)

    topic = Topic(
        text="如何设计一个高性能的电商网站？",
        scope_inner="技术架构和性能优化手段",
        scope_middle="团队分工、开发周期、成本评估",
        scope_outer="电商行业趋势、市场营销策略、融资计划",
    )

    results = engine.run(topic, max_rounds=2)

    for turn in results:
        print(f"\n========== 第 {turn.metadata['round']} 轮 ==========")
        for msg in turn.messages:
            prefix = "🛡️ " if msg.is_moderation else "   "
            rel = f" [相关性 {msg.relevance_score}/10]" if msg.relevance_score is not None else ""
            print(f"{prefix}{msg.sender_name}{rel}:\n{msg.content}\n")
        if turn.drift_detected:
            print(f"⚠️ 漂移警告：{turn.drift_report}")


if __name__ == '__main__':
    main()
