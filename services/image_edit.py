"""Step 4: GPT-Image 图片编辑 — 调用 OpenAI Images API 生成修复后的图片"""

import base64
import io
import os
import threading
import time

import requests

from config.settings import settings
from core.logging import logger
from core.utils import get_image_dimensions, pick_gpt_image_size

# 保护 os.environ 读写的全局锁
_env_lock = threading.Lock()


def generate_edited_image(image_bytes: bytes, image_format: str, prompt: str) -> dict:
    """调用 OpenAI Images API (gpt-image-2) 进行图片编辑（含重试）"""
    from openai import OpenAI, APIConnectionError, APITimeoutError, RateLimitError
    import httpx

    api_key = settings.OPENAI_API_KEY
    if not api_key:
        return {"success": False, "error": "OPENAI_API_KEY 未配置"}

    # 自动检测图片尺寸并选择合适的生成比例
    try:
        width, height = get_image_dimensions(image_bytes)
        target_size = pick_gpt_image_size(width, height)
        logger.info(f"[Step4] 原始图片尺寸: {width}x{height} → 生成尺寸: {target_size}")
    except Exception as e:
        logger.warning(f"[Step4] 无法检测图片尺寸, 使用默认 1024x1024: {e}")
        target_size = "1024x1024"

    logger.info(f"[Step4] 开始 GPT-Image 图片编辑 | 图片大小: {len(image_bytes)} bytes | 格式: {image_format}")
    logger.info(f"[Step4] 编辑提示词:\n{prompt}")

    # 需要清除的代理环境变量（包括 OpenAI SDK 读取的）
    proxy_env_keys = [
        "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
        "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy",
        "OPENAI_PROXY",
    ]

    def _call_api():
        """单次 API 调用"""
        # 清除代理环境变量（线程安全）
        with _env_lock:
            saved_env = {}
            for k in proxy_env_keys:
                if k in os.environ:
                    saved_env[k] = os.environ.pop(k)
        try:
            timeout = httpx.Timeout(connect=30.0, read=600.0, write=30.0, pool=30.0)
            http_client = httpx.Client(proxy=None, timeout=timeout)
            client = OpenAI(api_key=api_key, base_url=settings.OPENAI_API_BASE, timeout=600.0, http_client=http_client)

            image_file = io.BytesIO(image_bytes)
            image_file.name = f"image.{image_format}"

            result = client.images.edit(
                model="gpt-image-2",
                image=image_file,
                prompt=prompt,
                n=1,
                size=target_size,
            )

            image_data_b64 = result.data[0].b64_json
            if image_data_b64:
                return base64.b64decode(image_data_b64)
            else:
                image_url = result.data[0].url
                dl_resp = requests.get(image_url, timeout=120)
                return dl_resp.content
        finally:
            with _env_lock:
                for k, v in saved_env.items():
                    os.environ[k] = v

    # 重试逻辑：最多 3 次，遇到连接/超时错误重试
    max_retries = 3
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[Step4] 尝试 {attempt}/{max_retries}...")
            image_bytes_result = _call_api()
            logger.info(f"[Step4] GPT-Image 成功 | 生成图片大小: {len(image_bytes_result)} bytes")
            return {"success": True, "image_bytes": image_bytes_result}
        except (APIConnectionError, APITimeoutError) as e:
            last_error = e
            logger.warning(f"[Step4] 连接错误 (尝试 {attempt}): {type(e).__name__}: {e}")
            if attempt < max_retries:
                wait = 10 * attempt
                logger.info(f"[Step4] 等待 {wait}s 后重试...")
                time.sleep(wait)
        except RateLimitError as e:
            last_error = e
            logger.warning(f"[Step4] 频率限制: {e}")
            if attempt < max_retries:
                time.sleep(30)
        except Exception as e:
            last_error = e
            logger.error(f"[Step4] 未知错误: {type(e).__name__}: {e}")
            break  # 不可重试的错误

    return {"success": False, "error": f"图片编辑失败: {type(last_error).__name__}: {last_error}"}
