#!/usr/bin/env python3
"""Tests for the shared picture matcher. No network, no browser, seconds to run.

    venv/bin/python tools/gallery/test_pixels.py

These exist because the previous version of this test did not. `select.py` had a
duplicate check that hashed an 8x8 grayscale signature to a string and compared
strings for equality; two encodings of the same photograph differ in the last
bit, so it never matched, and it reported that no gallery contained a repeated
photograph. That is indistinguishable from the correct answer, so nothing noticed.

The suite below is written to fail on that class of mistake rather than on a
particular number: every "is the same picture" test is paired with a "is a
different picture" test, so a threshold that collapses to always-true or
always-false is caught even if the individual cases still look plausible.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pixels  # noqa: E402

GALLERY = Path(__file__).resolve().parent.parent.parent / "assets" / "images" / "gallery"


def reencode(path: Path, scale: float = 1.0, quality: int = 80) -> bytes:
    """The same photograph, encoded again at a different size and quality."""
    with Image.open(path) as raw:
        image = raw.convert("RGB")
        if scale != 1.0:
            image = image.resize(
                (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
            )
        buffer = io.BytesIO()
        image.save(buffer, "JPEG", quality=quality)
        return buffer.getvalue()


def originals() -> list[Path]:
    """Installed photographs, without the generated -400/-800 derivatives."""
    if not GALLERY.exists():
        return []
    return [p for p in sorted(GALLERY.glob("*.jpg")) if not p.stem.endswith(("-400", "-800"))]


def run() -> int:
    failures: list[str] = []
    passed = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal passed
        if condition:
            passed += 1
        else:
            failures.append(f"  {label}{(': ' + detail) if detail else ''}")

    files = originals()
    if len(files) < 2:
        print("not enough installed photographs to test against")
        return 1

    # -- the same picture, however it was encoded ---------------------------
    base = files[0]
    reference = pixels.of_path(base)
    check("a real file has a signature", reference is not None)
    assert reference is not None

    for scale, quality in ((1.0, 95), (1.0, 60), (0.5, 80), (0.25, 70), (1.5, 50)):
        score = pixels.distance(reference, pixels.of_bytes(reencode(base, scale, quality)))
        check(
            f"same picture at scale {scale} quality {quality} is the same",
            pixels.is_same(reference, pixels.of_bytes(reencode(base, scale, quality))),
            f"distance {score:.2f} > {pixels.SAME}",
        )

    # Its own served derivatives are the same picture. This is the case that
    # matters most in practice: build_image_variants.py writes -400 and -800
    # beside every original, so a matcher that cannot see through them reports
    # every photograph as unique.
    for width in (400, 800):
        derivative = GALLERY / f"{base.stem}-{width}.jpg"
        if derivative.exists():
            check(
                f"{derivative.name} is recognised as the same picture",
                pixels.is_same(reference, pixels.of_path(derivative)),
                f"distance {pixels.distance(reference, pixels.of_path(derivative)):.2f}",
            )

    # -- a different picture -------------------------------------------------
    closest = min(
        (pixels.distance(reference, pixels.of_path(other)), other.name)
        for other in files[1:]
    )
    check(
        "the nearest different picture is not the same",
        not pixels.is_same(reference, pixels.of_path(GALLERY / closest[1])),
        f"nearest is {closest[1]} at {closest[0]:.2f}",
    )
    print(
        f"  nearest different picture: {closest[1]} at {closest[0]:.2f} "
        f"(threshold {pixels.SAME}, margin {closest[0] / max(pixels.SAME, 0.01):.0f}x)"
    )

    # -- the failure this suite exists for -----------------------------------
    # A matcher that always says "different" passes every case above except the
    # "same picture" ones, so those are paired. What must be caught specifically
    # is a matcher that is *nearly* right: the 8x8 string comparison was.
    same_scores = [
        pixels.distance(reference, pixels.of_bytes(reencode(base, scale, quality)))
        for scale, quality in ((1.0, 95), (0.5, 80), (0.25, 70))
    ]
    check(
        "same-picture scores are far below the threshold, not just below it",
        max(same_scores) < pixels.SAME / 5,
        f"worst same-picture score {max(same_scores):.2f}",
    )
    check(
        "different-picture scores are far above the threshold, not just above it",
        closest[0] > pixels.SAME * 2,
        f"nearest different {closest[0]:.2f}",
    )

    # -- degenerate inputs ---------------------------------------------------
    check("a missing signature is never the same", not pixels.is_same(None, reference))
    check("a missing signature is never the same, either way", not pixels.is_same(reference, None))
    check("two missing signatures are not the same", not pixels.is_same(None, None))
    check("unreadable bytes give no signature", pixels.of_bytes(b"not an image") is None)
    check("a missing file gives no signature", pixels.of_path(GALLERY / "nope.jpg") is None)
    check("distance of mismatched lengths is infinite", pixels.distance([1.0], [1.0, 2.0]) == float("inf"))
    check("aspect of unreadable bytes is None", pixels.aspect(b"not an image") is None)
    check("first_duplicate ignores an unreadable signature", pixels.first_duplicate(None, []) is None)

    # -- first_duplicate -----------------------------------------------------
    seen = [(base.name, reference)]
    check(
        "first_duplicate finds the same picture under another name",
        pixels.first_duplicate(pixels.of_bytes(reencode(base, 0.5, 70)), seen) == base.name,
    )
    check(
        "first_duplicate does not find a different picture",
        pixels.first_duplicate(pixels.of_path(files[1]), seen) is None,
    )
    check("first_duplicate on an empty list finds nothing", pixels.first_duplicate(reference, []) is None)

    # -- of_ratio ------------------------------------------------------------
    # Cropping to 16:10 then comparing against a full frame of the same
    # photograph should still read as the same picture, which is what makes
    # recovery work for files that were cropped before they were installed.
    cropped = pixels.of_ratio(base.read_bytes(), 16 / 10)
    check("of_ratio reads a real image", cropped is not None)
    assert cropped is not None
    full = pixels.of_bytes(base.read_bytes())
    assert full is not None
    check(
        "a centre crop of a photograph is still the same photograph",
        pixels.is_same(cropped, full),
        f"distance {pixels.distance(cropped, full):.2f}",
    )
    check("of_ratio on unreadable bytes is None", pixels.of_ratio(b"nope", 1.6) is None)

    print(f"\n{passed + len(failures)} assertions, {passed} pass, {len(failures)} fail")
    for line in failures:
        print(line)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(run())
