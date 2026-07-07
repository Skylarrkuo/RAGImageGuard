"""Step 2: MaxKB 合规分析 — 提取子问题 + 并行查询 MaxKB 知识库"""

import json
from concurrent.futures import ThreadPoolExecutor

import requests

from config.settings import settings
from core.logging import logger


def _query_maxkb_single(query: str, base_url: str, api_key: str) -> tuple:
    """单次 MaxKB 查询，返回 (answer, sources)"""
    logger.debug(f"[MaxKB] 查询: {query[:100]}...")
    try:
        resp = requests.get(f"{base_url}/open", headers={"Authorization": f"Bearer {api_key}", "accept": "*/*"}, timeout=30)
        if resp.status_code != 200:
            logger.error(f"[MaxKB] 获取 chat_id 失败: {resp.status_code} - {resp.text[:200]}")
            return "", []
        chat_id = resp.json().get("data", "")
        logger.debug(f"[MaxKB] 获取 chat_id: {chat_id}")

        resp = requests.post(
            f"{base_url}/chat_message/{chat_id}",
            headers={"Authorization": f"Bearer {api_key}", "accept": "*/*"},
            data={"message": query, "stream": "true", "re_chat": "false"},
            timeout=(30, 300),
            stream=True,
        )
        if resp.status_code != 200:
            logger.error(f"[MaxKB] chat_message 请求失败: {resp.status_code} - {resp.text[:200]}")
            return "", []

        answer = ""
        sources = []
        for raw_line in resp.iter_lines():
            if not raw_line or not raw_line.startswith(b"data:"):
                continue
            json_str = raw_line[5:].decode("utf-8", errors="replace").strip()
            if not json_str:
                continue
            try:
                event = json.loads(json_str)
            except json.JSONDecodeError:
                continue

            for para in event.get("paragraph_list", []):
                meta = para.get("metadata", {})
                name = meta.get("document_name", "")
                if name and name not in sources:
                    sources.append(name)

            if event.get("node_type") == "ai-chat-node":
                content = event.get("content", "")
                if content:
                    answer += content

        logger.debug(f"[MaxKB] 查询完成 | 回答长度: {len(answer)} 字符 | 来源: {sources}")
        return answer, sources
    except Exception as e:
        logger.error(f"[MaxKB] 查询异常: {e}")
        return "", []


def extract_sub_queries(scene_description: str) -> list:
    """用 MiMo 从场景描述中提取合规检查子问题（4-5个，覆盖面广）"""
    api_key = settings.MIMO_API_KEY
    api_base = settings.MIMO_API_BASE

    # 保底问题：覆盖主要合规维度
    fallback_queries = [
        "旅游景区的标识标牌有哪些国家标准要求？",
        "旅游景区的安全防护设施有哪些标准要求？",
        "旅游景区的无障碍设施有哪些标准要求？",
    ]

    if not api_key:
        return fallback_queries

    prompt = f"""你是旅游景区合规检查专家。根据场景描述，生成覆盖全面的合规检查子问题。

【场景描述】
{scene_description}

要求：
1. 逐项检查场景中出现的每个设施/元素，不要遗漏
2. 覆盖这些维度：标识标牌、安全设施、无障碍设施、消防设施、照明、卫生环保、建筑装饰、信息服务设施、应急设施
3. 只针对场景中确实存在的内容提问，没出现的跳过
4. 每个问题简短具体，格式："XXX的国家标准要求？"（如"景区入口标识牌的文字和尺寸要求？"）
5. 输出4-5个问题，每行一个，不要编号，不要多余解释"""

    logger.info(f"[Step2] 开始提取合规子问题")
    logger.debug(f"[Step2] 场景描述:\n{scene_description[:500]}...")

    try:
        resp = requests.post(
            f"{api_base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "mimo-v2.5",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 600,
                "temperature": 0.3,
            },
            timeout=60,
        )
        if resp.status_code != 200:
            raise Exception(f"MiMo API error: {resp.status_code}")

        content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        queries = [q.strip() for q in content.strip().split("\n") if q.strip() and len(q.strip()) > 8]
        result = queries[:5] if queries else fallback_queries
        logger.info(f"[Step2] 提取到 {len(result)} 个子问题:")
        for i, q in enumerate(result):
            logger.info(f"  子问题{i+1}: {q}")
        return result
    except Exception as e:
        logger.warning(f"[Step2] 提取子问题失败，使用兜底问题: {e}")
        return fallback_queries


def analyze_compliance_with_maxkb(scene_description: str, user_role: str = "tourist") -> dict:
    """将场景描述发送到 MaxKB 知识库进行合规分析（并行查询）"""
    base_url = settings.MAXKB_SCENE_OPTIMIZE_BASE_URL
    api_key = settings.MAXKB_SCENE_OPTIMIZE_API_KEY or settings.MAXKB_PRO_API_KEY

    if not api_key:
        return {"success": False, "error": "MaxKB API Key 未配置"}

    # Step 1: 提取子问题
    sub_queries = extract_sub_queries(scene_description)
    queries = [f"请根据旅游景区相关国家标准回答：{sq}" for sq in sub_queries]
    logger.info(f"[Step2] 开始并行查询 MaxKB | 共 {len(queries)} 个问题")

    # Step 2: 并行查询 MaxKB（4路并发）
    results = [None] * len(queries)

    def _query_one(idx, q):
        answer, sources = _query_maxkb_single(q, base_url, api_key)
        results[idx] = (answer, sources)

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(_query_one, i, q) for i, q in enumerate(queries)]
        for f in futures:
            f.result()

    # Step 3: 汇总
    all_answers = []
    all_sources = []
    for i, (answer, sources) in enumerate(results):
        if answer:
            all_answers.append(f"**问题{i+1}**：{sub_queries[i]}\n\n{answer}")
        all_sources.extend(sources)

    if not all_answers:
        logger.error("[Step2] MaxKB 未返回有效回答")
        return {"success": False, "error": "MaxKB 未返回有效回答"}

    seen = set()
    unique_sources = [s for s in all_sources if not (s in seen or seen.add(s))]

    logger.info(f"[Step2] 合规分析完成 | 有效回答: {len(all_answers)} 个 | 来源文档: {len(unique_sources)} 个")

    return {"success": True, "analysis": "\n\n---\n\n".join(all_answers), "sources": unique_sources}
