#!/usr/bin/env python3
"""Deterministically validate the pitchdog-illustration Agent Skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
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


def validate(skill: Path, include_repository: bool) -> None:
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
            "provenance/SOURCE-MANIFEST.md",
            "scripts/build_asset_manifest.py",
            "scripts/build_contact_sheets.py",
            "scripts/package_skill.py",
            "scripts/validate_skill.py",
        ]
        for relative in required_root_files:
            require((ROOT / relative).is_file(), f"missing required repository file: {relative}")

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
        require(case_count >= 40, "eval suite must contain at least 40 adversarial cases")
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
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            manifest = {}
            ERRORS.append(f"invalid reference manifest: {error}")
        records = manifest.get("assets", []) if isinstance(manifest, dict) else []
        record_count = len(records)
        require(manifest.get("schemaVersion") == 1, "reference manifest schemaVersion must be 1")
        require(manifest.get("packVersion") == "2026-08-06-v1", "reference pack version mismatch")
        require(manifest.get("activeIllustrationCount") == 58, "active illustration count must be 58")
        require(manifest.get("contactSheetCount") == 2, "contact sheet count must be 2")
        require(manifest.get("uniqueOwnerApprovedAcrossEras") == 67, "approved historical union must be 67")
        require(record_count == 60, "reference manifest must contain 60 records")

        paths = [record.get("path") for record in records if isinstance(record, dict)]
        hashes = [record.get("sha256") for record in records if isinstance(record, dict) and record.get("kind") == "illustration"]
        require(len(paths) == len(set(paths)), "reference manifest paths must be unique")
        require(len(hashes) == len(set(hashes)), "active illustration bytes must be unique")
        tier_counts: dict[str, int] = {}
        checksum_lines: list[str] = []
        sensitive_binary_patterns = (
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
            except ValueError as error:
                ERRORS.append(f"{relative}: {error}")
                continue
            require(width == record.get("width") and height == record.get("height"), f"asset dimensions mismatch: {relative}")
            require(mode == record.get("mode") and bit_depth == record.get("bitDepth"), f"asset PNG mode mismatch: {relative}")
            tier = str(record.get("tier"))
            tier_counts[tier] = tier_counts.get(tier, 0) + (1 if record.get("kind") == "illustration" else 0)
            checksum_lines.append(f"{actual_hash}  {relative}")
            raw = path.read_bytes().lower()
            if b"c2pa" in raw and b"jumb" in raw:
                c2pa_count += 1
            for pattern in sensitive_binary_patterns:
                require(pattern not in raw, f"sensitive metadata marker {pattern!r} in {relative}")
        require(tier_counts.get("conceptual-ancestry") == 6, "Golden Six count mismatch")
        require(tier_counts.get("approved-website-breadth") == 30, "website-30 count mismatch")
        require(tier_counts.get("current-execution-authority") == 22, "approved-22 count mismatch")

        all_pngs = {path.relative_to(skill).as_posix() for path in (skill / "assets/references").rglob("*.png")}
        require(all_pngs == set(paths), "unmanifested or stale PNG path in reference pack")
        pack_hash = hashlib.sha256(("\n".join(checksum_lines) + "\n").encode()).hexdigest()
        require(pack_hash == manifest.get("referencePackSha256"), "reference pack aggregate checksum mismatch")
        checksum_file = skill / "assets/REFERENCE-PACK.sha256"
        if checksum_file.is_file():
            require(checksum_file.read_text(encoding="utf-8") == "\n".join(checksum_lines) + "\n", "REFERENCE-PACK.sha256 differs from manifest")
        spotty = next((record for record in records if str(record.get("path", "")).endswith("approved-22/01-spotty-quiet-afternoon.png")), None)
        require(spotty is not None, "corrected Spotty 01 record missing")
        if spotty:
            require(spotty.get("sha256") == "720e4445e0facbf05c4ab84c096fb0a14888c3fb41f0277984b416a84dea8d99", "Spotty 01 is not the four-limb corrected asset")

    if include_repository:
        require((ROOT / "LICENSE").read_bytes() == (skill / "LICENSE").read_bytes(), "root and skill licences must match")
        archive = ROOT / "archive/historical-approved-dogs-superseded"
        historical = sorted(archive.glob("*.png"))
        require(len(historical) == 9, "historical superseded dog archive must contain 9 PNGs")
        manifest_file = archive / "MANIFEST.sha256"
        require(manifest_file.is_file(), "historical archive checksum manifest missing")
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
        f"{c2pa_count} provenance-bearing PNGs, "
        f"{len(skill_text.splitlines())} SKILL.md lines, "
        f"{package_size} packaged bytes"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", type=Path, default=DEFAULT_SKILL)
    args = parser.parse_args()
    skill = args.skill.resolve()
    include_repository = skill == DEFAULT_SKILL.resolve()
    validate(skill, include_repository)


if __name__ == "__main__":
    main()
