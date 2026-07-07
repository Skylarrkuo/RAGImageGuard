"""Step 1: MiMo 2.5 视觉识别 — 调用 MiMo 视觉模型识别景区图片内容"""

import base64

import requests

from config.settings import settings
from core.logging import logger
from core.utils import get_mime


def recognize_with_mimo(image_bytes: bytes, image_format: str) -> dict:
    """调用 MiMo 2.5 视觉模型识别图片内容"""
    base64_image = base64.b64encode(image_bytes).decode()
    mime = get_mime(image_format)

    api_key = settings.MIMO_API_KEY
    api_base = settings.MIMO_API_BASE

    if not api_key:
        return {"success": False, "error": "MIMO_API_KEY 未配置"}

    prompt = """请用中文简洁描述这张景区图片中的场景，只需要客观描述画面内容，不需要分析是否合规。控制在1000字以内。

请按以下结构描述：

**场景类型**：这是什么地方（入口、步道、观景台、停车场、卫生间等）

**标识标牌**：画面中有哪些标识牌，上面写了什么，材质和状态如何

**基础设施**：路面、栏杆、照明、座椅、垃圾桶等设施的情况

**安全设施**：防护栏、警示标识、消防设备等

**无障碍设施**：坡道、盲道等

**建筑装饰**：建筑风格、装饰元素

**环境卫生**：清洁度、绿化状况

只描述你看到的，不要做评价或建议。"""

    logger.info(f"[Step1] 开始 MiMo 视觉识别 | 图片大小: {len(image_bytes)} bytes | 格式: {image_format} | MIME: {mime}")
    logger.debug(f"[Step1] 识别 Prompt:\n{prompt}")

    try:
        resp = requests.post(
            f"{api_base}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "mimo-v2.5",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime};base64,{base64_image}"},
                            },
                        ],
                    }
                ],
                "max_tokens": 2000,
            },
            timeout=120,
        )

        if resp.status_code != 200:
            logger.error(f"[Step1] MiMo API 返回错误: {resp.status_code} - {resp.text[:500]}")
            return {"success": False, "error": f"MiMo API 错误: {resp.status_code} - {resp.text}"}

        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not content or not content.strip():
            logger.warning("[Step1] MiMo 返回了空内容")
            return {"success": False, "error": "MiMo 视觉识别返回空结果，请重试"}

        logger.info(f"[Step1] 识别完成 | 响应长度: {len(content)} 字符")
        logger.debug(f"[Step1] 识别结果:\n{content}")
        return {"success": True, "description": content}
    except Exception as e:
        logger.exception(f"[Step1] MiMo 请求异常: {e}")
        return {"success": False, "error": f"MiMo 请求异常: {str(e)}"}
