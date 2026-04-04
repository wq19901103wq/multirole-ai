#!/usr/bin/env python3
"""Benchmark script for HarnessEngine.run() latency under different configurations."""

import json
import os
import sys
import time
import types
from datetime import datetime, timezone

# Add project root to path so imports resolve when run directly
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJECT_ROOT)

# model_router/providers/__init__.py eagerly imports all provider modules.
# If optional dependencies (anthropic, openai) are missing, inject minimal
# stubs so that benchmark imports succeed without requiring a venv.
for _mod_name in ("anthropic", "openai"):
    if _mod_name not in sys.modules:
        try:
            __import__(_mod_name)
        except ImportError:
            _dummy = types.ModuleType(_mod_name)
            if _mod_name == "anthropic":
                class _FakeAnthropic:
                    def __init__(self, **kwargs):
                        pass
                _dummy.Anthropic = _FakeAnthropic
            elif _mod_name == "openai":
                class _FakeOpenAI:
                    def __init__(self, **kwargs):
                        pass
                _dummy.OpenAI = _FakeOpenAI
            sys.modules[_mod_name] = _dummy

from core.topic import Topic
from harness_engine import HarnessEngine
from model_router import ModelRouter

# Prefer the existing MockProvider from tests; fall back to a local minimal version.
try:
    from tests.conftest import MockProvider
except Exception:  # pragma: no cover
    from model_router.providers.base import LLMProvider

    class MockProvider(LLMProvider):
        def __init__(self, responses=None):
            self.responses = responses or {}
            self.call_log = []

        @property
        def name(self) -> str:
            return "mock/test"

        def chat_completion(self, messages, system="", max_tokens=500, temperature=0.5, **kwargs):
            self.call_log.append({"messages": messages, "system": system, "max_tokens": max_tokens})
            for key, val in self.responses.items():
                if key in system:
                    return val
            return "关于'测试议题'，我的观点是：这是默认测试回复。\n\n以上观点与核心议题的相关性：9/10"


def run_benchmark(max_rounds: int, force_manual: bool, runs: int = 3) -> tuple:
    """Run HarnessEngine with the given config and return average latency."""
    topic = Topic(text="Benchmark test topic")
    mock = MockProvider()
    router = ModelRouter(default_provider=mock)
    engine = HarnessEngine(router=router)

    latencies = []
    for _ in range(runs):
        start = time.perf_counter()
        engine.run(topic=topic, max_rounds=max_rounds, force_manual=force_manual)
        elapsed = time.perf_counter() - start
        latencies.append(elapsed)

    avg_latency_ms = (sum(latencies) / len(latencies)) * 1000
    return avg_latency_ms, latencies


def main():
    max_rounds_values = [1, 2, 3]
    force_manual_values = [True, False]
    runs = 3

    results = []

    print("=" * 66)
    print("HarnessEngine.run() Benchmark")
    print("=" * 66)
    print(f"{'max_rounds':>12} | {'force_manual':>12} | {'avg_latency_ms':>14} | {'runs':>4}")
    print("-" * 66)

    for max_rounds in max_rounds_values:
        for force_manual in force_manual_values:
            avg_latency_ms, latencies = run_benchmark(max_rounds, force_manual, runs)
            result = {
                "max_rounds": max_rounds,
                "force_manual": force_manual,
                "avg_latency_ms": round(avg_latency_ms, 3),
                "runs": runs,
            }
            results.append(result)
            print(
                f"{max_rounds:>12} | {str(force_manual):>12} | {avg_latency_ms:>14.3f} | {runs:>4}"
            )

    print("=" * 66)

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }

    results_dir = os.path.join(_PROJECT_ROOT, "benchmarks")
    os.makedirs(results_dir, exist_ok=True)
    results_path = os.path.join(results_dir, "results.json")

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Results saved to {results_path}")


if __name__ == "__main__":
    main()
