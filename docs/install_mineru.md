# 安装 minerU

[minerU](https://github.com/opendatalab/MinerU) 是 OpenDataLab 出的 PDF→Markdown 工具，本项目用它把官方手册转成可后处理的 markdown。本文给 Windows 用户写；macOS/Linux 用户大体一致，差异在 GPU 配置。

## 先决条件

- Python ≥ 3.10（推荐 3.11/3.12）
- 16 GB RAM 起步（处理 4 MB Dakota 手册够用；77 MB 的 Sentaurus 30 份建议 32 GB）
- 磁盘 ≥ 5 GB（minerU 首次跑会下载 1–3 GB 模型）

## 1. 装 Python 包

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

## 2. 模型下载（首次运行会自动下）

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

## 3. 烟测

随便找个小 PDF 跑一遍，确认环境通：

```bash
mineru -p some_test.pdf -o ./_test_out -b pipeline
```

参数说明：
- `-p` 输入文件或目录
- `-o` 输出目录
- `-b pipeline` 强制 CPU 后端（首次烟测最稳）；GPU 环境可省略让 minerU 自选

成功的标志：`./_test_out/some_test/<backend>/some_test.md` 存在且非空，同目录有 `some_test_content_list.json`。

## 4. 与本仓库脚本配合

确认 `mineru` 在 PATH 后，回到仓库根目录跑：

```bash
python scripts/01_pdf_to_markdown.py --software dakota --dry-run
```

不报错且能列出 PDF 文件名即可。脱掉 `--dry-run` 就会真跑。后端选择由 `scripts/lib/backend_detect.py` 自动决定（有 CUDA 就用 GPU，没有就 pipeline）。

## 常见问题

| 症状 | 处理 |
|---|---|
| `mineru: command not found` | pip 装的是当前 Python 环境，确认 PATH 里有 `Scripts/`（Windows）或 `bin/`（Unix） |
| 首次跑卡在下载模型 | 设 `MINERU_MODEL_SOURCE=modelscope`；或挂梯子 |
| `CUDA out of memory` | 加 `-b pipeline` 退回 CPU；或换更小批次 |
| Sentaurus 跑了几小时 | 正常；30 个 PDF CPU 估算 4–10 小时。建议 GPU |

## 替换 minerU

如果你不想用 minerU——比如想换 [docling](https://github.com/DS4SD/docling)、[marker](https://github.com/VikParuchuri/marker)、商用 API——只要新工具能为每个 `<doc>.pdf` 在 `corpus/markdown/<software>/<doc>/` 下产出：

- `<doc>.md`
- `<doc>_content_list.json`（block 数组，每条至少含 `type`、`page_idx`、`text`，按阅读顺序）

`scripts/02_markdown_to_context.py` 就不用动。详见 [add_new_software.md](add_new_software.md) 末尾"如何换 PDF 引擎"小节。
