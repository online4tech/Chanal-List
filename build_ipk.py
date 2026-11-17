#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Online4Tech Enigma2 IPK Package Builder
Builds enigma2-plugin-extensions-online4tech_7.0_all.ipk natively on Windows/Linux
without requiring dpkg-deb or ar binaries.
"""
import os
import io
import time
import tarfile

VERSION = "7.0"
PKG_NAME = "enigma2-plugin-extensions-online4tech"
IPK_FILENAME = f"{PKG_NAME}_{VERSION}_all.ipk"
PLUGIN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugin")


def add_tar_bytes(tar, arcname, data_bytes, mode=0o644):
    ti = tarfile.TarInfo(name=arcname)
    ti.size = len(data_bytes)
    ti.mode = mode
    ti.uid = 0
    ti.gid = 0
    ti.uname = "root"
    ti.gname = "root"
    ti.mtime = int(time.time())
    tar.addfile(ti, io.BytesIO(data_bytes))


def make_ar_member(name, data, mode=0o100644):
    mtime = int(time.time())
    header = (
        f"{name:<16}"
        f"{mtime:<12}"
        f"{0:<6}"
        f"{0:<6}"
        f"{oct(mode)[2:]:<8}"
        f"{len(data):<10}"
        "`\n"
    ).encode("ascii")
    out = header + data
    if len(data) % 2 == 1:
        out += b"\n"
    return out


def build():
    plugin_py_path = os.path.join(PLUGIN_DIR, "plugin.py")
    icon_png_path = os.path.join(PLUGIN_DIR, "icon.png")

    if not os.path.exists(plugin_py_path):
        raise FileNotFoundError(f"Missing {plugin_py_path}")

    with open(plugin_py_path, "rb") as f:
        plugin_bytes = f.read()

    icon_bytes = b""
    if os.path.exists(icon_png_path):
        with open(icon_png_path, "rb") as f:
            icon_bytes = f.read()

    control_content = f"""Package: {PKG_NAME}
Version: {VERSION}
Description: Online4Tech Command Dashboard & Enigma2 Control Suite
Section: extra
Priority: optional
Maintainer: Online4Tech <support@online4tech.com>
Architecture: all
Homepage: https://github.com/online4tech/Chanal-List
""".encode("utf-8")

    postinst = b"""#!/bin/sh
echo "Online4Tech Command Dashboard installed! Please restart Enigma2 GUI."
exit 0
"""
    prerm = b"""#!/bin/sh
rm -rf /usr/lib/enigma2/python/Plugins/Extensions/Online4Tech/__pycache__
rm -f /usr/lib/enigma2/python/Plugins/Extensions/Online4Tech/*.pyc
exit 0
"""
    postrm = b"""#!/bin/sh
rm -rf /usr/lib/enigma2/python/Plugins/Extensions/Online4Tech
exit 0
"""

    control_buf = io.BytesIO()
    with tarfile.open(fileobj=control_buf, mode="w:gz", format=tarfile.GNU_FORMAT) as tar:
        add_tar_bytes(tar, "./control", control_content, 0o644)
        add_tar_bytes(tar, "./postinst", postinst, 0o755)
        add_tar_bytes(tar, "./prerm", prerm, 0o755)
        add_tar_bytes(tar, "./postrm", postrm, 0o755)

    data_buf = io.BytesIO()
    with tarfile.open(fileobj=data_buf, mode="w:gz", format=tarfile.GNU_FORMAT) as tar:
        base = "./usr/lib/enigma2/python/Plugins/Extensions/Online4Tech"
        add_tar_bytes(tar, base + "/__init__.py", b"# Online4Tech Panel\n", 0o644)
        add_tar_bytes(tar, base + "/plugin.py", plugin_bytes, 0o644)
        if icon_bytes:
            add_tar_bytes(tar, base + "/icon.png", icon_bytes, 0o644)

    with open(IPK_FILENAME, "wb") as f:
        f.write(b"!<arch>\n")
        f.write(make_ar_member("debian-binary", b"2.0\n"))
        f.write(make_ar_member("control.tar.gz", control_buf.getvalue()))
        f.write(make_ar_member("data.tar.gz", data_buf.getvalue()))

    print(f"Successfully built {IPK_FILENAME} ({os.path.getsize(IPK_FILENAME)} bytes)")


if __name__ == "__main__":
    build()
