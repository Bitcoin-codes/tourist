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
import math
import re
import sys
import urllib.parse
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pixels  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_FILES = [
    ROOT / "backend" / "data" / "destinations.json",
    ROOT / "backend" / "data" / "festivals.json",
]

# The strip renders only when there is a hero plus at least two more, so an array
# of one is dead weight in the data file. Must match select.py and apply.py.
MIN_WANT = 2
MAX_PHOTOS = 9

# Slots, in CSS pixels, and the device pixel ratio each has to survive.
#
# The first two are measured out of styles.css rather than written down here, so
# that restyling the modal cannot quietly leave this check measuring a box that no
# longer exists. The arithmetic, which is what the numbers came from originally:
#
#   .modal-card { max-width: 800px }
#   .modal-gallery { padding: var(--sp-4) var(--sp-6) 0 }   -> track is 800-48 = 752
#   .modal-gallery-item { flex: 0 0 calc((100% - 2 * var(--sp-3)) / 3) }
#                                                          -> (752-24)/3 = 242.7
#
# If the CSS cannot be parsed the fallbacks below are used and the run says so,
# because a check that silently measures the wrong box is worse than none.
STYLES = ROOT / "styles.css"
CREDITS_PATH = ROOT / "IMAGE-CREDITS.md"
FALLBACK_SLOTS: list[tuple[str, int, int]] = [
    ("gallery thumbnail", 243, 2),
    ("modal hero", 800, 2),
    ("full-size viewer", 1920, 1),
]


# Markdown links whose target contains parentheses, which Commons filenames
# routinely do: "File:Studies_of_nature_(IA_abc123).pdf". A `[text](url)`
# pattern stops at the first ")" and leaves the tail of the URL glued to the
# text, which put "…W Noel.pdf))" in an author name the first time this was
# written. Balanced one level of nesting, which is all these need.
_LINK = re.compile(r"\[([^\]]*)\]\(((?:[^()\s]|\([^()]*\))*)\)")


def _unlink(text: str) -> str:
    """The URL a markdown link points at, or the text unchanged if it is not one."""
    match = _LINK.search(text)
    return match.group(2).strip() if match else text.strip()


def _link_text(text: str) -> str:
    """The visible text of a markdown link, or the text unchanged if it is not one.

    Everything before the first "](" rather than the regex's first group: a
    cell that has been re-wrapped carries its brackets outside the link, and
    the group would then return "[[[Kwaku Berko" as an author's name. Reading
    the table correctly is this function's whole job -- with the old version it
    happily reported an attribution that had been mangled fourteen levels deep
    as fine.
    """
    head, separator, _tail = text.partition("](")
    return (head if separator else text).lstrip("[ \t").strip()


def credits_rows(markdown: str) -> list[tuple[str, str, str, str]] | None:
    """The gallery credits table as (place, filename, author, source) tuples.

    Returns None when the markers or the header are absent, so the caller can
    report that rather than quietly checking nothing -- a check that reads an
    empty table and finds it clean is the failure mode this function exists to
    avoid.
    """
    start = markdown.find("<!-- gallery-credits:start -->")
    end = markdown.find("<!-- gallery-credits:end -->")
    if start == -1 or end == -1 or end < start:
        return None

    rows: list[tuple[str, str, str, str]] = []
    header_seen = False
    for line in markdown[start:end].splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 5:
            continue
        if cells[0] == "Place":
            header_seen = True
            continue
        if set(cells[0]) <= set("-: "):
            continue
        if not header_seen:
            continue
        place, filename, author, _licence, source = cells
        rows.append(
            (place, filename.strip("`"), _link_text(author), _unlink(source))
        )
    return rows if header_seen else None


def non_image_credits(
    rows: list[tuple[str, str, str, str]]
) -> list[tuple[str, str, str, str]]:
    """Credits whose source is a scanned document rather than a photograph."""
    out = []
    for place, filename, author, source in rows:
        match = re.search(r"commons\.wikimedia\.org/wiki/File:(.+)$", source)
        target = (match.group(1) if match else source).strip()
        # Commons URLs percent-encode punctuation, and the markdown cell may still
        # carry a trailing bracket. Undo both before looking at the extension, or
        # the suffix reads ".pdf)" and the check passes on the very rows it exists
        # to catch -- which is what happened the first time this was written.
        target = urllib.parse.unquote(target).strip("()[]<> \t")
        suffix = ("." + target.rsplit(".", 1)[-1].lower()) if "." in target else ""
        if suffix in {".pdf", ".djvu", ".djv", ".djt", ".chm", ".epub"}:
            out.append((place, filename, author, target))
    return out


