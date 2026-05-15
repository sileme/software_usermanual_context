# 添加新软件

把一个新软件的 user manual 接入 `software_usermanual_context`，从 PDF 走到可被 Claude Code 查询的 `context_layer/<software>/`。

## 前置

- 装好 minerU：见 [install_mineru.md](install_mineru.md)
- 有该软件的官方 user manual PDF（一个或多个）

## 步骤

### 1. 命名

为软件取一个**短、全小写、无空格**的名字。这个名字会成为目录名、SKILL 引用的 key，改起来麻烦，一开始就定好。

例：
- `dakota` ✅
- `sentaurus` ✅
- `comsol_multiphysics` ❌（有下划线 OK 但太长）→ 用 `comsol`
- `Sentaurus TCAD` ❌（有空格、大写）

### 2. 放 PDF

```bash
mkdir -p corpus/raw/<software>/
cp /path/to/manual.pdf corpus/raw/<software>/
```

PDF 文件名也建议**短、可读、无空格**——它会成为 `context_layer/<software>/<doc>/` 的 `<doc>` 部分。比如 `dakota_Users-6.16.0.pdf` → `<doc> = dakota_Users-6.16.0`。

> `corpus/` 整体在 `.gitignore` 里。这是有意的：手册可能受版权限制，且生成的 markdown 太大不适合入库。

### 3. PDF → Markdown

```bash
python scripts/01_pdf_to_markdown.py --software <software>
```

加 `--dry-run` 可以先看会处理哪些文件。加 `--doc <name>` 可以只跑一份。

输出在 `corpus/markdown/<software>/<doc>/<backend>/`，含：
- `<doc>.md` ——主 markdown
- `<doc>_content_list.json` ——按阅读顺序的 block 列表（02 脚本要用）
- `images/` ——抽出的图

### 4. Markdown → context_layer

```bash
python scripts/02_markdown_to_context.py --software <software>
```

输出在 `context_layer/<software>/`，含：
- `index.md` ——软件入口（自动聚合所有 doc）
- `<doc>/index.md` ——单文档入口
- `<doc>/module_map.md` ——章节树（M1）
- `<doc>/provenance.json` ——块到 PDF 页码的回溯（M1）
- `<doc>/{task_cards,syntax,diagnostics}/_TODO.md` ——人工 + LLM 半自动补（M2）

### 5. 抽查

打开 `context_layer/<software>/<doc>/module_map.md`，对照 PDF 目录，确认章节没漏。

打开 `context_layer/<software>/index.md`，确认所有 doc 都被列入。

### 6. 提交

```bash
git add context_layer/<software>/
git commit -m "context_layer: add <software>"
```

`corpus/` 因为 gitignore 不会被加入，正常。

### 7. 让 Claude Code 知道

更新两处提及"已注册软件"的列表：
- `.claude/skills/software-manual-context/SKILL.md` 的 "Registered software" 小节
- `README.md` 的 "支持的软件" 小节

如果不更新，Skill 仍然能用（它会读 `context_layer/*/index.md`），但用户和 Claude Code 看不到一目了然的清单。

## 任务卡 / 语法 / 诊断（M2）

这三个目录在 M0/M1 阶段只有 `_TODO.md` 占位。M2 引入半自动 LLM pass + 人工 review，写作约定见 [skill_authoring.md](skill_authoring.md)。

## 如何换 PDF 引擎

`scripts/02_markdown_to_context.py` 与 minerU **解耦**——它只读两个文件：

```
corpus/markdown/<software>/<doc>/<anything>/<doc>.md
corpus/markdown/<software>/<doc>/<anything>/<doc>_content_list.json
```

后者是一个 JSON 数组，每条 block 至少含：

```json
{"type": "text|table|image|equation", "page_idx": 0, "text": "..."}
```

按阅读顺序排列。其它字段（`bbox`、`level`、`img_path` 等）允许存在，02 会忽略未知字段。

如果你换了别的工具（docling、marker、商用 API、自家脚本），让它把上面两个文件按相同路径吐出，01 直接换掉就行，02 不用动。

写一个新的 `01_<engine>_to_markdown.py` 与现有的 `01_pdf_to_markdown.py` 并列，用 `--engine` 参数挑也是一种思路；目前没做，因为只有 minerU。
