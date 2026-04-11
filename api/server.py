#!/usr/bin/env python3
"""
统一 API 入口。
前端（Web / 飞书 / 微信）统一调用 /v1/discuss，
由 WebAdapter 解析请求并渲染响应。
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import logging
import sys

# 配置详细日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

try:
    from flasgger import Swagger
except ImportError:
    Swagger = None

try:
    from flask_sock import Sock
except ImportError:
    Sock = None

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

if Sock is not None:
    sock = Sock(app)
else:
    sock = None

if Swagger is not None:
    Swagger(app, template={
        "swagger": "2.0",
        "info": {
            "title": "Multirole AI API",
            "description": "Multi-agent AI discussion system with drift guard",
            "version": "1.0.0",
        },
        "basePath": "/",
    })

# ========== 初始化各层 ==========
# 支持 DEMO_MODE：无需真实 API Key 即可测试完整交互流程
if os.environ.get("MULTIROLE_DEMO_MODE"):
    from examples.run_consensus_demo import DemoProvider
    default_provider = DemoProvider()
else:
    # 默认使用 Kimi Code 代理模式（127.0.0.1:18790）
    # 如需使用 Moonshot API，设置 MULTIROLE_KIMI_MODE=moonshot 和 KIMI_API_KEY
    os.environ.setdefault("MULTIROLE_KIMI_MODE", "proxy")
    ProviderRegistry.register("kimi", KimiProvider)
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


def _msg_to_event(msg, round_num):
    """把内部 Message 对象转成前端事件 dict。"""
    return {
        "event_type": "moderation" if msg.is_moderation else "message",
        "role_name": msg.sender_name or msg.sender_id or "Agent",
        "content": msg.content,
        "relevance": msg.metadata.get("relevance_score"),
        "round": round_num,
        "emoji": msg.metadata.get("emoji", "🤖"),
        "color": msg.metadata.get("color", "#667eea"),
    }


@app.route('/v1/discuss', methods=['POST'])
def discuss():
    """
    统一讨论接口
    ---
    tags:
      - Discussion
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            message:
              type: string
              example: "人工智能会取代程序员吗？"
            session_id:
              type: string
              example: "default"
            max_rounds:
              type: integer
              example: 2
            force_manual:
              type: boolean
              example: false
    responses:
      200:
        description: 讨论结果
        schema:
          type: object
          properties:
            events:
              type: array
            session_id:
              type: string
    """
    import time
    start_time = time.time()
    
    data = request.json or {}
    user_message = web_adapter.extract_user_message(data)
    session_id = web_adapter.extract_session_id(data)
    max_rounds = data.get("max_rounds", 2)
    force_manual = data.get("force_manual", False)
    
    logger.info(f"=" * 60)
    logger.info(f"[DISCUSS] 收到请求: session={session_id}, max_rounds={max_rounds}")
    logger.info(f"[DISCUSS] 用户消息: {user_message[:100]}...")

    if not user_message:
        logger.warning("[DISCUSS] 错误: 缺少 message 参数")
        return jsonify({"error": "message is required"}), 400

    try:
        logger.info("[DISCUSS] 开始运行讨论...")
        events = session_manager.run_discussion(
            session_id=session_id,
            user_message=user_message,
            max_rounds=max_rounds,
            force_manual=force_manual,
        )
        
        elapsed = time.time() - start_time
        logger.info(f"[DISCUSS] 讨论完成，生成 {len(events)} 个事件，耗时 {elapsed:.2f}s")
        
        rendered = web_adapter.render_events(events)
        logger.info(f"[DISCUSS] 渲染完成，返回 {len(rendered)} 个事件")
        logger.info(f"=" * 60)
        
        return jsonify({
            "events": rendered,
            "session_id": session_id,
        })
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[DISCUSS] 讨论失败: {e}, 耗时 {elapsed:.2f}s")
        logger.exception(e)
        return jsonify({"error": str(e)}), 500


@app.route('/v1/feishu/discuss', methods=['POST'])
def feishu_discuss():
    """
    飞书机器人统一讨论接口
    ---
    tags:
      - Discussion
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
    responses:
      200:
        description: 飞书交互卡片
    """
    data = request.json or {}
    user_message = feishu_adapter.extract_user_message(data)
    session_id = feishu_adapter.extract_session_id(data)
    max_rounds = data.get("max_rounds", 2) if "max_rounds" in data else 2
    force_manual = data.get("force_manual", False)

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    events = session_manager.run_discussion(
        session_id=session_id,
        user_message=user_message,
        max_rounds=max_rounds,
        force_manual=force_manual,
    )

    rendered = feishu_adapter.render_events(events)
    return jsonify(rendered)


@app.route('/v1/discuss/consensus', methods=['POST'])
def discuss_consensus():
    """
    共识讨论接口：持续多轮讨论直到达成一致或达到上限
    ---
    tags:
      - Discussion
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            message:
              type: string
              example: "远程工作是否值得推广？"
            session_id:
              type: string
              example: "default"
            max_rounds:
              type: integer
              example: 10
            force_manual:
              type: boolean
              example: false
    responses:
      200:
        description: 讨论结果（含 consensus_reached 标记）
    """
    data = request.json or {}
    user_message = web_adapter.extract_user_message(data)
    session_id = web_adapter.extract_session_id(data)
    max_rounds = data.get("max_rounds", 10)
    force_manual = data.get("force_manual", False)

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    events = session_manager.run_discussion_consensus(
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


def discuss_stream(ws):
    """
    WebSocket 实时流式讨论接口。
    客户端发送 JSON：{"message": "...", "session_id": "...", "max_rounds": 2}
    服务端逐条推送每个 Agent 的发言和 Moderator 总结。
    """
    try:
        raw = ws.receive(timeout=5)
        if not raw:
            ws.send(json.dumps({"error": "empty request"}))
            return
        data = json.loads(raw)
    except Exception as e:
        ws.send(json.dumps({"error": f"invalid json: {e}"}))
        return

    user_message = web_adapter.extract_user_message(data)
    session_id = web_adapter.extract_session_id(data)
    max_rounds = data.get("max_rounds", 2)

    if not user_message:
        ws.send(json.dumps({"error": "message is required"}))
        return

    ws.send(json.dumps({"type": "status", "text": "讨论开始"}))

    # 这里直接用 user_message 作为 topic text
    from core.topic import Topic
    topic_obj = Topic(text=user_message)

    def on_message(msg):
        evt = _msg_to_event(msg, msg.metadata.get("round", 0))
        ws.send(json.dumps({"type": "event", "payload": evt}))

    try:
        for turn in session_manager.engine.run_stream(
            topic=topic_obj,
            max_rounds=max_rounds,
            force_manual=True,
            on_message=on_message,
        ):
            ws.send(json.dumps({"type": "turn_end", "round": turn.metadata.get("round", 0)}))

        ws.send(json.dumps({"type": "done", "session_id": session_id}))
    except Exception as e:
        ws.send(json.dumps({"type": "error", "message": str(e)}))


def discuss_consensus_stream(ws):
    """
    WebSocket 共识讨论接口：持续多轮直到达成一致。
    客户端发送 JSON：{"message": "...", "session_id": "...", "max_rounds": 10}
    """
    try:
        raw = ws.receive(timeout=5)
        if not raw:
            ws.send(json.dumps({"error": "empty request"}))
            return
        data = json.loads(raw)
    except Exception as e:
        ws.send(json.dumps({"error": f"invalid json: {e}"}))
        return

    user_message = web_adapter.extract_user_message(data)
    session_id = web_adapter.extract_session_id(data)
    max_rounds = data.get("max_rounds", 10)

    if not user_message:
        ws.send(json.dumps({"error": "message is required"}))
        return

    ws.send(json.dumps({"type": "status", "text": "共识讨论开始（最多 " + str(max_rounds) + " 轮）"}))

    from core.topic import Topic
    topic_obj = Topic(text=user_message)

    def on_message(msg):
        evt = _msg_to_event(msg, msg.metadata.get("round", 0))
        ws.send(json.dumps({"type": "event", "payload": evt}))

    def on_consensus(consensus):
        ws.send(json.dumps({
            "type": "consensus_check",
            "reached": consensus.get("consensus_reached", False),
            "confidence": consensus.get("confidence", 0),
        }))

    try:
        for turn in session_manager.engine.run_until_consensus_stream(
            topic=topic_obj,
            max_rounds=max_rounds,
            force_manual=True,
            on_message=on_message,
            on_consensus=on_consensus,
        ):
            ws.send(json.dumps({"type": "turn_end", "round": turn.metadata.get("round", 0)}))
            if turn.metadata.get("consensus_reached"):
                ws.send(json.dumps({
                    "type": "consensus",
                    "summary": turn.metadata.get("consensus_summary", ""),
                }))
                break
            elif turn.metadata.get("round") == max_rounds and not turn.metadata.get("consensus_reached"):
                ws.send(json.dumps({"type": "timeout"}))
                break

        ws.send(json.dumps({"type": "done", "session_id": session_id}))
    except Exception as e:
        ws.send(json.dumps({"type": "error", "message": str(e)}))


if sock is not None:
    sock.route('/v1/discuss/stream')(discuss_stream)
    sock.route('/v1/discuss/consensus/stream')(discuss_consensus_stream)


@app.route('/health', methods=['GET'])
def health():
    """
    健康检查
    ---
    tags:
      - System
    responses:
      200:
        description: 服务状态
    """
    return jsonify({
        "status": "ok",
        "autogen_installed": engine.router.default_provider is not None,
    })


@app.route('/swagger-ui')
def swagger_ui():
    """兼容旧版 Swagger UI 重定向"""
    return jsonify({"swagger_url": "/apidocs/", "flasgger": True})


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
        .consensus-content { background: #e8f5e9; font-weight: 500; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-left: 8px; }
        .badge-drift { background: #ffebee; color: #c62828; }
        .badge-good { background: #e8f5e9; color: #2e7d32; }
        .input-area { background: white; padding: 20px; border-top: 1px solid #e0e0e0; display: flex; gap: 10px; max-width: 900px; margin: 0 auto; width: 100%; }
        .input-area textarea { flex: 1; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; resize: none; font-size: 14px; min-height: 60px; }
        .btn { padding: 12px 24px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 500; }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .btn-secondary { background: #e0e0e0; color: #333; }
        .divider { margin: 10px 0; text-align: center; color: #999; font-size: 12px; }
        .links { text-align: center; padding: 10px; font-size: 12px; }
        .links a { color: #667eea; margin: 0 10px; }
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
            <div class="links">
                <a href="/apidocs/" target="_blank">📘 Swagger API 文档</a>
                <a href="/swagger-ui" target="_blank">🔍 Swagger UI</a>
            </div>
        </div>
    </div>
    <div class="input-area">
        <textarea id="userInput" rows="2" placeholder="输入问题，发起多代理讨论..."></textarea>
        <button class="btn" id="sendBtn" onclick="startDiscussion()">发起讨论</button>
        <button class="btn btn-secondary" id="streamBtn" onclick="startStreamDiscussion()">实时流式讨论</button>
        <button class="btn btn-secondary" id="consensusBtn" onclick="startConsensusDiscussion()">🤝 共识讨论</button>
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
                appendEvent(roundDiv, evt);
            });
            btn.disabled = false; btn.textContent = '发起讨论'; container.scrollTop = container.scrollHeight;
        }

        function appendEvent(container, evt) {
            const isMod = evt.event_type === 'moderation';
            const isConsensus = evt.event_type === 'consensus';
            const meta = !isMod && !isConsensus && evt.relevance !== undefined
                ? `<span class="badge ${evt.relevance < 8 ? 'badge-drift' : 'badge-good'}">相关性 ${evt.relevance}/10</span>` : '';
            const div = document.createElement('div'); div.className = 'message';
            div.innerHTML = `
                <div class="message-header">
                    <div class="avatar" style="background:${evt.color}20;color:${evt.color};">${evt.emoji}</div>
                    <span class="role-name" style="color:${evt.color};">${evt.role_name}</span>${meta}
                </div>
                <div class="message-content ${isMod?'moderator-content':''} ${isConsensus?'consensus-content':''}" style="border-color:${evt.color};">${evt.content}</div>
            `;
            container.appendChild(div);
        }

        function startStreamDiscussion() {
            const input = document.getElementById('userInput');
            const btn = document.getElementById('streamBtn');
            const msg = input.value.trim();
            if (!msg) return;
            btn.disabled = true; btn.textContent = '流式讨论中...'; input.value = '';
            const container = document.getElementById('chatContainer');
            const roundDiv = document.createElement('div');
            roundDiv.className = 'discussion-round';
            roundDiv.innerHTML = `<div class="round-title">🗣️ ${msg.substring(0,30)}... (WebSocket 实时)</div>`;
            container.appendChild(roundDiv); container.scrollTop = container.scrollHeight;

            const ws = new WebSocket(`ws://${location.host}/v1/discuss/stream`);
            ws.onopen = () => {
                ws.send(JSON.stringify({message: msg, max_rounds: 2}));
            };
            ws.onmessage = (e) => {
                const data = JSON.parse(e.data);
                if (data.type === 'event') {
                    const evt = data.payload;
                    if (roundDiv.lastChild && roundDiv.lastChild.className === 'divider') {
                        const lastRoundText = roundDiv.lastChild.textContent;
                        const expected = `--- 第 ${evt.round} 轮`;
                        if (!lastRoundText.startsWith(expected)) {
                            const d = document.createElement('div');
                            d.className = 'divider';
                            d.textContent = `--- 第 ${evt.round} 轮 ${evt.event_type==='moderation'?'· 主持人对齐':''} ---`;
                            roundDiv.appendChild(d);
                        }
                    } else {
                        const d = document.createElement('div');
                        d.className = 'divider';
                        d.textContent = `--- 第 ${evt.round} 轮 ${evt.event_type==='moderation'?'· 主持人对齐':''} ---`;
                        roundDiv.appendChild(d);
                    }
                    appendEvent(roundDiv, evt);
                    container.scrollTop = container.scrollHeight;
                } else if (data.type === 'done') {
                    btn.disabled = false; btn.textContent = '实时流式讨论';
                    ws.close();
                } else if (data.type === 'error') {
                    roundDiv.innerHTML += `<div style="color:red">错误: ${data.message}</div>`;
                    btn.disabled = false; btn.textContent = '实时流式讨论';
                    ws.close();
                }
            };
            ws.onerror = (err) => {
                roundDiv.innerHTML += `<div style="color:red">WebSocket 连接失败</div>`;
                btn.disabled = false; btn.textContent = '实时流式讨论';
            };
        }

        function startConsensusDiscussion() {
            const input = document.getElementById('userInput');
            const btn = document.getElementById('consensusBtn');
            const msg = input.value.trim();
            if (!msg) return;
            btn.disabled = true; btn.textContent = '共识讨论中...'; input.value = '';
            const container = document.getElementById('chatContainer');
            const roundDiv = document.createElement('div');
            roundDiv.className = 'discussion-round';
            roundDiv.innerHTML = `<div class="round-title">🤝 ${msg.substring(0,30)}... (共识模式)</div>`;
            container.appendChild(roundDiv); container.scrollTop = container.scrollHeight;

            const ws = new WebSocket(`ws://${location.host}/v1/discuss/consensus/stream`);
            ws.onopen = () => {
                ws.send(JSON.stringify({message: msg, max_rounds: 8}));
            };
            ws.onmessage = (e) => {
                const data = JSON.parse(e.data);
                if (data.type === 'event') {
                    const evt = data.payload;
                    if (evt.event_type === 'consensus') {
                        const d = document.createElement('div');
                        d.className = 'divider';
                        d.style.color = '#2e7d32';
                        d.style.fontWeight = 'bold';
                        d.textContent = '--- ✅ 达成共识 ---';
                        roundDiv.appendChild(d);
                        appendEvent(roundDiv, evt);
                        container.scrollTop = container.scrollHeight;
                        return;
                    }
                    if (roundDiv.lastChild && roundDiv.lastChild.className === 'divider') {
                        const lastRoundText = roundDiv.lastChild.textContent;
                        const expected = `--- 第 ${evt.round} 轮`;
                        if (!lastRoundText.startsWith(expected)) {
                            const d = document.createElement('div');
                            d.className = 'divider';
                            d.textContent = `--- 第 ${evt.round} 轮 ${evt.event_type==='moderation'?'· 主持人对齐':''} ---`;
                            roundDiv.appendChild(d);
                        }
                    } else {
                        const d = document.createElement('div');
                        d.className = 'divider';
                        d.textContent = `--- 第 ${evt.round} 轮 ${evt.event_type==='moderation'?'· 主持人对齐':''} ---`;
                        roundDiv.appendChild(d);
                    }
                    appendEvent(roundDiv, evt);
                    container.scrollTop = container.scrollHeight;
                } else if (data.type === 'consensus_check') {
                    const d = document.createElement('div');
                    d.className = 'divider';
                    d.style.fontSize = '11px';
                    d.style.color = data.reached ? '#2e7d32' : '#999';
                    d.textContent = data.reached ? `--- 共识检测通过 (置信度 ${Math.round(data.confidence*100)}%) ---` : `--- 尚未达成共识 (置信度 ${Math.round(data.confidence*100)}%)，继续讨论 ---`;
                    roundDiv.appendChild(d);
                    container.scrollTop = container.scrollHeight;
                } else if (data.type === 'timeout') {
                    roundDiv.innerHTML += `<div style="color:#c62828;padding:10px;">⏹ 已达到最大轮次，未能达成共识</div>`;
                    container.scrollTop = container.scrollHeight;
                } else if (data.type === 'done') {
                    btn.disabled = false; btn.textContent = '🤝 共识讨论';
                    ws.close();
                } else if (data.type === 'error') {
                    roundDiv.innerHTML += `<div style="color:red">错误: ${data.message}</div>`;
                    btn.disabled = false; btn.textContent = '🤝 共识讨论';
                    ws.close();
                }
            };
            ws.onerror = (err) => {
                roundDiv.innerHTML += `<div style="color:red">WebSocket 连接失败</div>`;
                btn.disabled = false; btn.textContent = '🤝 共识讨论';
            };
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_DEMO


if __name__ == '__main__':
    # 禁用 debug 模式以避免 semaphore 泄漏问题
    app.run(host='0.0.0.0', port=8890, debug=False, threaded=True)
