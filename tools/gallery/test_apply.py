#!/usr/bin/env python3
"""Tests for the credits table, the non-image guard, and alt text.

    venv/bin/python tools/gallery/test_apply.py

Every test here corresponds to a defect that actually shipped or nearly did, and
each is written to fail on the specific mistake rather than on a number:

* **Two photographs of Cape Coast Castle were credited to 19th-century books
  about Scotland.** One was displayed. The pixel matcher cannot tell a rendered
  book page from a photograph, so the guard has to be a file-type test, and this
  checks it rejects the documents that caused it.

* **`apply.py` did not overwrite an existing `images` array.** It rebuilt each row
  by copying the old keys, which put the stale `images` back after the new one had
  been inserted -- dicts preserve insertion order, so the copy landed second and
  won. Two hand-written test entries survived a full re-apply while the credits
  table was regenerated underneath them, so the data file and the credits table
  disagreed and `check.py` found two photographs with no credit. This is the test
  for that, and it fails if the loop ever copies `images` again.

* **The non-image check passed on the very rows it was written for.** The source
  cell is a markdown link, so a `[text](url)` pattern captured the trailing `)`
  and the extension read as `.pdf)` rather than `.pdf`. Parsed from the table and
  then compared, which is what the shipped code does not do.

* **Alt text was filled with camera serials and register codes.** "Fort Nassau:
  Overzicht rce", "Adomi Bridge: P1100018 pano". A detail that says nothing is
  worse than no detail, because it crowds out the one true fact.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

ROOT = HERE.parent.parent


def load(name: str):
    """Import a sibling script by path. They are scripts, not a package."""
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


commons = load("commons")
check = load("check")
apply_ = load("apply")

CREDITS_MD = ROOT / "IMAGE-CREDITS.md"

# The two real defects, as the credits table actually rendered them.
SCOTLAND_PDF_ROW = (
    "| Cape Coast Castle | `cape-coast-castle-coast.jpg` | "
    "[Milner, George, 1829-1914 Johnson, W Noel]"
    "(https://commons.wikimedia.org/wiki/File:"
    "Studies_of_nature_on_the_coast_of_Arran_(IA_studiesofnatureo00milnrich).pdf) | "
    "Public domain | [Wikimedia Commons]"
    "(https://commons.wikimedia.org/wiki/File:"
    "Studies_of_nature_on_the_coast_of_Arran_(IA_studiesofnatureo00milnrich).pdf) |"
)
PHOTO_ROW = (
    "| Cape Coast Castle | `cape-coast-castle-34.jpg` | "
    "[Antorsu10](https://commons.wikimedia.org/wiki/File:Cape_Coast_Castle_34.jpg) | "
    "[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | "
    "[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Cape_Coast_Castle_34.jpg) |"
)
TABLE = (
    "<!-- gallery-credits:start -->\n"
    "| Place | Local file | Author | Licence | Source |\n"
    "| --- | --- | --- | --- | --- |\n"
    f"{SCOTLAND_PDF_ROW}\n{ PHOTO_ROW }\n"
    "<!-- gallery-credits:end -->\n"
)


def run() -> int:
    passed = 0
    failures: list[str] = []

    def check_that(label: str, condition: bool, detail: str = "") -> None:
        nonlocal passed
        if condition:
            passed += 1
        else:
            failures.append(f"  {label}{(': ' + detail) if detail else ''}")

    # -- is_raster_image: the guard that was missing entirely -----------------
    def record(title: str, mime: str = "image/jpeg", thumb: str = "https://x/thumb.jpg"):
        return {"title": title, "mime": mime, "thumburl": thumb}

    check_that(
        "a JPEG is a raster image",
        commons.is_raster_image(record("File:A.jpg")),
    )
    check_that(
        "a PNG is a raster image",
        commons.is_raster_image(record("File:A.png", mime="image/png")),
    )
    check_that(
        "a PDF is not a raster image",
        not commons.is_raster_image(
            record(
                "File:Book_(IA_x).pdf",
                mime="application/pdf",
                thumb="https://x/page1-1920px.jpg",
            )
        ),
        "this is the case that credited a castle to a book",
    )
    check_that(
        "a DjVu is not a raster image",
        not commons.is_raster_image(record("File:Book.djvu", mime="image/vnd.djvu")),
    )
    check_that(
        "a multi-page document is not a raster image, whatever its extension claims",
        not commons.is_raster_image(
            record("File:Pages.jpg", mime="image/jpeg", thumb="https://x/page1.jpg")
        ),
        "Commons serves page1.jpg for a document, which is the trap",
    )
    check_that(
        "a TIFF scan is not a raster image",
        not commons.is_raster_image(record("File:Scan.tif", mime="image/tiff")),
    )
    check_that(
        "a non-image MIME type is refused even with a .jpg name",
        not commons.is_raster_image(record("File:A.jpg", mime="application/pdf")),
    )
    check_that(
        "an SVG diagram is not a raster image",
        not commons.is_raster_image(record("File:Map.svg", mime="image/svg+xml")),
    )
    # A guard that refuses everything would pass all of the above.
    check_that(
        "an ordinary photograph is still allowed through",
        commons.is_raster_image(
            record("File:Cape_Coast_Castle_34.jpg", thumb="https://x/1920px-Cape.jpg")
        ),
    )

    # -- credits_rows --------------------------------------------------------
    rows = check.credits_rows(TABLE)
    check_that("the table parses", rows is not None and len(rows) == 2, f"got {rows!r}")
    if rows:
        place, filename, author, source = rows[0]
        check_that("the place survives parsing", place == "Cape Coast Castle", place)
        check_that("the filename loses its backticks", filename.endswith(".jpg"), filename)
        check_that(
            "an author with commas in the name is not truncated at the first one",
            author == "Milner, George, 1829-1914 Johnson, W Noel",
            author,
        )
        check_that(
            "a URL containing parentheses is unwrapped whole",
            source.endswith(".pdf") and "_(IA_" in source,
            source,
        )
    check_that(
        "a document with no markers is reported as unreadable, not as an empty table",
        check.credits_rows("no markers here") is None,
    )
    check_that(
        "a table with no header row is reported as unreadable",
        check.credits_rows(
            "<!-- gallery-credits:start -->\n| a | b | c | d | e |\n"
            "<!-- gallery-credits:end -->\n"
        )
        is None,
    )

    # -- non_image_credits: the check that passed on its own target ----------
    if rows:
        bad = check.non_image_credits(rows)
        check_that(
            "the PDF row is caught despite the markdown link and the parentheses",
            len(bad) == 1,
            f"found {len(bad)}",
        )
        if bad:
            check_that(
                "the caught row names the right file",
                bad[0][1] == "cape-coast-castle-coast.jpg",
                bad[0][1],
            )
        check_that(
            "a genuine photograph is not caught",
            not any(f == "cape-coast-castle-34.jpg" for _p, f, _a, _s in bad),
        )

    # -- the real credits file must parse and must be clean ------------------
    if CREDITS_MD.exists():
        live = check.credits_rows(CREDITS_MD.read_text())
        check_that("IMAGE-CREDITS.md parses", live is not None)
        if live:
            check_that(
                "IMAGE-CREDITS.md credits no scanned document",
                not check.non_image_credits(live),
                str(check.non_image_credits(live)[:2]),
            )

    # -- insert_images must overwrite a stale array -------------------------
    # The regression: rebuilding a row by copying its old keys put the stale
    # `images` back after the new one, because `images` sorts after `image` and
    # dicts preserve insertion order. Two hand-written entries survived a full
    # re-apply that way.
    #
    # Two rows, not one: MIN_WANT is 2, so a single photograph is deliberately not
    # written at all and the row goes to `too_thin` instead. Using one row here
    # would have tested the thin path and reported the overwrite bug as a pass.
    plan = [
        {
            "entity": "test-place",
            "file": "gallery/test-place-new.jpg",
            "title": "Test Place new.jpg",
            "author": "Someone",
            "licence": "CC BY 4.0",
        },
        {
            "entity": "test-place",
            "file": "gallery/test-place-newer.jpg",
            "title": "Test Place newer.jpg",
            "author": "Someone Else",
            "licence": "CC BY 4.0",
        },
    ]
    stale = {
        "id": "test-place",
        "name": "Test Place",
        "image": "assets/images/attractions/test.jpg",
        "images": [
            {"image": "assets/images/gallery/OLD.jpg", "alt": "hand written", "credit": "x"}
        ],
        "rating": 4.5,
    }
    rebuilt, touched, _thin = apply_.insert_images(plan, [dict(stale)])
    got = rebuilt[0].get("images", [])
    check_that("a stale images array is replaced, not kept", len(got) == 2, f"{got!r}")
    check_that(
        "not one entry of the stale array survives",
        not any(entry["image"].endswith("OLD.jpg") for entry in got),
        f"{got!r}",
    )
    check_that(
        "the replacement is the planned photograph",
        bool(got) and got[0]["image"].endswith("test-place-new.jpg"),
        f"{got!r}",
    )
    check_that("the row is still reported as touched", touched == ["test-place"])
    check_that("the surrounding fields survive the rebuild", rebuilt[0].get("rating") == 4.5)

    # A row with no `images` key at all must still gain one, and `images` must be
    # positioned after `image` so the rest of the site can rely on that order.
    fresh = {"id": "test-place", "name": "Test Place", "image": "a.jpg"}
    out2, _t, _th = apply_.insert_images(plan, [fresh])
    keys = list(out2[0])
    check_that("a row without images gains them", len(out2[0].get("images", [])) == 2)
    check_that(
        "images sits directly after image, for readers that assume it",
        keys.index("images") == keys.index("image") + 1,
        str(keys),
    )

    # Fewer than MIN_WANT gets nothing written, so nothing misleading is stored.
    out3, _t3, thin3 = apply_.insert_images(
        [plan[0] | {"entity": "lonely"}], [{"id": "lonely", "name": "Lonely", "image": "a.jpg"}]
    )
    check_that("a place with one photograph gets no array", "images" not in out3[0])
    check_that("and is reported as too thin", thin3 == ["lonely (1)"], str(thin3))

    # -- alt text: serials and jargon are not descriptions -------------------
    def alt_for(title: str, place: str = "Fort Nassau") -> str:
        return apply_.alt_text({"title": title}, place)[0]

    check_that(
        "a camera serial is not offered as a description",
        alt_for("Fort Nassau P1100018 pano.jpg") == "Photograph of Fort Nassau",
        alt_for("Fort Nassau P1100018 pano.jpg"),
    )
    check_that(
        "a register code is dropped but the real word beside it is kept",
        alt_for("Overzicht rce.jpg") == "Fort Nassau: Overzicht",
        alt_for("Overzicht rce.jpg"),
    )
    check_that(
        "a register code alone is not a description",
        alt_for("rce b001001.jpg") == "Photograph of Fort Nassau",
        alt_for("rce b001001.jpg"),
    )
    check_that(
        "the photography jargon alone is not a description",
        alt_for("Fort Nassau DSC0001234 img pano.jpg") == "Photograph of Fort Nassau",
        alt_for("Fort Nassau DSC0001234 img pano.jpg"),
    )
    check_that(
        "a word that does describe the view is kept",
        alt_for("Fort Nassau Westelijk bastion.jpg") == "Fort Nassau: Westelijk bastion",
        alt_for("Fort Nassau Westelijk bastion.jpg"),
    )
    check_that(
        "a word already in the place name is not repeated",
        apply_.alt_text({"title": "Adomi Bridge Asuogyaman.jpg"}, "Adomi Bridge")[0]
        == "Adomi Bridge: Asuogyaman",
        apply_.alt_text({"title": "Adomi Bridge Asuogyaman.jpg"}, "Adomi Bridge")[0],
    )
    check_that(
        "a name carrying only words already in the place name collapses to the plain form",
        apply_.alt_text({"title": "Adomi Bridge.jpg"}, "Adomi Bridge")[0]
        == "Photograph of Adomi Bridge",
    )
    parenthetical = apply_.alt_text({"title": "Castle.jpg"}, "Osu Castle (Fort Christiansborg)")
    check_that(
        "a parenthetical synonym does not stutter into the alt",
        parenthetical[0] == "Photograph of Osu Castle",
        parenthetical[0],
    )
    check_that(
        "a photo with no usable detail is flagged for review",
        apply_.alt_text({"title": "Cape Coast Castle 34.jpg"}, "Cape Coast Castle")[1] is True,
    )
    check_that(
        "a photo with usable detail is not flagged",
        apply_.alt_text({"title": "Fort Nassau gate bastion.jpg"}, "Fort Nassau")[1] is False,
    )

    print(f"\n{passed + len(failures)} assertions, {passed} pass, {len(failures)} fail")
    for line in failures:
        print(line)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(run())