"""流水线路由 — 识别、合规分析、提示词生成、图片编辑、完整流水线"""

import json
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from pathlib import Path

from flask import Blueprint, request, Response, jsonify, stream_with_context

from core.logging import logger
from core.utils import detect_image_format, create_thumbnail
from services.mimo import recognize_with_mimo
from services.maxkb import analyze_compliance_with_maxkb, extract_sub_queries, _query_maxkb_single
from services.prompt_gen import generate_edit_prompt
from services.image_edit import generate_edited_image
from services.history import save_history, update_history

from config.settings import settings

pipeline_bp = Blueprint("pipeline", __name__)

# 线程池
executor = ThreadPoolExecutor(max_workers=4)

# 图片保存目录（按类别分子目录）
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "data" / "uploads" / "images"
IMAGE_SUBDIRS = ("original", "generated", "refined", "thumb")
for _sub in IMAGE_SUBDIRS:
    (UPLOAD_DIR / _sub).mkdir(parents=True, exist_ok=True)


def _save_with_thumbnail(filename: str, image_bytes: bytes, subdir: str = "original"):
    """保存图片到指定子目录 + 在 thumb/ 下生成缩略图

    返回形如 "original/abc123.jpg" 的相对路径，可直接拼接 /images/ 前缀访问。
    """
    save_dir = UPLOAD_DIR / subdir
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / filename
    save_path.write_bytes(image_bytes)
    # 缩略图统一放 thumb/ 目录
    try:
        thumb_bytes = create_thumbnail(image_bytes)
        stem = filename.rsplit(".", 1)[0]
        thumb_path = UPLOAD_DIR / "thumb" / f"thumb_{stem}.jpg"
        thumb_path.write_bytes(thumb_bytes)
    except Exception as e:
        logger.warning(f"[Pipeline] 缩略图生成失败: {e}")
    return f"{subdir}/{filename}"


# ------------------------------------------------------------
# 单步端点
# ------------------------------------------------------------

@pipeline_bp.route("/api/recognize", methods=["POST"])
def api_recognize():
    """Step 1: 仅识别图片内容"""
    logger.info("=" * 60)
    logger.info("[API] POST /api/recognize 收到请求")
    image = request.files.get("image")
    if not image:
        return jsonify({"success": False, "error": "未上传图片"}), 400

    image_bytes = image.read()
    if not image_bytes:
        return jsonify({"success": False, "error": "图片为空"}), 400

    image_format = detect_image_format(image.filename or "", image.content_type or "")
    logger.info(f"[API] 图片信息: 文件名={image.filename}, 大小={len(image_bytes)} bytes, 格式={image_format}")
    future = executor.submit(recognize_with_mimo, image_bytes, image_format)
    result = future.result()
    logger.info(f"[API] /api/recognize 完成 | success={result.get('success')}")
    return jsonify(result)


@pipeline_bp.route("/api/analyze-compliance", methods=["POST"])
def api_analyze_compliance():
    """Step 2: 仅合规分析"""
    logger.info("=" * 60)
    logger.info("[API] POST /api/analyze-compliance 收到请求")
    scene_description = request.form.get("scene_description", "")
    user_role = request.form.get("user_role", "tourist")

    if not scene_description:
        return jsonify({"success": False, "error": "缺少场景描述"}), 400

    logger.info(f"[API] 场景描述长度: {len(scene_description)} 字符 | 用户角色: {user_role}")
    future = executor.submit(analyze_compliance_with_maxkb, scene_description, user_role)
    result = future.result()
    logger.info(f"[API] /api/analyze-compliance 完成 | success={result.get('success')}")
    return jsonify(result)


@pipeline_bp.route("/api/generate-prompt", methods=["POST"])
def api_generate_prompt():
    """Step 3: 仅生成提示词"""
    logger.info("=" * 60)
    logger.info("[API] POST /api/generate-prompt 收到请求")
    scene_description = request.form.get("scene_description", "")
    compliance_analysis = request.form.get("compliance_analysis", "")

    if not scene_description or not compliance_analysis:
        return jsonify({"success": False, "error": "缺少必要参数"}), 400

    logger.info(f"[API] 场景描述: {len(scene_description)} 字符 | 合规分析: {len(compliance_analysis)} 字符")
    future = executor.submit(generate_edit_prompt, scene_description, compliance_analysis)
    result = future.result()
    logger.info(f"[API] /api/generate-prompt 完成 | success={result.get('success')}")
    return jsonify(result)


