"""Detect the best minerU backend for the current host.

Returns one of:
  - "auto"     — let minerU pick (CUDA host; minerU's `hybrid-auto-engine` default)
  - "pipeline" — CPU-only fallback

Decision is intentionally simple: presence of CUDA via PyTorch -> auto, else pipeline.
We do NOT try to detect MPS (macOS) here because minerU's MPS support is
backend-specific; users on Apple silicon should pass --backend explicitly.
"""
from __future__ import annotations


def detect_backend() -> str:
    """Return "auto" if CUDA is available, else "pipeline"."""
    try:
        import torch  # noqa: WPS433 — optional dep, lazy import OK
    except ImportError:
        return "pipeline"
    try:
        if torch.cuda.is_available():
            return "auto"
    except Exception:
        pass
    return "pipeline"


def describe_backend(backend: str) -> str:
    """Human-readable one-liner for logging."""
    return {
        "auto": "GPU (CUDA detected; minerU default backend)",
        "pipeline": "CPU pipeline (no CUDA / fallback)",
        "vlm-transformers": "GPU vlm-transformers (forced)",
        "hybrid-auto-engine": "GPU hybrid-auto-engine (forced)",
    }.get(backend, backend)
