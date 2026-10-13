"""Build provenance, available without Git at runtime."""

import re
from pathlib import Path


def get_display_version(version: str) -> str:
    """Append the short packaged source revision when one is available."""
    try:
        commit = Path(__file__).with_name("build_commit.txt").read_text(encoding="ascii").strip()
    except (OSError, UnicodeError):
        return version
    if not re.fullmatch(r"[0-9a-fA-F]{7,64}", commit):
        return version
    return f"{version} (commit {commit[:7].lower()})"
