"""Build provenance.json — every block in the manual gets one entry mapping
chunk_id → {pdf, page, heading_path, type, preview}.

This file is the foundation of the "资料中无相关内容" rule:
    Skill checks `provenance.json` for keyword matches; absence of a
    matching entry == manual does not cover the topic == refuse.

Reads minerU's <doc>_content_list.json. If you swap PDF engines, ensure
the new engine writes a JSON list of blocks with at minimum:
    [{"type": "text|table|image|equation", "page_idx": <int>, "text": "..."}, ...]
preserving reading order. Other fields are tolerated and ignored.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


def build_provenance(content_list_path: Path, doc_name: str) -> Dict[str, dict]:
    """Read minerU's content_list.json and emit a flat provenance map.

    Schema (per chunk_id, format `<doc>:<seq>`):
        {
          "pdf": "<doc>.pdf",
          "page": <int, 1-indexed>,
          "heading_path": ["Chapter 1", "1.2 Section", ...],
          "type": "text|table|image|equation",
          "preview": "<first 80 chars of text, stripped>"
        }

    TODO (M1): implement. Tests should cover:
      - heading_path tracking as parser walks blocks (text headings update the stack)
      - page_idx 0-indexed in minerU → page 1-indexed in provenance
      - tables/images/equations have type set even if text is empty
    """
    raise NotImplementedError("M0 stub — see TODO in docstring")


def write_provenance(provenance: Dict[str, dict], out_path: Path) -> None:
    """Write provenance.json with stable key order and UTF-8 encoding."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
