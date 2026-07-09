# RAG_PNG — 景区图片合规检查 + AI 改图

基于 RAG（检索增强生成）的旅游景区图片合规检查系统，通过 AI 视觉识别景区图片内容，检索国家标准知识库进行合规分析，并自动修复不合规内容。

## 功能

1. **图片识别** — MiMo 2.5 视觉模型全面识别景区图片（11 个维度：场景、标识、设施、安全、无障碍、建筑、交通、人员、植物、杂物、边缘）
2. **合规分析** — 从场景描述提取子问题，并行查询 MaxKB 知识库获取国家标准合规判断
3. **提示词生成** — 基于完整合规分析结果，AI 生成图片编辑提示词（自动移除无关路人）
4. **智能改图** — GPT-image-2 自动检测图片比例，生成对应尺寸的修复图片
5. **补充编辑**（可选）— 用户可手动输入修正提示词进行二次精修，也可点击「结束」跳过直接完成流程

## 项目结构

```
RAG_PNG/
├── app.py                  # Flask 启动入口（应用工厂 + 全局异常处理）
├── config/
│   └── settings.py         # 环境变量配置 + UPLOAD_DIR 共享常量
├── core/
│   ├── executor.py         # 共享线程池（全局复用）
│   ├── logging.py          # 全局日志配置
│   └── utils.py            # 通用工具（格式检测、尺寸计算、缩略图生成）
├── services/
│   ├── mimo.py             # Step 1: MiMo 视觉识别
│   ├── maxkb.py            # Step 2: MaxKB 合规分析（子问题提取 + 重试 + 并行查询）
│   ├── prompt_gen.py       # Step 3: 改图提示词生成
│   ├── image_edit.py       # Step 4: GPT-Image 图片编辑（自动比例检测）
│   └── history.py          # 历史记录 SQLite 存储（CRUD + SQL 搜索 + 懒迁移）
├── routes/
│   ├── __init__.py         # Blueprint 注册中心
│   ├── pipeline.py         # 流水线路由（5 步流程、SSE 流式、补充编辑、结束流程）
│   ├── history.py          # 历史记录 CRUD
│   └── system.py           # 配置检查、图片服务（支持子目录）
├── frontend/
│   └── src/
│       ├── api/index.js    # API 调用封装（统一拦截器 + completeFlow）
│       ├── App.vue         # 主应用（上传 / 工作台 / 历史 三页切换）
│       ├── composables/
│       │   ├── useMarkdown.js       # Markdown 渲染
│       │   └── useCompareSlider.js  # 图片对比滑块拖拽逻辑
│       └── components/
│           ├── UploadPage.vue      # 上传页面
│           ├── Workspace.vue       # 工作台（5 步流程控制）
│           ├── PipelineSidebar.vue # 侧边栏步骤节点
│           ├── ContentPanel.vue    # 内容展示 + 补充编辑输入
│           ├── SummaryBar.vue      # 耗时统计栏
│           ├── HistoryPage.vue     # 历史记录列表 + 详情对比
│           └── AppModal.vue        # 自定义 Modal 组件（prompt/confirm）
├── data/
│   ├── history.db          # 历史记录 SQLite 数据库
│   └── uploads/images/     # 图片存储（按类别分目录）
│       ├── original/       # 上传的原始图片
│       ├── generated/      # Step 4 生成的图片
│       ├── refined/        # Step 5 补充编辑的图片
│       └── thumb/          # 缩略图（长边 400px）
├── .env                    # 环境变量（不提交）
├── .env.example            # 环境变量模板
├── requirements.txt        # Python 依赖
├── pytest.ini              # pytest 配置
└── tests/
    ├── conftest.py         # 测试夹具（Flask 应用、测试客户端、示例图片）
    ├── test_utils.py       # 工具函数测试
    ├── test_history.py     # 历史记录测试
    └── test_routes.py      # API 路由测试
```

## 快速开始

### 环境准备

> **必须使用 conda 虚拟环境 `rag-png`**（Python 3.11）

```bash
# 创建环境（仅首次）
conda create -n rag-png python=3.11 -y

# 激活环境（每次开发/运行/测试前必须执行）
conda activate rag-png

# 安装依赖
pip install -r requirements.txt
```

### 配置

复制 `.env.example` 为 `.env`，填入 API Key：

```bash
cp .env.example .env
```

**安全相关配置**（可选，生产环境建议设置）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `API_KEY` | 空（不启用） | API 访问密钥，设置后请求需携带 `X-API-Key` 头 |
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://localhost:8001` | CORS 允许的来源（逗号分隔） |
| `MAX_UPLOAD_MB` | `20` | 上传文件大小限制（MB） |
| `OPENAI_MODEL_NAME` | `gpt-image-2` | 图片编辑使用的模型 |

**超时配置**（可选，单位秒，留空使用默认值）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TIMEOUT_RECOGNIZE` | `130` | MiMo 识别超时 |
| `TIMEOUT_COMPLIANCE` | `310` | MaxKB 合规分析超时 |
| `TIMEOUT_PROMPT` | `130` | 提示词生成超时 |
| `TIMEOUT_IMAGE_EDIT` | `310` | GPT-image 编辑超时 |
| `TIMEOUT_HEARTBEAT` | `30` | SSE 心跳间隔 |

### 启动后端

```bash
conda activate rag-png
python app.py
```

后端运行在 `http://localhost:8001`

### 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 `http://localhost:5173`

### 运行测试

```bash
conda activate rag-png
pytest tests/ -v
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/config-check` | GET | 检查配置是否完整 |
| `/api/recognize` | POST | Step 1: 图片识别 |
| `/api/analyze-compliance` | POST | Step 2: 合规分析 |
| `/api/generate-prompt` | POST | Step 3: 生成编辑提示词 |
| `/api/generate-image` | POST | Step 4: AI 改图 |
| `/api/refine-image` | POST | Step 5: 补充编辑 |
| `/api/complete-flow` | POST | 结束流程（跳过 Step 5） |
| `/api/full-pipeline` | POST | 完整流水线（同步） |
| `/api/full-pipeline-stream` | POST | 完整流水线（SSE 实时推送） |
| `/api/history` | GET | 历史记录列表 |
| `/api/history/<record_id>` | GET | 历史记录详情 |
| `/api/history/<record_id>` | DELETE | 删除历史记录 |
| `/images/<path>` | GET | 获取图片（支持子目录） |

## 技术栈

- **后端**: Flask 3.x + Python 3.11
- **前端**: Vue 3.4 + Vite 5.x
- **AI 视觉**: MiMo 2.5（场景识别 + 提示词生成）
- **RAG 知识库**: MaxKB（国家标准检索）
- **图片编辑**: OpenAI GPT-image-2
- **图片处理**: Pillow（尺寸检测 + 缩略图生成）
- **前端**: API 统一拦截器（`request()` 自动检查 HTTP 状态码，非 2xx 抛出异常）
- **安全**: CORS 白名单 + 上传大小限制 + API Key 认证 + 线程安全锁 + 全局异常处理
- **测试**: pytest 44 个测试用例（工具函数 + 历史记录 + API 路由），必须在 `rag-png` conda 环境下运行