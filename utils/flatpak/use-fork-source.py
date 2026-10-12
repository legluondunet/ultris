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

# Upgrade the pinned Flathub DOSBox source while preserving the working package.
dosbox_source = (
    "        url: https://github.com/dosbox-staging/dosbox-staging/archive/v0.79.1.tar.gz\n"
    "        sha256: 43f23fd0a5cff55e06a3ba2be8403f872ae47423f3bb4f823301eaae8a39ac2f\n"
)
if updated.count(dosbox_source) != 1:
    sys.exit("Expected exactly one DOSBox Staging 0.79.1 source")
updated = updated.replace(
    dosbox_source,
    "        url: https://github.com/dosbox-staging/dosbox-staging/archive/refs/tags/v0.83.0.tar.gz\n"
    "        sha256: 9b36be5a666784adaeffa560bd0950691f851a76bdb97e7ae3c989561e91caf3\n",
    1,
)

# The 0.79.1 SDL2_net include fix is obsolete: 0.83.0's DOS sources no longer use SDL_net.h.
dosbox_patch = (
    "      # SDL2_net headers are no longer next to SDL2's, libdos needs the dep for SDL_net.h\n"
    "      - type: patch\n"
    "        path: patches/dosbox-staging-libdos-sdl2-net.patch\n"
)
if updated.count(dosbox_patch) != 1:
    sys.exit("Expected exactly one legacy DOSBox SDL2_net patch")
updated = updated.replace(dosbox_patch, "", 1)

# DOSBox 0.83 requires standalone Asio headers. Download them outside the sandbox.
dosbox_dependencies = "    modules:\n      # SDL2_net was dropped from the 26.08 runtime\n"
if updated.count(dosbox_dependencies) != 1:
    sys.exit("Expected exactly one DOSBox dependency list")
updated = updated.replace(
    dosbox_dependencies,
    "    modules:\n"
    "      - name: asio\n"
    "        buildsystem: simple\n"
    "        build-commands:\n"
    "          - cp -a asio/include/. /app/include/\n"
    "          - install -Dm644 asio/LICENSE_1_0.txt /app/share/licenses/asio/LICENSE_1_0.txt\n"
    "        sources:\n"
    "          - type: archive\n"
    "            url: https://github.com/chriskohlhoff/asio/archive/refs/tags/asio-1-30-2.tar.gz\n"
    "            sha256: 755bd7f85a4b269c67ae0ea254907c078d408cce8e1a352ad2ed664d233780e8\n"
    "      # SDL2_net was dropped from the 26.08 runtime\n",
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
    "    config-opts:\n      - -Duse_fluidsynth=false\n      - -Duse_slirp=false\n      - --wrap-mode=nofallback\n",
    1,
)

# Munt otherwise installs mt32emu.pc under /app/lib64/pkgconfig, which
# DOSBox Staging does not search before trying its network-only fallback.
munt_module = "      - name: munt\n        buildsystem: cmake-ninja\n        config-opts:\n"
if updated.count(munt_module) != 1:
    sys.exit("Expected exactly one Munt module")
updated = updated.replace(
    munt_module,
    munt_module + "          - -DCMAKE_INSTALL_LIBDIR=lib\n",
    1,
)

# The Flathub shared module installs Ayatana Ido in lib64 by default.
# Its dependent libayatana-indicator module searches /app/lib instead.
ayatana_manifest = manifest.parent / "shared-modules/libayatana-appindicator/libayatana-appindicator-gtk3.json"
ayatana = json.loads(ayatana_manifest.read_text())


def fix_ayatana_libraries(value):
    if isinstance(value, dict):
        if value.get("name") in (
            "ayatana-ido",
            "libayatana-ido",
            "libayatana-indicator",
        ):
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
