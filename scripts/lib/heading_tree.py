"""Parse a Markdown file's heading hierarchy into a tree.

Powers `module_map.md` generation in 02_markdown_to_context.py.

Usage:
    root = parse_headings(Path("foo.md"))
    md = render_module_map(root, doc_name="foo", anchor_prefix="../../corpus/markdown/sw/foo/foo.md")
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

# NOTE (M0 stub): this module's functions raise NotImplementedError.
# Implementation is M1 work, after the user runs minerU and we have real .md files
# to test against. The stubs document the intended contract.


HEADING_PATTERN = r"^(#{1,6})\s+(.+?)\s*$"


@dataclass
class HeadingNode:
    """One heading. Level 0 is a virtual root."""
    level: int
    title: str
    line: int  # 1-indexed line number in the source .md
    children: List["HeadingNode"] = field(default_factory=list)


def parse_headings(md_path: Path) -> HeadingNode:
    """Return a virtual root (level=0, title="") whose children are the H1s.

    Must skip headings inside fenced code blocks (``` ... ```).

    TODO (M1): implement. Tests should cover:
      - nested headings (H1 > H2 > H3)
      - heading-like text inside ``` blocks is ignored
      - skipped levels (H1 then H3) are tolerated (H3 attaches to nearest ancestor)
    """
    raise NotImplementedError("M0 stub — see TODO in docstring")


def render_module_map(root: HeadingNode, doc_name: str, anchor_prefix: str = "") -> str:
    """Render the heading tree as a nested-bullet markdown document.

    Each leaf links to `<anchor_prefix>#<slug>` so the user can click through
    to the source markdown (or PDF page if anchor_prefix points at provenance).

    TODO (M1): implement.
    """
    raise NotImplementedError("M0 stub — see TODO in docstring")
