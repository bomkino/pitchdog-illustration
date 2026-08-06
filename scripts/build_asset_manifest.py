#!/usr/bin/env python3
"""Build deterministic provenance and checksum records for public references."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from datetime import date
from pathlib import Path


PACK_VERSION = "2026-08-06-v1"
PACK_DATE = "2026-08-06"
RIGHTS_BASIS = "Copyright-owner authorization for public 0BSD release, 2026-08-06."

TIER_RULES = {
    "golden-six": {
        "tier": "conceptual-ancestry",
        "status": "owner-approved-gold-standard",
        "statusAuthority": "Owner-reviewed baseline dated 2026-07-24.",
        "sourceLineage": "Golden Six approved baseline.",
    },
    "website-30": {
        "tier": "approved-website-breadth",
        "status": "owner-approved-family-batch",
        "statusAuthority": "Owner-reviewed baseline dated 2026-07-24.",
        "sourceLineage": "Round 03 approved website set.",
    },
    "approved-22": {
        "tier": "current-execution-authority",
        "status": "locked-current-final",
        "statusAuthority": "Current production record; Spotty 01 corrected 2026-08-06.",
        "sourceLineage": "Current 22-final family rebuild.",
    },
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


def label(path: Path) -> str:
    stem = path.stem
    parts = stem.split("-", 1)
    if parts[0].isdigit() and len(parts) == 2:
        stem = parts[1]
    return stem.replace("-", " ")


def asset_record(skill_root: Path, path: Path, rules: dict[str, str]) -> dict[str, object]:
    width, height, mode, bit_depth = png_info(path)
    relative = path.relative_to(skill_root).as_posix()
    return {
        "path": relative,
        "id": path.stem,
        "label": label(path),
        "kind": "illustration",
        "tier": rules["tier"],
        "status": rules["status"],
        "statusAuthority": rules["statusAuthority"],
        "sourceLineage": rules["sourceLineage"],
        "publicRightsBasis": RIGHTS_BASIS,
        "sha256": sha256(path),
        "width": width,
        "height": height,
        "mode": mode,
        "bitDepth": bit_depth,
    }


def build(skill_root: Path) -> dict[str, object]:
    records: list[dict[str, object]] = []
    reference_root = skill_root / "assets/references"

    for folder, rules in TIER_RULES.items():
        files = sorted((reference_root / folder).glob("*.png"))
        expected = {"golden-six": 6, "website-30": 30, "approved-22": 22}[folder]
        if len(files) != expected:
            raise SystemExit(f"expected {expected} files in {folder}, found {len(files)}")
        records.extend(asset_record(skill_root, path, rules) for path in files)

    for filename, tier in (
        ("approved-22-contact-sheet.png", "current-execution-scan"),
        ("website-30-contact-sheet.png", "approved-website-scan"),
    ):
        path = reference_root / filename
        width, height, mode, bit_depth = png_info(path)
        records.append(
            {
                "path": path.relative_to(skill_root).as_posix(),
                "id": path.stem,
                "label": label(path),
                "kind": "contact-sheet",
                "tier": tier,
                "status": "derived-reference-scan",
                "statusAuthority": "Derived from bundled full-resolution references.",
                "sourceLineage": "Deterministic contact sheet; full-size source files remain authority.",
                "publicRightsBasis": RIGHTS_BASIS,
                "sha256": sha256(path),
                "width": width,
                "height": height,
                "mode": mode,
                "bitDepth": bit_depth,
            }
        )

    checksum_lines = [f"{record['sha256']}  {record['path']}" for record in records]
    pack_digest = hashlib.sha256(("\n".join(checksum_lines) + "\n").encode()).hexdigest()
    return {
        "schemaVersion": 1,
        "packVersion": PACK_VERSION,
        "packDate": PACK_DATE,
        "activeIllustrationCount": 58,
        "contactSheetCount": 2,
        "historicalApprovedSupersededCount": 9,
        "uniqueOwnerApprovedAcrossEras": 67,
        "referencePackSha256": pack_digest,
        "rightsBoundary": {
            "included": "Golden Six, website 30, and current locked 22 illustration files.",
            "excluded": "Real family photographs, private likeness evidence, rejected work, and third-party inspiration.",
            "licenceLimit": "0BSD covers copyright only; it grants no trademark, publicity, privacy, personality, endorsement, or moral rights beyond applicable law.",
        },
        "assets": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", type=Path, default=Path("skills/pitchdog-illustration"))
    args = parser.parse_args()
    skill_root = args.skill.resolve()
    manifest = build(skill_root)
    output = skill_root / "assets/reference-manifest.json"
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    checksum = skill_root / "assets/REFERENCE-PACK.sha256"
    checksum.write_text(
        "\n".join(f"{record['sha256']}  {record['path']}" for record in manifest["assets"]) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
