#!/usr/bin/env python3
"""Build same-environment reproducible full and ChatGPT-portable archives."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from PIL import Image, PngImagePlugin


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/pitchdog-illustration"
NAME = "pitchdog-illustration"
PORTABLE_ARCHIVE_BUDGET_BYTES = 25_000_000
ILLUSTRATION_MAX_LONG_EDGE = 800
CONTACT_SHEET_MAX_LONG_EDGE = 1280
PORTABLE_PACK_VERSION = "2026-08-06-v1-chatgpt-portable"
PORTABLE_DERIVATION = "Pillow 11.3.0 LANCZOS PNG derivative"
PINNED_PILLOW_VERSION = "11.3.0"
PNG_SRGB_RENDERING_INTENT = 0
KNOWN_OUTPUT_NAMES = {
    "pitchdog-illustration.zip",
    "pitchdog-illustration.zip.sha256",
    "pitchdog-illustration.skill",
    "pitchdog-illustration.skill.sha256",
    "pitchdog-illustration-full.zip",
    "pitchdog-illustration-full.zip.sha256",
    "pitchdog-illustration-full.skill",
    "pitchdog-illustration-full.skill.sha256",
    "SHA256SUMS",
    "SHA256SUMS.full",
    "SHA256SUMS.chatgpt",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def png_info(path: Path) -> tuple[int, int, str, int]:
    header = path.read_bytes()[:29]
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"not a valid PNG: {path}")
    width, height = struct.unpack(">II", header[16:24])
    bit_depth = header[24]
    colour_type = header[25]
    modes = {0: "grayscale", 2: "rgb", 3: "indexed", 4: "grayscale-alpha", 6: "rgba"}
    return width, height, modes.get(colour_type, f"png-colour-type-{colour_type}"), bit_depth


def validate_source(skill: Path) -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_skill.py"), "--skill", str(skill)],
        check=True,
    )


def resize_png(path: Path, max_long_edge: int) -> None:
    temporary = path.with_name(f".{path.name}.portable")
    with Image.open(path) as source:
        source.load()
        scale = min(1.0, max_long_edge / max(source.size))
        size = (
            max(1, round(source.width * scale)),
            max(1, round(source.height * scale)),
        )
        rendered = source if size == source.size else source.resize(size, Image.Resampling.LANCZOS)
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add(b"sRGB", bytes([PNG_SRGB_RENDERING_INTENT]))
        rendered.save(temporary, format="PNG", pnginfo=pnginfo, optimize=True, compress_level=9)
    temporary.replace(path)


def build_portable_skill(destination: Path) -> Path:
    shutil.copytree(SKILL, destination)
    manifest_path = destination / "assets/reference-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_pack_sha = manifest["referencePackSha256"]
    canonical_pixel_source = manifest.get("canonicalPixelSource")
    if not isinstance(canonical_pixel_source, dict):
        raise SystemExit("canonical manifest lacks immutable pixel-source provenance")

    checksum_lines: list[str] = []
    for record in manifest["assets"]:
        path = destination / record["path"]
        record["sourceSha256"] = record["sha256"]
        record["sourceWidth"] = record["width"]
        record["sourceHeight"] = record["height"]
        record["sourceC2paJumbMarker"] = record.get("c2paJumbMarker", False)
        long_edge = CONTACT_SHEET_MAX_LONG_EDGE if record["kind"] == "contact-sheet" else ILLUSTRATION_MAX_LONG_EDGE
        resize_png(path, long_edge)
        width, height, mode, bit_depth = png_info(path)
        record["sha256"] = sha256(path)
        record["width"] = width
        record["height"] = height
        record["mode"] = mode
        record["bitDepth"] = bit_depth
        record["derivation"] = PORTABLE_DERIVATION
        record["c2paJumbMarker"] = False
        record["sourceLineage"] = f"{record['sourceLineage']} ChatGPT-portable display derivative; canonical source receipt retained."
        checksum_lines.append(f"{record['sha256']}  {record['path']}")

    manifest["packVersion"] = PORTABLE_PACK_VERSION
    manifest["assetProfile"] = "chatgpt-portable"
    manifest["sourceReferencePackSha256"] = source_pack_sha
    manifest["portableRendering"] = {
        "purpose": "Fit the 25 MB Skills uploader gate observed on 2026-08-06 without dropping any active reference.",
        "illustrationMaxLongEdge": ILLUSTRATION_MAX_LONG_EDGE,
        "contactSheetMaxLongEdge": CONTACT_SHEET_MAX_LONG_EDGE,
        "resampler": "Pillow 11.3.0 LANCZOS",
        "format": "PNG",
        "colourSpaceDeclaration": "PNG sRGB chunk",
        "pngSrgbRenderingIntent": PNG_SRGB_RENDERING_INTENT,
        "metadataPolicy": "source metadata stripped; fresh sRGB declaration added",
        "pixelAuthority": "Immutable canonical public assets identified by canonicalPixelSource and each sourceSha256.",
    }
    source_checksum_lines = [f"{record['sourceSha256']}  {record['path']}" for record in manifest["assets"]]
    reconstructed_source_sha = hashlib.sha256(("\n".join(source_checksum_lines) + "\n").encode()).hexdigest()
    if reconstructed_source_sha != source_pack_sha:
        raise SystemExit("portable source receipts do not reconstruct the canonical reference-pack receipt")
    if canonical_pixel_source.get("referencePackSha256") != source_pack_sha:
        raise SystemExit("immutable canonical locator does not match the canonical reference-pack receipt")
    manifest["referencePackSha256"] = hashlib.sha256(("\n".join(checksum_lines) + "\n").encode()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (destination / "assets/REFERENCE-PACK.sha256").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    return destination


def build_archive(source_skill: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(path for path in source_skill.rglob("*") if path.is_file())
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = PurePosixPath(NAME) / PurePosixPath(path.relative_to(source_skill).as_posix())
            info = zipfile.ZipInfo(str(relative), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def verify_archive(archive_path: Path, source_skill: Path) -> None:
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
            source_files = {path.relative_to(source_skill) for path in source_skill.rglob("*") if path.is_file()}
            extracted_files = {path.relative_to(extracted) for path in extracted.rglob("*") if path.is_file()}
            if source_files != extracted_files:
                missing = sorted(str(path) for path in source_files - extracted_files)
                extra = sorted(str(path) for path in extracted_files - source_files)
                raise SystemExit(f"round-trip file mismatch; missing={missing}, extra={extra}")
            for relative in source_files:
                if (source_skill / relative).read_bytes() != (extracted / relative).read_bytes():
                    raise SystemExit(f"round-trip byte mismatch: {relative}")


def build_pair(source_skill: Path, dist: Path, basename: str, enforce_portable_budget: bool = False) -> tuple[Path, Path, str]:
    zip_path = dist / f"{basename}.zip"
    skill_path = dist / f"{basename}.skill"
    build_archive(source_skill, zip_path)
    verify_archive(zip_path, source_skill)
    shutil.copyfile(zip_path, skill_path)
    if zip_path.read_bytes() != skill_path.read_bytes():
        raise SystemExit(f".zip and .skill bytes differ for {basename}")
    if enforce_portable_budget and zip_path.stat().st_size >= PORTABLE_ARCHIVE_BUDGET_BYTES:
        raise SystemExit(
            f"portable archive is {zip_path.stat().st_size} bytes; it exceeds the {PORTABLE_ARCHIVE_BUDGET_BYTES}-byte "
            "Skills uploader gate observed on 2026-08-06"
        )
    digest = sha256(zip_path)
    for path in (zip_path, skill_path):
        receipt = path.with_suffix(path.suffix + ".sha256")
        expected_receipt = f"{digest}  {path.name}\n"
        receipt.write_text(expected_receipt, encoding="utf-8")
        if receipt.read_text(encoding="utf-8") != expected_receipt or sha256(path) != digest:
            raise SystemExit(f"checksum sidecar verification failed: {receipt}")
    return zip_path, skill_path, digest


def clean_known_outputs(dist: Path) -> None:
    """Make each requested profile exact even when its output directory is reused."""
    for name in KNOWN_OUTPUT_NAMES:
        (dist / name).unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    parser.add_argument("--profile", choices=("all", "full", "chatgpt"), default="all")
    args = parser.parse_args()
    dist = args.dist if args.dist.is_absolute() else ROOT / args.dist
    dist.mkdir(parents=True, exist_ok=True)
    clean_known_outputs(dist)

    if Image.__version__ != PINNED_PILLOW_VERSION:
        raise SystemExit(
            f"Pillow {PINNED_PILLOW_VERSION} is required for environment-scoped reproducible portable assets; "
            f"found {Image.__version__}"
        )

    validate_source(SKILL)
    built: list[tuple[Path, Path, str]] = []
    if args.profile in {"all", "full"}:
        built.append(build_pair(SKILL, dist, f"{NAME}-full"))
    if args.profile in {"all", "chatgpt"}:
        with tempfile.TemporaryDirectory(prefix="pitchdog-illustration-chatgpt-") as temp:
            portable = build_portable_skill(Path(temp) / NAME)
            validate_source(portable)
            built.append(build_pair(portable, dist, NAME, enforce_portable_budget=True))

    checksum_lines: list[str] = []
    for zip_path, skill_path, digest in built:
        checksum_lines.extend((f"{digest}  {zip_path.name}", f"{digest}  {skill_path.name}"))
        print(f"BUILT: {zip_path} ({zip_path.stat().st_size} bytes)")
        print(f"BUILT: {skill_path} ({skill_path.stat().st_size} bytes)")
        print(f"SHA256: {digest}")
    checksum_name = "SHA256SUMS" if args.profile == "all" else f"SHA256SUMS.{args.profile}"
    checksum_path = dist / checksum_name
    checksum_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print(f"CHECKSUMS: {checksum_path}")
    print("ROUND TRIP: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
