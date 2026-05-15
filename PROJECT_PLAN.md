# 项目开发计划 & 进度追踪

> **面向对象**：开发者
> **更新规则**：里程碑达成时更新状态；具体到某一步时展开子任务细节和进度；完成后删去子任务细节，仅保留里程碑完成标记。

---

## 总体目标

将 Dakota（1 份 ~4MB）和 Sentaurus（30 份 ~77MB）的 PDF 用户手册，通过 MinerU 转 Markdown，再结构化提取为 Context Layer，供其他 Claude Code 项目按需加载使用。

---

## Phase 1: 基础设施搭建

### M1 — 项目骨架初始化 ✅

- [x] 仓库创建 & 初始 commit
- [x] 目录结构创建 (`corpus/raw/`, `corpus/md/`, `context_layer/`, `scripts/`, `tests/`)
- [x] `CLAUDE.md` 项目规则文件
- [x] `.claude/skills/software-manual-context/SKILL.md` Skill 入口文件

### M2 — MinerU 转换链路（Dakota 先行）

- [ ] 环境准备：MinerU 安装 & 验证
- [ ] Dakota PDF 入库到 `corpus/raw/dakota/`
- [x] `scripts/convert_pdf_to_md.sh` — 单文件/批量 PDF → Markdown 转换脚本
- [ ] Dakota 手册完成 MinerU 转换，产出到 `corpus/md/dakota/`
- [ ] 转换质量检查（目录结构保留率、代码块识别、表格保真度）

### M3 — Context Layer 生成器

- [x] `scripts/build_context_layer.py` — 从 Markdown 提取结构化知识
  - [x] INDEX.md 生成（入口索引，含模块导航树）
  - [x] module_map.md 生成（章节→功能模块映射）
  - [x] syntax.md 生成（命令/参数/关键字语法片段）
  - [x] task_cards.md 生成（"如何做 X" 任务卡片）
  - [x] diagnostics.md 生成（错误信息→原因→解决方案）
- [ ] Dakota context_layer 产出验证 (需 PDF 入库后方可运行)

### M4 — Claude Code Skill 集成

- [x] `.claude/skills/software-manual-context/SKILL.md` 完善
  - [x] 定义何时触发 Skill
  - [x] 定义渐进式披露策略（先读 INDEX → 按需深入）
- [ ] 在测试项目中验证：Claude Code 能基于 context_layer 回答 Dakota 使用问题
- [ ] MVP 里程碑达成

---

## Phase 2: 规模化 & 多软件

### M5 — Sentaurus 批量处理

- [ ] Sentaurus 30 份 PDF 入库到 `corpus/raw/sentaurus/`
- [ ] 批量转换脚本适配（处理多文件命名、合并策略）
- [ ] Sentaurus 全部 Markdown 产出
- [ ] Sentaurus context_layer 产出（模块地图需处理跨手册引用）
- [ ] 质量检查通过

### M6 — 质量 & 测试

- [ ] context_layer 完整性校验脚本
- [ ] Markdown → Context Layer 转换覆盖率报告
- [ ] 多项目引用兼容性测试

---

## Phase 3: 持续演进

### M7 — 经验反馈回路

- [ ] 设计反馈收集格式（bug、调参经验、使用技巧）
- [ ] `corpus/feedback/` 目录 & 提交流程
- [ ] 反馈内容自动关联到 context_layer 对应模块

### M8 — 多框架适配

- [ ] MCP Server 封装（按模块提供查询工具）
- [ ] RAG 索引生成（为外部 RAG 系统提供分块后的 embedding-ready 文本）
- [ ] 其他 Agent 框架 Skill 格式导出

---

## 当前进行中

M1 完成，M2/M3 脚本已就绪。下一步依赖：Dakota PDF 入库 → MinerU 转换 → Context Layer 生成。需用户提供 PDF 文件。

---

## 变更日志

| 日期 | 内容 |
|------|------|
| 2026-05-15 | 初始化项目计划，定义 Phase 1-3 里程碑 |
| 2026-05-15 | M1 完成：目录结构、CLAUDE.md、SKILL.md |
