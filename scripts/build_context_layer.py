#!/usr/bin/env python3
"""
build_context_layer.py — 从 Markdown 手册生成结构化 Context Layer

用法:
    python scripts/build_context_layer.py --software dakota
    python scripts/build_context_layer.py --software sentaurus

产出 (context_layer/<software>/):
    INDEX.md        — 入口索引 (模块导航树 + 关键词映射)
    module_map.md   — 章节→功能模块映射
    syntax.md       — 命令/参数/关键字语法片段
    task_cards.md   — "如何做 X" 任务卡片
    diagnostics.md  — 错误信息/警告/排障条目
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def parse_args():
    p = argparse.ArgumentParser(description="从 Markdown 手册生成 Context Layer")
    p.add_argument("--software", required=True, help="软件名称 (dakota/sentaurus)")
    p.add_argument("--input-dir", default=None, help="Markdown 输入目录 (默认 corpus/md/<software>)")
    p.add_argument("--output-dir", default=None, help="Context Layer 输出目录 (默认 context_layer/<software>)")
    return p.parse_args()


def read_md_files(md_dir: Path) -> dict[str, str]:
    """读取目录下所有 .md 文件，返回 {文件名: 内容}。"""
    files = {}
    for p in sorted(md_dir.glob("*.md")):
        if p.name.startswith("_"):
            continue
        with open(p, encoding="utf-8") as f:
            files[p.stem] = f.read()
    return files


def extract_headings(content: str) -> list[tuple[int, str]]:
    """提取所有标题，返回 [(层级, 标题文本), ...]"""
    headings = []
    for line in content.splitlines():
        m = re.match(r"^(#{1,6})\s+(.+)", line)
        if m:
            headings.append((len(m.group(1)), m.group(2).strip()))
    return headings


def extract_code_blocks(content: str) -> list[str]:
    """提取所有代码块内容。"""
    blocks = []
    in_block = False
    buf = []
    for line in content.splitlines():
        if line.startswith("```"):
            if in_block:
                blocks.append("\n".join(buf))
                buf = []
                in_block = False
            else:
                in_block = True
        elif in_block:
            buf.append(line)
    return blocks


def extract_tables(content: str) -> list[str]:
    """提取 markdown 表格。"""
    tables = []
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        if re.match(r"^\|.+\|$", lines[i]) and i + 1 < len(lines):
            if re.match(r"^\|[\s\-:|]+\|$", lines[i + 1]):
                table = [lines[i], lines[i + 1]]
                j = i + 2
                while j < len(lines) and re.match(r"^\|.+\|$", lines[j]):
                    table.append(lines[j])
                    j += 1
                tables.append("\n".join(table))
                i = j
                continue
        i += 1
    return tables


def build_index(files: dict[str, str]) -> str:
    """生成 INDEX.md — 模块导航树 + 关键词索引。"""
    parts = ["# INDEX — 模块导航入口\n"]
    parts.append("## 模块导航树\n")

    all_keywords = defaultdict(list)

    for fname, content in files.items():
        headings = extract_headings(content)
        parts.append(f"### [{fname}]({fname}.md)\n")
        for level, title in headings:
            if level <= 3:
                indent = "  " * (level - 1)
                parts.append(f"{indent}- {title}\n")
                # 收集关键词
                for word in re.findall(r"[\w\-]+", title.lower()):
                    if len(word) > 3:
                        all_keywords[word].append(f"{fname} → {title}")

    parts.append("\n## 关键词索引\n")
    for kw in sorted(all_keywords):
        refs = all_keywords[kw]
        if len(refs) <= 5:
            parts.append(f"- **{kw}**: " + " / ".join(refs) + "\n")

    return "".join(parts)


def build_module_map(files: dict[str, str]) -> str:
    """生成 module_map.md — 章节与功能模块对应关系。"""
    parts = ["# Module Map — 模块地图\n"]
    parts.append("将手册章节映射到功能模块，标注模块间的上下游依赖。\n")

    for fname, content in files.items():
        headings = extract_headings(content)
        parts.append(f"## {fname}\n")
        parts.append("| 层级 | 模块/章节 | 说明 |\n")
        parts.append("|------|----------|------|\n")
        for level, title in headings:
            if level <= 3:
                tag = "章节" if level == 1 else ("子模块" if level == 2 else "条目")
                parts.append(f"| H{level} | {title} | {tag} |\n")
        parts.append("\n")

    return "".join(parts)


def build_syntax(files: dict[str, str]) -> str:
    """生成 syntax.md — 语法参考。"""
    parts = ["# Syntax Reference — 语法参考\n"]
    parts.append("提取自手册的命令、参数、关键字语法片段。\n")

    for fname, content in files.items():
        parts.append(f"## {fname}\n")

        # 提取代码块
        blocks = extract_code_blocks(content)
        for i, block in enumerate(blocks, 1):
            parts.append(f"### 语法片段 {i}\n")
            parts.append(f"```\n{block}\n```\n\n")

        # 提取参数表
        tables = extract_tables(content)
        for i, table in enumerate(tables, 1):
            # 只保留看起来像参数定义的表格
            if re.search(r"(参数|param|option|keyword|flag|argument)", table, re.IGNORECASE):
                parts.append(f"### 参数表 {i}\n")
                parts.append(table + "\n\n")

    return "".join(parts)


def build_task_cards(files: dict[str, str]) -> str:
    """生成 task_cards.md — 操作任务卡片。"""
    parts = ["# Task Cards — 任务卡片\n"]
    parts.append('"如何做 X" 类型的操作步骤，按模块分类。\n')

    howto_pattern = re.compile(
        r"(?:^|\n)(?:###?\s+)?(.*?(?:how\s+to|示例|example|usage|使用方法|操作步骤|步骤).*?)(?:\n|$)",
        re.IGNORECASE,
    )

    for fname, content in files.items():
        # 查找 How-to 相关段落
        matches = howto_pattern.findall(content)
        if matches:
            parts.append(f"## {fname}\n")
            for m in matches[:20]:  # 限制每文件最多 20 条
                clean = m.strip()
                if len(clean) > 5:
                    parts.append(f"- {clean}\n")
            parts.append("\n")

    # 如果未提取到内容，按 h2/h3 标题列出骨架
    if len(parts) <= 3:
        for fname, content in files.items():
            headings = extract_headings(content)
            parts.append(f"## {fname}\n")
            for level, title in headings:
                if 2 <= level <= 3:
                    parts.append(f"- {title}\n")
            parts.append("\n")

    return "".join(parts)


def build_diagnostics(files: dict[str, str]) -> str:
    """生成 diagnostics.md — 诊断条目。"""
    parts = ["# Diagnostics — 诊断条目\n"]
    parts.append("错误信息、警告、排障步骤。格式：错误信息 → 原因 → 解决方案。\n")

    error_patterns = [
        (r"(?i)(error|错误|fail|失败|exception|异常|cannot|could\s+not|unable)",
         "错误"),
        (r"(?i)(warning|warn|警告|caution|注意)",
         "警告"),
        (r"(?i)(troubleshoot|诊断|solve|解决|fix|修复|workaround)",
         "排障"),
    ]

    for fname, content in files.items():
        for pattern, category in error_patterns:
            matches = list(re.finditer(pattern, content))
            if matches:
                for m in matches[:10]:  # 限制每文件每类最多 10 条
                    start = max(0, m.start() - 50)
                    end = min(len(content), m.end() + 200)
                    snippet = content[start:end].strip().replace("\n", " ")
                    parts.append(f"- **[{category}]** ({fname}): ...{snippet}...\n")

        if len([p for p in parts if f"({fname})" in p]) == 0:
            parts.append(f"*（{fname} 中未自动识别到诊断条目，需人工补充）*\n")

    return "".join(parts)


def main():
    args = parse_args()
    sw = args.software

    md_dir = Path(args.input_dir) if args.input_dir else PROJECT_ROOT / "corpus" / "md" / sw
    out_dir = Path(args.output_dir) if args.output_dir else PROJECT_ROOT / "context_layer" / sw

    if not md_dir.is_dir():
        print(f"[ERROR] Markdown 目录不存在: {md_dir}")
        sys.exit(1)

    files = read_md_files(md_dir)
    if not files:
        print(f"[WARN] 未在 {md_dir} 中找到 .md 文件")
        sys.exit(0)

    print(f"[INFO] 处理 {len(files)} 个 Markdown 文件 → {out_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)

    builders = {
        "INDEX.md": build_index,
        "module_map.md": build_module_map,
        "syntax.md": build_syntax,
        "task_cards.md": build_task_cards,
        "diagnostics.md": build_diagnostics,
    }

    for fname, builder in builders.items():
        out_path = out_dir / fname
        out_path.write_text(builder(files), encoding="utf-8")
        print(f"  [OK] {fname}")

    print(f"[DONE] Context Layer 生成完成: {out_dir}")


if __name__ == "__main__":
    main()
