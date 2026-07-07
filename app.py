# ============================================================
# 景区图片合规检查 + AI 改图 — Flask API 后端
# 启动：python app.py
# API 文档：http://localhost:8001/api/config-check
# ============================================================

import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from flask import Flask
from flask_cors import CORS

from core.logging import setup_logging
from routes import register_all_blueprints


def create_app() -> Flask:
    """应用工厂函数"""
    setup_logging()

    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    register_all_blueprints(app)

    return app


if __name__ == "__main__":
    app = create_app()
    print("=" * 60)
    print("景区图片合规检查 Flask API")
    print("API 端点: http://localhost:8001/api/config-check")
    print("前端开发: cd frontend && npm run dev")
    print("=" * 60)
    app.run(host="0.0.0.0", port=8001, debug=True)
