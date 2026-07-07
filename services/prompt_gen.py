"""Step 3: 生成改图提示词 — 基于合规分析结果生成图片编辑提示词"""

import requests

from config.settings import settings
from core.logging import logger


def generate_edit_summary(edit_prompt: str) -> dict:
    """基于编辑提示词生成修改总结和建议"""
    api_key = settings.MIMO_API_KEY
    api_base = settings.MIMO_API_BASE

    if not api_key:
        return {"success": False, "error": "MIMO_API_KEY 未配置"}

    logger.info(f"[Step4-Summary] 开始生成修改总结 | 编辑提示词: {len(edit_prompt)} 字符")

    prompt = f"""你是图片编辑专家。根据以下图片编辑提示词，生成一份简洁的修改总结和建议。

【编辑提示词】
{edit_prompt}

要求：
1. 修改总结：用简洁的条目列出本次修改的主要内容（3-5 条）
2. 修改建议：给出 2-3 条进一步优化的建议
3. 用中文撰写
4. 格式要求：用 markdown 格式，标题用 ### ，条目用 - 开头
5. 直接输出内容，不要加其他前缀

输出格式示例：

### 修改总结
- 替换了不合规的标识牌为符合国标的样式
- 移除了画面中的无关路人
- 补充了缺失的安全警示标识

### 修改建议
- 建议检查标识牌的文字内容是否准确
- 可以考虑增加无障碍设施标识
- 建议对建筑外观进行美化处理"""

    max_retries = 3
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[Step4-Summary] 第 {attempt}/{max_retries} 次尝试...")
            resp = requests.post(
                f"{api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "mimo-v2.5",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.5,
                },
                timeout=60,
            )

            if resp.status_code != 200:
                last_error = f"MiMo API 错误: {resp.status_code} - {resp.text[:200]}"
                logger.error(f"[Step4-Summary] {last_error}")
                continue

            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            cleaned = content.strip()

            if not cleaned:
                last_error = "总结生成返回空结果"
                logger.warning(f"[Step4-Summary] 第 {attempt} 次返回空内容")
                continue

            logger.info(f"[Step4-Summary] 总结生成成功 | 第 {attempt} 次 | 长度: {len(cleaned)} 字符")
            return {"success": True, "summary": cleaned}

        except Exception as e:
            last_error = f"LLM 请求异常: {str(e)}"
            logger.exception(f"[Step4-Summary] 第 {attempt} 次异常: {e}")
            continue

    logger.error(f"[Step4-Summary] 重试 {max_retries} 次均失败: {last_error}")
    return {"success": False, "error": f"总结生成失败（重试{max_retries}次）: {last_error}"}


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
{scene_description}

【合规分析结果】
{compliance_analysis}

要求：
1. 提示词用于对原图进行局部修改，保持原图整体构图不变
2. 针对上述合规问题，详细描述每一项需要修改的内容（如：替换不合规标识、补充缺失设施、修正文字错误等），确保所有合规问题都被覆盖
3. 如果场景描述中提到了路人(包括电动车等骑行工具)、游客或无关人员，在提示词中明确要求将他们移除，使画面更干净专业
4. 用中文撰写，描述要具体、完整，不限字数
5. 直接输出提示词正文，不要加"提示词："等前缀，不要解释

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
                    "model": "mimo-v2.5-pro",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 10000,
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
