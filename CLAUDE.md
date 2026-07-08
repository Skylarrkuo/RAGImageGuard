# CLAUDE.md — RAG_PNG 项目指南

## 项目概述

**景区图片合规检查 + AI 改图系统**

基于 RAG（检索增强生成）的旅游景区图片合规检查系统，通过 AI 视觉识别景区图片内容，检索国家标准知识库进行合规分析，并自动修复不合规内容。

## 技术栈

| 层 | 技术 |
|---|------|
| **后端** | Flask 3.x + Python 3.11 |
| **前端** | Vue 3.4 + Vite 5.x |
| **AI 视觉** | MiMo 2.5（场景识别 + 提示词生成） |
| **RAG 知识库** | MaxKB（国家标准检索） |
| **图片编辑** | OpenAI GPT-image-2 |
| **图片处理** | Pillow（尺寸检测 + 缩略图生成） |
| **安全** | CORS 白名单 + 上传大小限制 + API Key 认证 + 线程安全锁 |

## 核心业务流程

```
上传图片 → [Step 1] MiMo 视觉识别 → [Step 2] MaxKB 合规分析 → [Step 3] 生成提示词 → [Step 4] GPT-image 改图 → [Step 5] 补充编辑（可选）
```

1. **场景识别**：调用 MiMo 2.5 视觉模型，按 11 个维度全面识别景区图片（场景类型、标识标牌、基础设施、安全设施、无障碍设施、建筑装饰、车辆与交通、人员、植物与自然、杂物与遮挡物、画面边缘与其他），max_tokens=4000
2. **合规分析**：从场景描述提取 4-5 个子问题（双 prompt 策略 + 3 次重试），携带完整场景描述并行查询 MaxKB 知识库获取国家标准合规判断
3. **提示词生成**：基于完整合规分析结果（不截断），AI 生成图片编辑提示词，自动包含移除无关路人的指令，max_tokens=10000
4. **智能改图**：自动检测原图宽高比，选择最接近的 GPT-image-2 尺寸（竖屏→1024x1536，横屏→1536x1024，方形→1024x1024）
5. **补充编辑**（可选）：用户可手动输入修正提示词进行二次精修，也可点击「结束」跳过此步直接完成流程。结果保存到历史记录

## 目录结构

```
RAG_PNG/
├── app.py                  # Flask 启动入口（应用工厂 create_app()，含安全中间件）
├── config/
│   └── settings.py         # 环境变量配置加载
├── core/
│   ├── logging.py          # 全局日志配置 + logger 导出
│   └── utils.py            # 通用工具（格式检测、MIME 映射、尺寸计算、缩略图生成）
├── services/
│   ├── mimo.py             # Step 1: MiMo 视觉识别（11 维度全面描述）
│   ├── maxkb.py            # Step 2: MaxKB 合规分析（子问题提取 + 重试 + 并行查询）
│   ├── prompt_gen.py       # Step 3: 改图提示词生成（完整内容、移除路人）
│   ├── image_edit.py       # Step 4: GPT-Image 图片编辑（自动比例检测）
│   └── history.py          # 历史记录 JSON 存储（save + update）
├── routes/
│   ├── __init__.py         # Blueprint 注册中心（register_all_blueprints）
│   ├── pipeline.py         # 流水线路由（5 步流程、SSE 流式、补充编辑、结束流程、缩略图生成）
│   ├── history.py          # 历史记录 CRUD 路由
│   └── system.py           # 系统路由（配置检查、图片服务，支持子目录路径）
├── frontend/
│   └── src/
│       ├── api/index.js    # API 调用封装（含 refineImage、completeFlow）
│       ├── App.vue         # 主应用（上传 / 工作台 / 历史 三页切换）
│       └── components/
│           ├── UploadPage.vue      # 上传页面
│           ├── Workspace.vue       # 工作台（5 步流程控制）
│           ├── PipelineSidebar.vue # 侧边栏步骤节点
│           ├── ContentPanel.vue    # 内容展示 + 补充编辑输入
│           ├── SummaryBar.vue      # 耗时统计栏
│           └── HistoryPage.vue     # 历史记录列表 + 详情对比
├── data/
│   ├── history.json        # 历史记录文件
│   └── uploads/images/     # 图片存储（按类别分目录）
│       ├── original/       # 上传的原始图片
│       ├── generated/      # Step 4 生成的图片
│       ├── refined/        # Step 5 补充编辑的图片
│       └── thumb/          # 缩略图（长边 400px，JPEG）
├── .env                    # 环境变量（不提交）
├── .env.example            # 环境变量模板
└── requirements.txt        # Python 依赖
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/config-check` | GET | 检查配置是否完整 |
| `/api/recognize` | POST | Step 1: 图片识别 |
| `/api/analyze-compliance` | POST | Step 2: 合规分析 |
| `/api/generate-prompt` | POST | Step 3: 生成编辑提示词 |
| `/api/generate-image` | POST | Step 4: AI 改图 |
| `/api/refine-image` | POST | Step 5: 补充编辑（图片 + 提示词 + history_id） |
| `/api/complete-flow` | POST | 结束流程（跳过 Step 5，标记完成） |
| `/api/full-pipeline` | POST | 完整流水线（同步） |
| `/api/full-pipeline-stream` | POST | 完整流水线（SSE 实时推送） |
| `/api/history` | GET | 历史记录列表 |
| `/api/history/<record_id>` | GET | 历史记录详情 |
| `/api/history/<record_id>` | DELETE | 删除历史记录 |
| `/images/<path:filepath>` | GET | 获取图片（支持子目录，如 `original/abc.jpg`） |

