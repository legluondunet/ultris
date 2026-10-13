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

# Keep hardware identification and SDL 1.2 compatibility components current.
source_updates = (
    (
        "https://github.com/vcrhonek/hwdata/archive/refs/tags/v0.349.tar.gz",
        "2591ebf85b36e6d953360a003b2991fc0a0c2c35d3fdbd3133f435098b0af3da",
        "https://github.com/vcrhonek/hwdata/archive/refs/tags/v0.412.tar.gz",
        "f0c64cd7e31d70a5fb3a52e53ab50a61e74c0421a6381eaa45114eec3bde5fe7",
    ),
    (
        "https://mirrors.edge.kernel.org/pub/software/utils/pciutils/pciutils-3.7.0.tar.gz",
        "2432e7a2e12000502d36cf769ab6e5a0cf4931e5050ccaf8b02984b2d3cb0948",
        "https://github.com/pciutils/pciutils/archive/refs/tags/v3.15.0.tar.gz",
        "06f467642057599acf396bc17340452fac3308f1e08be19e0c32587e42d7017b",
    ),
    (
        "https://github.com/libsdl-org/sdl12-compat/archive/refs/tags/release-1.2.68.tar.gz",
        "63c6e4dcc1154299e6f363c872900be7f3dcb3e42b9f8f57e05442ec3d89d02d",
        "https://github.com/libsdl-org/sdl12-compat/archive/refs/tags/release-1.2.78.tar.gz",
        "40ec5f0bab13a217ffae7aab0c450f1f798761e91fb185051b5211925c9da11a",
    ),
)
for old_url, old_hash, new_url, new_hash in source_updates:
    old_source = f"        url: {old_url}\n        sha256: {old_hash}\n"
    if updated.count(old_source) != 1:
        sys.exit(f"Expected exactly one pinned source for {old_url}")
    updated = updated.replace(
        old_source, f"        url: {new_url}\n        sha256: {new_hash}\n", 1
    )


# Update USB tools and BSD compatibility libraries from pinned release archives.
component_updates = (
    (
        "https://mirrors.edge.kernel.org/pub/linux/utils/usb/usbutils/usbutils-013.tar.xz",
        "9e23494fcc78b7a80ee29a07dd179c95ae2f71509c35728dbbabc2d1cca41338",
        "https://www.kernel.org/pub/linux/utils/usb/usbutils/usbutils-019.tar.xz",
        "659f40c440e31ba865c52c818a33d3ba6a97349e3353f8b1985179cb2aa71ec5",
    ),
    (
        "https://libbsd.freedesktop.org/releases/libbsd-0.10.0.tar.xz",
        "34b8adc726883d0e85b3118fa13605e179a62b31ba51f676136ecb2d0bc1a887",
        "https://libbsd.freedesktop.org/releases/libbsd-0.12.2.tar.xz",
        "b88cc9163d0c652aaf39a99991d974ddba1c3a9711db8f1b5838af2a14731014",
    ),
)
for old_url, old_hash, new_url, new_hash in component_updates:
    old_source = f"        url: {old_url}\n        sha256: {old_hash}\n"
    if updated.count(old_source) != 1:
        sys.exit(f"Expected exactly one pinned source for {old_url}")
    updated = updated.replace(
        old_source, f"        url: {new_url}\n        sha256: {new_hash}\n", 1
    )

usb_options = "  - name: usbutils\n    config-opts:\n      - --datadir=/app/share/hwdata\n      - --sbindir=/app/bin\n"
if updated.count(usb_options) != 1:
    sys.exit("Expected exactly one usbutils module")
updated = updated.replace(
    usb_options,
    "  - name: usbutils\n"
    "    buildsystem: meson\n"
    "    config-opts:\n"
    "      - --datadir=/app/share/hwdata\n"
    "      - --sbindir=/app/bin\n",
    1,
)

# libbsd now needs libmd; provide it for both native and Wine compatibility ABI.
bsd_module = "  - name: libbsd\n"
if updated.count(bsd_module) != 1:
    sys.exit("Expected exactly one native libbsd module")
updated = updated.replace(
    bsd_module,
    "  - name: libmd\n"
    "    sources: &libmd_sources\n"
    "      - type: archive\n"
    "        url: https://libbsd.freedesktop.org/releases/libmd-1.1.0.tar.xz\n"
    "        sha256: 1bd6aa42275313af3141c7cf2e5b964e8b1fd488025caf2f971f43b00776b332\n"
    "\n"
    "  - name: libmd-32bit\n"
    "    build-options:\n"
    "      arch:\n"
    "        x86_64: *compat_i386_opts\n"
    "    sources: *libmd_sources\n"
    "\n" + bsd_module,
    1,
)


