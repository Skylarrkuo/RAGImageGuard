"""从 .env 文件加载配置"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 加载项目根目录的 .env
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


class _Settings:
    """简单的配置容器，从环境变量读取值。

    属性在类定义时求值一次。测试中可直接赋值覆盖，也可调用 reload() 重新从环境变量读取。
    """

    # MiMo 视觉 / LLM
    MIMO_API_KEY: str = os.getenv("MIMO_API_KEY", "")
    MIMO_API_BASE: str = os.getenv("MIMO_API_BASE", "")

    # MaxKB 场景优化专用智能体
    MAXKB_SCENE_OPTIMIZE_BASE_URL: str = os.getenv("MAXKB_SCENE_OPTIMIZE_BASE_URL", "")
    MAXKB_SCENE_OPTIMIZE_API_KEY: str = os.getenv("MAXKB_SCENE_OPTIMIZE_API_KEY", "")

    # OpenAI（图片编辑）
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "")
    OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "")

    # 安全配置
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8001")
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "20"))
    API_KEY: str = os.getenv("API_KEY", "")

    def reload(self):
        """重新从环境变量读取所有配置值（方便测试中 monkeypatch.setenv 后刷新）"""
        self.MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
        self.MIMO_API_BASE = os.getenv("MIMO_API_BASE", "")
        self.MAXKB_SCENE_OPTIMIZE_BASE_URL = os.getenv("MAXKB_SCENE_OPTIMIZE_BASE_URL", "")
        self.MAXKB_SCENE_OPTIMIZE_API_KEY = os.getenv("MAXKB_SCENE_OPTIMIZE_API_KEY", "")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "")
        self.OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "")
        self.ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8001")
        self.MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "20"))
        self.API_KEY = os.getenv("API_KEY", "")


settings = _Settings()

# 共享的图片上传目录（按类别分子目录）
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "data" / "uploads" / "images"
