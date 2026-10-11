#!/usr/bin/env python3
"""Use the checked-out fork sources with Flathub's Lutris packaging manifest."""
import re
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
source = manifest.read_text()
pattern = (
    r"(  # Lutris app with dependencies\n"
    r"  - name: lutris\n"
    r"    buildsystem: meson\n"
    r"    sources:\n)"
    r"      - type: git\n"
    r"        url: https://github.com/lutris/lutris.git\n"
    r"        commit: [0-9a-f]+\n"
)
updated, count = re.subn(pattern, r"\g<1>      - type: dir\n        path: lutris-source\n", source)
if count != 1:
    sys.exit(f"Expected exactly one upstream Lutris source entry; found {count}")
manifest.write_text(updated)
print("Flathub manifest now builds the checked-out fork sources.")