def slots() -> tuple[list[tuple[str, int, int]], str]:
    """The display slots, and where the numbers came from.

    The source is returned as well as the numbers because the fallbacks are
    currently identical to what the parse produces, so comparing the two lists
    cannot tell success from failure -- it reports a fallback on a clean parse and
    would report success if the fallback happened to match. A check that
    misreports its own provenance is not a check.
    """
    try:
        css = STYLES.read_text()
    except OSError as error:
        return FALLBACK_SLOTS, f"styles.css unreadable ({error.strerror}), using recorded values"

    def px(name: str) -> int | None:
        match = re.search(rf"--{name}:\s*(\d+)px", css)
        return int(match.group(1)) if match else None

    card = re.search(r"\.modal-card\s*\{[^}]*?max-width:\s*(\d+)px", css, re.S)
    item = re.search(
        r"\.modal-gallery-item\s*\{[^}]*?flex:\s*0 0 calc\(\(100% - 2 \* var\(--sp-(\d+)\)\)",
        css,
        re.S,
    )
    gallery = re.search(r"\.modal-gallery\s*\{[^}]*?padding:[^;]*", css, re.S)
    if not (card and item and gallery):
        return FALLBACK_SLOTS, "could not find the modal rules in styles.css, using recorded values"

    sides = re.findall(r"var\(--sp-(\d+)\)", gallery.group(0))
    gap, side = px(f"sp-{item.group(1)}"), px(f"sp-{sides[1] if len(sides) > 1 else 6}")
    if not (gap and side):
        return FALLBACK_SLOTS, "could not read the spacing scale, using recorded values"

    modal = int(card.group(1))
    track = modal - 2 * side
    # Rounded up, not to nearest: the computed width is 242.67, and truncating it
    # to 242 would let through a 484px file that is 1.4px short at 2x. A check
    # that is a hair too strict costs nothing; one that is a hair too lax is the
    # blurred photograph this whole script exists to prevent.
    thumb = math.ceil((track - 2 * gap) / 3)
    # The viewer is capped by the viewport, not by a fixed width, so its number is
    # the master's own width: the master is the widest file this repository holds,
    # and displaying it at 1x is the case that is always sharp.
    return (
        [
            ("gallery thumbnail", thumb, 2),
            ("modal hero", modal, 2),
            ("full-size viewer", 1920, 1),
        ],
        f"measured from styles.css (modal {modal}px, {side}px side padding, {gap}px gap)",
    )

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
    credits = credits_rows(CREDITS_PATH.read_text()) if CREDITS_PATH.exists() else None
    warnings: list[str] = []

    # path -> the entities that use it, and the pixel signatures for duplicate
    # detection. A signature is a list of grey levels, not a hash, so this is a
    # list to scan rather than a dict to look up.
    used_by: dict[str, list[str]] = {}
    by_content: list[tuple[str, list[float]]] = []
    duplicates: list[str] = []
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

                # How sharp a photograph has to be depends on whether anything could
                # have been done about it.
                #
                # Installed files are byte-identical to the Commons 1920px downscale,
                # so the width on disk *is* the most Commons will ever serve: a file
                # narrower than 1920 means the original on Commons is that narrow,
                # because Commons does not upscale. There is no larger copy to fetch,
                # and no re-run of the pipeline changes it.
                #
                # So the only shortfall worth failing on is the thumbnail slot, at
                # 486px. Every Commons photograph of a place clears that by a wide
                # margin, so falling below it means a truncated download or a bad
                # write -- which is a real defect and is caught here.
                #
                # The hero slot (1600px) and the viewer (1920px) are bounded by the
                # source, not by the pipeline. Failing on them would drop good
                # photographs of Busua Beach and the Centre for National Culture --
                # whose originals are 1280x960 -- over a resolution that does not
                # exist anywhere. An empty gallery is indistinguishable from "this
                # place has no photographs", which is the failure this whole pipeline
                # is shaped to avoid, so these are reported and shipped, with the
                # shortfall stated rather than hidden.
                for name, css, ratio in slots()[0]:
                    needed = css * ratio
                    if width >= needed:
                        continue
                    message = f"{where}: {relative} is {width}px, {name} needs {needed}px"
                    if name == "gallery thumbnail":
                        errors.append(message)
                    else:
                        warnings.append(
                            message
                            + " (the Commons original is this size; nothing larger "
                            "exists, so it ships soft rather than not at all)"
                        )

                if width < height:
                    warnings.append(
                        f"{where}: {relative} is portrait ({width}x{height}); the 3:2 "
                        f"thumbnail will crop the sides"
                    )

                # Byte-identical detection is not enough: two Commons thumbnails
                # of the same photograph have different bytes and the same picture.
                # `pixels` is the shared implementation, so this, select.py and
                # recover.py all decide "same picture" with one threshold rather
                # than three that drift apart.
                mark = pixels.of_path(path)
                if mark is not None:
                    twin = pixels.first_duplicate(mark, by_content)
                    if twin is not None:
                        duplicates.append(
                            f"{entity} and {twin} hold the same picture, via {relative}"
                        )
                    else:
                        by_content.append((entity, mark))

            for alt, count in alts.items():
                if count > 1 and len(set(alts)) < len(images):
                    thin_alts.append(f"{entity}: {count}x {alt!r}")

    for relative, entities in sorted(used_by.items()):
        if len(entities) > 1:
            errors.append(
                f"{relative} is in {len(entities)} galleries: {', '.join(sorted(set(entities)))}. "
                f"A photograph belongs to one place; fix the plan, not the data file."
            )
    errors.extend(f"the same picture is filed twice: {item}" for item in duplicates)

    # -- photographs on disk that nothing shows ------------------------------
    # A warning, not an error: an unreferenced file needs no attribution and
    # breaks no licence. But it is dead weight in the repository, and it is the
    # visible trace of photographs the credit recovery installed and then failed
    # to match -- including the two scanned books that were credited to castles
    # before the file-type guard existed. Reporting them is how those stayed
    # findable after the plan that produced them was lost.
    gallery_dir = ROOT / "assets" / "images" / "gallery"
    if gallery_dir.is_dir():
        credited = {filename for _p, filename, _a, _s in (credits or [])}
        orphans = sorted(
            path.name
            for path in gallery_dir.glob("*.jpg")
            if not path.stem.endswith(("-400", "-800"))
            and f"assets/images/gallery/{path.name}" not in used_by
            and path.name not in credited
        )
        if orphans:
            spare = sum((gallery_dir / name).stat().st_size for name in orphans) / 1e6
            warnings.append(
                f"{len(orphans)} photograph(s) in assets/images/gallery are neither "
                f"shown nor credited ({spare:.1f} MB of dead weight): {', '.join(orphans[:4])}"
                f"{' ...' if len(orphans) > 4 else ''}"
            )

    # -- the credits table -------------------------------------------------
    # Parsed back out of IMAGE-CREDITS.md rather than read from the plan, because
    # the file is the durable record: /tmp has been wiped twice and the plan was
    # in it. A credit that survived into the published table while pointing at a
    # scanned book is an attribution to the wrong author, which is a licence
    # failure and not a cosmetic one.
    if credits is None:
        errors.append(
            f"the gallery credits table could not be read from {CREDITS_PATH.name}"
        )
    else:
        for place, filename, author, source in non_image_credits(credits):
            errors.append(
                f"{filename} (shown for {place}, credited to {author}) points at a "
                f"scanned document rather than a photograph: {source}. It cannot be "
                f"an image of the place, and crediting it to that author is wrong."
            )

    print(f"galleries checked : {len(DATA_FILES)} data files")
    print(f"photographs       : {total}")
    print(f"files referenced  : {len(used_by)}")
    measured, source = slots()
    print(f"  slots: {source}")
    for name, css, ratio in measured:
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
    #
    # Checked against the parsed rows, not against a substring search of the whole
    # file. The old version asked whether the filename appeared anywhere in
    # IMAGE-CREDITS.md between backticks, which a sentence of prose mentioning the
    # file would satisfy just as well as a table row -- so a photograph could be
    # unrecredited and the check would still pass, which is the failure this script
    # exists to prevent.
    credited_files = {filename for _place, filename, _author, _source in (credits or [])}
    missing_credits = [
        relative
        for relative in used_by
        if Path(relative).name not in credited_files
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
