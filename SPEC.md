# AI Debate Arena - 项目规格说明书

## 1. 项目概述

### 项目名称
**AI Debate Arena** - 智能辩论系统

### 核心定位
多智能体 AI 辩论系统，支持三方专业角色（投资人、技术专家、法务合规）对任意主题进行结构化辩论，辩论报告自动保存至 Obsidian 知识库，并可读取 Obsidian 笔记作为辩论上下文。

### 目标用户
- 创业者 - 检验商业计划书的完整性
- 投资人 - 获取第三方分析视角
- 研究者 - 结构化分析复杂话题

---

## 2. 功能规格

### 2.1 核心功能

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 三方辩论 | 投资人、技术专家、法务合规三轮观点 | P0 |
| 并行分析 | 初始阶段三方并行分析主题 | P0 |
| 串行辩论 | 多轮交叉辩论，每轮回应前序观点 | P0 |
| 总结报告 | 整合所有观点，输出结构化报告 | P0 |
| Obsidian 写入 | 辩论报告保存为 Markdown 到 Vault | P0 |
| Obsidian 读取 | 读取 Vault 笔记作为辩论上下文 | P0 |
| SSE 流式 | 实时推送辩论进度到前端 | P1 |
| 模型路由 | 按复杂度自动选择模型 | P2 |

### 2.2 角色定义

#### 投资人 (Investor)
- **关注点**：商业模式、市场规模、投资回报、竞争优势
- **分析维度**：市场潜力、商业可行性、财务预测、风险评估

#### 技术专家 (Tech Expert)
- **关注点**：技术实现、技术壁垒、工程可行性、技术选型
- **分析维度**：技术架构、实现难度、性能优化、安全性

#### 法务合规 (Legal/Compliance)
- **关注点**：数据合规、知识产权、法律风险、监管要求
- **分析维度**：合规性审查、合同风险、知识产权、数据保护

### 2.3 辩论流程

```
┌─────────────────────────────────────────────────────────────┐
│                     1. 题目设定                           │
│              (用户输入主题/上传BP/选择上下文)              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  2. 并行初始分析                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ 投资人   │  │ 技术专家 │  │ 法务合规 │            │
│  │ 并行分析 │  │ 并行分析 │  │ 并行分析 │            │
│  └──────────┘  └──────────┘  └──────────┘            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   3. 串行辩论 (N轮)                       │
│  Round 1: 投资人 → 技术专家 → 法务合规                  │
│  Round 2: 投资人 ← 技术专家 ← 法务合规                  │
│  Round N: ...                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    4. 最终总结                             │
│            (整合观点，输出结构化报告)                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   5. 保存到 Obsidian                      │
│         (生成 Markdown，保存到 Vault 目录)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 技术架构

### 3.1 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI | 高性能异步 Web 框架 |
| LLM 调用 | LiteLLM | 统一 OpenAI 兼容接口 |
| 流式输出 | SSE | 服务器发送事件 |
| 数据验证 | Pydantic | 请求/响应模型 |
| Markdown | python-frontmatter | Frontmatter 解析 |
| 配置文件 | python-dotenv | 环境变量管理 |

### 3.2 项目结构

```
ai-debate-arena/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── debate.py        # 辩论 API 路由
│   │   ├── core/
│   │   │   ├── config.py        # 配置管理
│   │   │   ├── llm.py           # LLM 调用封装
│   │   │   └── router.py        # 模型路由器
│   │   ├── models/
│   │   │   ├── debate.py       # 辩论数据模型
│   │   │   └── agent.py        # 角色定义
│   │   ├── services/
│   │   │   ├── debate_engine.py # 辩论引擎
│   │   │   ├── obsidian_writer.py # Obsidian 写入
│   │   │   └── obsidian_reader.py # Obsidian 读取
│   │   └── main.py             # FastAPI 入口
│   ├── requirements.txt
│   └── .env.example
├── docs/
│   ├── DEBATE_FLOW.md        # 辩论流程文档
│   └── API_REFERENCE.md       # API 文档
└── README.md
```

---

## 4. Obsidian 集成规格

### 4.1 Vault 目录结构

```
Obsidian Vault/
├── 99 - Meta/                    # 元信息
│   ├── Templates/                 # 辩论模板
│   │   └── debate-report.md
│   └── Hubs/                    # 主题枢纽
│       ├── Tech-Hub.md
│       ├── Legal-Hub.md
│       └── Business-Hub.md
├── 10 - Debates/                # 辩论记录
│   ├── 2026-04/
│   │   ├── debate-2026-04-25-xxx.md
│   │   └── debate-2026-04-26-yyy.md
│   └── 2026-05/
└── 20 - Context/                # 上下文资料
    ├── Business-Plans/
    ├── Tech-Analysis/
    └── Legal-Cases/
