# 接入 minerU

[minerU](https://github.com/opendatalab/MinerU) 是 OpenDataLab 出的 PDF→Markdown 工具，本项目用它把官方手册转成可后处理的 markdown。

**两种选择**：

| 选项 | 适合 | 成本 | 速度 |
|---|---|---|---|
| **A. 本地安装** | 文件多、敏感、想离线 | 一次 pip + 下模型 | CPU 慢；GPU 快 |
| **B. 云端 API** | 文件少、快捷、本机无 GPU | 调用次数计费 | 中等（取决于队列） |

两种方式产出的 markdown 布局完全相同，下游 `scripts/02_markdown_to_context.py` 不区分来源。

---

## 选项 A：本地安装

### 先决条件

- Python ≥ 3.10（推荐 3.11/3.12）
- 16 GB RAM 起步（处理 4 MB Dakota 手册够用；77 MB 的 Sentaurus 30 份建议 32 GB）
- 磁盘 ≥ 5 GB（minerU 首次跑会下载 1–3 GB 模型）

### 1. 装 Python 包

CPU 版本（无 GPU 也能跑，慢一些）：

```bash
pip install -U "mineru[all]"
```

如果你想用 GPU 加速（推荐 Sentaurus 这种量级），先按 [pytorch.org](https://pytorch.org/get-started/locally/) 选你的 CUDA 版本装好 `torch` + `torchvision`，再装 mineru：

```bash
# 例：CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -U "mineru[all]"
```

验证：

```bash
mineru --version
```

### 2. 模型下载（首次运行会自动下）

minerU 默认从 HuggingFace 拉模型。国内或受限网络环境下走 ModelScope 镜像：

PowerShell:

```powershell
$env:MINERU_MODEL_SOURCE = "modelscope"
```

cmd.exe:

```cmd
set MINERU_MODEL_SOURCE=modelscope
```

git-bash / WSL:

```bash
export MINERU_MODEL_SOURCE=modelscope
```

把这行加到你的 shell profile（PowerShell 的 `$PROFILE`、bash 的 `~/.bashrc`）就不用每次设。

### 3. 烟测

随便找个小 PDF 跑一遍，确认环境通：

```bash
mineru -p some_test.pdf -o ./_test_out -b pipeline
```

参数说明：
- `-p` 输入文件或目录
- `-o` 输出目录
- `-b pipeline` 强制 CPU 后端（首次烟测最稳）；GPU 环境可省略让 minerU 自选

成功的标志：`./_test_out/some_test/<backend>/some_test.md` 存在且非空，同目录有 `some_test_content_list.json`。

### 4. 与本仓库脚本配合

确认 `mineru` 在 PATH 后，回到仓库根目录跑：

```bash
python scripts/01_pdf_to_markdown.py --software dakota --dry-run
```

不报错且能列出 PDF 文件名即可。脱掉 `--dry-run` 就会真跑。后端选择由 `scripts/lib/backend_detect.py` 自动决定（有 CUDA 就用 GPU，没有就 pipeline）。

### 本地常见问题

| 症状 | 处理 |
|---|---|
| `mineru: command not found` | pip 装的是当前 Python 环境，确认 PATH 里有 `Scripts/`（Windows）或 `bin/`（Unix） |
| 首次跑卡在下载模型 | 设 `MINERU_MODEL_SOURCE=modelscope`；或挂梯子 |
| `CUDA out of memory` | 加 `--backend pipeline` 退回 CPU；或换更小批次 |
| Sentaurus 跑了几小时 | 正常；30 个 PDF CPU 估算 4–10 小时。建议 GPU 或换 API |

---

## 选项 B：云端 API（mineru.net）

不想装、本机没 GPU、或者只跑少量手册—直接调 minerU 官方 API。

### 1. 拿 token

去 [mineru.net](https://mineru.net) 注册账号 → 控制台 [apiManage](https://mineru.net/apiManage) 申请 API token。

### 2. 设环境变量

token 是敏感信息，**不要写进任何入 git 的文件**。

PowerShell（当前会话）：

```powershell
$env:MINERU_API_TOKEN = "你的token"
```

cmd.exe：

```cmd
set MINERU_API_TOKEN=你的token
```

git-bash / WSL：

```bash
export MINERU_API_TOKEN=你的token
```

要持久化就把上面对应行加到你 shell 的 profile（`$PROFILE`、`~/.bashrc` 等）。仓库根目录可以放一个 `.env`（已在 `.gitignore` 里）然后自己 `source` 它。

### 3. 跑

```bash
python scripts/01_pdf_to_markdown.py --software dakota --engine api
```

`--engine api` 时：
- 默认 `model_version=vlm`（视觉模型，准）；想用更便宜的 pipeline 模型加 `--backend pipeline`
- `--poll-interval 10`（默认每 10 秒查一次任务状态）
- `--timeout 1800`（默认 30 分钟）

流程：脚本调 `/file-urls/batch` 拿预签名上传 URL → PUT 上传每份 PDF → 轮询 `/extract-results/batch/{batch_id}` → 下载 zip → 解压到 `corpus/markdown/<software>/<doc>/auto/`（与本地 minerU 输出布局完全一致）。

### API 常见问题

| 症状 | 处理 |
|---|---|
| `MINERU_API_TOKEN env var is not set` | 见上面"设环境变量"步骤 |
| `urllib.error.HTTPError: 401` | token 过期或拼错；去 apiManage 重新生成 |
| `urllib.error.HTTPError: 429` | 触发限流；降低并发或加 `--poll-interval` |
| 卡在 `state=running` 很久 | 大文件（几十 MB）正常；调大 `--timeout` 或拆分 `--doc` 单独跑 |
| 某文件 `state=failed` | 看返回里 `err_msg`；通常是 PDF 加密、扫描质量太差、或文件过大（API 单文件有上限，查官方文档当前值） |

API 实时定价、上限、模型版本以 [官方文档](https://mineru.net/apiManage/docs) 为准；本项目代码只依赖 v4 endpoint 的字段，不做配额管理。

## 替换 minerU（用其他 PDF→Markdown 工具）

如果你不想用 minerU——比如想换 [docling](https://github.com/DS4SD/docling)、[marker](https://github.com/VikParuchuri/marker)、商用 API——只要新工具能为每个 `<doc>.pdf` 在 `corpus/markdown/<software>/<doc>/` 下产出：

- `<doc>.md`
- `<doc>_content_list.json`（block 数组，每条至少含 `type`、`page_idx`、`text`，按阅读顺序）

`scripts/02_markdown_to_context.py` 就不用动。详见 [add_new_software.md](add_new_software.md) 末尾"如何换 PDF 引擎"小节。
