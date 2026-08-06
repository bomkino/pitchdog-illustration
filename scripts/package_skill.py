#!/usr/bin/env python3
"""Build and round-trip a deterministic ChatGPT/Codex skill archive."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/pitchdog-illustration"
NAME = "pitchdog-illustration"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_source(skill: Path) -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_skill.py"), "--skill", str(skill)],
        check=True,
    )


def build_archive(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(path for path in SKILL.rglob("*") if path.is_file())
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = PurePosixPath(NAME) / PurePosixPath(path.relative_to(SKILL).as_posix())
            info = zipfile.ZipInfo(str(relative), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def verify_archive(archive_path: Path) -> None:
    with zipfile.ZipFile(archive_path) as archive:
        bad = archive.testzip()
        if bad:
            raise SystemExit(f"archive CRC failure: {bad}")
        names = archive.namelist()
        if not names:
            raise SystemExit("archive is empty")
        for name in names:
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts:
                raise SystemExit(f"unsafe archive path: {name}")
            if pure.parts[0] != NAME:
                raise SystemExit(f"wrong top-level folder: {name}")
            if any(part in {".DS_Store", "__MACOSX"} for part in pure.parts):
                raise SystemExit(f"junk archive entry: {name}")

        with tempfile.TemporaryDirectory(prefix="pitchdog-illustration-roundtrip-") as temp:
            root = Path(temp)
            archive.extractall(root)
            extracted = root / NAME
            validate_source(extracted)
            source_files = {path.relative_to(SKILL) for path in SKILL.rglob("*") if path.is_file()}
            extracted_files = {path.relative_to(extracted) for path in extracted.rglob("*") if path.is_file()}
            if source_files != extracted_files:
                missing = sorted(str(path) for path in source_files - extracted_files)
                extra = sorted(str(path) for path in extracted_files - source_files)
                raise SystemExit(f"round-trip file mismatch; missing={missing}, extra={extra}")
            for relative in source_files:
                if (SKILL / relative).read_bytes() != (extracted / relative).read_bytes():
                    raise SystemExit(f"round-trip byte mismatch: {relative}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    dist = args.dist if args.dist.is_absolute() else ROOT / args.dist

    validate_source(SKILL)
    zip_path = dist / f"{NAME}.zip"
    skill_path = dist / f"{NAME}.skill"
    build_archive(zip_path)
    verify_archive(zip_path)
    shutil.copyfile(zip_path, skill_path)

    if zip_path.read_bytes() != skill_path.read_bytes():
        raise SystemExit(".zip and .skill bytes differ")

    digest = sha256(zip_path)
    for path in (zip_path, skill_path):
        path.with_suffix(path.suffix + ".sha256").write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    (dist / "SHA256SUMS").write_text(
        f"{digest}  {zip_path.name}\n{digest}  {skill_path.name}\n",
        encoding="utf-8",
    )
    print(f"BUILT: {zip_path}")
    print(f"BUILT: {skill_path}")
    print(f"SHA256: {digest}")
    print("ROUND TRIP: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
