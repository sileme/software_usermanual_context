"""Thin wrapper around the minerU CLI.

We shell out to `mineru` rather than importing the Python API so that:
  - the wrapper survives minerU version upgrades that only affect the API,
  - users can drop in any other CLI that respects the same -p/-o contract.

If you swap minerU for a different PDF→markdown engine, the contract that
must hold for the rest of the pipeline (02_markdown_to_context.py) is:

    For each input <doc>.pdf, the engine MUST produce, somewhere under
    <output_dir>/<doc>/, the two files:
        <doc>.md
        <doc>_content_list.json   (minerU schema: list of blocks with
                                   {type, page_idx, text, ...} preserving
                                   reading order)
    Images may be placed under any subdirectory, referenced from <doc>.md
    by relative path.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def is_mineru_available() -> bool:
    """True iff `mineru --version` is on PATH and exits 0."""
    try:
        return subprocess.call(
            ["mineru", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ) == 0
    except (FileNotFoundError, OSError):
        return False


def run_mineru_cli(
    input_path: Path,
    output_dir: Path,
    backend: str = "auto",
    lang: str = "en",
) -> int:
    """Run `mineru -p input_path -o output_dir [-b backend] -l lang`.

    Returns the subprocess exit code (0 = success).
    `backend="auto"` omits the -b flag and lets minerU pick its default
    (currently hybrid-auto-engine when GPU is available).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["mineru", "-p", str(input_path), "-o", str(output_dir), "-l", lang]
    if backend != "auto":
        cmd += ["-b", backend]
    return subprocess.call(cmd)
