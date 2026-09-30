#!/usr/bin/env python3
"""Write a gallery plan into the site data, and the credits table beside it.

    venv/bin/python tools/gallery/apply.py --plan PLAN.json [--dry-run]

Two files change. `backend/data/destinations.json` and
`backend/data/festivals.json` gain an `images` array on every destination the
plan covers, and the gallery table inside `IMAGE-CREDITS.md` is regenerated
between its markers. Nothing else is touched: every other key, and the order the
keys appear in, is preserved exactly, because these files are read by the
frontend, the backend and a person, and a reformat is a large diff to review for
no benefit.

Why the credits table is generated rather than written
------------------------------------------------------
Attribution is a licence condition, not documentation. CC BY-SA 4.0 requires
that a reader be able to find the author, the licence and the source of every
reused photograph, and a table maintained by hand drifts from the data within a
couple of edits: somebody renames a file, or adds a gallery, and the table is
quietly wrong. Generating it from the same plan that produced the data means the
two cannot disagree.

Alt text
--------
The `alt` on each photograph is the destination's name plus whatever the
photographer's Commons file name added to it -- "Cape Coast Castle: inner court"
-- and "Photograph of {place}" where the file name added nothing. It is never
written from looking at the picture, because nothing in this pipeline looks at the
picture, and it is never taken from the Commons description, because a Commons
description is a catalogue entry rather than a description of a view: five
different photographs of Osu Castle share the sentence "located in Osu, Ghana, on
the coast of the Gulf of Guinea", and four of them would have shipped the same alt
text.

That leaves most alts thin, and `--alt-review` prints exactly which photographs
those are. Filling them in means looking at the photographs, which needs a browser
this process does not have. The count is reported rather than hidden behind a
sentence of plausible filler.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
CREDITS = ROOT / "IMAGE-CREDITS.md"
MARK_START = "<!-- gallery-credits:start -->"
MARK_END = "<!-- gallery-credits:end -->"
MARK_HEADING = "### Destination and festival gallery photographs"

# How much the frontend shows at once, and how many a gallery may hold. These
# must agree with tools/gallery/select.py; the strip is not rendered at all
# below MIN_WANT, so an array of one is dead weight in the file.
MIN_WANT = 2
MAX_PHOTOS = 6

DATA_FILES = {
    "destination": ROOT / "backend" / "data" / "destinations.json",
    "festival": ROOT / "backend" / "data" / "festivals.json",
}


# --------------------------------------------------------------------------
# alt text
# --------------------------------------------------------------------------
# Words that carry no information about *which* view a photograph shows: function
# words, media words ("photograph", "image"), and the place kinds and regions that
# appear in nearly every Ghanaian caption. A phrase built only from these restates
# the catalogue entry.
FILLER = set(
    """
    a an the this that these those it its is are was were be been being of in on
    at to for from by with within into onto over under near along across and or
    but as also too very much many more most some any all both each other another
    such same so than then there here where which who whom whose what when while
    during between among above below after before up down out off again further
    once only just now new old first second third last photo photograph photos
    picture pictures image images view views seen showing shows show shown taken
    file imagefile summary description english wikipedia wikimedia commons category
    ghana ghanaian african africa west western central eastern volta ashanti
    region regions district districts town city capital located location situated
    site sites known also called name named part lies lie stands stand
    castle castles fort forts building palace museum garden gardens park beach
    market markets lake river
    """.split()
)

# A photo numbered in the file name -- "Cape Coast Castle 35" -- is a serial, not
# a subject. Bare digits are dropped so they cannot be mistaken for one.
_NUMBER = re.compile(r"^\d+$")

MAX_SALIENT_WORDS = 5


def _content_words(text: str, place_words: set[str]) -> list[str]:
    """The words in `text` that add something to the place's own name.

    `place_words` is every word that names this destination, including its
    alternative names, so "Christiansborg Castle, Osu" contributes nothing while
    "the inner court" contributes two words.
    """
    out: list[str] = []
    for word in re.split(r"[^A-Za-z0-9']+", text):
        clean = word.strip("'").lower()
        if len(clean) < 3 or _NUMBER.match(clean) or clean in FILLER:
            continue
        if clean in place_words:
            continue
        out.append(clean)
    return out


def _place_words(place: str) -> set[str]:
    """Every word that names this place, including known alternative names.

    Imported rather than reimplemented: `filters.py` already holds the alias
    table, and a second, smaller copy of it here would drift from the one the
    selection used.
    """
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from filters import _alternative_words, _keys

    keys = set(_alternative_words(_keys(place))) | _keys(place)
    return keys | {word for words in keys for word in words}


def _phrase(words: list[str]) -> str:
    if not words:
        return ""
    text = " ".join(words[:MAX_SALIENT_WORDS])
    return text[0].upper() + text[1:]


def alt_text(row: dict[str, Any], place: str) -> tuple[str, bool]:
    """Return (alt, needs_review).

    An alt attribute is read by someone who cannot see the picture. The one thing
    that makes it worth hearing is the part that says *which* view this is: the
    inner court rather than the gate, the dungeon rather than the wall. So the alt
    is the place's name plus whatever the photographer's file name added to it, and
    nothing else.

    Only the file name, and that is a narrowing made after seeing what the
    alternative produced. Commons descriptions are catalogue entries, not view
    descriptions: five different photographs of Osu Castle all carry the same
    "located in Osu, Ghana, on the coast of the Gulf of Guinea", and four of them
    would have shipped the identical alt text. Reproducing them also stuttered --
    "Elmina Castle (St. George's Castle), elmina Castle also known as St. George
    of the Mine Castle" -- because the display name and the caption say the same
    thing twice. A description-derived alt was mostly the caption of the
    destination the user had already scrolled to.

    So a caption is not evidence about a frame, and the alt does not pretend to be
    one. Where the file name adds nothing -- "Cape Coast Castle 34", the majority
    of them -- the alt is "Photograph of {place}" and `needs_review` is True, so
    `--alt-review` lists exactly the photographs whose alt text a person should
    write after looking at them. That is a real gap, and it is reported rather
    than papered over with a sentence of filler.
    """
    title = row["title"].split(":", 1)[-1].rsplit(".", 1)[0].replace("_", " ")
    title = re.sub(r"\s+", " ", title).strip(" ,-–")
    place_words = _place_words(place)

    # The display name carries a parenthetical synonym -- "Osu Castle (Fort
    # Christiansborg)" -- which is a search aid in the data file and stutter in an
    # alt attribute. The primary name is what the page is headed with.
    primary = place.split(" (")[0].strip() or place

    detail = _phrase(_content_words(title, place_words))
    if detail:
        return f"{primary}: {detail}", False
    return f"Photograph of {primary}", True


# --------------------------------------------------------------------------
# credits
# --------------------------------------------------------------------------
def cell(value: str) -> str:
    """Escape a value for a Markdown table cell."""
    return (value or "").replace("|", "\\|").replace("\n", " ").strip()


def link(label: str, url: str) -> str:
    if not url:
        return cell(label)
    return f"[{cell(label)}]({url})"


def credits_table(rows: list[dict[str, Any]], names: dict[str, str]) -> list[str]:
    """The gallery attribution table, grouped by place."""
    by_place: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_place[names.get(row["entity"], row["entity"])].append(row)

    out = [
        MARK_START,
        "",
        MARK_HEADING,
        "",
        "These are the extra photographs shown in each destination's or festival's",
        "*View Details* window. Every one is reproduced unmodified from the Commons",
        "1920px downscale of the original, which is the repository's standard",
        "master width; the `-400` and `-800` files served to browsers are",
        "downscales of that same master, and the credit applies to them unchanged.",
        "",
        "| Place | Local file | Author | Licence | Source |",
        "| --- | --- | --- | --- | --- |",
    ]
    for place in sorted(by_place):
        for row in sorted(by_place[place], key=lambda r: r["file"]):
            source = row.get("source") or ""
            out.append(
                "| "
                + " | ".join(
                    [
                        cell(place),
                        f"`{row['file'].split('/')[-1]}`",
                        link(row.get("author", ""), source),
                        link(row.get("licence", ""), row.get("licence_url", "")),
                        link("Wikimedia Commons", source),
                    ]
                )
                + " |"
            )
    out += [
        "",
        f"{len(rows)} photographs across {len(by_place)} places, from "
        f"{len({r.get('author', '') for r in rows})} photographers. "
        "Licences in use: "
        + ", ".join(
            f"{licence} ({count})"
            for licence, count in Counter(r.get("licence", "?") for r in rows).most_common()
        )
        + ".",
        MARK_END,
    ]
    return out


def replace_credits(rows: list[dict[str, Any]], names: dict[str, str]) -> str:
    """Splice the generated table into IMAGE-CREDITS.md."""
    text = CREDITS.read_text()
    table = "\n".join(credits_table(rows, names))

    if MARK_START in text and MARK_END in text:
        return re.sub(
            re.escape(MARK_START) + r".*?" + re.escape(MARK_END), table, text, flags=re.S
        )

    # First run: put the table immediately before the maintainer notes, which is
    # where a reader looking for attribution on an individual photograph lands.
    heading = "## Notes for maintainers"
    if heading not in text:
        raise SystemExit(f"cannot find {heading!r} in {CREDITS}")
    return text.replace(heading, f"{table}\n\n{heading}", 1)


# --------------------------------------------------------------------------
# the run
# --------------------------------------------------------------------------
def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def load_plan(path: Path) -> list[dict[str, Any]]:
    """Read a plan as a flat list of rows, each carrying its `entity`.

    `select.py` writes a flat list. `recover.py` writes a dict keyed by entity id,
    because it reports per entity while it runs. Accepting both here means the
    two halves of the pipeline can be combined -- the recovered photographs for
    the 29 places that have files on disk, plus a fresh selection for the rest --
    which is the situation the site is actually in.
    """
    data = load_json(path)
    if isinstance(data, list):
        rows = list(data)
    elif isinstance(data, dict):
        rows = [{**row, "entity": entity} for entity, group in data.items() for row in group]
    else:
        raise SystemExit(f"{path} holds {type(data).__name__}, expected a list or a dict")

    for row in rows:
        for field in ("entity", "file", "title"):
            if not row.get(field):
                raise SystemExit(f"{path}: a plan row has no {field!r}: {row}")
        # The gallery is 3:2 and the installed files are full-frame, so the
        # thumbnail is a centre crop rather than a stretch. A plan row that
        # cannot say how big its file is will be caught here rather than showing
        # a browser-scaled image that is not what the record claims.
        row.setdefault("author", "")
        row.setdefault("licence", "")
        row.setdefault("licence_url", "")
        row.setdefault("source", "")
        row.setdefault("description", "")
    return rows


def write_json(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write with the repository's formatting: two-space indent, trailing newline.

    `ensure_ascii=False` keeps the en dashes and curly apostrophes already in the
    data readable in the file rather than as \\u escapes.
    """
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")


