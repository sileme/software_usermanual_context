"""Client for the minerU cloud API (https://mineru.net/api/v4/...).

Async/job-based flow (different from the local CLI):
  1. POST /file-urls/batch  -> get one pre-signed upload URL per file + batch_id
  2. PUT each PDF to its pre-signed URL (no auth header, body is raw bytes)
  3. Poll GET /extract-results/batch/{batch_id} until every file is state=done
  4. Download each `full_zip_url` and unpack into corpus/markdown/<software>/<doc>/

The unpacked zip mirrors local minerU's output: `auto/<doc>.md`,
`auto/<doc>_content_list.json`, `auto/images/`. So `scripts/02_markdown_to_context.py`
doesn't care whether the markdown came from local minerU or the API.

Auth: token in the `MINERU_API_TOKEN` environment variable. Get one at
https://mineru.net/apiManage (login required).

This module uses only Python stdlib (urllib + json + zipfile) — no requests dep.
"""
from __future__ import annotations

import io
import json
import os
import time
import urllib.request
import urllib.error
import zipfile
from pathlib import Path
from typing import Iterable

BASE_URL = "https://mineru.net/api/v4"
DEFAULT_POLL_INTERVAL = 10  # seconds
DEFAULT_TIMEOUT = 600        # per batch, seconds


class MineruAPIError(RuntimeError):
    pass


def _token() -> str:
    tok = os.environ.get("MINERU_API_TOKEN")
    if not tok:
        raise MineruAPIError(
            "MINERU_API_TOKEN env var is not set. "
            "Get a token at https://mineru.net/apiManage."
        )
    return tok


def _post_json(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        BASE_URL + path,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {_token()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_json(path: str) -> dict:
    req = urllib.request.Request(
        BASE_URL + path,
        headers={"Authorization": f"Bearer {_token()}"},
        method="GET",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _put_file(url: str, path: Path) -> None:
    """PUT a file to a pre-signed URL. No auth header (the signature is in the URL)."""
    data = path.read_bytes()
    req = urllib.request.Request(url, data=data, method="PUT")
    with urllib.request.urlopen(req) as resp:
        if resp.status not in (200, 204):
            raise MineruAPIError(f"upload PUT failed: status={resp.status}")


def request_upload_urls(filenames: list[str], model_version: str = "vlm") -> dict:
    """POST /file-urls/batch — request pre-signed upload URLs for a batch of files.

    Returns the raw API response. On success:
        {
          "code": 0,
          "data": {
            "batch_id": "<id>",
            "file_urls": ["https://...", ...]   # parallel to filenames
          },
          ...
        }
    """
    body = {
        "files": [{"name": name} for name in filenames],
        "model_version": model_version,
    }
    resp = _post_json("/file-urls/batch", body)
    if resp.get("code") != 0:
        raise MineruAPIError(f"file-urls/batch failed: {resp}")
    return resp


def upload_pdfs(pdf_paths: list[Path], model_version: str = "vlm") -> str:
    """Request upload URLs then PUT all files. Returns the batch_id.

    Extraction starts automatically on the server once each PUT completes.
    """
    names = [p.name for p in pdf_paths]
    resp = request_upload_urls(names, model_version=model_version)
    data = resp["data"]
    batch_id = data["batch_id"]
    urls = data["file_urls"]
    if len(urls) != len(pdf_paths):
        raise MineruAPIError(
            f"got {len(urls)} upload URLs for {len(pdf_paths)} files"
        )
    for pdf, url in zip(pdf_paths, urls):
        print(f"[api] upload {pdf.name}")
        _put_file(url, pdf)
    return batch_id


def poll_batch(
    batch_id: str,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    timeout: int = DEFAULT_TIMEOUT,
) -> list[dict]:
    """Poll GET /extract-results/batch/{batch_id} until every file is done or failed.

    Returns the per-file result list. Each entry has at minimum:
        {"file_name": "...", "state": "done|running|failed", "full_zip_url": "..." | None}
    """
    deadline = time.time() + timeout
    while True:
        resp = _get_json(f"/extract-results/batch/{batch_id}")
        if resp.get("code") != 0:
            raise MineruAPIError(f"poll failed: {resp}")
        results = resp["data"].get("extract_result", [])
        states = [r.get("state", "?") for r in results]
        done = sum(1 for s in states if s in ("done", "failed"))
        print(f"[api] batch {batch_id}: {done}/{len(states)} finished ({states})")
        if results and all(s in ("done", "failed") for s in states):
            return results
        if time.time() > deadline:
            raise MineruAPIError(f"batch {batch_id} timed out after {timeout}s")
        time.sleep(poll_interval)


def download_and_extract(zip_url: str, target_dir: Path) -> None:
    """Download a result zip and extract into target_dir (preserving zip structure).

    The zip's top-level layout from minerU API is `auto/<doc>.md`,
    `auto/<doc>_content_list.json`, `auto/images/`. Extracting into
    `corpus/markdown/<software>/<doc>/` therefore yields
    `corpus/markdown/<software>/<doc>/auto/<doc>.md` — same as local minerU.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(zip_url) as resp:
        buf = io.BytesIO(resp.read())
    with zipfile.ZipFile(buf) as zf:
        zf.extractall(target_dir)


def run_api_pipeline(
    pdf_paths: list[Path],
    out_dir: Path,
    model_version: str = "vlm",
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    timeout: int = DEFAULT_TIMEOUT,
) -> int:
    """End-to-end API call for a list of PDFs. Returns 0 on success, nonzero on partial failure.

    For each PDF `foo.pdf`, the result is unpacked into `out_dir/foo/`,
    yielding `out_dir/foo/auto/foo.md` etc. — identical to local minerU layout.
    """
    if not pdf_paths:
        return 0
    batch_id = upload_pdfs(pdf_paths, model_version=model_version)
    results = poll_batch(batch_id, poll_interval=poll_interval, timeout=timeout)

    by_name = {r.get("file_name"): r for r in results}
    rc = 0
    for pdf in pdf_paths:
        r = by_name.get(pdf.name)
        if r is None:
            print(f"[api] {pdf.name}: missing from results", flush=True)
            rc = 1
            continue
        if r.get("state") != "done":
            print(f"[api] {pdf.name}: state={r.get('state')} err={r.get('err_msg')}")
            rc = 1
            continue
        zip_url = r.get("full_zip_url")
        if not zip_url:
            print(f"[api] {pdf.name}: no full_zip_url in result")
            rc = 1
            continue
        target = out_dir / pdf.stem
        print(f"[api] {pdf.name}: download → {target}")
        download_and_extract(zip_url, target)
    return rc
