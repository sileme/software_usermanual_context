"""Convert one software's user-manual PDFs to Markdown via minerU.

Two engines supported:
  --engine local  (default)  use locally-installed minerU CLI
  --engine api               use the minerU cloud API (mineru.net)
                             needs MINERU_API_TOKEN env var

Reads:  corpus/raw/<software>/*.pdf
Writes: corpus/markdown/<software>/<doc>/<backend>/<doc>.md
        + <doc>_content_list.json + images/   (same layout for both engines)

Local backend defaults to `auto`: GPU if CUDA is detected, else CPU pipeline.
API model defaults to vlm unless --backend pipeline is passed.

Examples:
    python scripts/01_pdf_to_markdown.py --software dakota
    python scripts/01_pdf_to_markdown.py --software sentaurus --doc sdevice_ug
    python scripts/01_pdf_to_markdown.py --software sentaurus --backend pipeline
    python scripts/01_pdf_to_markdown.py --software dakota --engine api
    python scripts/01_pdf_to_markdown.py --software dakota --dry-run

minerU is imported lazily — `--help` and `--dry-run` work without it installed.
See docs/install_mineru.md for setup (both local install and API token).
"""
from __future__ import annotations

import argparse
import os
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
        help="Software name. Must match a subdirectory of corpus/raw/.",
    )
    parser.add_argument(
        "--doc",
        default=None,
        help="Optional: process a single PDF (filename stem, no .pdf). Default: all PDFs.",
    )
    parser.add_argument(
        "--engine",
        default="local",
        choices=["local", "api"],
        help="local = invoke locally-installed mineru CLI; api = call mineru.net cloud API "
             "(needs MINERU_API_TOKEN). Default: local.",
    )
    parser.add_argument(
        "--backend",
        default="auto",
        choices=["auto", "pipeline", "vlm-transformers", "hybrid-auto-engine"],
        help="local engine: minerU backend ('auto' = GPU if CUDA else pipeline). "
             "api engine: 'pipeline' maps to model_version=pipeline, anything else to vlm. "
             "Default: auto.",
    )
    parser.add_argument(
        "--lang",
        default="en",
        help="Document language hint passed to minerU. Default: en.",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=10,
        help="API engine only: seconds between batch-status polls. Default: 10.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="API engine only: max seconds to wait for a batch. Default: 1800 (30 min).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would run without invoking minerU.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    raw_dir = REPO_ROOT / "corpus" / "raw" / args.software
    out_dir = REPO_ROOT / "corpus" / "markdown" / args.software

    if not raw_dir.exists():
        print(f"[error] {raw_dir} does not exist. Place PDFs there first.", file=sys.stderr)
        return 2

    if args.doc:
        pdfs = [raw_dir / f"{args.doc}.pdf"]
        if not pdfs[0].exists():
            print(f"[error] {pdfs[0]} not found.", file=sys.stderr)
            return 2
    else:
        pdfs = sorted(raw_dir.glob("*.pdf"))

    if not pdfs:
        print(f"[error] no PDFs under {raw_dir}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(f"[dry-run] engine={args.engine} would process {len(pdfs)} file(s) into {out_dir}/")
        for pdf in pdfs:
            print(f"  - {pdf.name}")
        if args.engine == "local":
            print(f"[dry-run] backend={args.backend} lang={args.lang}")
        else:
            model = "pipeline" if args.backend == "pipeline" else "vlm"
            tok_set = "yes" if os.environ.get("MINERU_API_TOKEN") else "NO (will fail)"
            print(f"[dry-run] api model_version={model} token_set={tok_set} "
                  f"poll={args.poll_interval}s timeout={args.timeout}s")
        return 0

    if args.engine == "api":
        from lib.mineru_api import MineruAPIError, run_api_pipeline
        model = "pipeline" if args.backend == "pipeline" else "vlm"
        print(f"[info] engine=api model_version={model} count={len(pdfs)}")
        try:
            return run_api_pipeline(
                pdfs,
                out_dir,
                model_version=model,
                poll_interval=args.poll_interval,
                timeout=args.timeout,
            )
        except MineruAPIError as exc:
            print(f"[error] minerU API: {exc}", file=sys.stderr)
            return 4

    # --engine local: lazy imports — only needed when actually running.
    from lib.backend_detect import detect_backend, describe_backend
    from lib.mineru_runner import is_mineru_available, run_mineru_cli

    if not is_mineru_available():
        print(
            "[error] minerU CLI not found on PATH. "
            "See docs/install_mineru.md (option A — local install), "
            "or use --engine api.",
            file=sys.stderr,
        )
        return 3

    backend = detect_backend() if args.backend == "auto" else args.backend
    print(f"[info] engine=local backend={backend} ({describe_backend(backend)})")
    print(f"[info] processing {len(pdfs)} file(s) → {out_dir}/")

    rc = 0
    for pdf in pdfs:
        print(f"[run] {pdf.name}")
        code = run_mineru_cli(pdf, out_dir, backend=backend, lang=args.lang)
        if code != 0:
            print(f"[warn] {pdf.name} exited with code {code}", file=sys.stderr)
            rc = code
    return rc


if __name__ == "__main__":
    sys.exit(main())
