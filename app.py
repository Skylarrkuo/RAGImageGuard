# ============================================================
# 景区图片合规检查 + AI 改图 — Flask API 后端
# 启动：python app.py
# API 文档：http://localhost:8001/api/config-check
# ============================================================

import base64
import io
import json
import os
import re
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from pathlib import Path

# 项目根目录（app.py 现在位于根目录）
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import requests
from flask import Flask, request, Response, jsonify, send_from_directory, stream_with_context
from flask_cors import CORS

from config.settings import settings

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# 线程池（替代 FastAPI 的 run_in_threadpool）
executor = ThreadPoolExecutor(max_workers=4)

# 图片保存目录
UPLOAD_DIR = project_root / "data" / "uploads" / "images"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 历史记录文件
HISTORY_FILE = project_root / "data" / "history.json"

# ============================================================
# 工具函数
# ============================================================

def _load_history() -> list:
    """读取历史记录"""
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save_history(record: dict):
    """追加一条历史记录"""
    history = _load_history()
    history.insert(0, record)  # 最新在前
    # 最多保留 100 条
    if len(history) > 100:
        history = history[:100]
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

def _detect_image_format(filename: str, content_type: str = "") -> str:
    """从文件名或 content_type 检测图片格式"""
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext in ("jpg", "jpeg", "png", "webp", "gif"):
            return ext
    if "jpeg" in content_type or "jpg" in content_type:
        return "jpg"
    if "png" in content_type:
        return "png"
    if "webp" in content_type:
        return "webp"
    return "png"


def _get_mime(format: str) -> str:
    mapping = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp", "gif": "image/gif"}
    return mapping.get(format, "image/png")


def _read_upload_file(file_storage):
    """从 Flask FileStorage 读取字节"""
    return file_storage.read()


# ============================================================
# Step 1: MiMo 2.5 视觉识别
# ============================================================

def _recognize_with_mimo_sync(image_bytes: bytes, image_format: str) -> dict:
    """调用 MiMo 2.5 视觉模型识别图片内容（同步版本）"""
    base64_image = base64.b64encode(image_bytes).decode()
    mime = _get_mime(image_format)

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
            return {"success": False, "error": f"MiMo API 错误: {resp.status_code} - {resp.text}"}

        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"success": True, "description": content}
    except Exception as e:
        return {"success": False, "error": f"MiMo 请求异常: {str(e)}"}


# ============================================================
# Step 2: MaxKB 合规分析
# ============================================================

def _query_maxkb_single(query: str, base_url: str, api_key: str) -> tuple:
    """单次 MaxKB 查询，返回 (answer, sources)"""
    try:
        resp = requests.get(f"{base_url}/open", headers={"Authorization": f"Bearer {api_key}", "accept": "*/*"}, timeout=30)
        if resp.status_code != 200:
            return "", []
        chat_id = resp.json().get("data", "")

        resp = requests.post(
            f"{base_url}/chat_message/{chat_id}",
            headers={"Authorization": f"Bearer {api_key}", "accept": "*/*"},
            data={"message": query, "stream": "true", "re_chat": "false"},
            timeout=(30, 300),
            stream=True,
        )
        if resp.status_code != 200:
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

        return answer, sources
    except Exception:
        return "", []


def _extract_sub_queries(scene_description: str) -> list:
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
        return queries[:5] if queries else fallback_queries
    except Exception:
        return fallback_queries


def _analyze_compliance_with_maxkb_sync(scene_description: str, user_role: str = "tourist") -> dict:
    """将场景描述发送到 MaxKB 知识库进行合规分析（同步版本，并行2路查询）"""
    base_url = settings.MAXKB_SCENE_OPTIMIZE_BASE_URL
    api_key = settings.MAXKB_SCENE_OPTIMIZE_API_KEY or settings.MAXKB_PRO_API_KEY

    if not api_key:
        return {"success": False, "error": "MaxKB API Key 未配置"}

    # Step 1: 提取子问题
    sub_queries = _extract_sub_queries(scene_description)
    queries = [f"请根据旅游景区相关国家标准回答：{sq}" for sq in sub_queries]

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
        return {"success": False, "error": "MaxKB 未返回有效回答"}

    seen = set()
    unique_sources = [s for s in all_sources if not (s in seen or seen.add(s))]

    return {"success": True, "analysis": "\n\n---\n\n".join(all_answers), "sources": unique_sources}


