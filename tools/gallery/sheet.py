#!/usr/bin/env python3
"""Labelled contact sheets, so candidates can be judged as a set rather than a
round trip each.

Reading photographs one at a time costs a message apiece, and reading several
at once in this harness returns them shuffled against their paths -- which is
how a wrong place gets approved by tired eyes. So the photographs are tiled onto
one PNG per batch and every tile carries its own number and title beneath it:
the sheet cannot lose track of which photograph is which, and a batch of
destinations costs a single look.

Two sources:

* ``--plan`` tiles what is already on disk -- the photographs selected for
  installing -- and touches no network, so it can run while Commons is busy
  downloading for someone else. This is the gate before apply.

* the default tiles a checkpoint row's candidates, fetching thumbnails from
  Commons, for inspecting a pool that has not been through selection.

    venv/bin/python tools/gallery/sheet.py --plan gambaga-escarpment-lookout
    venv/bin/python tools/gallery/sheet.py --plan --out /tmp/opencode/batch1.png a b c
    venv/bin/python tools/gallery/sheet.py fort-royal --kept 9
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CHECKPOINT = REPO / ".gallery-state" / "select" / "select-checkpoint.jsonl"
PLAN = REPO / ".gallery-state" / "select" / "select-plan.json"

TILE_W = 340
LABEL_H = 46
HEADER_H = 30
PAD = 8
COLS = 3
TILE_H = int(TILE_W * 3 / 4)


def _plan_groups(entities: list[str]) -> list[tuple[str, list[dict]]]:
    """Plan rows grouped by entity, in the order the entities were named."""
    rows = json.loads(PLAN.read_text(encoding="utf-8"))
    groups: list[tuple[str, list[dict]]] = []
    for entity in entities:
        mine = [r for r in rows if r.get("entity") == entity]
        if mine:
            groups.append((entity, mine))
        else:
            print(f"  (nothing in the plan for {entity})", file=sys.stderr)
    if not groups:
        sys.exit("nothing in the plan to show")
    return groups


def _draw(groups: list[tuple[str, list[tuple[str, Image.Image | None]]]]) -> Image.Image:
    """Tile already-labelled images under one header per group."""
    font = ImageFont.load_default(size=13)
    title_font = ImageFont.load_default(size=15)
    cols = COLS
    height = 34
    for _, tiles in groups:
        height += HEADER_H
        rows = (len(tiles) + cols - 1) // cols
        height += rows * (TILE_H + LABEL_H + PAD) + PAD

    sheet = Image.new("RGB", (cols * (TILE_W + PAD) + PAD, height), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((PAD, 10), "gallery inspection sheet", fill="gray", font=title_font)

    y = 34
    for name, tiles in groups:
        draw.rectangle([PAD, y, sheet.width - PAD, y + HEADER_H - 6], fill="#eeeeee")
        draw.text(
            (PAD + 8, y + 6),
            f"{name}  --  {len(tiles)} photographs",
            fill="black",
            font=title_font,
        )
        y += HEADER_H
        for index, (label, image) in enumerate(tiles):
            x = PAD + (index % cols) * (TILE_W + PAD)
            ty = y + (index // cols) * (TILE_H + LABEL_H + PAD)
            if image is None:
                draw.rectangle([x, ty, x + TILE_W, ty + TILE_H], outline="red", width=2)
                draw.text((x + 10, ty + 10), "not available", fill="red", font=font)
            else:
                image.thumbnail((TILE_W, TILE_H))
                sheet.paste(image, (x + (TILE_W - image.width) // 2, ty))
            draw.text((x, ty + TILE_H + 4), label[:58], fill="black", font=font)
        y += ((len(tiles) + cols - 1) // cols) * (TILE_H + LABEL_H + PAD) + PAD
    return sheet


def _open(path: Path) -> Image.Image | None:
    try:
        return Image.open(path).convert("RGB")
    except Exception:  # noqa: BLE001 - a tile that will not open is reported
        return None


def build_plan(entities: list[str], out: Path) -> Path:
    """Tile the plan's own photographs, from disk, for the gate before apply."""
    groups: list[tuple[str, list[tuple[str, Image.Image | None]]]] = []
    for name, rows in _plan_groups(entities):
        tiles = []
        for index, row in enumerate(rows, start=1):
            path = REPO / "assets" / "images" / row["file"]
            label = f"{index}. {(row.get('title') or row['file'])[5:75]}"
            tiles.append((label, _open(path)))
        groups.append((name, tiles))
    out.parent.mkdir(parents=True, exist_ok=True)
    _draw(groups).save(out)
    return out


def _thumbnail(title: str, width: int = TILE_W) -> bytes | None:
    """The file's thumbnail, or None if Commons will not serve it.

    Special:FilePath redirects to the upload host and honours `width` -- the
    same way the site asks for a small variant, so the sheet shows the
    photograph roughly as it will be served.
    """
    name = urllib.parse.unquote(title.split(":", 1)[-1])
    url = (
        "https://commons.wikimedia.org/wiki/Special:FilePath/"
        f"{urllib.parse.quote(name)}?width={width}"
    )
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, headers={"User-Agent": "gallery-tool/1.0"}),
            timeout=30,
        ) as response:
            return response.read()
    except Exception as error:  # noqa: BLE001 - a missing tile is reported, not fatal
        print(f"  ! {title[:60]}: {error}", file=sys.stderr)
        return None


def build_checkpoint(entity: str, kept: int | None = None) -> Path:
    """Tile one entity's checkpoint candidates, fetching thumbnails as needed."""
    row: dict = {}
    with CHECKPOINT.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                record = json.loads(line)
            except ValueError:  # a line being appended while we read it
                continue
            if record.get("id") == entity:
                row = record
    if not row:
        sys.exit(f"no checkpoint row for {entity!r} -- has it been searched?")
    records = list(row.get("kept") or [])
    if kept:
        records = records[:kept]
    if not records:
        sys.exit(f"{entity}: no photographs waiting in the checkpoint")

    tiles: list[tuple[str, Image.Image | None]] = []
    for index, record in enumerate(records, start=1):
        blob = _thumbnail(record.get("title", ""))
        image: Image.Image | None = None
        if blob:
            try:
                image = Image.open(io.BytesIO(blob)).convert("RGB")
            except Exception:  # noqa: BLE001 - reported as a red frame
                image = None
        tiles.append((f"{index}. {record.get('title', '')[5:75]}", image))

    out = Path("/tmp/opencode/sheets") / f"{entity}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    _draw([(entity, tiles)]).save(out)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entities", nargs="*", help="destination ids")
    parser.add_argument("--kept", type=int, default=None, help="only the first N")
    parser.add_argument(
        "--plan",
        action="store_true",
        help="tile what is on disk (the gate before apply) instead of fetching",
    )
    parser.add_argument("--out", default=None, help="where to write the sheet")
    args = parser.parse_args()

    if args.plan:
        if not args.entities:
            rows = json.loads(PLAN.read_text(encoding="utf-8"))
            args.entities = list(dict.fromkeys(r["entity"] for r in rows))
        out = Path(args.out) if args.out else Path("/tmp/opencode/sheets/plan.png")
        print(build_plan(args.entities, out))
        return

    if len(args.entities) != 1:
        parser.error("exactly one entity, unless --plan is given")
    print(build_checkpoint(args.entities[0], args.kept))


if __name__ == "__main__":
    main()
