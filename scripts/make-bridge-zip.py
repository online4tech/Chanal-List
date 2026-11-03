#!/usr/bin/env python3
"""Builds bridge/Online4Tech-Bridge.zip from the files in bridge/ (run from the repo root)."""
import zipfile, pathlib

root = pathlib.Path("bridge")
out = root / "Online4Tech-Bridge.zip"
files = sorted(p for p in root.iterdir() if p.is_file() and p.suffix != ".zip")

with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in files:
        data = p.read_bytes()
        if p.suffix == ".bat":  # Windows batch files need CRLF line endings
            data = data.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        info = zipfile.ZipInfo(f"Online4Tech-Bridge/{p.name}", date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, data)
print("Wrote", out, "with", len(files), "files")