# ============================================================
# Step 3: 生成改图提示词
# ============================================================

def _generate_edit_prompt_sync(scene_description: str, compliance_analysis: str) -> dict:
    """基于识别结果和合规分析，生成 GPT-image-2 编辑提示词（同步版本）"""
    api_key = settings.MIMO_API_KEY
    api_base = settings.MIMO_API_BASE

    if not api_key:
        return {"success": False, "error": "MIMO_API_KEY 未配置"}

    # 从合规分析中提取关键违规点（去掉标准条文编号等冗余信息，保留问题描述和结论）
    issues = []
    for block in compliance_analysis.split("---"):
        lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
        # 跳过纯标准编号行（如 GB/T xxx、GB xxx），保留有意义的描述
        key_lines = []
        for line in lines:
            # 跳过标准引用行、空行、纯标点行
            if re.match(r'^(GB|GB/T|根据|依据|按照|参考)\s*\d', line):
                continue
            if len(line) < 8:
                continue
            key_lines.append(line)
        if key_lines:
            # 取前2行作为该问题的摘要
            issues.append("；".join(key_lines[:2]))
    issues_summary = "\n".join(f"- {s}" for s in issues[:3]) if issues else compliance_analysis[:500]

    prompt = f"""根据以下景区场景和合规问题，生成一个简短的图片编辑提示词。

【场景】{scene_description[:300]}

【发现的合规问题】
{issues_summary}

要求：
- 保持原图构图，只修改不合规的部分
- 中文撰写，150字以内
- 只输出提示词，不要解释

提示词："""

    try:
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
            return {"success": False, "error": f"MiMo API 错误: {resp.status_code} - {resp.text}"}

        data = resp.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {"success": True, "prompt": content.strip()}
    except Exception as e:
        return {"success": False, "error": f"LLM 请求异常: {str(e)}"}


# ============================================================
# Step 4: GPT-image-1 图片编辑
# ============================================================

def _generate_edited_image_sync(image_bytes: bytes, image_format: str, prompt: str) -> dict:
    """调用 OpenAI Images API (gpt-image-2) 进行图片编辑（同步版本）"""
    from openai import OpenAI
    import httpx

    api_key = settings.OPENAI_API_KEY
    if not api_key:
        return {"success": False, "error": "OPENAI_API_KEY 未配置"}

    try:
        # 设置较长超时，图片生成可能需要 60-120 秒，禁用代理
        http_client = httpx.Client(proxy=None, timeout=300.0)
        client = OpenAI(api_key=api_key, base_url=settings.OPENAI_API_BASE, timeout=300.0, http_client=http_client)

        # 将图片转为 file-like 对象
        image_file = io.BytesIO(image_bytes)
        image_file.name = f"image.{image_format}"

        # 调用图片编辑接口
        result = client.images.edit(
            model="gpt-image-2",
            image=image_file,
            prompt=prompt,
            n=1,
            size="1024x1024",
        )

        image_data_b64 = result.data[0].b64_json
        if image_data_b64:
            image_bytes_result = base64.b64decode(image_data_b64)
        else:
            # 如果返回的是 URL，下载图片
            image_url = result.data[0].url
            dl_resp = requests.get(image_url, timeout=120)
            image_bytes_result = dl_resp.content

        return {"success": True, "image_bytes": image_bytes_result}

    except Exception as e:
        return {"success": False, "error": f"图片编辑失败: {str(e)}"}


# ============================================================
# API 端点
# ============================================================

@app.route("/images/<filename>")
def serve_image(filename):
    """提供上传/生成的图片"""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        return jsonify({"error": "图片不存在"}), 404
    mime = _get_mime(file_path.suffix.lstrip("."))
    return Response(file_path.read_bytes(), mimetype=mime)


