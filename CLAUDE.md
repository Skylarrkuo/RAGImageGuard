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

## 核心业务流程

```
上传图片 → [Step 1] MiMo 视觉识别 → [Step 2] MaxKB 合规分析 → [Step 3] 生成提示词 → [Step 4] GPT-image 改图
```

1. **场景识别**：调用 MiMo 2.5 视觉模型，识别景区图片中的场景类型、标识标牌、基础设施、安全设施等
2. **合规分析**：从场景描述提取子问题，并行查询 MaxKB 知识库获取国家标准合规判断
3. **提示词生成**：基于合规分析结果，AI 生成图片编辑提示词（保持构图，只修改不合规部分）
4. **智能改图**：调用 GPT-image-2 API 生成修复后的图片

## 目录结构

```
RAG_PNG/
├── app.py                  # Flask 后端主文件（所有 API 端点）
├── config/
│   └── settings.py         # 环境变量配置加载
├── frontend/
│   ├── src/
│   │   ├── api/index.js    # API 调用封装
│   │   ├── App.vue         # 主应用（页面路由）
│   │   └── components/
│   │       ├── UploadPage.vue      # 上传页面
│   │       ├── Workspace.vue       # 工作台（流程控制）
│   │       ├── PipelineSidebar.vue # 侧边栏步骤节点
│   │       ├── ContentPanel.vue    # 内容展示面板
│   │       └── SummaryBar.vue      # 耗时统计栏
│   └── package.json
├── data/uploads/images/    # 上传/生成的图片存储
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
| `/api/full-pipeline` | POST | 完整流水线（同步） |
| `/api/full-pipeline-stream` | POST | 完整流水线（SSE 实时推送） |
| `/images/<filename>` | GET | 获取上传/生成的图片 |

## 环境变量

必须在 `.env` 文件中配置（参考 `.env.example`）：

```bash
# MiMo 视觉/LLM
MIMO_API_KEY=xxx
MIMO_API_BASE=https://xxx

# MaxKB 知识库
MAXKB_STANDARD_BASE_URL=xxx
MAXKB_STANDARD_API_KEY=xxx
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

### 后端 (app.py)

- 使用 `ThreadPoolExecutor(max_workers=4)` 处理并发请求
- MaxKB 合规分析采用 **4 路并行查询**：先用 MiMo 提取 4-5 个子问题（覆盖标识、安全、无障碍、消防、卫生等维度），再并行查询知识库
- SSE 流式端点 (`/api-full-pipeline-stream`) 支持实时推送每个步骤进度
- 图片格式自动检测：支持 jpg/png/webp/gif
- 生成的图片保存在 `data/uploads/images/` 目录

### 前端 (Vue 3)

- 两页结构：`UploadPage`（上传）→ `Workspace`（工作台）
- 支持 3 种运行模式：`full`（完整流水线）、`step1`（仅识别）、`step2`（仅合规分析）
- SSE 流式解析：`consumeSSEStream()` 函数处理服务端推送事件
- 步骤重试：每个步骤失败后可单独重试，无需重新开始
- Markdown 渲染：合规分析结果使用 `marked` 库渲染

## 开发注意事项

1. **API 调用超时**：MiMo 识别 120s，MaxKB 查询 300s，GPT-image 编辑 300s
2. **代理设置**：OpenAI 客户端显式禁用代理 (`proxy=None`)
3. **并发控制**：MaxKB 并行查询限制为 4 路
4. **文件命名**：上传图片使用 `original_{uuid}.{ext}`，生成图片使用 `generated_{uuid}.png`
5. **前端开发**：API 基础路径为空字符串（同源），Vite 开发服务器代理到后端 8001 端口