def insert_images(
    rows: list[dict[str, Any]], existing: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """Rebuild each row with an `images` array, positioned after `image`.

    Rebuilding rather than mutating in place is what keeps the key order stable:
    `dict` preserves insertion order, so starting a fresh dict from the original
    row and adding `images` at the point where `image` was puts it in a sensible
    place instead of at the end, next to `guideContact`.

    A place with fewer than `MIN_WANT` photographs gets no array at all. The row
    would be ignored by `stripHtml()`, which returns an empty string below two, so
    writing one puts data in the file that a maintainer will reasonably believe is
    being shown and is not. Those photographs still appear in the credits table,
    which is generated from the plan rather than from the data, so the
    attribution survives without the data file implying a display that does not
    happen.

    Returns (rows, entities with an array, entities with too few photographs).
    """
    plans: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for plan_row in rows:
        plans[plan_row["entity"]].append(plan_row)

    out: list[dict[str, Any]] = []
    touched: list[str] = []
    too_thin: list[str] = []
    for row in existing:
        entity_id = row["id"]
        if entity_id not in plans:
            out.append(row)
            continue
        chosen = plans[entity_id][:MAX_PHOTOS]
        if len(chosen) < MIN_WANT:
            out.append(row)
            too_thin.append(f"{entity_id} ({len(chosen)})")
            continue
        images = []
        for plan_row in chosen:
            alt, _ = alt_text(plan_row, row.get("name", entity_id))
            credit = ", ".join(
                part for part in (plan_row.get("author"), plan_row.get("licence")) if part
            )
            images.append(
                {"image": f"assets/images/{plan_row['file']}", "alt": alt, "credit": credit}
            )
        rebuilt: dict[str, Any] = {}
        for key, value in row.items():
            rebuilt[key] = value
            if key == "image":
                rebuilt["images"] = images
        if "images" not in rebuilt:
            rebuilt["images"] = images
        out.append(rebuilt)
        touched.append(entity_id)
    return out, touched, too_thin


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--plan", required=True, help="plan JSON from select.py or recover.py")
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    parser.add_argument(
        "--alt-review",
        action="store_true",
        help="list the alt texts that are only a file name, for someone to improve",
    )
    args = parser.parse_args()

    plan = load_plan(Path(args.plan))
    names: dict[str, str] = {}
    for path in DATA_FILES.values():
        for row in load_json(path):
            names[row["id"]] = row.get("name") or row["id"]

    missing = [
        row["file"]
        for row in plan
        if not (ROOT / "assets" / "images" / row["file"]).exists()
    ]
    if missing:
        print(f"{len(missing)} planned files are not on disk:", file=sys.stderr)
        for name in missing[:10]:
            print(f"  {name}", file=sys.stderr)
        return 1

    per_place: dict[str, int] = Counter(row["entity"] for row in plan)
    thin = sorted(name for name, count in per_place.items() if count < MIN_WANT)
    unknown = sorted(set(per_place) - set(names))
    if unknown:
        print(f"plan names {len(unknown)} ids that are not in the data: {unknown[:5]}", file=sys.stderr)
        return 1

    print(f"plan: {len(plan)} photographs across {len(per_place)} places")
    print(f"  render a strip (>= {MIN_WANT}): {len(per_place) - len(thin)}")
    print(f"  too thin, hero only      : {len(thin)} {thin if thin else ''}")

    thin_alts = [
        (row["entity"], row["file"].split("/")[-1], alt_text(row, names.get(row["entity"], ""))[0])
        for row in plan
        if alt_text(row, names.get(row["entity"], ""))[1]
    ]
    print(
        f"  alt text with nothing but the place name: {len(thin_alts)} of {len(plan)}"
        "  (needs a person who can see the site)"
    )
    if args.alt_review:
        print("\nAlt texts to write after looking at the photograph:")
        for entity, filename, alt in thin_alts:
            print(f"  {entity:32} {filename:52} {alt}")

    if args.dry_run:
        print("\ndry run, nothing written")
        return 0

    skipped: list[str] = []
    for kind, path in DATA_FILES.items():
        rows = load_json(path)
        ids = {row["id"] for row in rows}
        subset = [row for row in plan if row["entity"] in ids]
        if not subset:
            continue
        rebuilt, touched, too_thin = insert_images(subset, rows)
        write_json(path, rebuilt)
        skipped.extend(too_thin)
        print(f"  {path.name}: {len(touched)} places given an images array")

    if skipped:
        print(
            f"  {len(skipped)} place(s) have too few photographs for the row to render, "
            f"so none was written: {', '.join(skipped)}"
        )

    CREDITS.write_text(replace_credits(plan, names))
    print("  IMAGE-CREDITS.md: gallery table written")
    print("\nnext: venv/bin/python tools/build_image_variants.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