@pipeline_bp.route("/api/generate-image", methods=["POST"])
def api_generate_image():
    """Step 4: 仅图片编辑"""
    logger.info("=" * 60)
    logger.info("[API] POST /api/generate-image 收到请求")
    image = request.files.get("image")
    prompt = request.form.get("prompt", "")

    if not image:
        return jsonify({"success": False, "error": "未上传图片"}), 400
    if not prompt:
        return jsonify({"success": False, "error": "缺少提示词"}), 400

    image_bytes = image.read()
    if not image_bytes:
        return jsonify({"success": False, "error": "图片为空"}), 400

    image_format = detect_image_format(image.filename or "", image.content_type or "")
    logger.info(f"[API] 图片: {image.filename} ({len(image_bytes)} bytes, {image_format}) | 提示词: {prompt[:100]}...")
    future = executor.submit(generate_edited_image, image_bytes, image_format, prompt)
    result = future.result()
    logger.info(f"[API] /api/generate-image 完成 | success={result.get('success')}")

    if result.get("success"):
        # 保存生成的图片 + 缩略图
        filename = f"generated_{uuid.uuid4().hex[:8]}.png"
        rel_path = _save_with_thumbnail(filename, result["image_bytes"], subdir="generated")
        result["image_url"] = f"/images/{rel_path}"
        del result["image_bytes"]

    return jsonify(result)


@pipeline_bp.route("/api/refine-image", methods=["POST"])
def api_refine_image():
    """Step 5: 补充编辑 — 用户手动输入修正提示词，对已修改图片进行二次编辑"""
    logger.info("=" * 60)
    logger.info("[API] POST /api/refine-image 收到请求")
    image = request.files.get("image")
    prompt = request.form.get("prompt", "")
    history_id = request.form.get("history_id", "")

    if not image:
        return jsonify({"success": False, "error": "未上传图片"}), 400
    if not prompt:
        return jsonify({"success": False, "error": "缺少修正提示词"}), 400

    image_bytes = image.read()
    if not image_bytes:
        return jsonify({"success": False, "error": "图片为空"}), 400

    image_format = detect_image_format(image.filename or "", image.content_type or "")
    logger.info(f"[API] 图片: {image.filename} ({len(image_bytes)} bytes, {image_format}) | 修正提示词: {prompt[:100]}...")
    future = executor.submit(generate_edited_image, image_bytes, image_format, prompt)
    result = future.result()
    logger.info(f"[API] /api/refine-image 完成 | success={result.get('success')}")

    if result.get("success"):
        filename = f"refined_{uuid.uuid4().hex[:8]}.png"
        rel_path = _save_with_thumbnail(filename, result["image_bytes"], subdir="refined")
        result["image_url"] = f"/images/{rel_path}"
        del result["image_bytes"]

        # 更新历史记录
        if history_id:
            update_history(history_id, {
                "refine_prompt": prompt,
                "refined_image": rel_path,
                "status": "refined",
            })

    return jsonify(result)


# ------------------------------------------------------------
# 完整流水线
# ------------------------------------------------------------

