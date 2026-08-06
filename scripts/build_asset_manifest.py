#!/usr/bin/env python3
"""Build stable provenance and checksum records for public references."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


PACK_VERSION = "2026-08-06-v1"
PACK_DATE = "2026-08-06"
RIGHTS_BASIS = "Copyright-owner authorization for public 0BSD release, 2026-08-06."
CANONICAL_REPOSITORY = "https://github.com/bomkino/pitchdog-illustration"
CANONICAL_RELEASE_TAG = "v1.0.0"
CANONICAL_COMMIT = "1ade97592e3779e26f0280a02a58505de935d955"
CANONICAL_MANIFEST_PATH = "skills/pitchdog-illustration/assets/reference-manifest.json"
CANONICAL_MANIFEST_SHA256 = "4cba40dd6f01e3997d1913c4a4c89a88c0b707811aef9c11c95611fb3426fae8"
CANONICAL_REFERENCE_PACK_SHA256 = "d99b9c379b5e3336d3c19055ef29147698796276b8cef86ed8ee557356ca1c65"

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

CURRENT_STATUS_OVERRIDES = {
    "01-manali-lightning-sensible-shoes.png": {
        "status": "owner-approved-current-final",
        "statusAuthority": "Owner-reviewed baseline dated 2026-07-24; reused unchanged in the current 22.",
        "sourceLineage": "Manali owner-approved gold standard reused in the current 22.",
    },
    "02-manali-good-chair-quiet-idea.png": {
        "status": "owner-approved-current-final",
        "statusAuthority": "Owner-reviewed baseline dated 2026-07-24; reused unchanged in the current 22.",
        "sourceLineage": "Manali owner-approved gold standard reused in the current 22.",
    },
    "03-manali-unfolded-horizon.png": {
        "status": "owner-approved-current-final",
        "statusAuthority": "Owner-reviewed baseline dated 2026-07-24; reused unchanged in the current 22.",
        "sourceLineage": "Manali owner-approved gold standard reused in the current 22.",
    },
    "01-juno-loose-end-of-impossible.png": {
        "status": "owner-approved-current-final",
        "statusAuthority": "Owner gate recorded 2026-07-30 in QA-OWNER-GATES-2026-07-30.md.",
        "sourceLineage": "Current Juno final promoted from owner-approved candidate v5.",
    },
    "01-kumail-persuaded-knot.png": {
        "status": "owner-approved-current-final",
        "statusAuthority": "Owner gate recorded 2026-07-30 in QA-OWNER-GATES-2026-07-30.md.",
        "sourceLineage": "Current Kumail lower-body repair approved and promoted.",
    },
    "02-kumail-doorway-learned-outline.png": {
        "status": "owner-approved-current-final",
        "statusAuthority": "Owner gate recorded 2026-07-30 in QA-OWNER-GATES-2026-07-30.md.",
        "sourceLineage": "Current Kumail lower-body repair approved and promoted.",
    },
    "03-kumail-smallest-failure.png": {
        "status": "owner-approved-current-final",
        "statusAuthority": "Owner gate recorded 2026-07-30 in QA-OWNER-GATES-2026-07-30.md.",
        "sourceLineage": "Current Kumail lower-body repair approved and promoted.",
    },
    "04-kumail-applauded-thought.png": {
        "status": "owner-approved-current-final",
        "statusAuthority": "Owner gate recorded 2026-07-30 in QA-OWNER-GATES-2026-07-30.md.",
        "sourceLineage": "Current Kumail lower-body repair approved and promoted.",
    },
}

WEBSITE_CURRENT_USE_OVERRIDES = {
    "28-go-get-em.png": {
        "identityAuthority": "prohibited-current-juno",
        "knownLimitations": [
            "Juno predates the current likeness and sisters-scale lock and reads materially larger than the required 1.1× relationship."
        ],
        "reuseCondition": (
            "Metaphor and dated placement evidence only. If the final Process coda retains this slot, "
            "rebuild Juno from current approved-22 identity and 1.1× scale authority before use."
        ),
    },
    "30-lost-page.png": {
        "identityAuthority": "prohibited-current-juno",
        "knownLimitations": [
            "Juno is broad, stocky, and generic relative to the current lean body, darker muzzle, feathered ears, and narrow-face lock."
        ],
        "reuseCondition": (
            "Metaphor and dated 404 placement evidence only. Rebuild Juno from current approved-22 identity authority; "
            "do not reuse these pixels as current likeness evidence."
        ),
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


def has_c2pa_jumb_marker(path: Path) -> bool:
    raw = path.read_bytes().lower()
    return b"c2pa" in raw and b"jumb" in raw


def asset_record(skill_root: Path, path: Path, rules: dict[str, str]) -> dict[str, object]:
    width, height, mode, bit_depth = png_info(path)
    relative = path.relative_to(skill_root).as_posix()
    authority = {**rules}
    if path.parent.name == "approved-22":
        authority.update(CURRENT_STATUS_OVERRIDES.get(path.name, {}))
    if path.parent.name == "website-30":
        authority.update(WEBSITE_CURRENT_USE_OVERRIDES.get(path.name, {}))
    record: dict[str, object] = {
        "path": relative,
        "id": path.stem,
        "label": label(path),
        "kind": "illustration",
        "tier": authority["tier"],
        "status": authority["status"],
        "statusAuthority": authority["statusAuthority"],
        "sourceLineage": authority["sourceLineage"],
        "publicRightsBasis": RIGHTS_BASIS,
        "sha256": sha256(path),
        "width": width,
        "height": height,
        "mode": mode,
        "bitDepth": bit_depth,
        "c2paJumbMarker": has_c2pa_jumb_marker(path),
    }
    for field in ("identityAuthority", "knownLimitations", "reuseCondition"):
        if field in authority:
            record[field] = authority[field]
    return record


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
                "statusAuthority": "Derived from bundled canonical references.",
                "sourceLineage": "Generated contact sheet; canonical source files remain authority.",
                "publicRightsBasis": RIGHTS_BASIS,
                "sha256": sha256(path),
                "width": width,
                "height": height,
                "mode": mode,
                "bitDepth": bit_depth,
                "c2paJumbMarker": has_c2pa_jumb_marker(path),
            }
        )

    checksum_lines = [f"{record['sha256']}  {record['path']}" for record in records]
    pack_digest = hashlib.sha256(("\n".join(checksum_lines) + "\n").encode()).hexdigest()
    if pack_digest != CANONICAL_REFERENCE_PACK_SHA256:
        raise SystemExit(
            "reference pixels changed without a new immutable canonical source locator; "
            f"expected {CANONICAL_REFERENCE_PACK_SHA256}, found {pack_digest}"
        )
    return {
        "schemaVersion": 1,
        "packVersion": PACK_VERSION,
        "packDate": PACK_DATE,
        "assetProfile": "canonical-full-resolution",
        "activeIllustrationCount": 58,
        "contactSheetCount": 2,
        "historicalApprovedSupersededCount": 9,
        "historicalOwnerApprovedBaselineCount": 48,
        "currentLockedFinalCount": 22,
        "currentOwnerAcceptedCount": 8,
        "currentLockedWithoutRecordedOwnerAcceptanceCount": 14,
        "crossEraOverlapCount": 3,
        "uniqueApprovedOrLockedAcrossEras": 67,
        "uniqueOwnerAcceptedAcrossErasKnownCount": 53,
        "referencePackSha256": pack_digest,
        "canonicalPixelSource": {
            "repository": CANONICAL_REPOSITORY,
            "releaseTag": CANONICAL_RELEASE_TAG,
            "commit": CANONICAL_COMMIT,
            "manifestPath": CANONICAL_MANIFEST_PATH,
            "manifestSha256": CANONICAL_MANIFEST_SHA256,
            "assetProfile": "canonical-full-resolution",
            "referencePackSha256": CANONICAL_REFERENCE_PACK_SHA256,
        },
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
