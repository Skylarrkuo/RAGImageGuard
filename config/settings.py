"""从 .env 文件加载配置"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 加载项目根目录的 .env
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


class _Settings:
    """简单的配置容器，从环境变量读取值"""

    # MiMo 视觉 / LLM
    MIMO_API_KEY: str = os.getenv("MIMO_API_KEY", "")
    MIMO_API_BASE: str = os.getenv("MIMO_API_BASE", "")

    # MaxKB
    MAXKB_STANDARD_BASE_URL: str = os.getenv("MAXKB_STANDARD_BASE_URL", "")
    MAXKB_STANDARD_API_KEY: str = os.getenv("MAXKB_STANDARD_API_KEY", "")
    MAXKB_PRO_BASE_URL: str = os.getenv("MAXKB_PRO_BASE_URL", "")
    MAXKB_PRO_API_KEY: str = os.getenv("MAXKB_PRO_API_KEY", "")
    MAXKB_SCENE_OPTIMIZE_BASE_URL: str = os.getenv("MAXKB_SCENE_OPTIMIZE_BASE_URL", "")
    MAXKB_SCENE_OPTIMIZE_API_KEY: str = os.getenv("MAXKB_SCENE_OPTIMIZE_API_KEY", "")

    # OpenAI（图片编辑）
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "")
    OPENAI_MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "")


settings = _Settings()
