# RAG_PNG — 景区图片合规检查 + AI 改图

基于 RAG（检索增强生成）的旅游景区图片合规检查系统，支持 AI 智能改图。

## 功能

1. **图片识别** — 调用 MiMo 2.5 视觉模型识别景区图片内容
2. **合规分析** — 通过 MaxKB 知识库检索国家标准进行合规判断
3. **提示词生成** — AI 生成图片编辑提示词
4. **智能改图** — 调用 GPT-image API 自动修复不合规内容

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

## 技术栈

- **后端**: Flask + OpenAI / MiMo / MaxKB API
- **前端**: Vue 3 + Vite
- **知识库**: MaxKB (RAG)