@app.route("/api/recognize", methods=["POST"])
def api_recognize():
    """Step 1: 仅识别图片内容"""
    image = request.files.get("image")
    if not image:
        return jsonify({"success": False, "error": "未上传图片"}), 400

    image_bytes = image.read()
    if not image_bytes:
        return jsonify({"success": False, "error": "图片为空"}), 400

    image_format = _detect_image_format(image.filename or "", image.content_type or "")
    future = executor.submit(_recognize_with_mimo_sync, image_bytes, image_format)
    result = future.result()
    return jsonify(result)


@app.route("/api/analyze-compliance", methods=["POST"])
def api_analyze_compliance():
    """Step 2: 仅合规分析"""
    scene_description = request.form.get("scene_description", "")
    user_role = request.form.get("user_role", "tourist")

    if not scene_description:
        return jsonify({"success": False, "error": "缺少场景描述"}), 400

    future = executor.submit(_analyze_compliance_with_maxkb_sync, scene_description, user_role)
    result = future.result()
    return jsonify(result)


@app.route("/api/generate-prompt", methods=["POST"])
def api_generate_prompt():
    """Step 3: 仅生成提示词"""
    scene_description = request.form.get("scene_description", "")
    compliance_analysis = request.form.get("compliance_analysis", "")

    if not scene_description or not compliance_analysis:
        return jsonify({"success": False, "error": "缺少必要参数"}), 400

    future = executor.submit(_generate_edit_prompt_sync, scene_description, compliance_analysis)
    result = future.result()
    return jsonify(result)


@app.route("/api/generate-image", methods=["POST"])
def api_generate_image():
    """Step 4: 仅图片编辑"""
    image = request.files.get("image")
    prompt = request.form.get("prompt", "")

    if not image:
        return jsonify({"success": False, "error": "未上传图片"}), 400
    if not prompt:
        return jsonify({"success": False, "error": "缺少提示词"}), 400

    image_bytes = image.read()
    if not image_bytes:
        return jsonify({"success": False, "error": "图片为空"}), 400

    image_format = _detect_image_format(image.filename or "", image.content_type or "")
    future = executor.submit(_generate_edited_image_sync, image_bytes, image_format, prompt)
    result = future.result()

    if result.get("success"):
        # 保存生成的图片
        filename = f"generated_{uuid.uuid4().hex[:8]}.png"
        save_path = UPLOAD_DIR / filename
        save_path.write_bytes(result["image_bytes"])
        result["image_url"] = f"/images/{filename}"
        del result["image_bytes"]

    return jsonify(result)


