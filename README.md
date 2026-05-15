# software_usermanual_context

将复杂软件的 User Manual 转化为 Claude Code 可按需加载的背景知识层（Context Layer），使不熟悉该软件的人也能通过 Claude Code 查询功能、理解用法、生成配置/脚本，并逐步辅助软件自动调度与多软件耦合开发。

## 解决什么问题

TCAD 软件（如 Dakota、Sentaurus）的用户手册动辄数百页、数十 MB，开发者很难在编写项目代码时快速查阅。本项目将这些手册：

1. **入库** — 原始 PDF 收集到 `corpus/raw/`
2. **转写** — 通过 [MinerU](https://github.com/opendatalab/MinerU) 将 PDF 转为 Markdown
3. **结构化** — 从 Markdown 提取模块地图、语法参考、任务卡、诊断条目
4. **产出 Context Layer** — 生成 Claude Code 可用的结构化知识文件，在其他项目中直接引用

## 当前支持的软件

| 软件 | 手册数量 | 原始大小 | 状态 |
|------|---------|---------|------|
| Dakota | 1 份 | ~4 MB | 待入库 |
| Sentaurus | 30 份 | ~77 MB | 待入库 |

## 快速开始

### 1. 克隆本仓库

```bash
git clone <this-repo-url>
cd software_usermanual_context
```

### 2. 放入原始 PDF

将 Dakota 或 Sentaurus 的 PDF 手册放入 `corpus/raw/<software_name>/` 目录：

```bash
# 示例
cp /path/to/dakota-manual.pdf corpus/raw/dakota/
cp /path/to/sentaurus/*.pdf corpus/raw/sentaurus/
```

### 3. 运行 MinerU 转换

```bash
# 安装 MinerU（首次）
pip install mineru

# 执行转换脚本
bash scripts/convert_pdf_to_md.sh corpus/raw/dakota corpus/md/dakota
bash scripts/convert_pdf_to_md.sh corpus/raw/sentaurus corpus/md/sentaurus
```

### 4. 生成 Context Layer

```bash
python scripts/build_context_layer.py --software dakota
python scripts/build_context_layer.py --software sentaurus
```

产出在 `context_layer/<software_name>/` 目录下。

### 5. 在其他项目中使用

在目标项目的 `CLAUDE.md` 中引用：

```markdown
# 参见 Dakota 手册上下文
@../software_usermanual_context/context_layer/dakota/INDEX.md
```

或通过 Claude Code Skill 按需加载：

```markdown
# .claude/skills/dakota/SKILL.md
参考 context_layer/dakota/ 下的模块地图和语法参考回答问题。
```

## 目录结构

```text
software_usermanual_context/
  README.md                       # 本文件
  CLAUDE.md                       # 项目级 Claude Code 规则
  PROJECT_PLAN.md                 # 开发者项目计划 & 进度追踪
  .claude/
    skills/
      software-manual-context/
        SKILL.md                  # 可注册到其他项目的 Skill
        task_cards/               # 任务卡片（"如何做 X"）
        syntax/                   # 语法参考
        diagnostics/              # 诊断条目
  corpus/
    raw/                          # 原始 PDF 手册
      dakota/
      sentaurus/
    md/                           # MinerU 转换后的 Markdown
      dakota/
      sentaurus/
  context_layer/                  # 最终产出的结构化知识
    dakota/
      INDEX.md                    # 入口索引
      module_map.md               # 模块地图
      syntax.md                   # 语法参考
      task_cards.md               # 任务卡片
      diagnostics.md              # 诊断条目
    sentaurus/
      INDEX.md
      module_map.md
      syntax.md
      task_cards.md
      diagnostics.md
  scripts/                        # 处理脚本
    convert_pdf_to_md.sh          # PDF → Markdown 批量转换
    build_context_layer.py        # Markdown → Context Layer
  tests/                          # 质量检查
```

## Context Layer 概念

| 概念 | 说明 |
|------|------|
| **Context Engineering** | 设计模型在何时看到哪些上下文 |
| **Progressive Disclosure** | 默认只暴露入口索引，需要时再读取语法、任务卡、诊断和原始出处 |
| **Context Compression** | 将大手册压缩为模块地图、任务卡、语法片段和故障诊断 |
| **Skill-ready Knowledge Base** | 可被 Claude Code Skill 直接使用的背景知识层 |
| **Operational Knowledge Capture** | 将调试反馈、bug 记录、使用经验沉淀为可复用知识 |

## MVP 目标

1. 注册一个软件 user manual 入库
2. 建立软件模块地图
3. 将手册内容压缩为语法参考和诊断条目
4. 生成一个 Claude Code 项目级 Skill
5. Claude Code 能基于这些文件回答软件使用问题

## 拓展规划

1. 纳入使用反馈、网络零散信息
2. 适配 MCP、RAG 及其他 Agent 框架
3. 支持多软件耦合场景的交叉引用