# Modernise video compatibility libraries and the GLX diagnostic tool.
old_module = (
    "  - name: v4l2-utils\n"
    "    config-opts: &v4l2_config_opts\n"
    "      - --disable-v4l-utils\n"
    "      - --disable-qv4l2\n"
    "      - --disable-qvidcap\n"
    "    sources: &v4l2_sources\n"
    "      - type: archive\n"
    "        url: https://linuxtv.org/downloads/v4l-utils/v4l-utils-1.20.0.tar.bz2\n"
    "        sha256: 956118713f7ccb405c55c7088a6a2490c32d54300dd9a30d8d5008c28d3726f7\n"
    "\n"
    "  - name: v4l2-utils-32bit\n"
    "    build-options:\n"
    "      arch:\n"
    "        x86_64: *compat_i386_opts\n"
    "    config-opts: *v4l2_config_opts\n"
    "    sources: *v4l2_sources\n"
    "\n"
)
new_module = (
    "  - name: v4l2-utils\n"
    "    buildsystem: meson\n"
    "    config-opts: &v4l2_config_opts\n"
    "      - -Dv4l-utils=false\n"
    "      - -Dqv4l2=disabled\n"
    "      - -Dqvidcap=disabled\n"
    "      - -Dbpf=disabled\n"
    "      - -Dv4l2-tracer=disabled\n"
    "      - -Ddoxygen-doc=disabled\n"
    "    sources: &v4l2_sources\n"
    "      - type: archive\n"
    "        url: https://linuxtv.org/downloads/v4l-utils/v4l-utils-1.32.0.tar.xz\n"
    "        sha256: 6828828a17775526eb93fb258a9294d1d1073d633c344dd71ecd4e7a1ffb7dfc\n"
    "\n"
    "  - name: v4l2-utils-32bit\n"
    "    buildsystem: meson\n"
    "    build-options:\n"
    "      arch:\n"
    "        x86_64: *compat_i386_opts\n"
    "    config-opts: *v4l2_config_opts\n"
    "    sources: *v4l2_sources\n"
    "\n"
)
if updated.count(old_module) != 1:
    sys.exit("Expected exactly one original v4l-utils module block")
updated = updated.replace(old_module, new_module, 1)

old_module = (
    "  - name: mesa-demos\n"
    "    config-opts:\n"
    "      - --without-glut\n"
    "      - --bindir=/app/lib/mesa-demos\n"
    "    make-args:\n"
    "      - -C\n"
    "      - src/xdemos\n"
    "      - glxinfo\n"
    "    no-make-install: true\n"
    "    build-commands:\n"
    "      - install -D src/xdemos/glxinfo -t /app/bin/\n"
    "    sources:\n"
    "      - type: archive\n"
    "        url: https://mesa.freedesktop.org/archive/demos/mesa-demos-8.4.0.tar.bz2\n"
    "        sha256: 01e99c94a0184e63e796728af89bfac559795fb2a0d6f506fa900455ca5fff7d\n"
    "    cleanup:\n"
    "      - /lib/mesa-demos\n"
    "    modules:\n"
    "      - shared-modules/glew/glew.json\n"
    "\n"
)
new_module = (
    "  - name: mesa-demos\n"
    "    buildsystem: meson\n"
    "    config-opts:\n"
    "      - -Dglut=disabled\n"
    "      - -Dx11=enabled\n"
    "      - -Degl=disabled\n"
    "      - -Dgles1=disabled\n"
    "      - -Dgles2=disabled\n"
    "      - -Dosmesa=disabled\n"
    "      - -Dwayland=disabled\n"
    "      - -Dvulkan=disabled\n"
    "      - -Dlibdrm=disabled\n"
    "    make-args:\n"
    "      - src/xdemos/glxinfo\n"
    "    no-make-install: true\n"
    "    build-commands:\n"
    "      - install -Dm755 src/xdemos/glxinfo /app/bin/glxinfo\n"
    "    sources:\n"
    "      - type: archive\n"
    "        url: https://archive.mesa3d.org/demos/mesa-demos-9.0.0.tar.xz\n"
    "        sha256: 3046a3d26a7b051af7ebdd257a5f23bfeb160cad6ed952329cdff1e9f1ed496b\n"
    "    cleanup:\n"
    "      - /lib/mesa-demos\n"
    "    modules:\n"
    "      - shared-modules/glew/glew.json\n"
    "\n"
)
if updated.count(old_module) != 1:
    sys.exit("Expected exactly one original mesa-demos module block")
