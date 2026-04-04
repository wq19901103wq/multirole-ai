#!/usr/bin/env python3
"""
统一 API 入口。
前端（Web / 飞书 / 微信）统一调用 /v1/discuss，
由 WebAdapter 解析请求并渲染响应。
未来可扩展 /v1/feishu/discuss、/v1/wechat/discuss 等路由。
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

# 把项目根目录加入 PYTHONPATH
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_router.providers.kimi import KimiProvider
from model_router.router import ModelRouter
from model_router.registry import ProviderRegistry
from harness_engine.engine import HarnessEngine
from session.manager import SessionManager
from session.store_redis import RedisSessionStore
from adapters.web import WebAdapter
from adapters.feishu import FeishuAdapter

app = Flask(__name__)
CORS(app)

# ========== 初始化各层 ==========
# 1. 注册 provider
ProviderRegistry.register("kimi", KimiProvider)

# 2. 模型路由层
default_provider = ProviderRegistry.create("kimi")
router = ModelRouter(default_provider=default_provider)

# 3. Harness Engine
engine = HarnessEngine(router=router)

# 4. 会话层（支持环境变量切换 Redis）
if os.environ.get("MULTIROLE_REDIS_URL"):
    import urllib.parse
    url = urllib.parse.urlparse(os.environ["MULTIROLE_REDIS_URL"])
    store = RedisSessionStore(
        host=url.hostname or "localhost",
        port=url.port or 6379,
        password=url.password,
        db=int(url.path.lstrip("/") or 0),
    )
    session_manager = SessionManager(engine=engine, store=store)
else:
    session_manager = SessionManager(engine=engine)

# 5. 适配器
web_adapter = WebAdapter()
feishu_adapter = FeishuAdapter()


@app.route('/v1/discuss', methods=['POST'])
def discuss():
    """
    统一讨论接口。
    Request:
        {
            "message": "用户问题",
            "session_id": "可选，默认 default",
            "max_rounds": 2
        }
    Response:
        {
            "events": [ ... ],
            "session_id": "..."
        }
    """
    data = request.json or {}
    user_message = web_adapter.extract_user_message(data)
    session_id = web_adapter.extract_session_id(data)
    max_rounds = data.get("max_rounds", 2)
    force_manual = data.get("force_manual", False)

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    events = session_manager.run_discussion(
        session_id=session_id,
        user_message=user_message,
        max_rounds=max_rounds,
        force_manual=force_manual,
    )

    rendered = web_adapter.render_events(events)
    return jsonify({
        "events": rendered,
        "session_id": session_id,
    })


@app.route('/v1/feishu/discuss', methods=['POST'])
def feishu_discuss():
    """
    飞书机器人统一讨论接口。
    接收飞书事件回调格式，返回飞书交互卡片格式。
    """
    data = request.json or {}
    user_message = feishu_adapter.extract_user_message(data)
    session_id = feishu_adapter.extract_session_id(data)
    max_rounds = data.get("max_rounds", 2) if "max_rounds" in data else 2
    force_manual = data.get("force_manual", False)

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    # 把默认 provider 换成 mock（测试环境）或保持现有 provider
    events = session_manager.run_discussion(
        session_id=session_id,
        user_message=user_message,
        max_rounds=max_rounds,
        force_manual=force_manual,
    )

    rendered = feishu_adapter.render_events(events)
    return jsonify(rendered)


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "autogen_installed": engine.router.default_provider is not None,
    })


# ========== Web 演示页面 ==========
HTML_DEMO = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Multirole AI - Harness Engine Demo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; height: 100vh; display: flex; flex-direction: column; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }
        .chat-container { flex: 1; overflow-y: auto; padding: 20px; max-width: 900px; margin: 0 auto; width: 100%; }
        .discussion-round { margin-bottom: 20px; padding: 20px; background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .round-title { font-size: 18px; font-weight: bold; color: #667eea; margin-bottom: 15px; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }
        .message { margin-bottom: 12px; }
        .message-header { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
        .avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; }
        .role-name { font-weight: 600; font-size: 14px; }
        .message-content { background: #f8f9fa; padding: 12px; border-radius: 8px; border-left: 3px solid; margin-left: 42px; line-height: 1.6; }
        .moderator-content { background: #fff8e1; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-left: 8px; }
        .badge-drift { background: #ffebee; color: #c62828; }
        .badge-good { background: #e8f5e9; color: #2e7d32; }
        .input-area { background: white; padding: 20px; border-top: 1px solid #e0e0e0; display: flex; gap: 10px; max-width: 900px; margin: 0 auto; width: 100%; }
        .input-area textarea { flex: 1; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; resize: none; font-size: 14px; min-height: 60px; }
        .btn { padding: 12px 24px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 500; }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .divider { margin: 10px 0; text-align: center; color: #999; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Multirole AI - Harness Engine</h1>
        <p>分层架构：Adapters → Session → Harness(AutoGen) → ModelRouter → Kimi</p>
    </div>
    <div class="chat-container" id="chatContainer">
        <div class="discussion-round">
            <div class="round-title">💡 架构说明</div>
            <ul style="color: #666; line-height: 1.8; margin-left: 20px;">
                <li><b>Adapters</b>：前端适配层（Web / 飞书 / 微信 / 小程序）</li>
                <li><b>Session Layer</b>：会话状态管理与事件流转</li>
                <li><b>Harness Engine</b>：基于 AutoGen 的多代理协调（含防漂移）</li>
                <li><b>DriftGuard</b>：TopicAnchor + ModeratorCheckpoint + ContextTruncator</li>
                <li><b>Model Router</b>：统一路由 Kimi / OpenAI / Claude 等模型</li>
            </ul>
        </div>
    </div>
    <div class="input-area">
        <textarea id="userInput" rows="2" placeholder="输入问题，发起多代理讨论..."></textarea>
        <button class="btn" id="sendBtn" onclick="startDiscussion()">发起讨论</button>
    </div>
    <script>
        async function startDiscussion() {
            const input = document.getElementById('userInput');
            const btn = document.getElementById('sendBtn');
            const msg = input.value.trim();
            if (!msg) return;
            btn.disabled = true; btn.textContent = '讨论中...'; input.value = '';
            const container = document.getElementById('chatContainer');
            const roundDiv = document.createElement('div');
            roundDiv.className = 'discussion-round';
            roundDiv.innerHTML = `<div class="round-title">🗣️ ${msg.substring(0,30)}...</div><div style="padding:20px;color:#666;">讨论中...</div>`;
            container.appendChild(roundDiv); container.scrollTop = container.scrollHeight;

            const res = await fetch('/v1/discuss', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: msg, max_rounds: 2})
            });
            const data = await res.json();
            roundDiv.innerHTML = `<div class="round-title">🗣️ ${msg.substring(0,30)}${msg.length>30?'...':''}</div>`;

            let currentRound = 0;
            data.events.forEach(evt => {
                if (evt.round !== currentRound) {
                    currentRound = evt.round;
                    const d = document.createElement('div');
                    d.className = 'divider'; d.textContent = `--- 第 ${currentRound} 轮 ${evt.event_type==='moderation'?'· 主持人对齐':''} ---`;
                    roundDiv.appendChild(d);
                }
                const isMod = evt.event_type === 'moderation';
                const meta = !isMod && evt.relevance !== undefined
                    ? `<span class="badge ${evt.relevance < 8 ? 'badge-drift' : 'badge-good'}">相关性 ${evt.relevance}/10</span>` : '';
                const div = document.createElement('div'); div.className = 'message';
                div.innerHTML = `
                    <div class="message-header">
                        <div class="avatar" style="background:${evt.color}20;color:${evt.color};">${evt.emoji}</div>
                        <span class="role-name" style="color:${evt.color};">${evt.role_name}</span>${meta}
                    </div>
                    <div class="message-content ${isMod?'moderator-content':''}" style="border-color:${evt.color};">${evt.content}</div>
                `;
                roundDiv.appendChild(div);
            });
            btn.disabled = false; btn.textContent = '发起讨论'; container.scrollTop = container.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_DEMO


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8890, debug=True)
