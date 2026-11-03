#!/usr/bin/env python3
"""Generate tested, standalone-folder Perl distributions for each platform.

These are portable Perl packages, NOT compiled machine-code binaries.
Windows EXE, when available, is separately built with PAR::Packer.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import tarfile
import tempfile
import zipfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", required=True, choices=("linux-x86_64", "macos-perl", "windows-x86_64"))
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    if len(args.source_sha) < 12:
        parser.error("An upstream commit SHA is required")
    version = str(json.loads(Path("META.json").read_text(encoding="utf-8"))["version"])
    stem = f"exiftool-{version}-{args.source_sha[:12]}-{args.platform}"
    destination = Path("out")
    destination.mkdir(exist_ok=True)

    files = ["exiftool", "README", "LICENSE", "Changes", "Makefile.PL", "META.json"]
    dirs = ["lib", "arg_files", "config_files", "fmt_files", "html"]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / stem
        root.mkdir()
        for filename in files:
            shutil.copy2(filename, root / ("exiftool.pl" if args.platform == "windows-x86_64" and filename == "exiftool" else filename))
        for dirname in dirs:
            shutil.copytree(dirname, root / dirname)

        if args.platform == "windows-x86_64":
            (root / "exiftool.bat").write_bytes(b'@echo off\r\nperl "%~dp0exiftool.pl" %*\r\n')
        else:
            runner = root / "exiftool"
            runner.chmod(runner.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        (root / "MIRROR-BUILD.json").write_text(json.dumps({
            "source": "https://github.com/exiftool/exiftool",
            "upstream_commit": args.source_sha,
            "exiftool_version": version,
            "platform": args.platform,
            "requires_perl": True,
            "unofficial_mirror_build": True,
        }, indent=2) + "\n", encoding="utf-8")

        if args.platform == "windows-x86_64":
            archive = destination / f"{stem}.zip"
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=7) as zf:
                for item in sorted(root.rglob("*")):
                    if item.is_file():
                        zf.write(item, arcname=item.relative_to(root.parent))
        else:
            archive = destination / f"{stem}.tar.gz"
            with tarfile.open(archive, "w:gz") as tf:
                tf.add(root, arcname=root.name)
        if archive.stat().st_size == 0:
            raise RuntimeError(f"Empty archive: {archive}")
        print(f"Packaged {archive} ({archive.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
