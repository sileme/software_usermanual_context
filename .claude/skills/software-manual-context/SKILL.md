---
name: software-manual-context
description: Answer questions about engineering software (currently Dakota and Sentaurus TCAD) using their official user manuals. Use when the user asks how to do something in the software, what a command/keyword/parameter means, what an error or warning indicates, what modules exist, or any "how do I X in <software>" question. Loads a per-software index and module map first, then drills into task cards, syntax pages, and diagnostics on demand. MUST refuse to invent any content not present in the loaded manual context.
---

# software-manual-context

Manual-backed Q&A for registered engineering software. Source of truth: `context_layer/<software>/<doc>/`.

## R1 — Hard refusal rule

If the user's question is **not covered** by the loaded `context_layer/`, your reply MUST start with the literal line:

```
资料中无相关内容
```

Optionally followed by one paragraph beginning with `**非手册内容**：` containing general advice clearly labeled as outside the manual. Never paraphrase manual content you have not actually loaded.

## Registered software

Read `context_layer/<software>/index.md` for the canonical, up-to-date list. As of this writing:

- **dakota** — `dakota_Users-6.16.0.pdf`. Optimization, UQ, sensitivity analysis. Single user manual.
- **sentaurus** — 30 user guides for the Sentaurus TCAD suite (sdevice, sprocess, svisual, swb, etc.). Each guide is a separate `<doc>/` under `context_layer/sentaurus/`.

If the user asks about a software not in the list above and not in `context_layer/`, respond with R1.

## Progressive disclosure protocol

Do **not** pre-load everything. Walk this ladder, stopping at the rung that answers the question:

1. **Always**: `context_layer/<software>/index.md` → identify which `<doc>/` is relevant.
2. **Always**: `context_layer/<software>/<doc>/module_map.md` → locate the chapter/section.
3. **On keyword query** (e.g. "how do I use `Mesh`"): `grep -li "<keyword>" context_layer/<software>/<doc>/{syntax,task_cards}/*.md`, then read only matching files.
4. **On error/warning query**: `grep -li "<symptom>" context_layer/<software>/<doc>/diagnostics/*.md`, read only matches.
5. **Cite**: every factual claim ends with `[<doc>.pdf p.<n>]` from `provenance.json`.

If steps 3–4 only find `_TODO.md` placeholders (the curated layers are M2 work, not yet filled in), fall back to step 2: point the user to the relevant chapter in `module_map.md` and say so explicitly.

## Refusal template

```
资料中无相关内容

**非手册内容**：<one short paragraph of general advice, labeled as outside the manual. Optional. Skip if you have nothing useful to add.>

可参考 `context_layer/<software>/<doc>/module_map.md` 的「<nearest chapter>」章节进一步查阅原文。
```

## Examples

### Positive — keyword in syntax/

User: "Sentaurus sdevice 里 `Physics` 段怎么开 SRH recombination？"

Action: read `context_layer/sentaurus/sdevice_ug/index.md` → `module_map.md` (locate Physics chapter) → grep `syntax/` for `Recombination` → read matching card.

Reply (skeleton):
> 在 `Physics{}` 段里加 `Recombination(SRH)`，可附 `(DopingDep)` 等修饰符开启浓度依赖 [sdevice_ug.pdf p.<n>]。完整列表见 module_map 的 Physics → Recombination 章节。

### Positive — diagnostic match

User: "sprocess 报 `Error: mesh refinement failed`，怎么办？"

Action: grep `context_layer/sentaurus/sprocess_ug/diagnostics/` for `mesh refinement failed`. If matched, read; if only `_TODO.md`, fall back to module_map 的 Meshing/Troubleshooting 章节。

### Negative — refusal

User: "Dakota 怎么对接 ANSYS Fluent？"

Action: grep dakota context_layer for `Fluent` → no hit.

Reply:
> 资料中无相关内容
>
> **非手册内容**：Dakota 通过通用 black-box 接口（analysis_driver）与外部 CAE 工具耦合，理论上可调任何能命令行驱动的求解器；具体到 Fluent 通常需要写 journal 脚本 + 文件交换中间层。建议查 `dakota_Users-6.16.0.pdf` 的 "Interfaces" 章节确认参数传递格式。
>
> 可参考 `context_layer/dakota/dakota_Users-6.16.0/module_map.md` 的「Interfaces」章节进一步查阅原文。