@app.route("/api/full-pipeline", methods=["POST"])
def api_full_pipeline():
    """完整流水线：识别 → 合规分析 → 生成提示词 → 图片编辑"""
    image = request.files.get("image")
    if not image:
        return jsonify({"success": False, "error": "未上传图片"}), 400

    image_bytes = image.read()
    if not image_bytes:
        return jsonify({"success": False, "error": "图片为空"}), 400

    image_format = _detect_image_format(image.filename or "", image.content_type or "")

    # 保存原图
    original_filename = f"original_{uuid.uuid4().hex[:8]}.{image_format}"
    (UPLOAD_DIR / original_filename).write_bytes(image_bytes)
    original_url = f"/images/{original_filename}"

    results = {"original_url": original_url, "steps": {}}

    # Step 1: 识别
    t1 = time.time()
    recognize_result = _recognize_with_mimo_sync(image_bytes, image_format)
    results["steps"]["recognize"] = {"time_ms": int((time.time() - t1) * 1000), **recognize_result}

    if not recognize_result.get("success"):
        results["total_time_ms"] = int((time.time() - t1) * 1000)
        return jsonify(results)

    scene_description = recognize_result["description"]

    # Step 2: 合规分析
    t2 = time.time()
    compliance_result = _analyze_compliance_with_maxkb_sync(scene_description)
    results["steps"]["compliance"] = {"time_ms": int((time.time() - t2) * 1000), **compliance_result}

    if not compliance_result.get("success"):
        results["total_time_ms"] = int((time.time() - t1) * 1000)
        return jsonify(results)

    # Step 3: 生成提示词
    t3 = time.time()
    prompt_result = _generate_edit_prompt_sync(scene_description, compliance_result["analysis"])
    results["steps"]["prompt"] = {"time_ms": int((time.time() - t3) * 1000), **prompt_result}

    if not prompt_result.get("success"):
        results["total_time_ms"] = int((time.time() - t1) * 1000)
        return jsonify(results)

    # Step 4: 图片编辑
    t4 = time.time()
    image_result = _generate_edited_image_sync(image_bytes, image_format, prompt_result["prompt"])
    results["steps"]["image_edit"] = {"time_ms": int((time.time() - t4) * 1000)}

    if image_result.get("success"):
        gen_filename = f"generated_{uuid.uuid4().hex[:8]}.png"
        gen_path = UPLOAD_DIR / gen_filename
        gen_path.write_bytes(image_result["image_bytes"])
        results["steps"]["image_edit"]["success"] = True
        results["steps"]["image_edit"]["image_url"] = f"/images/{gen_filename}"
    else:
        results["steps"]["image_edit"]["success"] = False
        results["steps"]["image_edit"]["error"] = image_result.get("error")

    results["total_time_ms"] = int((time.time() - t1) * 1000)

    # 自动保存历史记录
    now = datetime.now(timezone(timedelta(hours=8)))
    record = {
        "id": uuid.uuid4().hex[:12],
        "created_at": now.isoformat(timespec="seconds"),
        "mode": "full",
        "original_image": original_filename,
        "generated_image": None,
        "scene_description": scene_description if recognize_result.get("success") else None,
        "compliance_analysis": compliance_result.get("analysis") if compliance_result.get("success") else None,
        "compliance_queries": [],
        "edit_prompt": prompt_result.get("prompt") if prompt_result.get("success") else None,
        "step_times": {
            "step1_ms": results["steps"].get("recognize", {}).get("time_ms"),
            "step2_ms": results["steps"].get("compliance", {}).get("time_ms"),
            "step3_ms": results["steps"].get("prompt", {}).get("time_ms"),
            "step4_ms": results["steps"].get("image_edit", {}).get("time_ms"),
        },
        "status": "completed" if results["steps"].get("image_edit", {}).get("success") else "partial",
    }
    gen_img = results["steps"].get("image_edit", {}).get("image_url")
    if gen_img:
        record["generated_image"] = gen_img.split("/")[-1]
    _save_history(record)

    return jsonify(results)


