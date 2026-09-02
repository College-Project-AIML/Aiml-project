"""Helpers for presenting official scheme destinations safely."""

from urllib.parse import urlparse


def is_direct_scheme_link(link: str | None) -> bool:
    """Return false for a portal homepage, true for a deeper scheme URL."""
    if not link:
        return False
    parsed = urlparse(link.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    path = parsed.path.rstrip("/")
    return bool(path or parsed.query or parsed.fragment)
