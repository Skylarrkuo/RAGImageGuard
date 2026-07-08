"""测试夹具 — Flask 应用、测试客户端、示例图片"""

import io
import os
import sys

import pytest
from PIL import Image

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def _clean_env(tmp_path, monkeypatch):
    """每个测试用例使用独立的临时数据库和环境变量"""
    db_path = tmp_path / "history.db"
    monkeypatch.setenv("MIMO_API_KEY", "test-key")
    monkeypatch.setenv("MIMO_API_BASE", "http://test")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_BASE", "http://test")
    monkeypatch.setenv("MAXKB_SCENE_OPTIMIZE_BASE_URL", "http://test")
    monkeypatch.setenv("MAXKB_SCENE_OPTIMIZE_API_KEY", "test-key")
    yield db_path


@pytest.fixture
def app(tmp_path, monkeypatch):
    """创建测试用 Flask 应用（使用临时数据库）"""
    # 重载 settings 以读取新的环境变量
    from config.settings import settings
    settings.reload()

    # 指向临时数据库
    import services.history as hist_mod
    monkeypatch.setattr(hist_mod, "DB_PATH", tmp_path / "history.db")

    from app import create_app
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app):
    """Flask 测试客户端"""
    return app.test_client()


@pytest.fixture
def sample_image_bytes():
    """生成一个 100x100 红色测试图片的字节（JPEG）"""
    img = Image.new("RGB", (100, 100), "red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def large_image_bytes():
    """生成一个 4000x3000 大图的字节（JPEG）"""
    img = Image.new("RGB", (4000, 3000), "blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


@pytest.fixture
def sample_rgba_image_bytes():
    """生成一个带透明通道的测试图片字节（PNG）"""
    img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