@app.route("/api/full-pipeline-stream", methods=["POST"])
def api_full_pipeline_stream():
    """完整流水线（SSE 实时推送）：识别 → 合规分析 → 生成提示词 → 图片编辑"""
    image = request.files.get("image")
    if not image:
        return jsonify({"success": False, "error": "未上传图片"}), 400

    image_bytes = image.read()
    if not image_bytes:
        return jsonify({"success": False, "error": "图片为空"}), 400

    image_format = _detect_image_format(image.filename or "", image.content_type or "")

    # 保存原图
    original_filename = f"original_{uuid.uuid4().hex[:8]}.{image_format}"
    (UPLOAD_DIR / original_filename).write_bytes(image_bytes)
    original_url = f"/images/{original_filename}"

    # 使用场景优化专用智能体
    maxkb_base_url = settings.MAXKB_SCENE_OPTIMIZE_BASE_URL
    maxkb_api_key = settings.MAXKB_SCENE_OPTIMIZE_API_KEY or settings.MAXKB_PRO_API_KEY

    def _stream_compliance(scene_desc: str):
        """流式合规分析：提取子问题 → 并行2路查询 MaxKB"""
        sub_queries = _extract_sub_queries(scene_desc)
        queries = [f"请根据旅游景区相关国家标准回答：{sq}" for sq in sub_queries]

        all_sources = []

        # 并行查询，每批4个
        def _fetch_one(idx, q):
            answer, sources = _query_maxkb_single(q, maxkb_base_url, maxkb_api_key)
            return idx, answer, sources

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(_fetch_one, i, q) for i, q in enumerate(queries)]
            for f in futures:
                idx, answer, sources = f.result()
                # 按完成顺序推送事件
                yield {"type": "query_start", "index": idx, "question": sub_queries[idx]}
                if answer:
                    yield {"type": "content", "index": idx, "text": answer}
                all_sources.extend(sources)
                yield {"type": "query_end", "index": idx}

        # 去重
        seen = set()
        unique_sources = [s for s in all_sources if not (s in seen or seen.add(s))]
        yield {"type": "sources", "sources": unique_sources}

    def generate():
        t_total = time.time()
        # 用于收集历史记录的中间变量
        hist = {
            "id": uuid.uuid4().hex[:12],
            "created_at": datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds"),
            "mode": "full",
            "original_image": original_filename,
            "generated_image": None,
            "scene_description": None,
            "compliance_analysis": None,
            "compliance_queries": [],
            "edit_prompt": None,
            "step_times": {},
            "status": "partial",
        }
        hist_queries = []  # 收集子问题

        def _save_and_done():
            hist["compliance_queries"] = hist_queries
            _save_history(hist)

        yield f"data: {json.dumps({'type': 'original', 'url': original_url}, ensure_ascii=False)}\n\n"

        # Step 1: 识别
        t1 = time.time()
        yield f"data: {json.dumps({'type': 'step', 'step': 'recognize', 'status': 'running'}, ensure_ascii=False)}\n\n"
        recognize_result = _recognize_with_mimo_sync(image_bytes, image_format)
        step_data = {"type": "step", "step": "recognize", "time_ms": int((time.time() - t1) * 1000), **recognize_result}
        hist["step_times"]["step1_ms"] = step_data["time_ms"]
        yield f"data: {json.dumps(step_data, ensure_ascii=False)}\n\n"

        if not recognize_result.get("success"):
            _save_and_done()
            yield f"data: {json.dumps({'type': 'done', 'total_time_ms': int((time.time() - t_total) * 1000)}, ensure_ascii=False)}\n\n"
            return

        scene_description = recognize_result["description"]
        hist["scene_description"] = scene_description

        # Step 2: 合规分析（流式）
        t2 = time.time()
        yield f"data: {json.dumps({'type': 'step', 'step': 'compliance', 'status': 'running'}, ensure_ascii=False)}\n\n"

        full_answer = ""
        final_sources = []
        for chunk in _stream_compliance(scene_description):
            if chunk["type"] == "content":
                full_answer += chunk["text"]
                # 将回答分配到对应的历史子问题
                for hq in hist_queries:
                    if hq["index"] == chunk["index"]:
                        hq["answer"] = chunk["text"]
                        break
                # 实时推送每个内容块（带 index 精确匹配问题）
                yield f"data: {json.dumps({'type': 'compliance_chunk', 'index': chunk['index'], 'text': chunk['text']}, ensure_ascii=False)}\n\n"
            elif chunk["type"] == "sources":
                final_sources = chunk["sources"]
            elif chunk["type"] == "query_start":
                hist_queries.append({"index": chunk["index"], "question": chunk["question"], "answer": ""})
                yield f"data: {json.dumps({'type': 'compliance_query', 'index': chunk['index'], 'question': chunk['question']}, ensure_ascii=False)}\n\n"
            elif chunk["type"] == "query_end":
                yield f"data: {json.dumps({'type': 'query_end', 'index': chunk['index']}, ensure_ascii=False)}\n\n"

        t2_ms = int((time.time() - t2) * 1000)
        hist["step_times"]["step2_ms"] = t2_ms

        if not full_answer:
            yield f"data: {json.dumps({'type': 'step', 'step': 'compliance', 'time_ms': t2_ms, 'success': False, 'error': 'MaxKB 未返回有效回答'}, ensure_ascii=False)}\n\n"
            _save_and_done()
            yield f"data: {json.dumps({'type': 'done', 'total_time_ms': int((time.time() - t_total) * 1000)}, ensure_ascii=False)}\n\n"
            return

        # 将回答按 index 分配到 hist_queries
        # 由于 _stream_compliance 按完成顺序返回，回答是完整的一块
        # 需要按顺序匹配：content 事件的 index 对应 hist_queries 中的条目
        # 重新从 chunk 收集中按 index 累加
        hist["compliance_analysis"] = full_answer
        yield f"data: {json.dumps({'type': 'step', 'step': 'compliance', 'time_ms': t2_ms, 'success': True, 'analysis': full_answer, 'sources': final_sources}, ensure_ascii=False)}\n\n"

        # Step 3: 生成提示词
        t3 = time.time()
        yield f"data: {json.dumps({'type': 'step', 'step': 'prompt', 'status': 'running'}, ensure_ascii=False)}\n\n"
        prompt_result = _generate_edit_prompt_sync(scene_description, full_answer)
        step_data = {"type": "step", "step": "prompt", "time_ms": int((time.time() - t3) * 1000), **prompt_result}
        hist["step_times"]["step3_ms"] = step_data["time_ms"]
        yield f"data: {json.dumps(step_data, ensure_ascii=False)}\n\n"

        if not prompt_result.get("success"):
            _save_and_done()
            yield f"data: {json.dumps({'type': 'done', 'total_time_ms': int((time.time() - t_total) * 1000)}, ensure_ascii=False)}\n\n"
            return

        hist["edit_prompt"] = prompt_result.get("prompt")

        # Step 4: 图片编辑
        t4 = time.time()
        yield f"data: {json.dumps({'type': 'step', 'step': 'image_edit', 'status': 'running'}, ensure_ascii=False)}\n\n"
        image_result = _generate_edited_image_sync(image_bytes, image_format, prompt_result["prompt"])
        step_data = {"type": "step", "step": "image_edit", "time_ms": int((time.time() - t4) * 1000)}
        hist["step_times"]["step4_ms"] = step_data["time_ms"]
        if image_result.get("success"):
            gen_filename = f"generated_{uuid.uuid4().hex[:8]}.png"
            (UPLOAD_DIR / gen_filename).write_bytes(image_result["image_bytes"])
            step_data["success"] = True
            step_data["image_url"] = f"/images/{gen_filename}"
            hist["generated_image"] = gen_filename
            hist["status"] = "completed"
        else:
            step_data["success"] = False
            step_data["error"] = image_result.get("error")
        yield f"data: {json.dumps(step_data, ensure_ascii=False)}\n\n"

        _save_and_done()
        yield f"data: {json.dumps({'type': 'done', 'total_time_ms': int((time.time() - t_total) * 1000)}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ============================================================
