"""Step 1: MiMo 2.5 视觉识别 — 调用 MiMo 视觉模型识别景区图片内容"""

import base64

import requests

from config.settings import settings
from core.logging import logger
from core.utils import get_mime, resize_for_api


def recognize_with_mimo(image_bytes: bytes, image_format: str) -> dict:
    """调用 MiMo 2.5 视觉模型识别图片内容"""
    base64_image = base64.b64encode(resize_for_api(image_bytes)).decode()
    mime = get_mime(image_format)

    api_key = settings.MIMO_API_KEY
    api_base = settings.MIMO_API_BASE

    if not api_key:
        return {"success": False, "error": "MIMO_API_KEY 未配置"}

    prompt = """请用中文详细描述这张图片中的所有内容，要求不遗漏画面中的任何元素，包括主要场景、附属设施、遮挡物、路人、无关建筑、杂物等。只需要客观描述，不需要分析是否合规。

请按以下结构逐项描述：

**场景类型**：这是什么地方（入口、步道、观景台、停车场、卫生间等）

**标识标牌**：画面中所有的标识牌、指示牌、告示牌、广告牌等，逐一列出，写明上面的文字内容、颜色、材质和状态

**基础设施**：路面、栏杆、照明、座椅、垃圾桶、配电箱、管线、地砖等所有设施

**安全设施**：防护栏、警示标识、消防设备、监控摄像头等

**无障碍设施**：坡道、盲道、无障碍通道等

**建筑装饰**：建筑风格、装饰元素、外立面、屋顶、门窗等

**车辆与交通**：画面中的车辆（类型、颜色、位置）、交通标线、道闸等

**人员**：画面中的路人、工作人员，描述其大致位置、穿着、行为

**植物与自然**：树木、灌木、草坪、花卉、水体等

**杂物与遮挡物**：临时堆放物、施工围挡、垃圾桶满溢、乱贴乱挂（包括多余的标识牌）等

**画面边缘与其他**：画面边缘可见的建筑、设施或其他不完整的元素

每个类别下逐项列出所有观察到的内容，描述要具体详尽。"""

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
                "max_tokens": 4000,
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
