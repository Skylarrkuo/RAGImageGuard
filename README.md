# RAG_PNG — 景区图片合规检查 + AI 改图

基于 RAG（检索增强生成）的旅游景区图片合规检查系统，支持 AI 智能改图。

## 功能

1. **图片识别** — 调用 MiMo 2.5 视觉模型识别景区图片内容
2. **合规分析** — 通过 MaxKB 知识库检索国家标准进行合规判断
3. **提示词生成** — AI 生成图片编辑提示词
4. **智能改图** — 调用 GPT-image API 自动修复不合规内容

## 项目结构

```
RAG_PNG/
├── app.py                  # Flask 启动入口（应用工厂 create_app()）
├── config/
│   └── settings.py         # 环境变量配置加载
├── core/
│   ├── logging.py          # 全局日志配置
│   └── utils.py            # 通用工具函数
├── services/
│   ├── mimo.py             # Step 1: MiMo 视觉识别
│   ├── maxkb.py            # Step 2: MaxKB 合规分析
│   ├── prompt_gen.py       # Step 3: 提示词生成
│   ├── image_edit.py       # Step 4: GPT-Image 图片编辑
│   └── history.py          # 历史记录存储
├── routes/
│   ├── pipeline.py         # 流水线路由（识别、合规、改图、SSE）
│   ├── history.py          # 历史记录 CRUD
│   └── system.py           # 配置检查、图片服务
├── frontend/               # Vue 3 前端
└── data/uploads/images/    # 上传/生成的图片
```

## 快速开始

### 环境准备

```bash
conda create -n rag-png python=3.11 -y
conda activate rag-png
pip install -r requirements.txt
```

### 配置

复制 `.env.example` 为 `.env`，填入 API Key：

```bash
cp .env.example .env
```

### 启动后端

```bash
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

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/config-check` | GET | 检查配置 |
| `/api/recognize` | POST | 图片识别 |
| `/api/analyze-compliance` | POST | 合规分析 |
| `/api/generate-prompt` | POST | 生成编辑提示词 |
| `/api/generate-image` | POST | AI 改图 |
| `/api/full-pipeline` | POST | 完整流水线 |
| `/api/full-pipeline-stream` | POST | 完整流水线（SSE） |
| `/api/history` | GET | 历史记录列表 |
| `/images/<filename>` | GET | 获取图片 |

## 技术栈

- **后端**: Flask + OpenAI / MiMo / MaxKB API
- **前端**: Vue 3 + Vite
- **知识库**: MaxKB (RAG)