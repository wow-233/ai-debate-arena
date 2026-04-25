# AI Debate Arena

多智能体 AI 辩论系统 - 支持三方专业角色（投资人、技术专家、法务合规）对任意主题进行结构化辩论。

## 功能特性

- 🤖 **三方辩论**: 投资人、技术专家、法务合规多轮交叉辩论
- 📝 **Obsidian 集成**: 辩论报告自动保存到 Obsidian Vault
- 🔗 **上下文感知**: 读取 Obsidian 笔记作为辩论背景资料
- ⚡ **实时流输出**: SSE 流式推送辩论进度
- 🎯 **智能模型路由**: 按任务复杂度自动选择模型

## 快速开始

### 方式一：直接运行 EXE（推荐）

下载 `dist/AI-Debate-Arena/AI-Debate-Arena.exe`，双击运行即可。

### 方式二：从源码运行

```bash
git clone https://github.com/yourusername/ai-debate-arena.git
cd ai-debate-arena
```

### 2. 配置环境

```bash
cd backend
cp .env.example .env
# 编辑 .env 填入你的配置
```

配置项说明:

| 变量 | 说明 | 示例 |
|------|------|------|
| `OPENAI_API_KEY` | API 密钥 | `sk-xxx` |
| `OPENAI_BASE_URL` | API 地址 | `https://api.deepseek.com` |
| `OBSIDIAN_VAULT_PATH` | Obsidian 库路径 | `D:\Obsidian\Vault` |

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 启动服务

```bash
python -m app.main
```

或使用 uvicorn:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问 API

- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## API 使用

### 开始辩论

```bash
curl -X POST http://localhost:8000/api/debate/start \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "电商平台商业模式可行性",
    "rounds": 3
  }'
```

### 订阅辩论进度 (SSE)

```bash
curl -N http://localhost:8000/api/debate/{debate_id}/stream
```

### 获取辩论结果

```bash
curl http://localhost:8000/api/debate/{debate_id}
```

### 列出 Obsidian 笔记

```bash
curl http://localhost:8000/api/obsidian/notes
```

### 读取 Obsidian 笔记

```bash
curl http://localhost:8000/api/obsidian/notes/20%20-%20Context/Business/plan.md
```

## 项目结构

```
ai-debate-arena/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── debate.py        # API 路由
│   │   ├── core/
│   │   │   ├── config.py        # 配置管理
│   │   │   ├── llm.py           # LLM 调用
│   │   │   └── router.py        # 模型路由
│   │   ├── models/
│   │   │   ├── debate.py       # 数据模型
│   │   │   └── agent.py        # 角色定义
│   │   ├── services/
│   │   │   ├── debate_engine.py # 辩论引擎
│   │   │   ├── obsidian_writer.py # 写入服务
│   │   │   └── obsidian_reader.py # 读取服务
│   │   └── main.py             # 入口
│   ├── requirements.txt
│   └── .env.example
├── SPEC.md                    # 项目规格
└── README.md
```

## 辩论流程

```
1. 题目设定 → 用户输入主题/选择上下文
2. 并行分析 → 投资人在、技术专家、法务合规三方同时分析
3. 串行辩论 → N 轮交叉辩论
4. 最终总结 → AI 整合各方观点
5. 保存报告 → 自动写入 Obsidian
```

## Obsidian 集成

辩论报告保存到 `10 - Debates/{年-月}/` 目录，包含完整 frontmatter:

```yaml
---
title: "AI辩论: 电商平台商业模式"
date: 2026-04-25
type: debate_report
tags: [debate, business, ai]
participants: [investor, tech_expert, legal]
---
```

## License

MIT

---

## exe 文件说明

打包后的 exe 位于 `dist/AI-Debate-Arena/` 目录：

```
dist/AI-Debate-Arena/
├── AI-Debate-Arena.exe      # 主程序
├── _internal/              # 依赖库
└── .env.example            # 示例配置
```

运行前先创建 `.env` 文件，配置 `OPENAI_API_KEY` 等参数。