updated = updated.replace(old_module, new_module, 1)


# Update HTML parsing libraries together, retaining Python 3.10 support.
html_original = (
    "      - name: soupsieve\n"
    "        buildsystem: simple\n"
    "        build-commands:\n"
    '          - pip3 install --no-index --no-build-isolation --prefix="${FLATPAK_DEST}"\n'
    '            --find-links="file://${PWD}" soupsieve\n'
    "        sources:\n"
    "          - type: file\n"
    "            url: https://files.pythonhosted.org/packages/49/37/673d6490efc51ec46d198c75903d99de"
    "59baffdd47aea3d071b80a9e4e89/soupsieve-2.4.1-py3-none-any.whl\n"
    "            sha256: 1c1bfee6819544a3447586c889157365a27e10d88cde3ad3da0cf0ddf646feb8\n"
    "      - name: beautifulsoup4\n"
    "        buildsystem: simple\n"
    "        build-commands:\n"
    '          - pip3 install --no-index --no-build-isolation --prefix="${FLATPAK_DEST}"\n'
    '            --find-links="file://${PWD}" beautifulsoup4\n'
    "        sources:\n"
    "          - type: file\n"
    "            url: https://files.pythonhosted.org/packages/21/0a/47fdf541c97fd9b6a610cb5fd5181753"
    "08a7cc60569962e776ac52420387/beautifulsoup4-4.6.3-py3-none-any.whl\n"
    "            sha256: 194ec62a25438adcb3fdb06378b26559eda1ea8a747367d34c33cef9c7f48d57\n"
)
html_updated = (
    "      - name: soupsieve\n"
    "        buildsystem: simple\n"
    "        build-commands:\n"
    '          - pip3 install --no-index --no-build-isolation --prefix="${FLATPAK_DEST}"\n'
    '            --find-links="file://${PWD}" soupsieve\n'
    "        sources:\n"
    "          - type: file\n"
    "            url: https://files.pythonhosted.org/packages/66/87/5ed59e1d0290564e2027ed066c52b059"
    "892c4637741337fc0967183c8d4d/soupsieve-2.10-py3-none-any.whl\n"
    "            sha256: 8596eb8967d744174820280fa62b4542a2e955bfaccca73ed8a13c6eb8e9b502\n"
    "      - name: beautifulsoup4\n"
    "        buildsystem: simple\n"
    "        build-commands:\n"
    '          - pip3 install --no-index --no-build-isolation --prefix="${FLATPAK_DEST}"\n'
    '            --find-links="file://${PWD}" beautifulsoup4\n'
    "        sources:\n"
    "          - type: file\n"
    "            url: https://files.pythonhosted.org/packages/88/c6/92fcd42f1ba33e1184263f25bfabf3d2"
    "7c383410470f169e4b8163bf9c17/beautifulsoup4-4.15.0-py3-none-any.whl\n"
    "            sha256: d6f88de62e1d4e38ecb1077eb9724cd0eff29d2a08ca16a401e9b9e93f117cf9\n"
)
if updated.count(html_original) != 1:
    sys.exit("Expected exactly one original HTML parsing module block")
updated = updated.replace(html_original, html_updated, 1)

# GLU's Meson default installs glu.pc under /app/lib64/pkgconfig,
# but the subsequent mesa-demos module looks for it under /app/lib/pkgconfig.