@pipeline_bp.route("/api/full-pipeline", methods=["POST"])
def api_full_pipeline():
    """完整流水线：识别 → 合规分析 → 生成提示词 → 图片编辑"""
    logger.info("=" * 60)
    logger.info("[API] POST /api/full-pipeline 收到请求")
    image = request.files.get("image")
    if not image:
        return jsonify({"success": False, "error": "未上传图片"}), 400

    image_bytes = image.read()
    if not image_bytes:
        return jsonify({"success": False, "error": "图片为空"}), 400

    image_format = detect_image_format(image.filename or "", image.content_type or "")
    logger.info(f"[Pipeline] 图片: {image.filename} ({len(image_bytes)} bytes, {image_format})")

    # 保存原图
    original_filename = f"original_{uuid.uuid4().hex[:8]}.{image_format}"
    original_rel = _save_with_thumbnail(original_filename, image_bytes, subdir="original")
    original_url = f"/images/{original_rel}"

    results = {"original_url": original_url, "steps": {}}

    # Step 1: 识别
    logger.info("[Pipeline] ========== Step 1: MiMo 视觉识别 ==========")
    t1 = time.time()
    recognize_result = recognize_with_mimo(image_bytes, image_format)
    results["steps"]["recognize"] = {"time_ms": int((time.time() - t1) * 1000), **recognize_result}
    logger.info(f"[Pipeline] Step 1 完成 | 耗时: {results['steps']['recognize']['time_ms']}ms | success={recognize_result.get('success')}")

    if not recognize_result.get("success"):
        results["total_time_ms"] = int((time.time() - t1) * 1000)
        return jsonify(results)

    scene_description = recognize_result["description"]

    # Step 2: 合规分析
    logger.info("[Pipeline] ========== Step 2: MaxKB 合规分析 ==========")
    t2 = time.time()
    compliance_result = analyze_compliance_with_maxkb(scene_description)
    results["steps"]["compliance"] = {"time_ms": int((time.time() - t2) * 1000), **compliance_result}
    logger.info(f"[Pipeline] Step 2 完成 | 耗时: {results['steps']['compliance']['time_ms']}ms | success={compliance_result.get('success')}")

    if not compliance_result.get("success"):
        results["total_time_ms"] = int((time.time() - t1) * 1000)
        return jsonify(results)

    # Step 3: 生成提示词
    logger.info("[Pipeline] ========== Step 3: 生成改图提示词 ==========")
    t3 = time.time()
    prompt_result = generate_edit_prompt(scene_description, compliance_result["analysis"])
    results["steps"]["prompt"] = {"time_ms": int((time.time() - t3) * 1000), **prompt_result}
    logger.info(f"[Pipeline] Step 3 完成 | 耗时: {results['steps']['prompt']['time_ms']}ms | success={prompt_result.get('success')}")

    if not prompt_result.get("success"):
        results["total_time_ms"] = int((time.time() - t1) * 1000)
        return jsonify(results)

    # Step 4: 图片编辑
    logger.info("[Pipeline] ========== Step 4: GPT-Image 图片编辑 ==========")
    t4 = time.time()
    image_result = generate_edited_image(image_bytes, image_format, prompt_result["prompt"])
    results["steps"]["image_edit"] = {"time_ms": int((time.time() - t4) * 1000)}
    logger.info(f"[Pipeline] Step 4 完成 | 耗时: {results['steps']['image_edit']['time_ms']}ms | success={image_result.get('success')}")

    gen_rel = None
    if image_result.get("success"):
        gen_filename = f"generated_{uuid.uuid4().hex[:8]}.png"
        gen_rel = _save_with_thumbnail(gen_filename, image_result["image_bytes"], subdir="generated")
        results["steps"]["image_edit"]["success"] = True
        results["steps"]["image_edit"]["image_url"] = f"/images/{gen_rel}"
    else:
        results["steps"]["image_edit"]["success"] = False
        results["steps"]["image_edit"]["error"] = image_result.get("error")

    results["total_time_ms"] = int((time.time() - t1) * 1000)
    logger.info(f"[Pipeline] 全流程完成 | 总耗时: {results['total_time_ms']}ms")

    # 自动保存历史记录
    now = datetime.now(timezone(timedelta(hours=8)))
    record = {
        "id": uuid.uuid4().hex[:12],
        "created_at": now.isoformat(timespec="seconds"),
        "mode": "full",
        "original_image": original_rel,
        "generated_image": gen_rel,
        "scene_description": scene_description if recognize_result.get("success") else None,
        "compliance_analysis": compliance_result.get("analysis") if compliance_result.get("success") else None,
        "compliance_queries": [],
        "edit_prompt": prompt_result.get("prompt") if prompt_result.get("success") else None,
        "refine_prompt": None,
        "refined_image": None,
        "step_times": {
            "step1_ms": results["steps"].get("recognize", {}).get("time_ms"),
            "step2_ms": results["steps"].get("compliance", {}).get("time_ms"),
            "step3_ms": results["steps"].get("prompt", {}).get("time_ms"),
            "step4_ms": results["steps"].get("image_edit", {}).get("time_ms"),
        },
        "status": "completed" if results["steps"].get("image_edit", {}).get("success") else "partial",
    }
    save_history(record)

    return jsonify(results)


