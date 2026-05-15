"""Split a PDF into chunks of at most `max_pages` pages.

minerU's cloud API limits a single uploaded file to 200 pages. Several of
our manuals (Dakota at 347, Sentaurus sdevice_ug at 1530) exceed that, so
01_pdf_to_markdown.py transparently pre-splits them. The split parts get
re-merged into a single markdown after the API returns — callers downstream
(02_markdown_to_context.py) only ever see the merged output.

Needs pypdf (already a minerU dependency, so it's in the conda env).
"""
from __future__ import annotations

from pathlib import Path


def split_pdf(src: Path, dst_dir: Path, max_pages: int) -> list[tuple[Path, int]]:
    """Split `src` into `dst_dir/<stem>_partNN.pdf` chunks of <= max_pages pages.

    Returns `[(part_path, page_count), ...]`. If `src` already fits in
    `max_pages` (or `max_pages <= 0`), returns `[(src, page_count)]` without
    writing anything.

    Existing part files are overwritten.
    """
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(str(src))
    n_pages = len(reader.pages)
    if max_pages <= 0 or n_pages <= max_pages:
        return [(src, n_pages)]

    dst_dir.mkdir(parents=True, exist_ok=True)
    num_parts = (n_pages + max_pages - 1) // max_pages
    width = max(2, len(str(num_parts)))
    parts: list[tuple[Path, int]] = []
    for i in range(num_parts):
        start = i * max_pages
        end = min((i + 1) * max_pages, n_pages)
        writer = PdfWriter()
        for page in reader.pages[start:end]:
            writer.add_page(page)
        out = dst_dir / f"{src.stem}_part{i + 1:0{width}d}.pdf"
        with open(out, "wb") as fh:
            writer.write(fh)
        parts.append((out, end - start))
    return parts
