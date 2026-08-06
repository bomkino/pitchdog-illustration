#!/usr/bin/env python3
"""Validate the pitchdog-illustration Agent Skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import zlib
from pathlib import Path
from urllib.parse import unquote

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install PyYAML==6.0.2.", file=sys.stderr)
    raise SystemExit(2)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SKILL = ROOT / "skills" / "pitchdog-illustration"
ERRORS: list[str] = []
CORRECTED_SPOTTY_SHA256 = "720e4445e0facbf05c4ab84c096fb0a14888c3fb41f0277984b416a84dea8d99"
CANONICAL_PROFILE = "canonical-full-resolution"
CHATGPT_PROFILE = "chatgpt-portable"
CANONICAL_REPOSITORY = "https://github.com/bomkino/pitchdog-illustration"
CANONICAL_RELEASE_TAG = "v1.0.0"
CANONICAL_COMMIT = "1ade97592e3779e26f0280a02a58505de935d955"
CANONICAL_MANIFEST_PATH = "skills/pitchdog-illustration/assets/reference-manifest.json"
CANONICAL_MANIFEST_SHA256 = "4cba40dd6f01e3997d1913c4a4c89a88c0b707811aef9c11c95611fb3426fae8"
CANONICAL_REFERENCE_PACK_SHA256 = "d99b9c379b5e3336d3c19055ef29147698796276b8cef86ed8ee557356ca1c65"
RELEASE_V101_ARCHIVE_SHA256 = {
    "pitchdog-illustration-full.zip": "ec06bd9298487626bf6bb471f04eb7c95eb6f068a0ab928b9d436976bcb3e24a",
    "pitchdog-illustration-full.skill": "ec06bd9298487626bf6bb471f04eb7c95eb6f068a0ab928b9d436976bcb3e24a",
    "pitchdog-illustration.zip": "68e6c9288f70ae2fb5fe8d68df8f8caef9d6cfba730af2070d73628a604a8977",
    "pitchdog-illustration.skill": "68e6c9288f70ae2fb5fe8d68df8f8caef9d6cfba730af2070d73628a604a8977",
}
CURRENT_OWNER_ACCEPTED_FILENAMES = {
    "01-manali-lightning-sensible-shoes.png",
    "02-manali-good-chair-quiet-idea.png",
    "03-manali-unfolded-horizon.png",
    "01-juno-loose-end-of-impossible.png",
    "01-kumail-persuaded-knot.png",
    "02-kumail-doorway-learned-outline.png",
    "03-kumail-smallest-failure.png",
    "04-kumail-applauded-thought.png",
}
PROHIBITED_CURRENT_JUNO_RECORDS = {
    "28-go-get-em": {
        "knownLimitations": [
            "Juno predates the current likeness and sisters-scale lock and reads materially larger than the required 1.1× relationship."
        ],
        "reuseCondition": (
            "Metaphor and dated placement evidence only. If the final Process coda retains this slot, "
            "rebuild Juno from current approved-22 identity and 1.1× scale authority before use."
        ),
    },
    "30-lost-page": {
        "knownLimitations": [
            "Juno is broad, stocky, and generic relative to the current lean body, darker muzzle, feathered ears, and narrow-face lock."
        ],
        "reuseCondition": (
            "Metaphor and dated 404 placement evidence only. Rebuild Juno from current approved-22 identity authority; "
            "do not reuse these pixels as current likeness evidence."
        ),
    },
}
SENSITIVE_BINARY_PATTERNS = (
    b"/users/",
    b"file:" + b"///",
    b"gpslatitude",
    b"gpslongitude",
    b"latitude",
    b"longitude",
    b"\"prompt\"",
    b"github_pat_",
    b"-----begin private key-----",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        ERRORS.append(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def png_info(path: Path) -> tuple[int, int, str, int]:
    header = path.read_bytes()[:29]
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("invalid PNG signature or IHDR")
    width, height = struct.unpack(">II", header[16:24])
    bit_depth = header[24]
    colour_type = header[25]
    modes = {0: "grayscale", 2: "rgb", 3: "indexed", 4: "grayscale-alpha", 6: "rgba"}
    return width, height, modes.get(colour_type, f"png-colour-type-{colour_type}"), bit_depth


def png_chunks(path: Path) -> list[tuple[bytes, bytes]]:
    raw = path.read_bytes()
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("invalid PNG signature")
    chunks: list[tuple[bytes, bytes]] = []
    cursor = 8
    saw_iend = False
    while cursor < len(raw):
        if cursor + 12 > len(raw):
            raise ValueError("truncated PNG chunk")
        length = struct.unpack(">I", raw[cursor : cursor + 4])[0]
        chunk_type = raw[cursor + 4 : cursor + 8]
        payload_start = cursor + 8
        payload_end = payload_start + length
        crc_end = payload_end + 4
        if crc_end > len(raw):
            raise ValueError("PNG chunk exceeds file boundary")
        payload = raw[payload_start:payload_end]
        expected_crc = struct.unpack(">I", raw[payload_end:crc_end])[0]
        actual_crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ValueError(f"PNG chunk CRC mismatch: {chunk_type!r}")
        chunks.append((chunk_type, payload))
        cursor = crc_end
        if chunk_type == b"IEND":
            saw_iend = True
            break
    if not saw_iend or cursor != len(raw):
        raise ValueError("PNG does not end cleanly at IEND")
    return chunks


def duplicate_yaml_keys(path: Path) -> list[str]:
    try:
        root = yaml.compose(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        ERRORS.append(f"invalid YAML in {path}: {error}")
        return []
    duplicates: list[str] = []

    def walk(node: yaml.Node, location: str) -> None:
        if isinstance(node, yaml.MappingNode):
            seen: set[str] = set()
            for key_node, value_node in node.value:
                key = str(getattr(key_node, "value", "<complex-key>"))
                key_location = f"{location}.{key}" if location else key
                if key in seen:
                    duplicates.append(key_location)
                seen.add(key)
                walk(value_node, key_location)
        elif isinstance(node, yaml.SequenceNode):
            for index, item in enumerate(node.value):
                walk(item, f"{location}[{index}]")

    if root is not None:
        walk(root, "")
    return duplicates


def validate(skill: Path, include_repository: bool, release_dist: Path | None = None) -> None:
    required_skill_files = [
        "SKILL.md",
        "LICENSE",
        "NOTICE.md",
        "agents/openai.yaml",
        "assets/reference-manifest.json",
        "assets/REFERENCE-PACK.sha256",
        "assets/references/approved-22-contact-sheet.png",
        "assets/references/website-30-contact-sheet.png",
        "evals/evals.json",
        "references/anti-patterns.md",
        "references/approved-catalog.md",
        "references/calibration.md",
        "references/identity-and-relationships.md",
        "references/metaphor-engine.md",
        "references/production-and-provenance.md",
        "references/prompting-and-tools.md",
        "references/qa-and-rejection.md",
        "references/reference-system.md",
        "references/visual-law.md",
        "references/website-approved-catalog.md",
        "references/website-inventory.md",
        "templates/illustration-brief.md",
        "templates/character-lock.md",
        "templates/metaphor-thumbnails.md",
        "templates/candidate-review.md",
        "templates/final-metadata.md",
    ]
    for relative in required_skill_files:
        require((skill / relative).is_file(), f"missing required skill file: {relative}")

    if include_repository:
        required_root_files = [
            "README.md",
            "LICENSE",
            "NOTICE.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "CODE_OF_CONDUCT.md",
            "CHANGELOG.md",
            "requirements-dev.txt",
            "docs/source-resolution.md",
            "docs/evaluation-report.md",
            "docs/releases/v1.0.1.md",
            "provenance/SOURCE-MANIFEST.md",
            "provenance/RELEASE-ASSETS-v1.0.1.sha256",
            "scripts/build_asset_manifest.py",
            "scripts/build_contact_sheets.py",
            "scripts/package_skill.py",
            "scripts/validate_skill.py",
        ]
        for relative in required_root_files:
            require((ROOT / relative).is_file(), f"missing required repository file: {relative}")
        workflow_path = ROOT / ".github/workflows/validate.yml"
        require(workflow_path.is_file(), "missing GitHub validation workflow")
        if workflow_path.is_file():
            require(not duplicate_yaml_keys(workflow_path), "GitHub workflow contains duplicate YAML keys")
            workflow_text = workflow_path.read_text(encoding="utf-8")
            for required_command in (
                'quick_validate.py "$portable_dir/pitchdog-illustration"',
                "cmp dist/pitchdog-illustration-full.zip dist-profile-full/pitchdog-illustration-full.zip",
                "cmp dist/pitchdog-illustration.zip dist-profile-chatgpt/pitchdog-illustration.zip",
            ):
                require(required_command in workflow_text, f"GitHub workflow omits release gate: {required_command}")

    skill_md = skill / "SKILL.md"
    if not skill_md.is_file():
        return
    skill_text = skill_md.read_text(encoding="utf-8")
    frontmatter = re.match(r"\A---\n(.*?)\n---\n", skill_text, re.DOTALL)
    require(frontmatter is not None, "SKILL.md must start with YAML frontmatter")
    if frontmatter:
        try:
            metadata = yaml.safe_load(frontmatter.group(1))
        except yaml.YAMLError as error:
            metadata = None
            ERRORS.append(f"invalid SKILL.md frontmatter YAML: {error}")
        require(isinstance(metadata, dict), "SKILL.md frontmatter must be a mapping")
        if isinstance(metadata, dict):
            require(set(metadata) == {"name", "description"}, "frontmatter must contain only name and description")
            name = metadata.get("name")
            description = metadata.get("description")
            require(name == "pitchdog-illustration", "frontmatter name must be pitchdog-illustration")
            require(isinstance(name, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) is not None, "invalid skill name")
            require(isinstance(description, str) and 180 <= len(description) <= 1024, "description must be 180-1024 characters")
            require("$pitchdog-illustration" in str(description), "description must include explicit invocation")
    require(skill.name == "pitchdog-illustration", "skill folder must match frontmatter name")
    require(len(skill_text.splitlines()) < 500, "SKILL.md must remain under 500 lines")

    markdown_files = list(skill.rglob("*.md"))
    if include_repository:
        markdown_files.extend(path for path in ROOT.rglob("*.md") if ".git" not in path.parts and skill not in path.parents)
    link_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for markdown in markdown_files:
        text = markdown.read_text(encoding="utf-8")
        for target in link_pattern.findall(text):
            target = target.strip().split("#", 1)[0]
            if not target or re.match(r"^(?:https?://|mailto:)", target):
                continue
            resolved = (markdown.parent / unquote(target)).resolve()
            require(resolved.exists(), f"broken local link in {markdown}: {target}")

    text_extensions = {".md", ".yaml", ".yml", ".json", ".txt", ".py"}
    text_roots = [skill]
    if include_repository:
        text_roots = [ROOT]
    seen: set[Path] = set()
    secret_patterns = (
        re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
        re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
        re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"),
        re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    )
    for base in text_roots:
        for path in base.rglob("*"):
            if path in seen or not path.is_file() or path.suffix.lower() not in text_extensions:
                continue
            if any(part in {".git", ".venv", "dist"} for part in path.parts):
                continue
            seen.add(path)
            text = path.read_text(encoding="utf-8")
            private_user_prefix = "/" + "Users" + "/"
            private_file_uri = "file:" + "///"
            placeholder_pattern = re.compile(
                r"\[(?:TO" + r"DO|T" + r"BD)\]|\bT" + r"BD\b",
                re.IGNORECASE,
            )
            require(private_user_prefix not in text, f"private absolute path in {path}")
            require(private_file_uri not in text, f"private file URI in {path}")
            require(placeholder_pattern.search(text) is None, f"placeholder in {path}")
            for pattern in secret_patterns:
                require(pattern.search(text) is None, f"possible secret in {path}")

    openai_path = skill / "agents/openai.yaml"
    if openai_path.is_file():
        try:
            openai = yaml.safe_load(openai_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            openai = None
            ERRORS.append(f"invalid agents/openai.yaml: {error}")
        interface = openai.get("interface", {}) if isinstance(openai, dict) else {}
        require(set(openai or {}) == {"interface"}, "openai.yaml must contain only interface at top level")
        require(interface.get("display_name") == "pitch.dog Illustration", "openai display_name mismatch")
        short = interface.get("short_description", "")
        require(isinstance(short, str) and 25 <= len(short) <= 64, "openai short_description must be 25-64 characters")
        require("$pitchdog-illustration" in str(interface.get("default_prompt", "")), "default_prompt must mention $pitchdog-illustration")

    eval_path = skill / "evals/evals.json"
    case_count = 0
    if eval_path.is_file():
        try:
            evals = json.loads(eval_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            evals = {}
            ERRORS.append(f"invalid evals JSON: {error}")
        cases = evals.get("cases", []) if isinstance(evals, dict) else []
        case_count = len(cases)
        require(case_count >= 45, "eval suite must contain at least 45 adversarial cases")
        ids = [case.get("id") for case in cases if isinstance(case, dict)]
        require(len(ids) == len(set(ids)), "eval IDs must be unique")
        for case in cases:
            require(isinstance(case, dict), "every eval case must be a mapping")
            if not isinstance(case, dict):
                continue
            for field in ("id", "prompt", "expected_mode", "must", "must_not", "failure_caught"):
                require(bool(case.get(field)), f"eval {case.get('id', '<missing>')} lacks {field}")

    for path in skill.rglob("*"):
        require(not path.is_symlink(), f"symlink not allowed: {path.relative_to(skill)}")
        if path.name.startswith("."):
            require(False, f"hidden file not allowed in skill: {path.relative_to(skill)}")
        if path.is_file():
            require(path.suffix.lower() not in {".ttf", ".otf", ".woff", ".woff2", ".eot", ".exe", ".dylib", ".so", ".sh"}, f"forbidden binary or executable: {path.relative_to(skill)}")
            require(not path.read_bytes().startswith(b"version https://git-lfs.github.com/spec"), f"Git LFS pointer not allowed: {path.relative_to(skill)}")
    require(not (skill / "scripts").exists(), "runtime skill must not contain executable scripts")
    package_size = sum(path.stat().st_size for path in skill.rglob("*") if path.is_file())
    require(package_size < 150_000_000, "skill package must stay below 150 MB")

    manifest_path = skill / "assets/reference-manifest.json"
    record_count = 0
    c2pa_count = 0
    asset_profile = "missing"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            manifest = {}
            ERRORS.append(f"invalid reference manifest: {error}")
        records = manifest.get("assets", []) if isinstance(manifest, dict) else []
        record_count = len(records)
        asset_profile = manifest.get("assetProfile")
        require(manifest.get("schemaVersion") == 1, "reference manifest schemaVersion must be 1")
        require(asset_profile in {CANONICAL_PROFILE, CHATGPT_PROFILE}, "unknown reference asset profile")
        expected_pack_version = "2026-08-06-v1-chatgpt-portable" if asset_profile == CHATGPT_PROFILE else "2026-08-06-v1"
        require(manifest.get("packVersion") == expected_pack_version, "reference pack version mismatch")
        require(manifest.get("activeIllustrationCount") == 58, "active illustration count must be 58")
        require(manifest.get("contactSheetCount") == 2, "contact sheet count must be 2")
        require(manifest.get("historicalApprovedSupersededCount") == 9, "historical superseded count must be 9")
        require(manifest.get("historicalOwnerApprovedBaselineCount") == 48, "historical owner-approved baseline must be 48")
        require(manifest.get("currentLockedFinalCount") == 22, "current locked-final count must be 22")
        require(manifest.get("currentOwnerAcceptedCount") == 8, "current owner-accepted count must be 8")
        require(
            manifest.get("currentLockedWithoutRecordedOwnerAcceptanceCount") == 14,
            "current locked-without-recorded-owner-acceptance count must be 14",
        )
        require(manifest.get("crossEraOverlapCount") == 3, "cross-era overlap count must be 3")
        require(manifest.get("uniqueApprovedOrLockedAcrossEras") == 67, "approved-or-locked historical union must be 67")
        require(manifest.get("uniqueOwnerAcceptedAcrossErasKnownCount") == 53, "known owner-accepted union must be 53")
        require(record_count == 60, "reference manifest must contain 60 records")

        canonical = manifest.get("canonicalPixelSource", {})
        expected_canonical = {
            "repository": CANONICAL_REPOSITORY,
            "releaseTag": CANONICAL_RELEASE_TAG,
            "commit": CANONICAL_COMMIT,
            "manifestPath": CANONICAL_MANIFEST_PATH,
            "manifestSha256": CANONICAL_MANIFEST_SHA256,
            "assetProfile": CANONICAL_PROFILE,
            "referencePackSha256": CANONICAL_REFERENCE_PACK_SHA256,
        }
        require(canonical == expected_canonical, "immutable canonical pixel-source locator mismatch")

        paths = [record.get("path") for record in records if isinstance(record, dict)]
        hashes = [record.get("sha256") for record in records if isinstance(record, dict) and record.get("kind") == "illustration"]
        source_hashes = [record.get("sourceSha256") for record in records if isinstance(record, dict) and record.get("kind") == "illustration"]
        require(len(paths) == len(set(paths)), "reference manifest paths must be unique")
        require(len(hashes) == len(set(hashes)), "active illustration bytes must be unique")
        if asset_profile == CHATGPT_PROFILE:
            require(
                package_size < 25_000_000,
                "portable skill exceeds the 25 MB repository budget based on the Skills uploader gate observed on 2026-08-06",
            )
            require(len(source_hashes) == len(set(source_hashes)), "portable source illustration hashes must be unique")
            require(
                re.fullmatch(r"[0-9a-f]{64}", str(manifest.get("sourceReferencePackSha256", ""))) is not None,
                "portable manifest lacks the canonical reference-pack receipt",
            )
            rendering = manifest.get("portableRendering", {})
            require(rendering.get("illustrationMaxLongEdge") == 800, "portable illustration edge policy mismatch")
            require(rendering.get("contactSheetMaxLongEdge") == 1280, "portable contact-sheet edge policy mismatch")
            require(rendering.get("colourSpaceDeclaration") == "PNG sRGB chunk", "portable colour-space declaration mismatch")
            require(rendering.get("pngSrgbRenderingIntent") == 0, "portable sRGB rendering intent mismatch")
            require(
                rendering.get("metadataPolicy") == "source metadata stripped; fresh sRGB declaration added",
                "portable metadata policy mismatch",
            )
        tier_counts: dict[str, int] = {}
        checksum_lines: list[str] = []
        source_checksum_lines: list[str] = []
        for record in records:
            if not isinstance(record, dict):
                require(False, "reference manifest record must be a mapping")
                continue
            relative = record.get("path")
            require(isinstance(relative, str) and relative.startswith("assets/references/"), f"invalid asset path: {relative}")
            path = skill / str(relative)
            require(path.is_file(), f"manifested asset missing: {relative}")
            if not path.is_file():
                continue
            actual_hash = sha256(path)
            require(actual_hash == record.get("sha256"), f"asset checksum mismatch: {relative}")
            try:
                width, height, mode, bit_depth = png_info(path)
                chunks = png_chunks(path)
            except ValueError as error:
                ERRORS.append(f"{relative}: {error}")
                continue
            require(width == record.get("width") and height == record.get("height"), f"asset dimensions mismatch: {relative}")
            require(mode == record.get("mode") and bit_depth == record.get("bitDepth"), f"asset PNG mode mismatch: {relative}")
            raw = path.read_bytes().lower()
            actual_c2pa_marker = b"c2pa" in raw and b"jumb" in raw
            require(record.get("c2paJumbMarker") is actual_c2pa_marker, f"C2PA/JUMBF marker receipt mismatch: {relative}")
            if asset_profile == CHATGPT_PROFILE:
                source_sha = record.get("sourceSha256")
                source_width = record.get("sourceWidth")
                source_height = record.get("sourceHeight")
                require(re.fullmatch(r"[0-9a-f]{64}", str(source_sha or "")) is not None, f"portable source hash missing: {relative}")
                require(isinstance(source_width, int) and source_width >= width, f"portable source width invalid: {relative}")
                require(isinstance(source_height, int) and source_height >= height, f"portable source height invalid: {relative}")
                edge_limit = 1280 if record.get("kind") == "contact-sheet" else 800
                require(max(width, height) <= edge_limit, f"portable long edge exceeds policy: {relative}")
                require(record.get("derivation") == "Pillow 11.3.0 LANCZOS PNG derivative", f"portable derivation missing: {relative}")
                require(isinstance(record.get("sourceC2paJumbMarker"), bool), f"portable source provenance marker missing: {relative}")
                srgb_chunks = [payload for chunk_type, payload in chunks if chunk_type == b"sRGB"]
                require(srgb_chunks == [b"\x00"], f"portable PNG must contain one perceptual sRGB chunk: {relative}")
                require(
                    not any(chunk_type == b"iCCP" for chunk_type, _ in chunks),
                    f"portable PNG must not carry a competing ICC profile: {relative}",
                )
                chunk_types = [chunk_type for chunk_type, _ in chunks]
                require(
                    len(chunk_types) >= 4
                    and chunk_types[:2] == [b"IHDR", b"sRGB"]
                    and chunk_types[-1] == b"IEND"
                    and all(chunk_type == b"IDAT" for chunk_type in chunk_types[2:-1]),
                    f"portable PNG contains unexpected or misordered metadata chunks: {relative}",
                )
                source_checksum_lines.append(f"{source_sha}  {relative}")
            tier = str(record.get("tier"))
            tier_counts[tier] = tier_counts.get(tier, 0) + (1 if record.get("kind") == "illustration" else 0)
            checksum_lines.append(f"{actual_hash}  {relative}")
            if b"c2pa" in raw and b"jumb" in raw:
                c2pa_count += 1
            for pattern in SENSITIVE_BINARY_PATTERNS:
                require(pattern not in raw, f"sensitive metadata marker {pattern!r} in {relative}")
        require(tier_counts.get("conceptual-ancestry") == 6, "Golden Six count mismatch")
        require(tier_counts.get("approved-website-breadth") == 30, "website-30 count mismatch")
        require(tier_counts.get("current-execution-authority") == 22, "approved-22 count mismatch")
        current_records = [
            record for record in records
            if isinstance(record, dict) and record.get("tier") == "current-execution-authority"
        ]
        recorded_owner_accepted = {
            Path(str(record.get("path"))).name
            for record in current_records
            if record.get("status") == "owner-approved-current-final"
        }
        require(
            recorded_owner_accepted == CURRENT_OWNER_ACCEPTED_FILENAMES,
            "current per-file owner-acceptance receipts do not match recorded gates",
        )
        for record in current_records:
            filename = Path(str(record.get("path"))).name
            expected_status = "owner-approved-current-final" if filename in CURRENT_OWNER_ACCEPTED_FILENAMES else "locked-current-final"
            require(record.get("status") == expected_status, f"current status truth mismatch: {filename}")

        prohibited_juno_records = {
            str(record.get("id")): record
            for record in records
            if record.get("identityAuthority") == "prohibited-current-juno"
        }
        require(
            set(prohibited_juno_records) == set(PROHIBITED_CURRENT_JUNO_RECORDS),
            "exactly website records 28 and 30 must be prohibited as current Juno identity authority",
        )
        for record_id, expected in PROHIBITED_CURRENT_JUNO_RECORDS.items():
            record = prohibited_juno_records.get(record_id, {})
            require(record.get("knownLimitations") == expected["knownLimitations"], f"legacy Juno limitation mismatch: {record_id}")
            require(record.get("reuseCondition") == expected["reuseCondition"], f"legacy Juno reuse condition mismatch: {record_id}")
        for record in records:
            if str(record.get("id")) not in PROHIBITED_CURRENT_JUNO_RECORDS:
                require(
                    not any(field in record for field in ("identityAuthority", "knownLimitations", "reuseCondition")),
                    f"unexpected current-use warning fields: {record.get('id')}",
                )

        all_pngs = {path.relative_to(skill).as_posix() for path in (skill / "assets/references").rglob("*.png")}
        require(all_pngs == set(paths), "unmanifested or stale PNG path in reference pack")
        pack_hash = hashlib.sha256(("\n".join(checksum_lines) + "\n").encode()).hexdigest()
        require(pack_hash == manifest.get("referencePackSha256"), "reference pack aggregate checksum mismatch")
        if isinstance(canonical, dict):
            expected_source_pack = manifest.get("sourceReferencePackSha256", manifest.get("referencePackSha256"))
            require(
                canonical.get("referencePackSha256") == expected_source_pack,
                "canonical locator receipt differs from its source reference pack",
            )
        if asset_profile == CHATGPT_PROFILE:
            source_pack_hash = hashlib.sha256(("\n".join(source_checksum_lines) + "\n").encode()).hexdigest()
            require(
                source_pack_hash == manifest.get("sourceReferencePackSha256"),
                "portable source receipts do not reconstruct the canonical reference-pack receipt",
            )
        checksum_file = skill / "assets/REFERENCE-PACK.sha256"
        if checksum_file.is_file():
            require(checksum_file.read_text(encoding="utf-8") == "\n".join(checksum_lines) + "\n", "REFERENCE-PACK.sha256 differs from manifest")
        spotty = next((record for record in records if str(record.get("path", "")).endswith("approved-22/01-spotty-quiet-afternoon.png")), None)
        require(spotty is not None, "corrected Spotty 01 record missing")
        if spotty:
            spotty_receipt = spotty.get("sourceSha256") if asset_profile == CHATGPT_PROFILE else spotty.get("sha256")
            require(spotty_receipt == CORRECTED_SPOTTY_SHA256, "Spotty 01 is not derived from the four-limb corrected asset")
        if asset_profile == CANONICAL_PROFILE:
            require(c2pa_count == 54, "canonical pack C2PA/JUMBF marker count must remain exactly 54")
        elif asset_profile == CHATGPT_PROFILE:
            require(c2pa_count == 0, "portable derivatives must not retain stale embedded provenance payloads")

    if include_repository:
        require((ROOT / "LICENSE").read_bytes() == (skill / "LICENSE").read_bytes(), "root and skill licences must match")
        release_receipt = ROOT / "provenance/RELEASE-ASSETS-v1.0.1.sha256"
        expected_release_lines = [f"{digest}  {name}" for name, digest in RELEASE_V101_ARCHIVE_SHA256.items()]
        if release_receipt.is_file():
            require(
                release_receipt.read_text(encoding="utf-8") == "\n".join(expected_release_lines) + "\n",
                "v1.0.1 release receipt differs from pinned archive hashes",
            )
        release_notes = ROOT / "docs/releases/v1.0.1.md"
        if release_notes.is_file():
            notes = release_notes.read_text(encoding="utf-8")
            for digest in set(RELEASE_V101_ARCHIVE_SHA256.values()):
                require(digest in notes, f"v1.0.1 release notes omit archive hash: {digest}")
        if release_dist is not None:
            for name, digest in RELEASE_V101_ARCHIVE_SHA256.items():
                release_asset = release_dist / name
                require(release_asset.is_file(), f"pinned v1.0.1 release asset missing: {name}")
                if release_asset.is_file():
                    require(sha256(release_asset) == digest, f"release asset differs from pinned v1.0.1 receipt: {name}")
        archive = ROOT / "archive/historical-approved-dogs-superseded"
        historical = sorted(archive.glob("*.png"))
        require(len(historical) == 9, "historical superseded dog archive must contain 9 PNGs")
        for path in historical:
            require(not path.is_symlink(), f"historical archive symlink not allowed: {path.name}")
            try:
                png_info(path)
                png_chunks(path)
            except ValueError as error:
                ERRORS.append(f"historical archive {path.name}: {error}")
                continue
            raw = path.read_bytes().lower()
            for pattern in SENSITIVE_BINARY_PATTERNS:
                require(pattern not in raw, f"sensitive metadata marker {pattern!r} in historical archive {path.name}")
        manifest_file = archive / "MANIFEST.sha256"
        require(manifest_file.is_file(), "historical archive checksum manifest missing")
        require(not manifest_file.is_symlink(), "historical archive checksum manifest must not be a symlink")
        if manifest_file.is_file():
            expected = [f"{sha256(path)}  {path.name}" for path in historical]
            require(manifest_file.read_text(encoding="utf-8") == "\n".join(expected) + "\n", "historical archive checksum mismatch")

    if ERRORS:
        print("FAIL")
        for error in ERRORS:
            print(f"- {error}")
        raise SystemExit(1)

    print(
        "PASS: "
        f"{len(required_skill_files)} required skill files, "
        f"{case_count} evals, {record_count} manifested references, "
        f"{c2pa_count} C2PA/JUMBF marker-bearing PNGs, "
        f"{len(skill_text.splitlines())} SKILL.md lines, {asset_profile} profile, "
        f"{package_size} packaged bytes"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", type=Path, default=DEFAULT_SKILL)
    parser.add_argument("--release-dist", type=Path)
    args = parser.parse_args()
    skill = args.skill.resolve()
    release_dist = args.release_dist.resolve() if args.release_dist else None
    include_repository = skill == DEFAULT_SKILL.resolve()
    validate(skill, include_repository, release_dist)


if __name__ == "__main__":
    main()
