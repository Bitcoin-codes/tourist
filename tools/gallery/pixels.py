#!/usr/bin/env python3
"""Deciding whether two image files are the same picture.

    from pixels import of_path, distance, SAME

The problem this solves comes up in three places and each of them had its own
copy of the answer, which is how a rule ends up meaning three things:

* `recover.py` must recognise an installed file as the Commons thumbnail it came
  from, without a person comparing them;
* `select.py` must notice that two Commons files are the same frame before it puts
  both in a gallery;
* `check.py` must notice that one photograph has been filed under two places.

The test is a 16x16 grayscale signature compared by mean absolute difference.
Why that works: a signature is a very lossy description of a picture, so two
genuinely different photographs of the same place -- a castle from the road and
from the courtyard -- differ by tens of grey levels on average, while the same
photograph resized, re-encoded at a lower quality, or converted to grayscale
first barely moves it at all.

Measured on this repository's own 109 files, which is where the threshold below
comes from rather than from a guess:

    same picture, re-encoded at quality 95 ...........  0.03
    same picture, re-encoded at quality 60 ...........  0.19
    same picture, half size ..........................  0.07
    same picture, quarter size ........................  0.12
    same picture, 1.5x size at quality 50 .............  0.11
    closest different picture, of 108 files .......... 37.58
    the same comparison with a bare 8x8 signature ....  fails

That last line is why this exists as a module rather than a line in each caller.
A first attempt hashed an 8x8 grayscale signature to a string and compared
strings. Two encodings of one photograph differ by a least-significant bit, so
the comparison never matched anything, and the duplicate check reported that no
gallery contained a repeated picture -- which is the answer a check gives when it
cannot see, and is indistinguishable from the answer when there is none.

It is not, and cannot be, a statement about *what* is in the picture. Two
photographs of the same place with the same composition -- the same doorway shot
taken twice -- will read as the same photograph. That is the right answer for all
three callers: they are asking "is this the same file of pixels", not "is this the
same view", and the ones that care about subject matter use `filters.py` on the
Commons metadata instead.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from PIL import Image

# 16x16 rather than smaller. At 8x8 a signature is 64 numbers for a whole frame,
# which is few enough that a coarse difference in a dark corner outweighs a
# complete change in the subject.
SIG = 16

# Mean absolute grey-level difference below which two signatures are the same
# picture. The nearest measurement on either side is 0.19 and 37.58, so this sits
# in a gap roughly two hundred times wider than the spread within the class, and
# is deliberately far from both ends of it.
SAME = 10.0


def pixels(image: Image.Image) -> list[float]:
    """The signature of an already-opened image, as grey levels."""
    return list(image.convert("L").resize((SIG, SIG), Image.LANCZOS).getdata())


def of_bytes(data: bytes) -> list[float] | None:
    """The signature of an encoded image held in memory, or None if unreadable."""
    try:
        with Image.open(io.BytesIO(data)) as image:
            return pixels(image)
    except Exception:
        return None


def of_path(path: Path) -> list[float] | None:
    """The signature of an image on disk, or None if unreadable."""
    try:
        with Image.open(path) as image:
            return pixels(image)
    except Exception:
        return None


def of_ratio(data: bytes, ratio: float) -> list[float] | None:
    """The signature after centre-cropping to `ratio` first.

    Needed when one side is a full frame and the other is already cropped, which
    is the case for anything that was cropped before being installed. Comparing
    them head-on measures the crop rather than the subject, and two photographs of
    the same place can then score close on crop geometry alone.
    """
    try:
        with Image.open(io.BytesIO(data)) as raw:
            image = raw.convert("L")
            width, height = image.size
            if width / height > ratio:
                new_width = int(round(height * ratio))
                left = (width - new_width) // 2
                image = image.crop((left, 0, left + new_width, height))
            else:
                new_height = int(round(width / ratio))
                top = (height - new_height) // 2
                image = image.crop((0, top, width, top + new_height))
            return pixels(image)
    except Exception:
        return None


def distance(a: list[float], b: list[float]) -> float:
    """Mean absolute difference between two signatures."""
    if not a or not b or len(a) != len(b):
        return float("inf")
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def is_same(a: list[float] | None, b: list[float] | None) -> bool:
    """True when two signatures describe the same picture."""
    if a is None or b is None:
        return False
    return distance(a, b) < SAME


def first_duplicate(
    mark: list[float] | None, seen: list[tuple[str, list[float]]]
) -> str | None:
    """The label of the first entry that is the same picture as `mark`, if any.

    A linear scan rather than a dictionary keyed on the signature, because a
    signature is not a hash and two files that are the same picture do not produce
    identical signatures -- they produce *nearly* identical ones, and the whole
    point of the distance is to notice that. A few hundred comparisons of 256
    numbers each is nothing.
    """
    if mark is None:
        return None
    for label, other in seen:
        if is_same(mark, other):
            return label
    return None


def aspect(path_or_bytes: Any) -> float | None:
    """Width over height, or None if the image cannot be read."""
    try:
        if isinstance(path_or_bytes, (bytes, bytearray)):
            with Image.open(io.BytesIO(path_or_bytes)) as image:
                return image.size[0] / image.size[1]
        with Image.open(path_or_bytes) as image:
            return image.size[0] / image.size[1]
    except Exception:
        return None
