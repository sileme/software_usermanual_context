# 写作约定：task_cards / syntax / diagnostics

这三个目录是 `context_layer/<software>/<doc>/` 下需要**人工 + LLM 半自动**填充的三种卡片。M0/M1 阶段只有 `_TODO.md` 占位；M2 阶段开始填。

本文给参与 curation 的人（也包括 Claude Code）读，规定卡片格式，让 SKILL 的渐进式披露能稳定 grep。

## 通用规则

- **一文件一主题**。文件名 = 主题 slug，全小写、连字符分隔。例 `mesh-refinement.md`、`error-singular-jacobian.md`。
- **每条事实必须可回溯**。卡片里出现的命令、参数、错误码，必须能在 `provenance.json` 里找到对应 chunk_id；引用方式见下面各类卡片的"引用"字段。
- **不要重复手册原文**。卡片是"压缩 + 重组"，不是复制。原文长段引用最多 2–3 句，超出请引用链接到 `module_map.md` 的章节。
- **不要编造**。看不懂或手册没说的，写"资料中无相关内容"或干脆不写这条；不要为了"看起来全面"补默认值。
- 文件以 `_DRAFT_` 前缀表示草稿（人工尚未核对），SKILL 会在加载时降级处理。

## 三类卡片

### task_cards/ ——"如何做 X"

回答"我想用这个软件做某件事，怎么做"。

文件结构：

```markdown
---
task: <短动词短语>
software: <software>
doc: <doc>
related: [<其他卡片 slug>, ...]
---

# <Task title>

## 适用场景

<一段：什么时候要做这件事>

## 步骤

1. ...
2. ...

## 关键参数

| 参数 | 说明 | 默认值 | 引用 |
|---|---|---|---|
| `Mesh.MaxAngle` | ... | 30 | [<doc>.pdf p.42] |

## 完整示例

```<语言>
<最短可运行示例>
```

## 引用

- [<doc>.pdf p.42] — 章节 X.Y
- [<doc>.pdf p.43] — 章节 X.Y.Z
```

### syntax/ ——命令/关键词参考

回答"这个关键词/命令是什么意思，怎么写"。

文件结构：

```markdown
---
keyword: <关键词原文>
software: <software>
doc: <doc>
kind: command|block|directive|option
---

# `<keyword>`

## 语法

```<语言>
<语法签名>
```

## 参数

| 参数 | 类型 | 必选 | 说明 | 引用 |
|---|---|---|---|---|

## 行为

<一段精简描述>

## 上下文

<它放在哪个 block 里、依赖什么前置设置>

## 示例

```<语言>
<最短示例>
```

## 引用

- [<doc>.pdf p.<n>]
```

### diagnostics/ ——错误/警告查询

回答"我看到这条错误/警告，怎么办"。

文件结构：

```markdown
---
symptom: "<错误信息字符串，原样照抄>"
software: <software>
doc: <doc>
severity: error|warning|info
---

# <symptom 简化版>

## 原文

```
<错误信息原样>
```

## 触发条件

<什么情况会出这条>

## 修复

1. ...
2. ...

## 类似 / 易混

- `<其他 symptom>` → [<相关卡片>]

## 引用

- [<doc>.pdf p.<n>]
```

## 命名约定速查

| 目录 | slug 形如 |
|---|---|
| `task_cards/` | `<动词>-<对象>` 例：`define-mesh`、`run-parameter-sweep` |
| `syntax/` | `<keyword 小写>` 例：`mesh`、`physics-recombination` |
| `diagnostics/` | `<symptom 简化>` 例：`error-singular-jacobian`、`warn-mesh-too-coarse` |

## 半自动生成（M2 计划）

M2 会引入一个 `scripts/03_curate.py`（暂未实现），思路：

1. 扫 `provenance.json`，按 heading 关键词分桶（`Troubleshooting`/`Error` → diagnostics 候选；`Syntax`/带代码块 → syntax 候选；`Procedure`/`How to` → task_cards 候选）。
2. 对每个候选生成 `_DRAFT_<slug>.md`，调 LLM 按上面格式填充。
3. 人工 review 后去掉 `_DRAFT_` 前缀。

在该脚本到位前，全靠手写——但格式必须严格按本文。SKILL 的 grep 依赖文件名约定。