## 环境变量

必须在 `.env` 文件中配置（参考 `.env.example`）：

```bash
# ---- 安全配置 ----
API_KEY=                          # API 访问密钥（留空=不启用认证，生产环境务必设置）
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8001  # CORS 允许的来源（逗号分隔）
MAX_UPLOAD_MB=20                  # 上传文件大小限制（MB）

# MiMo 视觉/LLM
MIMO_API_KEY=xxx
MIMO_API_BASE=https://xxx

# MaxKB 场景优化专用智能体
MAXKB_SCENE_OPTIMIZE_BASE_URL=xxx
MAXKB_SCENE_OPTIMIZE_API_KEY=xxx

# OpenAI 图片编辑
OPENAI_API_KEY=xxx
OPENAI_API_BASE=https://xxx
```

## 快速启动

```bash
# 后端
conda activate rag-png
python app.py  # 运行在 http://localhost:8001

# 前端（另开终端）
cd frontend
npm install
npm run dev   # 运行在 http://localhost:5173
```

## 关键实现细节

### 后端架构

- **分层结构**：`core/`（基础设施）→ `services/`（业务逻辑）→ `routes/`（HTTP 端点）→ `app.py`（入口）
- **应用工厂**：`create_app()` 函数便于测试和扩展
- **Blueprint 模块化**：`pipeline_bp`、`history_bp`、`system_bp` 分别注册
- 使用 `ThreadPoolExecutor(max_workers=4)` 处理并发请求（定义在 `routes/pipeline.py`）
- MaxKB 合规分析采用 **4 路并行查询**：先用 MiMo 提取 4-5 个子问题（覆盖标识、安全、无障碍、消防、卫生等维度），再并行查询知识库
- 子问题提取采用 **双 prompt 策略**：详细版 → 精简版 → 兜底问题，`_call_mimo()` 带 3 次重试
- SSE 流式端点 (`/api/full-pipeline-stream`) 支持实时推送每个步骤进度，`done` 事件携带 `history_id`
- 图片格式自动检测：支持 jpg/png/webp/gif
- **图片存储按类别分目录**：`original/`、`generated/`、`refined/`、`thumb/`
- **缩略图自动生成**：`_save_with_thumbnail()` 保存原图时同步生成长边 400px 的 JPEG 缩略图
- **图片比例自适应**：`pick_gpt_image_size()` 根据原图宽高比选择 GPT-image-2 最接近的尺寸
- 历史记录存储在 `data/history.json`，支持 `save_history()` 和 `update_history()` 两种操作
- **流程结束**：`/api/complete-flow` 端点处理用户跳过 Step 5 的场景，标记 `status: "completed"` + `step5_skipped: true`
- **Step 5 计时**：`api_refine_image` 记录 `step5_ms` 耗时到历史记录

### 前端 (Vue 3)

- 三页结构：`UploadPage`（上传）→ `Workspace`（工作台）→ `HistoryPage`（历史记录）
- 工作台支持 **5 步流程**：识别 → 合规分析 → 提示词生成 → 图片编辑 → 补充编辑
- 支持 3 种运行模式：`full`（完整流水线）、`step1`（仅识别）、`step2`（仅合规分析）
- SSE 流式解析：`consumeSSEStream()` 函数处理服务端推送事件
- 步骤重试：每个步骤失败后可单独重试，无需重新开始（含 Step 5）
- Markdown 渲染：合规分析结果使用 `marked` 库渲染
- **历史记录**：列表页加载缩略图（`thumbUrl()` 函数），详情页显示原图/生成图对比滑块，支持精修图对比和 Step 5 信息展示
- **补充编辑**：ContentPanel 中 Step 5 输入区域（缩略图预览 + 文本框 + 按钮），提供「开始修正」和「结束」两个操作
- **图片预览**：Step 4/5 生成图片默认显示缩略图（240px），点击打开全屏 Lightbox 进行修改前后对比（拖拽滑块），支持 Escape 关闭
- 图片居中显示，max-width 900px

## 开发注意事项

1. **API 调用超时**：MiMo 识别 120s，MaxKB 查询 300s，GPT-image 编辑 300s
2. **代理设置**：OpenAI 客户端显式禁用代理 (`proxy=None`)，环境变量操作通过 `threading.Lock` 保证线程安全
3. **并发控制**：MaxKB 并行查询限制为 4 路
4. **文件命名**：上传图片 `original/{uuid}.{ext}`，生成图片 `generated/{uuid}.png`，精修图片 `refined/{uuid}.png`，缩略图 `thumb/thumb_{uuid}.jpg`
5. **前端开发**：API 基础路径为空字符串（同源），Vite 开发服务器代理到后端 8001 端口
6. **图片安全**：`/images/<path:filepath>` 路由含目录遍历防护（`resolve()` + 前缀校验）
7. **Pillow 依赖**：`requirements.txt` 中 `Pillow>=10.0.0`，用于图片尺寸检测和缩略图生成
8. **CORS 安全**：`ALLOWED_ORIGINS` 环境变量控制允许的来源，默认仅允许 localhost 开发地址，生产环境需配置实际域名
9. **上传限制**：`MAX_CONTENT_LENGTH` 由 `MAX_UPLOAD_MB` 控制（默认 20MB），超限自动返回 413
10. **API 认证**：配置 `API_KEY` 后，所有 `/api/*` 请求需携带 `X-API-Key` 头（`/api/config-check` 和 `/images/*` 自动放行）；留空则不启用认证
11. **线程安全**：`services/image_edit.py` 中代理环境变量的清除/恢复通过全局 `_env_lock` 保护，避免并发请求互相污染