# ------------------------------------------------------------
# SSE 流式流水线
# ------------------------------------------------------------

@pipeline_bp.route("/api/full-pipeline-stream", methods=["POST"])
def api_full_pipeline_stream():
    """完整流水线（SSE 实时推送）：识别 → 合规分析 → 生成提示词 → 图片编辑"""
    logger.info("=" * 60)
    logger.info("[API] POST /api/full-pipeline-stream 收到请求 (SSE)")
    image = request.files.get("image")
    if not image:
        return jsonify({"success": False, "error": "未上传图片"}), 400

    image_bytes = image.read()
    if not image_bytes:
        return jsonify({"success": False, "error": "图片为空"}), 400

    image_format = detect_image_format(image.filename or "", image.content_type or "")
    logger.info(f"[SSE] 图片: {image.filename} ({len(image_bytes)} bytes, {image_format})")

    # 保存原图 + 缩略图
    original_filename = f"original_{uuid.uuid4().hex[:8]}.{image_format}"
    original_rel = _save_with_thumbnail(original_filename, image_bytes, subdir="original")
    original_url = f"/images/{original_rel}"

    # 使用场景优化专用智能体
    maxkb_base_url = settings.MAXKB_SCENE_OPTIMIZE_BASE_URL
    maxkb_api_key = settings.MAXKB_SCENE_OPTIMIZE_API_KEY

    def _stream_compliance(scene_desc: str):
        """流式合规分析：提取子问题 → 并行查询 MaxKB"""
        sub_queries = extract_sub_queries(scene_desc)
        queries = [f"以下是景区场景描述：\n{scene_desc}\n\n请根据以上场景和旅游景区相关国家标准回答：{sq}" for sq in sub_queries]
        logger.info(f"[SSE-Compliance] 开始并行查询 MaxKB | 共 {len(queries)} 个问题")

        all_sources = []

        # 并行查询，每批4个
        def _fetch_one(idx, q):
            logger.debug(f"[SSE-Compliance] 查询问题 {idx+1}: {q[:80]}...")
            answer, sources = _query_maxkb_single(q, maxkb_base_url, maxkb_api_key)
            logger.debug(f"[SSE-Compliance] 问题 {idx+1} 完成 | 回答长度: {len(answer)} 字符")
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
            "original_image": original_rel,
            "generated_image": None,
            "scene_description": None,
            "compliance_analysis": None,
            "compliance_queries": [],
            "edit_prompt": None,
            "refine_prompt": None,
            "refined_image": None,
            "step_times": {},
            "status": "partial",
        }
        hist_queries = []  # 收集子问题

        def _save_and_done():
            hist["compliance_queries"] = hist_queries
            save_history(hist)

        yield f"data: {json.dumps({'type': 'original', 'url': original_url}, ensure_ascii=False)}\n\n"

        # Step 1: 识别
        logger.info("[SSE] ========== Step 1: MiMo 视觉识别 ==========")
        t1 = time.time()
        yield f"data: {json.dumps({'type': 'step', 'step': 'recognize', 'status': 'running'}, ensure_ascii=False)}\n\n"
        recognize_result = recognize_with_mimo(image_bytes, image_format)
        step_data = {"type": "step", "step": "recognize", "time_ms": int((time.time() - t1) * 1000), **recognize_result}
        logger.info(f"[SSE] Step 1 完成 | 耗时: {step_data['time_ms']}ms | success={recognize_result.get('success')}")
        hist["step_times"]["step1_ms"] = step_data["time_ms"]
        yield f"data: {json.dumps(step_data, ensure_ascii=False)}\n\n"

        if not recognize_result.get("success"):
            _save_and_done()
            yield f"data: {json.dumps({'type': 'done', 'total_time_ms': int((time.time() - t_total) * 1000), 'history_id': hist['id']}, ensure_ascii=False)}\n\n"
            return

        scene_description = recognize_result["description"]
        hist["scene_description"] = scene_description

        # Step 2: 合规分析（流式）
        logger.info("[SSE] ========== Step 2: MaxKB 合规分析 ==========")
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
        logger.info(f"[SSE] Step 2 完成 | 耗时: {t2_ms}ms | 回答长度: {len(full_answer)} 字符 | 来源: {len(final_sources)} 个")

        if not full_answer:
            yield f"data: {json.dumps({'type': 'step', 'step': 'compliance', 'time_ms': t2_ms, 'success': False, 'error': 'MaxKB 未返回有效回答'}, ensure_ascii=False)}\n\n"
            _save_and_done()
            yield f"data: {json.dumps({'type': 'done', 'total_time_ms': int((time.time() - t_total) * 1000), 'history_id': hist['id']}, ensure_ascii=False)}\n\n"
            return

        hist["compliance_analysis"] = full_answer
        yield f"data: {json.dumps({'type': 'step', 'step': 'compliance', 'time_ms': t2_ms, 'success': True, 'analysis': full_answer, 'sources': final_sources}, ensure_ascii=False)}\n\n"

        # Step 3: 生成提示词
        logger.info("[SSE] ========== Step 3: 生成改图提示词 ==========")
        t3 = time.time()
        yield f"data: {json.dumps({'type': 'step', 'step': 'prompt', 'status': 'running'}, ensure_ascii=False)}\n\n"
        prompt_result = generate_edit_prompt(scene_description, full_answer)
        step_data = {"type": "step", "step": "prompt", "time_ms": int((time.time() - t3) * 1000), **prompt_result}
        logger.info(f"[SSE] Step 3 完成 | 耗时: {step_data['time_ms']}ms | success={prompt_result.get('success')}")
        hist["step_times"]["step3_ms"] = step_data["time_ms"]
        yield f"data: {json.dumps(step_data, ensure_ascii=False)}\n\n"

        if not prompt_result.get("success"):
            _save_and_done()
            yield f"data: {json.dumps({'type': 'done', 'total_time_ms': int((time.time() - t_total) * 1000), 'history_id': hist['id']}, ensure_ascii=False)}\n\n"
            return

        hist["edit_prompt"] = prompt_result.get("prompt")

        # Step 4: 图片编辑
        logger.info("[SSE] ========== Step 4: GPT-Image 图片编辑 ==========")
        t4 = time.time()
        yield f"data: {json.dumps({'type': 'step', 'step': 'image_edit', 'status': 'running'}, ensure_ascii=False)}\n\n"
        image_result = generate_edited_image(image_bytes, image_format, prompt_result["prompt"])
        step_data = {"type": "step", "step": "image_edit", "time_ms": int((time.time() - t4) * 1000)}
        logger.info(f"[SSE] Step 4 完成 | 耗时: {step_data['time_ms']}ms | success={image_result.get('success')}")
        hist["step_times"]["step4_ms"] = step_data["time_ms"]
        if image_result.get("success"):
            gen_filename = f"generated_{uuid.uuid4().hex[:8]}.png"
            gen_rel = _save_with_thumbnail(gen_filename, image_result["image_bytes"], subdir="generated")
            step_data["success"] = True
            step_data["image_url"] = f"/images/{gen_rel}"
            hist["generated_image"] = gen_rel
            hist["status"] = "completed"
        else:
            step_data["success"] = False
            step_data["error"] = image_result.get("error")
        yield f"data: {json.dumps(step_data, ensure_ascii=False)}\n\n"

        _save_and_done()
        total_ms = int((time.time() - t_total) * 1000)
        logger.info(f"[SSE] 全流程完成 | 总耗时: {total_ms}ms")
        yield f"data: {json.dumps({'type': 'done', 'total_time_ms': total_ms, 'history_id': hist['id']}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
