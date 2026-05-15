"""Build context_layer/<software>/ from corpus/markdown/<software>/.

Reads (per doc):  corpus/markdown/<software>/<doc>/<backend>/<doc>.md
                  corpus/markdown/<software>/<doc>/<backend>/<doc>_content_list.json
Writes:           context_layer/<software>/index.md                    (aggregator)
                  context_layer/<software>/<doc>/index.md
                  context_layer/<software>/<doc>/module_map.md         (auto)
                  context_layer/<software>/<doc>/provenance.json       (auto)
                  context_layer/<software>/<doc>/task_cards/_TODO.md   (placeholder)
                  context_layer/<software>/<doc>/syntax/_TODO.md       (placeholder)
                  context_layer/<software>/<doc>/diagnostics/_TODO.md  (placeholder)

This script is **decoupled from minerU**: it only reads the two JSON+MD files
above. Swapping minerU for another PDF→markdown engine requires no changes
here as long as the engine writes those files at the same paths.

Examples:
    python scripts/02_markdown_to_context.py --software dakota
    python scripts/02_markdown_to_context.py --software sentaurus
    python scripts/02_markdown_to_context.py --software dakota --doc dakota_Users-6.16.0
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--software",
        required=True,
        help="Software name. Must match a subdirectory of corpus/markdown/.",
    )
    parser.add_argument(
        "--doc",
        default=None,
        help="Optional: process a single doc (subdirectory name). Default: all docs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written without writing anything.",
    )
    return parser.parse_args()


def find_doc_artifacts(doc_dir: Path) -> tuple[Path | None, Path | None]:
    """Locate the .md and _content_list.json under a doc dir.

    minerU nests outputs under <backend>/ (e.g. auto/, pipeline/, vlm/).
    We glob for the first matching pair, ignoring backend name.

    Returns (md_path, content_list_path) or (None, None) if not found.
    """
    md_candidates = list(doc_dir.rglob("*.md"))
    md = next((p for p in md_candidates if not p.name.startswith("_")), None)
    if md is None:
        return None, None
    content_list = md.with_name(md.stem + "_content_list.json")
    return (md, content_list if content_list.exists() else None)


def write_placeholders(doc_out: Path, doc_name: str, dry_run: bool) -> None:
    """Create _TODO.md placeholder files for the curated layers."""
    placeholders = {
        "task_cards/_TODO.md": (
            f"# Task cards for {doc_name} — TODO\n\n"
            "This directory will hold curated 'how to do X' cards extracted "
            "from the user manual. M2 work — see docs/skill_authoring.md.\n"
        ),
        "syntax/_TODO.md": (
            f"# Syntax / keyword reference for {doc_name} — TODO\n\n"
            "One file per command/keyword/section. M2 work — see "
            "docs/skill_authoring.md.\n"
        ),
        "diagnostics/_TODO.md": (
            f"# Error / warning lookup for {doc_name} — TODO\n\n"
            "One file per symptom string. M2 work — see "
            "docs/skill_authoring.md.\n"
        ),
    }
    for rel, body in placeholders.items():
        target = doc_out / rel
        if dry_run:
            print(f"[dry-run] write {target}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")


def process_doc(doc_dir: Path, software: str, dry_run: bool) -> bool:
    """Process one doc directory. Returns True on success."""
    doc_name = doc_dir.name
    md_path, content_list_path = find_doc_artifacts(doc_dir)
    if md_path is None:
        print(f"[skip] {doc_name}: no .md found under {doc_dir}", file=sys.stderr)
        return False

    doc_out = REPO_ROOT / "context_layer" / software / doc_name
    print(f"[run] {software}/{doc_name}: md={md_path.relative_to(REPO_ROOT)}")

    # M0 stub: write placeholders + a minimal index.md per doc.
    # M1 will plug in: parse_headings → render_module_map, build_provenance → write_provenance.
    if not dry_run:
        doc_out.mkdir(parents=True, exist_ok=True)
        (doc_out / "index.md").write_text(
            f"# {doc_name}\n\n"
            f"Source: `corpus/raw/{software}/{doc_name}.pdf`\n\n"
            f"Markdown: `{md_path.relative_to(REPO_ROOT)}`\n\n"
            "- `module_map.md` — chapter tree (M1: auto-generated; M0: not yet)\n"
            "- `provenance.json` — chunk → PDF page (M1)\n"
            "- `task_cards/`, `syntax/`, `diagnostics/` — curated layers (M2)\n",
            encoding="utf-8",
        )
        # Module map and provenance are M1 stubs in lib/ — will raise if called.
        # Skip silently in M0; the placeholder _TODO.md still gets written.
    write_placeholders(doc_out, doc_name, dry_run)
    return True


def write_software_index(software: str, doc_names: list[str], dry_run: bool) -> None:
    """Top-level context_layer/<software>/index.md aggregating all docs."""
    out = REPO_ROOT / "context_layer" / software / "index.md"
    body_lines = [
        f"# {software}\n",
        "",
        f"Registered software in `software_usermanual_context`. {len(doc_names)} document(s).\n",
        "",
        "## Documents\n",
        "",
    ]
    for name in sorted(doc_names):
        body_lines.append(f"- [`{name}/`](./{name}/index.md)")
    body = "\n".join(body_lines) + "\n"
    if dry_run:
        print(f"[dry-run] write {out}")
        print(body)
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")


def main() -> int:
    args = parse_args()

    md_dir = REPO_ROOT / "corpus" / "markdown" / args.software
    if not md_dir.exists():
        print(
            f"[error] {md_dir} does not exist. "
            "Run scripts/01_pdf_to_markdown.py first.",
            file=sys.stderr,
        )
        return 2

    if args.doc:
        doc_dirs = [md_dir / args.doc]
        if not doc_dirs[0].exists():
            print(f"[error] {doc_dirs[0]} not found.", file=sys.stderr)
            return 2
    else:
        doc_dirs = sorted(p for p in md_dir.iterdir() if p.is_dir())

    if not doc_dirs:
        print(f"[error] no doc subdirectories under {md_dir}", file=sys.stderr)
        return 2

    processed: list[str] = []
    for d in doc_dirs:
        if process_doc(d, args.software, args.dry_run):
            processed.append(d.name)

    if processed:
        write_software_index(args.software, processed, args.dry_run)
        print(f"[done] {len(processed)} doc(s) processed for {args.software}")
        return 0
    print(f"[error] no docs processed for {args.software}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
