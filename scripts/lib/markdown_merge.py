"""Merge minerU per-part outputs back into a single doc.

minerU's cloud-API zips actually have a *flat* layout (not the nested
`auto/<doc>.md` we initially assumed):

    <part_root>/
        full.md
        <uuid>_content_list.json
        <uuid>_content_list_v2.json
        <uuid>_model.json
        <uuid>_origin.pdf
        images/<hash>.jpg

This module normalises that into the local-minerU style and stitches
multiple parts together. Output written under `target_dir`:

    <target_dir>/auto/<doc_name>.md
    <target_dir>/auto/<doc_name>_content_list.json
    <target_dir>/auto/images/<part_stem>_<orig>.{png,jpg,...}

`page_idx` in the content-list JSON is rebased to the *original* PDF's
page numbering by adding the cumulative offset of preceding parts.
Image paths inside both the markdown body and the content-list are
rewritten to point at the prefixed filenames under the merged
`images/` directory.

When only one part is given (PDF didn't need splitting), this still
runs — it just normalises naming without any cross-part shifting.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


def _find_md(part_root: Path) -> Path:
    """Locate the main markdown file inside a downloaded part."""
    candidates = [part_root / "full.md"]
    candidates += [p for p in part_root.glob("*.md") if not p.name.startswith("_")]
    for c in candidates:
        if c.is_file():
            return c
    raise FileNotFoundError(f"no .md inside {part_root}")


def _find_content_list(part_root: Path) -> Path | None:
    """Locate the content-list JSON inside a downloaded part.

    Prefers `*_content_list.json` over the `_v2` variant (v2 has a different
    schema we don't read). Returns None if no content list is present.
    """
    primary = sorted(part_root.glob("*_content_list.json"))
    primary = [p for p in primary if "_v2" not in p.name]
    if primary:
        return primary[0]
    v2 = sorted(part_root.glob("*_content_list*.json"))
    return v2[0] if v2 else None


def merge_parts(
    part_roots: list[Path],
    part_page_counts: list[int],
    target_dir: Path,
    doc_name: str,
) -> None:
    """Merge multiple minerU part outputs into a single doc under `target_dir`.

    `part_roots[i]` is the root directory of part i (containing full.md etc.).
    `part_page_counts[i]` is the page count of part i in the *original* PDF
    (used to advance the page_idx offset between parts).

    Writes:
        <target_dir>/auto/<doc_name>.md
        <target_dir>/auto/<doc_name>_content_list.json
        <target_dir>/auto/images/<part_stem>_<file>
    """
    if len(part_roots) != len(part_page_counts):
        raise ValueError("part_roots and part_page_counts must have the same length")

    target_auto = target_dir / "auto"
    target_auto.mkdir(parents=True, exist_ok=True)
    target_imgs = target_auto / "images"
    target_imgs.mkdir(exist_ok=True)

    md_chunks: list[str] = []
    content_chunks: list[dict] = []
    page_offset = 0

    for part_root, page_count in zip(part_roots, part_page_counts):
        part_stem = part_root.name
        md_path = _find_md(part_root)
        md_text = md_path.read_text(encoding="utf-8")

        part_imgs = part_root / "images"
        if part_imgs.is_dir():
            for img in part_imgs.iterdir():
                if img.is_file():
                    new_name = f"{part_stem}_{img.name}"
                    shutil.copy2(img, target_imgs / new_name)

        # Rewrite image refs inside the markdown body: `images/foo.jpg` → `images/<part>_foo.jpg`.
        md_text = re.sub(
            r"(images/)([^\s)\"']+)",
            lambda m: f"{m.group(1)}{part_stem}_{m.group(2)}",
            md_text,
        )
        md_chunks.append(md_text.strip())

        cl_path = _find_content_list(part_root)
        if cl_path is not None:
            try:
                blocks = json.loads(cl_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                blocks = []
            if isinstance(blocks, list):
                for block in blocks:
                    if isinstance(block, dict):
                        if isinstance(block.get("page_idx"), int):
                            block["page_idx"] += page_offset
                        img_path = block.get("img_path")
                        if isinstance(img_path, str) and img_path:
                            fname = img_path.rsplit("/", 1)[-1]
                            block["img_path"] = f"images/{part_stem}_{fname}"
                content_chunks.extend(blocks)

        page_offset += page_count

    (target_auto / f"{doc_name}.md").write_text(
        "\n\n".join(md_chunks) + "\n", encoding="utf-8"
    )
    (target_auto / f"{doc_name}_content_list.json").write_text(
        json.dumps(content_chunks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
