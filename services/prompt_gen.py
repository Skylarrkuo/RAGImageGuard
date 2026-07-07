"""Step 3: 生成改图提示词 — 基于合规分析结果生成图片编辑提示词"""

import requests

from config.settings import settings
from core.logging import logger


def generate_edit_prompt(scene_description: str, compliance_analysis: str) -> dict:
    """基于识别结果和合规分析，生成 GPT-image-2 编辑提示词"""
    api_key = settings.MIMO_API_KEY
    api_base = settings.MIMO_API_BASE

    if not api_key:
        return {"success": False, "error": "MIMO_API_KEY 未配置"}

    logger.info(f"[Step3] 开始生成改图提示词 | 合规分析: {len(compliance_analysis)} 字符")
    logger.debug(f"[Step3] 场景描述:\n{scene_description[:300]}")
    logger.debug(f"[Step3] 合规分析:\n{compliance_analysis[:500]}")

    prompt = f"""你是图片编辑专家。根据以下景区场景和合规分析结果，生成一个用于 AI 改图的编辑提示词。

【场景描述】
{scene_description[:300]}

【合规分析结果】
{compliance_analysis[:2000]}

要求：
1. 提示词用于对原图进行局部修改，保持原图整体构图不变
2. 针对上述合规问题，描述需要修改的内容（如：替换不合规标识、补充缺失设施、修正文字错误等）
3. 用中文撰写，150字以内
4. 直接输出提示词正文，不要加"提示词："等前缀，不要解释

编辑提示词："""

    max_retries = 3
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[Step3] 第 {attempt}/{max_retries} 次尝试...")
            resp = requests.post(
                f"{api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "mimo-v2.5",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.5,
                },
                timeout=60,
            )

            if resp.status_code != 200:
                last_error = f"MiMo API 错误: {resp.status_code} - {resp.text[:200]}"
                logger.error(f"[Step3] {last_error}")
                continue

            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            # 清理可能的前缀
            cleaned = content.strip()
            for prefix in ("编辑提示词：", "提示词：", "提示词:"):
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix):].strip()

            if not cleaned:
                last_error = "提示词生成返回空结果"
                logger.warning(f"[Step3] 第 {attempt} 次返回空内容")
                continue

            logger.info(f"[Step3] 提示词生成成功 | 第 {attempt} 次 | 长度: {len(cleaned)} 字符")
            logger.debug(f"[Step3] 生成的提示词:\n{cleaned}")
            return {"success": True, "prompt": cleaned}

        except Exception as e:
            last_error = f"LLM 请求异常: {str(e)}"
            logger.exception(f"[Step3] 第 {attempt} 次异常: {e}")
            continue

    logger.error(f"[Step3] 重试 {max_retries} 次均失败: {last_error}")
    return {"success": False, "error": f"提示词生成失败（重试{max_retries}次）: {last_error}"}
