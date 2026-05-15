"""Client for the minerU cloud API (https://mineru.net/api/v4/...).

Async/job-based flow (different from the local CLI):
  1. POST /file-urls/batch  -> get one pre-signed upload URL per file + batch_id
  2. PUT each PDF to its pre-signed URL (no auth header, body is raw bytes,
     and NO Content-Type — minerU's URLs are signed without one)
  3. Poll GET /extract-results/batch/{batch_id} until every file is state=done
  4. Download each `full_zip_url` and unpack into corpus/markdown/<software>/<doc>/

The downloaded zip has a FLAT layout (not the `auto/<doc>.md` we initially
assumed): `full.md`, `<uuid>_content_list.json`, `<uuid>_content_list_v2.json`,
`<uuid>_model.json`, `<uuid>_origin.pdf`, `images/<hash>.jpg`. `markdown_merge.py`
normalises that into local-minerU style — `<doc>/auto/<doc>.md` +
`<doc>_content_list.json` — so `scripts/02_markdown_to_context.py` doesn't
care whether the markdown came from local minerU or the API.

The API also caps each uploaded file at 200 pages. PDFs longer than that
are pre-split by `pdf_split.py` into `<stem>_partNN.pdf`; each part is
uploaded individually, and the resulting markdowns are merged back with
`page_idx` rebased to the original PDF's page numbering.

Auth: token in the `MINERU_API_TOKEN` environment variable. Get one at
https://mineru.net/apiManage (login required).

This module uses only Python stdlib (urllib + http.client + json + zipfile)
— no `requests` dep.
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
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body_text = _safe_read_error(exc)
        raise MineruAPIError(
            f"POST {path} -> HTTP {exc.code} {exc.reason}: {body_text}"
        ) from exc


def _get_json(path: str) -> dict:
    req = urllib.request.Request(
        BASE_URL + path,
        headers={"Authorization": f"Bearer {_token()}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body_text = _safe_read_error(exc)
        raise MineruAPIError(
            f"GET {path} -> HTTP {exc.code} {exc.reason}: {body_text}"
        ) from exc


def _safe_read_error(exc: urllib.error.HTTPError) -> str:
    """Best-effort read of the error response body for diagnostics."""
    try:
        raw = exc.read()
    except Exception:
        return "<no body>"
    try:
        return raw.decode("utf-8", errors="replace")[:2000]
    except Exception:
        return repr(raw[:2000])


def _put_file(url: str, path: Path) -> None:
    """PUT a file to a pre-signed URL.

    minerU/OSS signs the URL WITHOUT a Content-Type header. urllib.request,
    however, auto-injects `Content-Type: application/x-www-form-urlencoded`
    whenever a PUT/POST has a body — this changes the StringToSign that OSS
    re-computes server-side, producing HTTP 403 SignatureDoesNotMatch.

    We therefore drop down to http.client so we control headers exactly:
    only `Content-Length` is sent (required by HTTP/1.1), no Content-Type,
    no Authorization (the signature lives in the URL query string).
    """
    import http.client
    from urllib.parse import urlsplit

    parts = urlsplit(url)
    host = parts.hostname
    if host is None:
        raise MineruAPIError(f"bad presigned URL (no host): {url[:120]}...")
    port = parts.port or (443 if parts.scheme == "https" else 80)
    selector = parts.path + (f"?{parts.query}" if parts.query else "")
    data = path.read_bytes()

    conn_cls = http.client.HTTPSConnection if parts.scheme == "https" else http.client.HTTPConnection
    conn = conn_cls(host, port, timeout=300)
    try:
        conn.putrequest("PUT", selector, skip_accept_encoding=True)
        conn.putheader("Content-Length", str(len(data)))
        conn.endheaders()
        conn.send(data)
        resp = conn.getresponse()
        body = resp.read()
        if resp.status not in (200, 204):
            text = body.decode("utf-8", errors="replace")[:2000]
            raise MineruAPIError(
                f"PUT {path.name} -> HTTP {resp.status} {resp.reason}: {text}"
            )
    finally:
        conn.close()


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

    The zip's layout is flat: `full.md`, `<uuid>_content_list.json`, `images/`.
    Extracting into `.parts/<doc>/<part_stem>/` therefore yields
    `.parts/<doc>/<part_stem>/full.md` etc. — `markdown_merge.merge_parts`
    then normalises this into `<doc>/auto/<doc>.md`.
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
    max_pages_per_file: int = 0,
) -> int:
    """End-to-end API call for a list of PDFs. Returns 0 on success, nonzero on partial failure.

    For each PDF `foo.pdf` ≤ `max_pages_per_file` pages (or if max_pages_per_file<=0),
    the result is unpacked into `out_dir/foo/`, yielding `out_dir/foo/auto/foo.md` etc.

    PDFs longer than the limit are pre-split into `<stem>_partNN.pdf`, each part
    is sent to the API individually, and the resulting markdowns are merged back
    into `out_dir/foo/auto/foo.md` (with `page_idx` rebased to the original PDF).
    Per-part artefacts live under `out_dir/.parts/foo/<part_stem>/` and are
    preserved for debugging / re-merge.
    """
    if not pdf_paths:
        return 0

    from lib.pdf_split import split_pdf
    from lib.markdown_merge import merge_parts

    # 1. Split (or pass through). part_records[i] = (orig_pdf, [(part_path, page_count), ...])
    part_records: list[tuple[Path, list[tuple[Path, int]]]] = []
    upload_list: list[Path] = []
    for pdf in pdf_paths:
        parts_dir = out_dir / ".parts" / pdf.stem
        parts = split_pdf(pdf, parts_dir, max_pages=max_pages_per_file)
        if len(parts) > 1:
            print(f"[split] {pdf.name}: {len(parts)} parts (<={max_pages_per_file} pages each)")
        part_records.append((pdf, parts))
        for part_path, _ in parts:
            upload_list.append(part_path)

    # 2. Upload all parts together as one batch.
    print(f"[api] uploading {len(upload_list)} file(s) (model_version={model_version})")
    batch_id = upload_pdfs(upload_list, model_version=model_version)
    results = poll_batch(batch_id, poll_interval=poll_interval, timeout=timeout)
    by_name = {r.get("file_name"): r for r in results}

    # 3. Download per part, then merge (always — merge handles single-part too
    #    so the API zip's flat layout gets normalised to <doc>/auto/<doc>.md).
    rc = 0
    for pdf, parts in part_records:
        part_roots: list[Path] = []
        part_pages: list[int] = []
        ok = True
        for part_path, page_count in parts:
            r = by_name.get(part_path.name)
            if r is None:
                print(f"[api] {part_path.name}: missing from results", flush=True)
                rc = 1
                ok = False
                continue
            if r.get("state") != "done":
                print(f"[api] {part_path.name}: state={r.get('state')} err={r.get('err_msg')}")
                rc = 1
                ok = False
                continue
            zip_url = r.get("full_zip_url")
            if not zip_url:
                print(f"[api] {part_path.name}: no full_zip_url in result")
                rc = 1
                ok = False
                continue
            # Always stage parts under .parts/<doc>/<part_stem>/ — keeps the
            # final <doc>/ clean for the merged output.
            target = out_dir / ".parts" / pdf.stem / part_path.stem
            print(f"[api] {part_path.name}: download -> {target}")
            download_and_extract(zip_url, target)
            part_roots.append(target)
            part_pages.append(page_count)

        if ok and part_roots:
            merge_target = out_dir / pdf.stem
            label = "merge" if len(part_roots) > 1 else "normalize"
            print(f"[{label}] {pdf.name}: {len(part_roots)} part(s) -> "
                  f"{merge_target}/auto/{pdf.stem}.md")
            merge_parts(part_roots, part_pages, merge_target, pdf.stem)
    return rc
