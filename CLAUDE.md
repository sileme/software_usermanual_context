# CLAUDE.md — software_usermanual_context 项目规则

## 项目身份

本项目是将复杂软件（Dakota、Sentaurus）的 PDF 用户手册转化为 Claude Code 可按需加载的结构化知识层的工程管道。

**核心信条**：不是"总结文档"，而是"构建可查询、可渐进加载的知识图谱"。

## 目录约定

| 目录 | 性质 | 说明 |
|------|------|------|
| `corpus/raw/` | 输入 | 用户放入的原始 PDF 手册，只读 |
| `corpus/md/` | 中间产物 | MinerU 转换后的 Markdown，自动生成 |
| `context_layer/` | 最终产出 | 结构化知识文件，供其他项目引用 |
| `scripts/` | 工具 | 转换与构建脚本，幂等可复用 |
| `tests/` | 质控 | 校验 context_layer 完整性 |
| `.claude/skills/` | Skill | 可被其他项目载入的 Skill 定义 |

## 渐进式披露策略

回答软件使用问题时，按以下顺序加载上下文：

1. **INDEX.md** — 先查模块导航树和关键词索引，定位相关模块
2. **module_map.md** — 确认模块边界和上下游依赖
3. **task_cards.md / syntax.md** — 查找具体操作步骤或语法片段
4. **diagnostics.md** — 如涉及报错/排障，补充诊断条目
5. **corpus/md/** 原始 Markdown — 仅在前四层无法回答时才回退到原始手册

禁止一次性加载全部 context_layer 文件到上下文中。

## 回答规则

- 引用 context_layer 中的信息时，注明来源文件路径
- 如 context_layer 中无相关信息，明确告知"手册中未覆盖"，不要编造
- 生成的配置/脚本应标注参考了哪个模块的哪条语法条目
- 优先使用 task_cards 中的已验证步骤，而非从 syntax 自行拼装

## 开发规则

- 所有脚本必须幂等（重复运行不产生副作用）
- 每次完成一个处理阶段后，删除中间临时文件
- 先处理 Dakota（1 份手册），验证全流程后再处理 Sentaurus（30 份）
- 修改 context_layer 产出格式前，更新 MODEL_PLAN.md 中的对应描述
