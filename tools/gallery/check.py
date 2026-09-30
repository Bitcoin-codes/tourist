#!/usr/bin/env python3
"""Check the gallery data and the files behind it, without a browser.

    venv/bin/python tools/gallery/check.py

This is the QA that does not need eyes. It cannot tell whether a photograph is
sharp, well exposed, or actually shows the place it is filed under -- that needs
a person looking at the site, and there is no browser attached to this session.
What it can do is check every promise the rest of the pipeline makes, and several
of those are things that break silently:

* every `images` entry names a file that exists, at a size that fills the slot it
  will be painted into without upscaling;
* every entry carries alt text and a credit, because a missing alt is invisible
  in a screenshot and a missing credit breaks a licence condition;
* no photograph appears in two galleries, which is the whole point of the
  one-gallery-per-photograph rule in `select.py`;
* the arrays are the shape `normaliseExtraPhotos()` in the frontend expects, and
  a gallery with a single photograph is not written at all, because the strip
  renders only from two.

Sharpness is checked against the widest slot that will display the file, not the
smallest. The full-size viewer serves the master at up to 1920 CSS pixels, so a
file narrower than that is upscaled somewhere in the site, and it is easier to
know now than from a screenshot of a blurred photo.

Exit status is non-zero on any error, so this can gate a commit.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILES = [
    ROOT / "backend" / "data" / "destinations.json",
    ROOT / "backend" / "data" / "festivals.json",
]
CREDITS = ROOT / "IMAGE-CREDITS.md"

# The strip renders only when there is a hero plus at least two more, so an array
# of one is dead weight in the data file. Must match select.py and apply.py.
MIN_WANT = 2
MAX_PHOTOS = 6

# Slots, in CSS pixels, and the device pixel ratio each has to survive. Taken from
# styles.css and frontend/js/images.js; if those change, these must change with
# them or this check stops meaning anything.
SLOTS: list[tuple[str, int, int]] = [
    # name, css width, device pixel ratio to survive
    ("gallery thumbnail", 245, 2),   # .modal-gallery-thumb, 3:2
    ("modal hero", 800, 2),          # .modal-hero image, 800w
    ("full-size viewer", 1920, 1),   # serves the master itself
]

# Licence words that must appear in a credit string. A credit that names an author
# but not a licence does not satisfy CC BY or CC BY-SA attribution.
LICENCE_WORDS = re.compile(
    r"\b(CC0|CC BY(?:-SA)?|public domain|Public domain|PDM)\b", re.I
)

# The shape normaliseExtraPhotos() reads. Extra keys are fine; missing ones are not.
REQUIRED_KEYS = ("image", "alt", "credit")


def size_of(path: Path) -> tuple[int, int] | None:
    try:
        with Image.open(path) as image:
            return image.size
    except Exception:
        return None


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    # path -> the entities that use it, and the pixel sha1 for duplicate detection
    used_by: dict[str, list[str]] = {}
    by_content: dict[str, list[str]] = {}
    thin: list[str] = []
    thin_alts: list[str] = []
    total = 0

    for data_file in DATA_FILES:
        rows = json.loads(data_file.read_text())
        for row in rows:
            entity = row["id"]
            images = row.get("images")
            if images is None:
                continue
            if not isinstance(images, list) or not images:
                errors.append(f"{entity}: images is not a non-empty list")
                continue
            if len(images) < MIN_WANT:
                thin.append(f"{entity} ({len(images)})")
            if len(images) > MAX_PHOTOS:
                errors.append(f"{entity}: {len(images)} photographs, more than the {MAX_PHOTOS} max")

            alts: Counter[str] = Counter()
            for index, entry in enumerate(images):
                where = f"{entity} images[{index}]"
                if not isinstance(entry, dict):
                    errors.append(f"{where}: not an object")
                    continue
                missing = [key for key in REQUIRED_KEYS if not entry.get(key)]
                if missing:
                    errors.append(f"{where}: missing {', '.join(missing)}")
                    continue
                total += 1

                alt = str(entry["alt"]).strip()
                alts[alt] += 1
                if not alt:
                    errors.append(f"{where}: alt is empty")

                credit = str(entry["credit"]).strip()
                if not LICENCE_WORDS.search(credit):
                    errors.append(f"{where}: credit does not name a licence: {credit!r}")

                relative = str(entry["image"])
                path = ROOT / relative
                used_by.setdefault(relative, []).append(entity)
                if not path.exists():
                    errors.append(f"{where}: {relative} does not exist")
                    continue

                size = size_of(path)
                if size is None:
                    errors.append(f"{where}: {relative} is not a readable image")
                    continue
                width, height = size

                # The thumbnail is centre-cropped to 3:2, so what matters there is
                # that the frame is wide enough. A portrait file is not an error --
                # cover crops it -- but it is worth saying out loud.
                for name, css, ratio in SLOTS:
                    needed = css * ratio
                    if width < needed:
                        message = f"{where}: {relative} is {width}px, {name} needs {needed}px"
                        if name == "full-size viewer":
                            warnings.append(message + " (the viewer will upscale it)")
                        else:
                            errors.append(message)

                if width < height:
                    warnings.append(
                        f"{where}: {relative} is portrait ({width}x{height}); the 3:2 "
                        f"thumbnail will crop the sides"
                    )

                # Byte-identical detection is not enough: two Commons thumbnails
                # of the same photograph at the same size have different bytes but
                # the same picture. Comparing a downscaled grayscale signature
                # catches that, at the cost of decoding the file once.
                try:
                    with Image.open(path) as image:
                        signature = image.convert("L").resize((8, 8)).tobytes().hex()
                except Exception:
                    signature = f"{width}x{height}"
                by_content.setdefault(signature, []).append(entity)

            for alt, count in alts.items():
                if count > 1 and len(set(alts)) < len(images):
                    thin_alts.append(f"{entity}: {count}x {alt!r}")

    for relative, entities in sorted(used_by.items()):
        if len(entities) > 1:
            errors.append(
                f"{relative} is in {len(entities)} galleries: {', '.join(sorted(set(entities)))}. "
                f"A photograph belongs to one place; fix the plan, not the data file."
            )
    for signature, entities in sorted(by_content.items()):
        if len(set(entities)) > 1:
            errors.append(
                f"the same picture is filed under {len(set(entities))} places: "
                f"{', '.join(sorted(set(entities)))}"
            )

    print(f"galleries checked : {len(DATA_FILES)} data files")
    print(f"photographs       : {total}")
    print(f"files referenced  : {len(used_by)}")
    for name, css, ratio in SLOTS:
        print(f"  {name:20} {css} CSS px at {ratio}x = {css * ratio}px needed")
    if thin:
        print(f"\ntoo thin to render a strip ({len(thin)}):")
        for item in thin:
            print(f"  {item}")

    if thin_alts:
        print(f"\nrepeated alt text within one gallery ({len(thin_alts)}):")
        for item in thin_alts:
            print(f"  {item}")

    if warnings:
        print(f"\nwarnings ({len(warnings)}):")
        for item in warnings:
            print(f"  {item}")

    # Attribution is a licence condition, so a photograph with no row in the
    # credits table is an error rather than a warning.
    text = CREDITS.read_text()
    missing_credits = [
        relative for relative in used_by if f"`{Path(relative).name}`" not in text
    ]
    if missing_credits:
        errors.append(
            f"{len(missing_credits)} photographs are not in IMAGE-CREDITS.md: "
            f"{', '.join(sorted(missing_credits)[:5])}"
        )

    if errors:
        print(f"\nFAIL: {len(errors)} problems")
        for item in errors:
            print(f"  {item}")
        return 1
    print("\nOK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
