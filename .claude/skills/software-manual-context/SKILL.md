# software-manual-context Skill

将 Dakota/Sentaurus 用户手册知识注入 Claude Code 的项目级 Skill。

## 触发条件

当用户在当前项目中提出以下类型问题时，激活此 Skill：

- 询问 Dakota 或 Sentaurus 软件的功能、用法、命令语法
- 请求生成 Dakota/Sentaurus 的输入文件、配置脚本
- 遇到 Dakota/Sentaurus 的报错信息需要排障
- 询问 "如何在 Dakota/Sentaurus 中做 X" 类型的操作问题
- 需要了解某个模块的参数含义和取值范围

## 不触发的情况

- 纯粹的编程问题（与 Dakota/Sentaurus 无关）
- 通用的 Linux/Shell/Python 问题
- 项目自身的代码问题（非软件使用问题）

## 渐进式披露加载策略

回答前，按以下顺序逐层加载上下文，每层加载后判断是否足够回答问题：

### 第 1 层：入口索引

首先读取 `<软件名>/INDEX.md`，获取：
- 模块导航树（该软件的模块层级结构）
- 关键词→模块映射表
- 各模块的一句话描述

根据用户问题的关键词匹配模块，确定需要深入哪些模块。

### 第 2 层：模块地图 + 任务卡/语法

根据第 1 层的定位，选择性读取：
- `<软件名>/module_map.md` 中对应模块的章节
- `<软件名>/task_cards.md` 中匹配的操作任务
- `<软件名>/syntax.md` 中相关的命令/参数条目

### 第 3 层：诊断条目

如果问题涉及报错、警告或异常行为，读取：
- `<软件名>/diagnostics.md` 中匹配的错误码/错误信息

### 第 4 层：原始手册回退

仅当上述三层均无法回答时，才读取 `corpus/md/<软件名>/` 下的原始 Markdown 手册。

## 回答模板

```
## 回答

[基于 context_layer 的具体回答]

**参考来源**：
- context_layer/<软件名>/INDEX.md — 模块定位
- context_layer/<软件名>/syntax.md — [具体条目]
- context_layer/<软件名>/task_cards.md — [具体任务]
```

## 当前覆盖范围

| 软件 | context_layer 路径 | 状态 |
|------|-------------------|------|
| Dakota | `context_layer/dakota/` | 待生成 |
| Sentaurus | `context_layer/sentaurus/` | 待生成 |

## 维护规则

- 添加新软件时，在 `context_layer/<新软件>/` 下按相同结构生成文件
- 反馈经验、bug 记录追加到 `diagnostics.md` 末尾，标注日期和来源
- 语法条目需包含：关键字、参数表、取值范围、示例、出处（原始手册章节号）
