# software_usermanual_context

把工程软件的官方 user manual 转成 **Claude Code 可按需加载的背景知识层**——不熟悉该软件的人也能通过对话查询用法、理解参数、生成脚本，而不用从头读几百页 PDF。

当前已规划：

| 软件 | 文档 | 状态 |
|---|---|---|
| **dakota** | `dakota_Users-6.16.0.pdf`（优化、不确定性量化、灵敏度分析） | M0 脚手架就绪，待用户跑 pipeline |
| **sentaurus** | 30 份 TCAD user guide（`sdevice_ug`、`sprocess_ug`、`svisual_ug`、`swb_ug`、…） | 同上 |

> 开发者路线图见 [ROADMAP.md](ROADMAP.md)。

## 它解决什么

工程软件手册通常很厚（Dakota 单本 4 MB、Sentaurus 全套 77 MB），一次性塞给 LLM 既贵又会触发 hallucination。本项目按 **Manual-to-Skill Context Engineering** 思路把手册拆成：

- **`module_map.md`** —— 章节树骨架，默认加载，告诉 Claude 哪本手册讲了哪些事
- **`provenance.json`** —— 每个文本块到 PDF 页码的回溯索引，保证回答可追溯
- **`task_cards/` / `syntax/` / `diagnostics/`** —— 按"如何做 X"、"关键词怎么写"、"这条错误怎么办"切分的细颗粒卡片，按需 grep

加上一条硬规则：**手册没说的，回答以「资料中无相关内容」开头，再可选附通用建议**——不允许 paraphrase 没读过的内容。

## 两类用户

### 角色 A：只想查软件用法

你不需要装任何东西。前提是有人已经把你想问的软件入库（`context_layer/<software>/` 已存在）。

1. 用 Claude Code 打开本仓库
2. 提问，例如：
   - "Sentaurus sdevice 里 `Physics{}` 段怎么开 SRH recombination？"
   - "Dakota 跑参数扫描需要哪些 input 段？"
   - "Sprocess 报 `mesh refinement failed`，从哪查起？"

Claude Code 会自动按渐进式披露读 `context_layer/<software>/`：先入口、再章节、最后命中关键词的卡片，回答附 `[<doc>.pdf p.<n>]` 引用。

**当手册未覆盖时**：回答会以「资料中无相关内容」开头，可能附「非手册内容：」的通用建议（明确标注是手册外推断）。这是有意设计——你能立刻判断哪些信息是手册说的、哪些是常识猜测。

### 角色 B：想新增一个软件

把一个新软件的手册接入仓库，让角色 A 能查它。

```bash
# 0. 装 minerU（一次性）
#    见 docs/install_mineru.md

# 1. 放 PDF
mkdir -p corpus/raw/<software>/
cp /your/path/manual.pdf corpus/raw/<software>/

# 2. PDF → Markdown（可能跑几小时，看 GPU/CPU）
python scripts/01_pdf_to_markdown.py --software <software>

# 3. Markdown → context_layer
python scripts/02_markdown_to_context.py --software <software>

# 4. 抽查 + 提交
git add context_layer/<software>/
git commit -m "context_layer: add <software>"
```

详细流程见 [docs/add_new_software.md](docs/add_new_software.md)，命名约定、抽查清单都在里面。

## 仓库结构

```text
software_usermanual_context/
  README.md                              你正在读
  ROADMAP.md                             开发者路线图
  CLAUDE.md                              Claude Code 项目级规则
  .claude/skills/software-manual-context/
    SKILL.md                             Skill 定义（渐进式披露 + 拒答规则）
  context_layer/                         ★ 唯一入 git 的产物层 ★
    <software>/index.md                  软件入口
    <software>/<doc>/index.md            单文档入口
    <software>/<doc>/module_map.md       章节树
    <software>/<doc>/provenance.json     块 → PDF 页码
    <software>/<doc>/task_cards/         curated 任务卡
    <software>/<doc>/syntax/             curated 关键词参考
    <software>/<doc>/diagnostics/        curated 错误诊断
  corpus/                                gitignored（PDF 与中间产物）
    raw/<software>/*.pdf                 原始 PDF
    markdown/<software>/<doc>/...        minerU 输出
  scripts/
    01_pdf_to_markdown.py                PDF → Markdown 包装
    02_markdown_to_context.py            Markdown → context_layer
    lib/                                 backend 探测、minerU 包装、章节解析、provenance
  docs/
    install_mineru.md                    minerU 安装（Windows GPU/CPU）
    add_new_software.md                  入库完整流程
    skill_authoring.md                   task_cards / syntax / diagnostics 写作约定
```

`corpus/` 整体 gitignored：手册可能受版权限制，且生成的中间产物体积大且可重生成；仓库只追踪 `context_layer/`。

## 技术栈

- **PDF → Markdown**：[minerU](https://github.com/opendatalab/MinerU)（可替换；02 脚本与 PDF 引擎解耦，见 `docs/add_new_software.md`）
- **Markdown → context_layer**：纯 Python，无第三方依赖
- **运行时知识层**：Claude Code 通过项目级 Skill 加载

## 当前限制（M0 → M1 过渡期）

- `task_cards/`、`syntax/`、`diagnostics/` 目前只有 `_TODO.md` 占位，**M2 才半自动填充**。M1 期间 Claude Code 回答以 `module_map.md` + `provenance.json` 为主，命中卡片的回答会回退到"看 module_map 第 X 章"的指引。
- `scripts/lib/heading_tree.py` 和 `provenance.py` 在 M0 是 stub，M1 实装。
- 仅支持英文手册（minerU `--lang en`）；中日韩手册需调 `--lang` 参数并验证 OCR 表现。

## 贡献 / 提问

- 想加新软件：照 [docs/add_new_software.md](docs/add_new_software.md) 做
- 想改 SKILL/CLAUDE 规则：先在 issue 里讨论；特别是「资料中无相关内容」拒答字符串不要随意改
- 开发进度：[ROADMAP.md](ROADMAP.md) 的 "Currently Working On" 块
- 开发成MCP server