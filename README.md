# OpenClaw Skills

> 一套面向 OpenClaw 平台的可插拔 Python 技能集合，每个技能独立封装、独立依赖，即插即用。

## 项目简介

本项目是个人开发的 [OpenClaw](https://github.com/openclaw) 技能仓库，采用**模块化、插件化**设计理念。每个技能作为独立子项目，拥有完整的代码、依赖与文档，可直接被 OpenClaw Agent 加载调用，也可单独作为 CLI 工具运行。

当前已包含以下技能：

| 技能 | 描述 | 核心技术 |
|------|------|----------|
| [checkin-manager](./checkin-manager) | 基于 SQLite 的打卡记录管理工具，支持分类校验、时间范围查询、逻辑删除与恢复、汇总统计 | SQLite, argparse, tomllib |
| [multimodal-vision](./multimodal-vision) | 多模态图片理解与生成工具，集成 Gemini 3.1 Flash 模型，支持图片内容分析、OCR 提取和文本生成图片 | httpx, OpenAI-compatible API |

## 项目结构

```
.
├── checkin-manager/          # 打卡管理器技能
│   ├── main.py               # 主入口（CLI + API 函数）
│   ├── config.toml           # 分类与数据库配置
│   ├── pyproject.toml        # uv 依赖配置
│   └── SKILL.md              # 技能使用文档
├── multimodal-vision/        # 多模态视觉技能
│   ├── main.py               # 主入口（VisionClient 类 + CLI）
│   ├── pyproject.toml        # uv 依赖配置
│   └── SKILL.md              # 技能使用文档
└── README.md                 # 本文件
```

## 快速开始

### 环境要求

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)（推荐）或系统 Python

### 运行单个技能

每个技能目录下均可独立运行：

```bash
cd checkin-manager
uv run python main.py categories
uv run python main.py add --category 健身 --duration 60 --note "练了胸和背"
```

```bash
cd multimodal-vision
uv run python main.py understand -i ./photo.jpg -p "描述这张图片"
uv run python main.py generate -p "日落海边的风景" -o ./sunset.png
```

> 若未安装 `uv`，可直接使用 `python main.py <command>` 运行。

### 作为模块调用

```python
from checkin_manager.main import add_record, summary
from multimodal_vision.main import VisionClient

# 打卡管理
result = add_record(category="学习", duration=120, note="阅读技术文档")
stats = summary(start_date="2026-04-01", end_date="2026-04-30")

# 图片理解
with VisionClient() as client:
    description = client.understand_image("./photo.jpg", prompt="这张图片里有什么？")
```

## 技能详情

### checkin-manager

一个功能完整的打卡记录管理 CLI 工具，适用于追踪健身、学习、阅读等日常习惯。

**核心能力：**
- **CRUD 操作**：增加、查询、更新、删除、恢复打卡记录
- **分类校验**：打卡分类通过 `config.toml` 统一管理，支持动态重命名
- **时间标准化**：自动将多种时间格式统一为 ISO 8601 标准
- **逻辑删除**：支持软删除与恢复，数据可追溯
- **汇总统计**：按分类汇总条数、总时长、平均时长、最近打卡时间
- **日期范围筛选**：支持按起止日期灵活查询

**数据库表结构：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER | 主键，自增 |
| `created_at` | TEXT | 记录创建时间 |
| `updated_at` | TEXT | 记录修改时间 |
| `checkin_time` | TEXT | 打卡时间 |
| `duration_minutes` | INTEGER | 任务进行时间（分钟） |
| `location` | TEXT | 打卡地点 |
| `category` | TEXT | 打卡分类 |
| `note` | TEXT | 备注 |
| `is_deleted` | INTEGER | 逻辑删除标记（0=未删除，1=已删除） |

详细用法请查阅 [checkin-manager/SKILL.md](./checkin-manager/SKILL.md)。

---

### multimodal-vision

基于 OpenAI 兼容协议的多模态图片理解与生成工具。

**核心能力：**
- **图片理解（Vision）**：分析、描述图片内容，支持 OCR 文字提取，单图/多图输入
- **图片生成（Image Generation）**：根据文本描述生成图片，自动保存为本地文件
- **混合工作流**：可组合「理解参考图 → 生成新图」的完整 pipeline

**模型配置：**

| 能力 | 模型 | 端点 |
|------|------|------|
| 图片理解 | `gemini-3.1-flash-lite-preview` | `https://api.vectorengine.ai/v1/chat/completions` |
| 图片生成 | `gemini-3.1-flash-image-preview` | `https://api.vectorengine.ai/v1/chat/completions` |

详细用法请查阅 [multimodal-vision/SKILL.md](./multimodal-vision/SKILL.md)。

## 技术栈

- **语言**：Python 3.10+
- **依赖管理**：[uv](https://docs.astral.sh/uv/)
- **数据库**：SQLite（checkin-manager）
- **HTTP 客户端**：httpx（multimodal-vision）
- **API 协议**：OpenAI-compatible Chat Completions API

## 开发规范

1. **技能隔离**：每个技能独立目录，拥有独立的 `pyproject.toml` 和依赖，禁止跨技能引入硬编码依赖
2. **文档先行**：新增技能必须包含 `SKILL.md`，说明触发场景、可用命令、接口函数及约束条件
3. **配置外置**：用户可配置项（如分类列表、数据库路径）统一写入 `config.toml`，代码中通过配置文件读取
4. **CLI 友好**：所有技能均提供 `argparse` 命令行入口，支持 `uv run python main.py <command>` 直接运行
5. **接口暴露**：核心功能以纯函数或类的形式暴露，便于被 OpenClaw Agent 直接调用

## 添加新技能

1. 在项目根目录创建新的技能文件夹（如 `new-skill/`）
2. 编写 `main.py` 实现核心功能，提供 CLI 入口和可调用接口
3. 编写 `pyproject.toml` 管理依赖
4. 编写 `SKILL.md` 描述技能的使用方式与约束
5. 在根目录 `README.md` 的「技能列表」中注册新技能
6. 提交并推送：

```bash
git add .
git commit -m "Add new-skill: <简短描述>"
git push origin main
```

## License

MIT
