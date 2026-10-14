"""
Serve the built React frontend (frontend/dist) from server.py. Stdlib only.

Content types are hardcoded, not taken from `mimetypes`: on Windows, mimetypes
reads the registry and can return text/plain for .js, and browsers refuse to
run a module script served as text/plain.
"""
import os

DIST = os.path.realpath(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist"))

_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
}


def built():
    return os.path.isfile(os.path.join(DIST, "index.html"))


def resolve(url_path):
    """Return (bytes, content_type) for a file inside DIST, else None.
    Rejects anything that resolves outside DIST (path traversal)."""
    rel = url_path.split("?")[0].lstrip("/") or "index.html"
    full = os.path.realpath(os.path.join(DIST, rel))
    if not full.startswith(DIST + os.sep) or not os.path.isfile(full):
        return None
    ctype = _TYPES.get(os.path.splitext(full)[1].lower(), "application/octet-stream")
    with open(full, "rb") as f:
        return f.read(), ctype