# 历史记录 API
# ============================================================

@app.route("/api/history", methods=["GET"])
def api_get_history():
    """获取历史记录列表"""
    history = _load_history()
    return jsonify({"success": True, "records": history})


@app.route("/api/history/<record_id>", methods=["GET"])
def api_get_history_detail(record_id):
    """获取单条历史记录详情"""
    history = _load_history()
    for record in history:
        if record.get("id") == record_id:
            return jsonify({"success": True, "record": record})
    return jsonify({"success": False, "error": "记录不存在"}), 404


@app.route("/api/history/<record_id>", methods=["DELETE"])
def api_delete_history(record_id):
    """删除一条历史记录"""
    history = _load_history()
    new_history = [r for r in history if r.get("id") != record_id]
    if len(new_history) == len(history):
        return jsonify({"success": False, "error": "记录不存在"}), 404
    HISTORY_FILE.write_text(json.dumps(new_history, ensure_ascii=False, indent=2), encoding="utf-8")
    return jsonify({"success": True})


@app.route("/api/config-check")
def api_config_check():
    """检查配置是否完整"""
    return jsonify({
        "mimo": {
            "api_key_configured": bool(settings.MIMO_API_KEY),
            "api_base": settings.MIMO_API_BASE,
        },
        "maxkb": {
            "standard_key_configured": bool(settings.MAXKB_STANDARD_API_KEY),
            "pro_key_configured": bool(settings.MAXKB_PRO_API_KEY),
            "standard_url": settings.MAXKB_STANDARD_BASE_URL,
        },
        "openai": {
            "api_key_configured": bool(settings.OPENAI_API_KEY),
            "api_base": settings.OPENAI_API_BASE,
            "model": settings.OPENAI_MODEL_NAME,
        },
    })


# ============================================================
# 启动
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("景区图片合规检查 Flask API")
    print("API 端点: http://localhost:8001/api/config-check")
    print("前端开发: cd frontend && npm run dev")
    print("=" * 60)
    app.run(host="0.0.0.0", port=8001, debug=True)
