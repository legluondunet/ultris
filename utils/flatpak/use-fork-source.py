#!/usr/bin/env python3
"""Use the checked-out fork sources with Flathub's Lutris packaging manifest."""

import json
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
updated, count = re.subn(
    pattern, r"\g<1>      - type: dir\n        path: lutris-source\n", source
)
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

# DOSBox Staging's optional FluidSynth fallback tries to download a source
# archive from inside Flatpak's network-isolated build sandbox.
dosbox_module = "  - name: dosbox-staging\n    buildsystem: meson\n"
if updated.count(dosbox_module) != 1:
    sys.exit("Expected exactly one DOSBox Staging module")
updated = updated.replace(
    dosbox_module,
    "  - name: dosbox-staging\n    buildsystem: meson\n"
    "    config-opts:\n      - -Duse_fluidsynth=false\n      - -Duse_slirp=false\n",
    1,
)

# The Flathub shared module installs Ayatana Ido in lib64 by default.
# Its dependent libayatana-indicator module searches /app/lib instead.
ayatana_manifest = (
    manifest.parent / "shared-modules/libayatana-appindicator/libayatana-appindicator-gtk3.json"
)
ayatana = json.loads(ayatana_manifest.read_text())


def fix_ayatana_libraries(value):
    if isinstance(value, dict):
        if value.get("name") in ("ayatana-ido", "libayatana-ido", "libayatana-indicator"):
            opts = value.setdefault("config-opts", [])
            if "-DCMAKE_INSTALL_LIBDIR=lib" not in opts:
                opts.append("-DCMAKE_INSTALL_LIBDIR=lib")
            return 1
        return sum(fix_ayatana_libraries(child) for child in value.values())
    if isinstance(value, list):
        return sum(fix_ayatana_libraries(child) for child in value)
    return 0


if fix_ayatana_libraries(ayatana) != 2:
    sys.exit("Expected Ayatana Ido and Indicator modules in shared packaging")
ayatana_manifest.write_text(json.dumps(ayatana, indent=2) + "\n")

manifest.write_text(updated)
print("Flathub manifest now builds the fork with GLU and Ayatana libraries in /app/lib.")

