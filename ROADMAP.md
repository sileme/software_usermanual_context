# Roadmap

给开发者读。最终用户看 [README.md](README.md)。

## Vision

把工程软件的官方手册转成 Claude Code 可按需加载的背景知识层（`context_layer/`），让不熟悉该软件的人也能通过对话查询用法、生成配置脚本，并逐步走向多软件耦合开发的自动化。

## Milestones

- [x] **M0 — 脚手架**：仓库结构、SKILL/CLAUDE 规则、scripts 骨架、文档骨架、.gitignore（2026-05-15）
- [ ] **M1 — 首批入库**：dakota + sentaurus 跑通 PDF→markdown→`context_layer/` 的自动产物（`index.md`/`module_map.md`/`provenance.json`）
- [ ] **M2 — 任务卡半自动**：实现 `scripts/03_curate.py`，对每份 doc 半自动生成 `task_cards/`、`syntax/`、`diagnostics/` 草稿
- [ ] **M3 — 反馈接入**：把网络搜集、issue tracker、社区帖子、个人调试记录归并进 `context_layer/<software>/feedback/`
- [ ] **M4 — 框架适配**：MCP server 暴露（让 Cursor / Continue / 其他 IDE 也能用同一份 `context_layer/`）、RAG 索引、其他 agent 框架适配

## Currently Working On

<!-- BEGIN: currently-working-on -->
（无活跃工作。下一个 milestone 接手时按本节末尾的"进度更新流程"填回。）
<!-- END: currently-working-on -->

## Backlog

下面这些尚未排上 milestone，按用户需求决定优先级。

- **MCP server 化**：把 SKILL 的"读 context_layer 然后回答 + 拒答规则"包装成 MCP server，让非 Claude Code 客户端（Cursor、Continue、Cline、Zed AI 等）也能复用同一份 `context_layer/`。属 M4 范畴，但优先级建议提前——一旦 M2 任务卡填好，MCP 化的边际收益就显现。
- 单元测试：`scripts/lib/heading_tree.py` 与 `provenance.py` 实现后补 `tests/`（pytest fixtures 用一个 1 页的小 PDF）
- `Makefile` 或 `justfile`：把 `01 → 02 → git add` 串成一条命令
- 多语言手册支持：当前 `--lang` 写死英文；中文/日文手册要看 minerU OCR 表现
- `context_layer/` 的版本化：手册升级（dakota 6.16 → 6.17）时如何 diff、是否双版本并存
- Skill 输出引用页码后，加一个 `scripts/verify_provenance.py` 校验 SKILL 回答里所有 `[<doc>.pdf p.<n>]` 都能在 `provenance.json` 里命中
- 把 SKILL.md 的 "Registered software" 列表自动从 `context_layer/*/index.md` 生成，避免手抖
- API 调用费用 / 配额监控：`scripts/01_pdf_to_markdown.py --engine api` 走云端 API 时，记录每次 batch 的页数和耗时到 `corpus/.api_log.jsonl`（gitignored），便于事后看花了多少

## 工程约定

- **02 脚本与 PDF 引擎解耦**：02 只读 `<doc>.md` + `<doc>_content_list.json`；换引擎只动 01。详见 `docs/add_new_software.md`。
- **拒答字符串**：永远用中文「资料中无相关内容」，即使手册是英文。修改前先在 issue 里讨论。
- **`.agent/`** 是模型自用工作笔记，gitignored；每个开发周期结束删除。**不要把它当 ROADMAP 的草稿**——半成品想法记 `.agent/PLAN.md`，公开规划写这里。

## 进度更新流程

完成一个 milestone 时：
1. 在 Milestones 下把 `[ ]` 改 `[x]` 并加日期
2. 把 "Currently Working On" 区块**清空内容、保留 BEGIN/END 注释**，等下一个 milestone 接手时重填
3. 新开 milestone 的工作时把详情写回 "Currently Working On"

`grep -A20 "BEGIN: currently-working-on" ROADMAP.md` 可以扫到当前活跃工作。
