#!/usr/bin/env python3
"""Rebuild a gallery plan out of the credits table in IMAGE-CREDITS.md.

    venv/bin/python tools/gallery/plan_from_credits.py --out /tmp/opencode/plan.json

Why this exists: the plan that produced the credits table lived in /tmp, which has
been wiped twice. The credits table is generated from the plan and committed, so
it is the only surviving record of which Commons file each installed photograph
came from, who shot it and under what licence -- and it can be read back into a
plan. This is what makes the loss recoverable rather than total.

It is not a substitute for a plan. It cannot know the fields the plan carried
that never reached the credits table: the Commons title in full, the original's
dimensions, the search score, the description. `title` is reconstructed from the
Commons filename, which is the part alt text is built from, so alt text is
regenerated exactly as it would have been. What is lost is reported.

Two classes of row are dropped rather than carried forward:

* **Rows credited to a scanned document.** A PDF or DjVu rendered to JPEG is a
  page of a book, and no pixel comparison can tell that from a photograph. Two
  Cape Coast Castle photographs were credited this way, to 19th-century books
  about Scotland. They are dropped here so they cannot be written back into the
  data file, and reported so the drop is visible.
* **A second copy of a picture already in the set.** Two Cape Coast Castle files
  are the same photograph at distance 0.97. Showing both is a visible repeat, so
  the later one is dropped and reported.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pixels  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
CREDITS = ROOT / "IMAGE-CREDITS.md"
DATA_FILES = [
    ROOT / "backend" / "data" / "destinations.json",
    ROOT / "backend" / "data" / "festivals.json",
]
GALLERY = ROOT / "assets" / "images" / "gallery"

NON_IMAGE = {".pdf", ".djvu", ".djv", ".djt", ".chm", ".epub"}

_LINK = re.compile(r"\[([^\]]*)\]\(((?:[^()\s]|\([^()]*\))*)\)")


def unlink(text: str) -> str:
    match = _LINK.search(text)
    return match.group(2).strip() if match else text.strip()


def link_text(text: str) -> str:
    match = _LINK.search(text)
    return match.group(1).strip() if match else text.strip()


def credits_rows(markdown: str) -> list[tuple[str, str, str, str, str]]:
    start = markdown.find("<!-- gallery-credits:start -->")
    end = markdown.find("<!-- gallery-credits:end -->")
    if start == -1 or end == -1:
        raise SystemExit("IMAGE-CREDITS.md has no gallery credits markers")
    rows = []
    header = False
    for line in markdown[start:end].splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 5:
            continue
        if cells[0] == "Place":
            header = True
            continue
        if set(cells[0]) <= set("-: ") or not header:
            continue
        rows.append(
            (
                cells[0],
                cells[1].strip("`"),
                link_text(cells[2]),
                link_text(cells[3]),
                unlink(cells[4]),
            )
        )
    if not rows:
        raise SystemExit("the gallery credits table is empty")
    return rows


def place_ids() -> dict[str, str]:
    """Display name -> entity id, from the data files.

    Built from the data rather than assumed, because the credits table is keyed on
    the display name and the plan is keyed on the id, and those two have to be the
    same string or every row silently fails to join.
    """
    names: dict[str, str] = {}
    ambiguous: list[str] = []
    for path in DATA_FILES:
        for row in json.loads(path.read_text()):
            name, entity = row.get("name", ""), row.get("id", "")
            if not name or not entity:
                continue
            if name in names and names[name] != entity:
                ambiguous.append(f"{name!r} is both {names[name]} and {entity}")
                continue
            names[name] = entity
    if ambiguous:
        for note in ambiguous:
            print(f"  ambiguous place name: {note}", file=sys.stderr)
    return names


def commons_title(source: str) -> str:
    """The Commons file title, from the credit's source URL."""
    match = re.search(r"commons\.wikimedia\.org/wiki/File:(.+)$", source)
    target = urllib.parse.unquote(match.group(1) if match else source)
    return target.strip("()[]<> \t")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="/tmp/opencode/plan.json")
    args = parser.parse_args()

    names = place_ids()
    rows = credits_rows(CREDITS.read_text())
    print(f"credits table    : {len(rows)} rows, {len(names)} places known")

    plan: list[dict[str, Any]] = []
    dropped_docs: list[str] = []
    unknown: list[str] = []

    for place, filename, author, licence, source in rows:
        title = commons_title(source)
        suffix = ("." + title.rsplit(".", 1)[-1].lower()) if "." in title else ""
        if suffix in NON_IMAGE:
            dropped_docs.append(f"{filename} -> {title} (credited to {author})")
            continue
        entity = names.get(place)
        if entity is None:
            unknown.append(f"{place} ({filename})")
            continue
        plan.append(
            {
                "entity": entity,
                "file": f"gallery/{filename}",
                "title": title,
                "author": author,
                "licence": licence,
                "licence_url": "",
                "source": source,
                "description": "",
                "rebuilt_from": "IMAGE-CREDITS.md",
            }
        )

    print(f"dropped, credited to a scanned document: {len(dropped_docs)}")
    for note in dropped_docs:
        print(f"  {note}")
    if unknown:
        print(f"dropped, place name not in the data files: {len(unknown)}")
        for note in unknown:
            print(f"  {note}")

    # Second copies of a picture already in the set. Compared across the whole plan,
    # not per place, because one photograph filed under two places is the failure
    # select.py exists to prevent and this is the last chance to notice it.
    seen: list[tuple[str, list[float]]] = []
    duplicates: list[str] = []
    kept: list[dict[str, Any]] = []
    for row in plan:
        path = GALLERY / Path(row["file"]).name
        mark = pixels.of_path(path)
        if mark is None:
            duplicates.append(f"{row['file']}: not a readable image, dropped")
            continue
        twin = pixels.first_duplicate(mark, seen)
        if twin is not None:
            duplicates.append(f"{row['file']}: the same picture as {twin}, dropped")
            continue
        seen.append((row["file"], mark))
        kept.append(row)

    print(f"dropped, a second copy of a picture already present: {len(duplicates)}")
    for note in duplicates:
        print(f"  {note}")

    by_place: dict[str, int] = {}
    for row in kept:
        by_place[row["entity"]] = by_place.get(row["entity"], 0) + 1
    thin = sorted(e for e, n in by_place.items() if n < 2)
    print(f"\nplan: {len(kept)} photographs across {len(by_place)} places")
    print(f"  too few for the row to render (< 2): {len(thin)} {thin}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(kept, indent=2, ensure_ascii=False) + "\n")
    print(f"written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())