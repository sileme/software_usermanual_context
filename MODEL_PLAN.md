# 模型自读执行计划

> **面向对象**：Claude Code 模型自身
> **核心规则**：每个开发过程结束后，删除该过程中产生的中间文件（临时脚本、调试输出、中间产物），只保留最终的代码和结果文件。

---

## 全局约定

1. **中间文件清理**：每次执行完一个 Pipeline 阶段后，删除该阶段的临时/中间产物。例如：
   - MinerU 转换产生的中间 JSON/临时文件 → 删除
   - 调试用的临时脚本 → 删除
   - 处理日志（如无报错）→ 删除
2. **命名规范**：
   - 脚本：`scripts/<动词>_<目标>.{sh,py}`
   - 中间 Markdown：`corpus/md/<software>/<manual_name>.md`
   - Context Layer 产出：`context_layer/<software>/<类型>.md`
3. **幂等性**：所有脚本必须支持重复运行而不产生重复/错误结果。
4. **每次只处理一个软件**：先完成 Dakota 全流程，验证通过后再处理 Sentaurus。

---

## Pipeline 总览

```
corpus/raw/<software>/*.pdf        ← 用户放入
        │
        ▼  [MinerU]
corpus/md/<software>/*.md         ← PDF → Markdown
        │
        ▼  [build_context_layer.py]
context_layer/<software>/          ← 结构化知识产出
  ├── INDEX.md                     ← 入口索引
  ├── module_map.md                ← 模块地图
  ├── syntax.md                    ← 语法参考
  ├── task_cards.md                ← 任务卡片
  └── diagnostics.md               ← 诊断条目
```

---

## Phase 1: 基础设施

### Step 1.1 — 创建目录结构

- 创建所有必要目录
- 产出 `.gitkeep` 占位文件
- **完成后删除**：无中间产物

### Step 1.2 — 编写 CLAUDE.md

- 内容：项目规则、context_layer 引用方式、渐进式披露策略
- 位置：项目根目录
- **完成后删除**：无中间产物

### Step 1.3 — 编写 MinerU 转换脚本

- 脚本：`scripts/convert_pdf_to_md.sh`
- 功能：
  - 接收输入目录（PDF）和输出目录（Markdown）
  - 调用 `mineru` 逐文件转换
  - 保留原始文件名，`.pdf` → `.md`
  - 记录转换日志到 `corpus/md/<software>/_conversion.log`
- **完成后删除**：测试用的临时 PDF（如有）

---

## Phase 2: Dakota 全流程（先行验证）

### Step 2.1 — Dakota PDF 入库 & 转换

- 将 Dakota PDF 放入 `corpus/raw/dakota/`
- 运行 `scripts/convert_pdf_to_md.sh corpus/raw/dakota corpus/md/dakota`
- 验证 Markdown 产出质量
- **完成后删除**：MinerU 产生的中间 JSON/layout 文件、临时图片（如不需要）

### Step 2.2 — 编写 Context Layer 生成器

- 脚本：`scripts/build_context_layer.py`
- 功能：
  - 读取 `corpus/md/<software>/` 下所有 `.md`
  - 分析章节结构（h1-h4 标题层级）
  - 生成 `INDEX.md`：所有模块的导航树，含关键词索引
  - 生成 `module_map.md`：章节到功能模块的映射
  - 生成 `syntax.md`：提取代码块、命令行、参数表
  - 生成 `task_cards.md`：识别 "How to" / 操作步骤段落
  - 生成 `diagnostics.md`：识别错误信息/警告/排障段落
- **完成后删除**：调试用的临时分析日志、中间提取的 JSON（如有）

### Step 2.3 — Dakota Context Layer 生成 & 验证

- 运行 `python scripts/build_context_layer.py --software dakota`
- 人工检查 5 种产出的完整性和准确性
- 在另一个 Claude Code 项目中引用，验证可用性
- **完成后删除**：验证用的临时测试项目引用（如创建了测试目录）

### Step 2.4 — Skill 文件编写

- 完善 `.claude/skills/software-manual-context/SKILL.md`
- 定义触发条件、加载策略、回答模板
- **完成后删除**：无中间产物

---

## Phase 3: Sentaurus 规模化

### Step 3.1 — Sentaurus PDF 批量入库 & 转换

- 将 30 份 Sentaurus PDF 放入 `corpus/raw/sentaurus/`
- 运行批量转换
- 检查转换质量（大文件超时处理、内存控制）
- **完成后删除**：MinerU 中间产物

### Step 3.2 — Sentaurus Context Layer 生成

- 运行 `python scripts/build_context_layer.py --software sentaurus`
- 处理跨手册引用（30 份手册间的模块关联）
- **完成后删除**：中间分析日志

---

## Phase 4: 质量保证

### Step 4.1 — 编写校验脚本

- `tests/validate_context_layer.py`：检查 context_layer 文件完整性、链接有效性、篇幅覆盖率
- **完成后删除**：无中间产物

---

## 中间文件清理清单

每个 Step 完成后，检查并删除以下类型的临时文件：

| 文件类型 | 示例 | 删除时机 |
|----------|------|----------|
| MinerU 中间产物 | `*.json`, `*_layout.*`, `*_middle.*` | Step 2.1 / 3.1 完成后 |
| 临时调试脚本 | `debug_*.py`, `test_tmp.sh` | 所在 Step 完成后 |
| 转换日志（无报错时） | `_conversion.log` | 确认转换无误后 |
| 验证用临时目录 | `test_project/` | Step 2.3 验证完成后 |
| 重复/中间 MD | 手动修正前保留的旧版本 | 确认新版无误后 |
