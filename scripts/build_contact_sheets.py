#!/usr/bin/env python3
"""Build the website-30 scan sheet from the bundled full-resolution files."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


CANVAS = (230, 224, 216)
TILE = (246, 328, 320)
MARGIN = 20
GAP = 16
COLS = 5
IMAGE_WIDTH = 220
IMAGE_HEIGHT = 280
LABEL_HEIGHT = 32


def font() -> ImageFont.ImageFont:
    candidates = (
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    )
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), 13)
    return ImageFont.load_default(size=13)


def make_sheet(source: Path, output: Path) -> None:
    files = sorted(source.glob("*.png"))
    if len(files) != 30:
        raise SystemExit(f"expected 30 website PNGs, found {len(files)}")

    rows = (len(files) + COLS - 1) // COLS
    width = MARGIN * 2 + COLS * IMAGE_WIDTH + (COLS - 1) * GAP
    height = MARGIN * 2 + rows * (IMAGE_HEIGHT + LABEL_HEIGHT) + (rows - 1) * GAP
    sheet = Image.new("RGB", (width, height), CANVAS)
    draw = ImageDraw.Draw(sheet)
    label_font = font()

    for index, path in enumerate(files):
        row, col = divmod(index, COLS)
        x = MARGIN + col * (IMAGE_WIDTH + GAP)
        y = MARGIN + row * (IMAGE_HEIGHT + LABEL_HEIGHT + GAP)
        with Image.open(path) as source_image:
            image = source_image.convert("RGB")
            contained = ImageOps.contain(
                image,
                (IMAGE_WIDTH, IMAGE_HEIGHT),
                Image.Resampling.LANCZOS,
            )
        tile = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), TILE)
        paste_x = (IMAGE_WIDTH - contained.width) // 2
        paste_y = (IMAGE_HEIGHT - contained.height) // 2
        tile.paste(contained, (paste_x, paste_y))
        sheet.paste(tile, (x, y))

        label = path.stem
        if len(label) > 31:
            label = label[:30] + "…"
        draw.text((x + 2, y + IMAGE_HEIGHT + 7), label, fill=(36, 34, 32), font=label_font)

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, format="PNG", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", type=Path, default=Path("skills/pitchdog-illustration"))
    args = parser.parse_args()
    root = args.skill.resolve()
    make_sheet(
        root / "assets/references/website-30",
        root / "assets/references/website-30-contact-sheet.png",
    )


if __name__ == "__main__":
    main()
