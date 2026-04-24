#!/usr/bin/env python3
"""
统一 API 入口。
前端（Web / 飞书 / 微信）统一调用 /v1/discuss，
由 WebAdapter 解析请求并渲染响应。
"""
import os
import sys
import logging

from flask import Flask
from flask_cors import CORS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model_router.providers.kimi import KimiProvider
from model_router.router import ModelRouter
from model_router.registry import ProviderRegistry
from harness_engine.engine import HarnessEngine
from session.manager import SessionManager
from session.store_redis import RedisSessionStore
from adapters.web import WebAdapter
from adapters.feishu import FeishuAdapter

from api import state
from api.routes import register_routes

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
if os.environ.get("MULTIROLE_DEMO_MODE"):
    from examples.run_consensus_demo import DemoProvider
    default_provider = DemoProvider()
else:
    os.environ.setdefault("MULTIROLE_KIMI_MODE", "proxy")
    ProviderRegistry.register("kimi", KimiProvider)
    default_provider = ProviderRegistry.create("kimi")

router = ModelRouter(default_provider=default_provider)
engine = HarnessEngine(router=router)

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

web_adapter = WebAdapter()
feishu_adapter = FeishuAdapter()

# 共享状态
state.session_manager = session_manager
state.web_adapter = web_adapter
state.feishu_adapter = feishu_adapter
state.engine = engine

# 注册路由
register_routes(app, sock)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8890, debug=False, threaded=True)