# Update Python runtime dependencies without changing their offline build methods.
python_source_updates = (
    (
        "https://files.pythonhosted.org/packages/54/ed/79a089b6be93607fa5cdaedf301d7dfb23af5f25c398d5ead2525b063e17/pyyaml-6.0.2.tar.gz",
        "d584d9ec91ad65861cc08d42e834324ef890a082e591037abe114850ff7bbc3e",
        "https://files.pythonhosted.org/packages/05/8e/961c0007c59b8dd7729d542c61a4d537767a59645b82a0b521206e1e25c2/pyyaml-6.0.3.tar.gz",
        "d76623373421df22fb4cf8817020cbb7ef15c725b9d5e45f17e189bfc384190f",
    ),
    (
        "https://files.pythonhosted.org/packages/b5/47/ac709629ddb9779fee29b7d10ae9580f60a4b37e49bce72360ddf9a79cdc/setproctitle-1.3.2.tar.gz",
        "b9fb97907c830d260fa0658ed58afd48a86b2b88aac521135c352ff7fd3477fd",
        "https://files.pythonhosted.org/packages/49/b0/6b8a516c5a9e9630bd5293db78314ac012f690305fe93beadea388626efb/setproctitle-1.3.8.tar.gz",
        "cafe209d064a6efb88cb45a03e97981ff8832802b2b5d009dde0197a3b7b41c8",
    ),
    (
        "https://files.pythonhosted.org/packages/b5/7e/ddfbd640ac9a82e60718558a3de7d5988a7d4648385cf00318f60a8b073a/distro-1.7.0.tar.gz",
        "151aeccf60c216402932b52e40ee477a939f8d58898927378a02abbe852c1c39",
        "https://files.pythonhosted.org/packages/fc/f8/98eea607f65de6527f8a2e8885fc8015d3e6f5775df186e443e0964a11c3/distro-1.9.0.tar.gz",
        "2fa77c6fd8940f116ee1d6b94a2f90b13b5ea8d019b98bc8bafdcabcdd9bdbed",
    ),
)
for old_url, old_hash, new_url, new_hash in python_source_updates:
    pinned_source = rf"url: {re.escape(old_url)}\n(?P<indent> +)sha256: {old_hash}\n"
    replacement = f"url: {new_url}\n" + rf"\g<indent>sha256: {new_hash}" + "\n"
    updated, count = re.subn(pinned_source, replacement, updated)
    if count != 1:
        sys.exit(
            f"Expected exactly one pinned Python source for {old_url}; found {count}"
        )


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

# The 0.83.0 archive lists a removed misc directory instead of its internal shaders.
dosbox_hash = (
    "        sha256: 9b36be5a666784adaeffa560bd0950691f851a76bdb97e7ae3c989561e91caf3\n"
)
shader_command = """sed -i "s/'misc'/'_internal'/" resources/shaders/meson.build"""
# Repair DOSBox 0.83.0's incomplete Meson integration of its bundled RIFF parser.
riff_commands = (
    "sed -i \"/    'midi.cpp',/a     'midi_synth.cpp',\" src/midi/meson.build",
    "sed -i '/#define DOSBOX_VERSION /a #define DOSBOX_VERSION_SHORT \"0.83\"' src/dosbox_config.h.in",
    "sed -i \"/'riffcpp.cpp',/a )\" src/libs/riffcpp/meson.build",
    "sed -i \"/subdir('src\\/libs\\/residfp')/a subdir('src/libs/riffcpp')\" meson.build",
    'sed -i "s/        libriffcpp,/        libriffcpp_dep,/" src/hardware/meson.build',
    'sed -i "/    libtalchorus_dep,/a     libriffcpp_dep," meson.build',
)
riff_yaml = "".join(f"          - {json.dumps(command)}\n" for command in riff_commands)

if updated.count(dosbox_hash) != 1:
    sys.exit("Expected exactly one DOSBox Staging 0.83.0 archive")