```

### 4.2 Frontmatter 设计

```yaml
---
title: "AI辩论: 电商平台商业模式"
date: 2026-04-25
last_updated: 2026-04-25
type: debate_report
tags: [debate, business, ai]
participants: [investor, tech_expert, legal]
topic: "电商平台商业模式可行性"
related: [[Business-Hub], [Tech-Hub]]
round: 3
status: completed
---
```

### 4.3 辩论报告结构

```markdown
# AI辩论: 电商平台商业模式

**日期**: 2026-04-25  
**主题**: 电商平台商业模式可行性  
**参与角色**: 投资人、技术专家、法务合规  

## 📊 执行摘要

[AI 生成的总结]

## 👔 投资人观点

### 初始分析
[分析内容]

### 辩论要点
- 观点1: ...
- 观点2: ...

## 🔧 技术专家观点

### 初始分析
[分析内容]

### 辩论要点
- 观点1: ...
- 观点2: ...

## ⚖️ 法务合规观点

### 初始分析
[分析内容]

### 辩论要点
- 观点1: ...
- 观点2: ...

## 🎯 最终结论

[综合各方观点的结论]

## 📚 参考资料

- [[相关笔记1]]
- [[相关笔记2]]
```

---

## 5. API 设计

### 5.1 端点定义

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/debate/start | 开始新辩论 |
| GET | /api/debate/{id}/stream | SSE 流式辩论过程 |
| GET | /api/debate/{id} | 获取辩论结果 |
| GET | /api/obsidian/notes | 列出 Vault 笔记 |
| GET | /api/obsidian/notes/{path} | 读取笔记内容 |

### 5.2 请求/响应模型

```python
# 开始辩论请求
class DebateStartRequest:
    topic: str                          # 辩论主题
    context_paths: List[str] = []        # 关联的 Obsidian 笔记路径
    rounds: int = 3                     # 辩论轮数
    model_tier: str = "auto"            # 模型层级: auto/fast/balanced/deep

# 辩论流式事件
class DebateStreamEvent:
    event_type: str                     # analysis/debate/conclusion/done/error
    round: int                         # 当前轮次
    agent: str                         # 当前角色
    content: str                       # 内容
    timestamp: datetime
```

---

## 6. 模型路由策略

| 任务类型 | 模型示例 | 场景 |
|----------|----------|------|
| Fast | GPT-4o-mini, Claude-Haiku, Gemini-Flash | 简单分析、摘要、格式转换 |
| Balanced | GPT-4o, Claude-Sonnet | 标准分析、常规辩论 |
| Deep | GPT-4, Claude-Opus | 复杂推理、多轮辩论、深度总结 |

---

## 7. 配置说明

### 环境变量 (.env)

```bash
# LLM 配置 (OpenAI 兼容)
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat

# 模型层级配置
MODEL_FAST=gpt-4o-mini
MODEL_BALANCED=deepseek-chat
MODEL_DEEP=deepseek-chat

# Obsidian 配置
OBSIDIAN_VAULT_PATH=D:\path\to\obsidian\vault

# 服务器配置
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:3000
```

---

## 8. 部署需求

- Python 3.10+
- FastAPI
- LiteLLM
- Obsidian Vault 目录访问权限

---

## 9. 后续功能 (Roadmap)

- [ ] Web 前端界面
- [ ] 辩论模板自定义
- [ ] 历史辩论搜索
- [ ] 多模型对比模式
- [ ] 导出 PDF/HTML
