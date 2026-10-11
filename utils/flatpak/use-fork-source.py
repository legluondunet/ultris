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
# GLU's Meson default installs glu.pc under /app/lib64/pkgconfig,
# but the subsequent mesa-demos module looks for it under /app/lib/pkgconfig.
glu_module = "  - name: glu\n    buildsystem: meson\n"
if updated.count(glu_module) != 1:
    sys.exit("Expected exactly one native GLU module")
updated = updated.replace(
    glu_module,
    "  - name: glu\n    buildsystem: meson\n    config-opts:\n      - --libdir=lib\n",
    1,
)

manifest.write_text(updated)
print("Flathub manifest now builds the fork and installs native GLU under /app/lib.")