updated = updated.replace(
    dosbox_hash,
    dosbox_hash
    + "      - type: shell\n        commands:\n"
    + f"          - {json.dumps(shader_command)}\n"
    + riff_yaml,
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
dosbox_dependencies = (
    "    modules:\n      # SDL2_net was dropped from the 26.08 runtime\n"
)
if updated.count(dosbox_dependencies) != 1:
    sys.exit("Expected exactly one DOSBox dependency list")
updated = updated.replace(
    dosbox_dependencies,
    "    modules:\n"
    "      - name: SDL2_image\n"
    "        buildsystem: cmake-ninja\n"
    "        builddir: true\n"
    "        config-opts:\n"
    "          - -DCMAKE_INSTALL_LIBDIR=lib\n"
    "          - -DSDL2IMAGE_VENDORED=OFF\n"
    "          - -DSDL2IMAGE_SAMPLES=OFF\n"
    "          - -DSDL2IMAGE_TESTS=OFF\n"
    "        sources:\n"
    "          - type: archive\n"
    "            url: https://github.com/libsdl-org/SDL_image/releases/download/"
    "release-2.8.12/SDL2_image-2.8.12.tar.gz\n"
    "            sha256: 393f5efb50536ec13ca4f4affb69cc9966d3c3f969e6c5e701faddf9f9785381\n"
    "      - name: asio\n"
    "        buildsystem: simple\n"
    "        build-commands:\n"
    "          - cp -a asio/include/. /app/include/\n"
    "          - mkdir -p /app/lib/pkgconfig\n"
    "          - \"printf '%s\\\\n' 'prefix=/app' 'includedir=${prefix}/includ"
    "e' '' 'Name: Asio' 'Description: Standalone Asio headers' 'Version: 1."
    "30.2' 'Cflags: -I${includedir}' > /app/lib/pkgconfig/asio.pc\"\n"
    "          - install -Dm644 asio/LICENSE_1_0.txt /app/share/licenses/asio/LICENSE_1_0.txt\n"
    "        sources:\n"
    "          - type: archive\n"
    "            url: https://github.com/chriskohlhoff/asio/archive/refs/tags/asio-1-30-2.tar.gz\n"
    "            sha256: 755bd7f85a4b269c67ae0ea254907c078d408cce8e1a352ad2ed664d233780e8\n"
    "      # SDL2_net was dropped from the 26.08 runtime\n",
    1,
)

# DOSBox 0.83 uses the newer FluidSynth portamento API.
fluid_source = (
    "        url: https://github.com/FluidSynth/fluidsynth/archive/v2.3.5.tar.gz\n"
    "        sha256: f89e8e983ecfb4a5b4f5d8c2b9157ed18d15ed2e36246fa782f18abaea550e0d\n"
)
if updated.count(fluid_source) != 1:
    sys.exit("Expected exactly one FluidSynth 2.3.5 source")
updated = updated.replace(
    fluid_source,
    "        url: https://github.com/FluidSynth/fluidsynth/archive/refs/tags/v2.6.1.tar.gz\n"
    "        sha256: 3d258a3bf97cc20c59eeebfe62c2432fae88adda74d3ad098681c76e0ebf446b\n",
    1,
)
# Supply FluidSynth's pinned GCEM headers before entering the offline build sandbox.
fluid_hash = (
    "        sha256: 3d258a3bf97cc20c59eeebfe62c2432fae88adda74d3ad098681c76e0ebf446b\n"
)
if updated.count(fluid_hash) != 1:
    sys.exit("Expected exactly one FluidSynth 2.6.1 archive")
updated = updated.replace(
    fluid_hash,
    fluid_hash
    + "      - type: archive\n"
    + "        url: https://github.com/kthohr/gcem/archive/012ae73c6d0a2cb09ffe86475f5c6fba3926e200.zip\n"
    + "        sha256: 28159274c54e9640354852e172d10d88eb159f4e7f2fea42edbcd20105ed3526\n"
    + "        dest: gcem\n",
    1,
)

fluid_patch = (
    "      - type: patch\n        path: patches/fluidsynth-cmake-policy.patch\n"
)
if updated.count(fluid_patch) != 1:
    sys.exit("Expected exactly one obsolete FluidSynth gentables patch")
updated = updated.replace(fluid_patch, "", 1)
fluid_module = "  - name: fluidsynth\n    buildsystem: cmake-ninja\n    config-opts:\n"
if updated.count(fluid_module) != 1:
    sys.exit("Expected exactly one FluidSynth module")
updated = updated.replace(
    fluid_module,
    "  - name: fluidsynth\n    buildsystem: cmake-ninja\n    builddir: true\n"
    "    config-opts:\n      - -DCMAKE_INSTALL_LIBDIR=lib\n",
    1,
)
slirp_module = "      - name: libslirp\n        buildsystem: meson\n"
if updated.count(slirp_module) != 1:
    sys.exit("Expected exactly one libslirp module")
updated = updated.replace(
    slirp_module,
    slirp_module + "        config-opts:\n          - --libdir=lib\n",
    1,
)

# Enable MIDI and Ethernet with manifest-provided dependencies, without network fallbacks.
dosbox_module = "  - name: dosbox-staging\n    buildsystem: meson\n"
if updated.count(dosbox_module) != 1:
    sys.exit("Expected exactly one DOSBox Staging module")
updated = updated.replace(
    dosbox_module,
    "  - name: dosbox-staging\n    buildsystem: meson\n"
    "    config-opts:\n      - -Duse_fluidsynth=true\n      - -Duse_slirp=true\n      - --wrap-mode=nofallback\n",
    1,
)

# Munt otherwise installs mt32emu.pc under /app/lib64/pkgconfig, which
# DOSBox Staging does not search before trying its network-only fallback.
munt_module = (
    "      - name: munt\n        buildsystem: cmake-ninja\n        config-opts:\n"
)
if updated.count(munt_module) != 1:
    sys.exit("Expected exactly one Munt module")
updated = updated.replace(
    munt_module,
    munt_module + "          - -DCMAKE_INSTALL_LIBDIR=lib\n",
    1,
)

# The Flathub shared module installs Ayatana Ido in lib64 by default.
# Its dependent libayatana-indicator module searches /app/lib instead.
ayatana_manifest = (
    manifest.parent
    / "shared-modules/libayatana-appindicator/libayatana-appindicator-gtk3.json"
)
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
print(
    "Flathub manifest now builds the fork with GLU and Ayatana libraries in /app/lib."
)
