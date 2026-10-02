#!/usr/bin/env python3
"""Tests for the credit-recovery name matcher.

This is the part of the pipeline that decides *which Commons file an installed
photograph came from*, and every wrong answer here becomes a licence violation
or a photograph credited to the wrong place. It had no tests at all, which is how
the bug below survived a full recovery run that reported 81 successful credits
while this function had never once returned a match.

The bug: `slug_key` reduced a Commons *title* and `local_key` reduced an
installed *filename*, and the two disagreed by a trailing "jpg" for every file
in the project -- because "j", "p" and "g" are all letters and so survive a
letters-and-digits filter. The name-matching stage therefore never matched
anything, every recovery silently fell through to the slower pixel stage, and
the report said "Commons has never heard of this file" for all 112 of them.

The failure was invisible because it is indistinguishable from the truth: a
slug that does not match looks exactly like a file Commons has not heard of.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

_spec = importlib.util.spec_from_file_location("recover", HERE / "recover.py")
recover = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(recover)

PASSED = 0
FAILED: list[str] = []


def check_that(what: str, got: object, expected: object) -> None:
    """Assert, and report what actually came back when it fails."""
    global PASSED
    if got == expected:
        PASSED += 1
    else:
        FAILED.append(f"{what}\n      expected {expected!r}\n      got      {got!r}")


# ---------------------------------------------------------------------------
# the bug: the extension has to leave the key, or nothing ever matches
# ---------------------------------------------------------------------------
check_that(
    "a Commons title and the filename derived from it reduce to the same key",
    recover.slug_key("Cape Coast Castle 09 05 2025.jpg"),
    recover.local_key("cape-coast-castle-09-05-2025.jpg"),
)
check_that(
    "the extension is dropped rather than folded into the key",
    recover.slug_key("Cape Coast Castle 09 05 2025.jpg"),
    "capecoastcastle09052025",
)
# Every format the pipeline will install, because a .png title reaching the
# matcher must not behave differently from a .jpg one.
for _suffix in (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".gif"):
    check_that(
        f"{_suffix} is recognised as an extension and dropped",
        recover.slug_key(f"Fort Nassau gate{_suffix}"),
        "fortnassaugate",
    )

# Digits are part of the identity of a photograph, not decoration. A date in a
# filename is the main thing distinguishing two shots of the same place, so a
# matcher that dropped digits would call them the same picture.
check_that(
    "digits in a title are kept",
    recover.slug_key("Fort Nassau 1990"),
    "fortnassau1990",
)
check_that(
    "a numeric suffix distinguishes two photographs of one place",
    recover.slug_key("Osu Castle 01.jpg") != recover.slug_key("Osu Castle 02.jpg"),
    True,
)

# A title that merely ends in something dot-shaped is not an extension, and
# "Nji Gbetkom" has no dot at all. Stripping blindly would eat real words.
check_that(
    "a title with no extension is untouched",
    recover.slug_key("Nji Gbetkom"),
    "njigbetkom",
)
check_that(
    "punctuation is still stripped from the middle of a title",
    recover.slug_key("Kejetia-Markt.jpg"),
    "kejetiamarkt",
)
check_that(
    "accents fold rather than survive as separate letters",
    recover.slug_key("Fort Bátienstein.jpg"),
    "fortbatienstein",
)

# ---------------------------------------------------------------------------
# the second half: installed names disagree about whether they carry the entity
# id, so both forms have to be offered
# ---------------------------------------------------------------------------
check_that(
    "a filename that repeats the entity id alone matches only when stripped",
    "poort" in recover.local_keys("fort-nassau-mouri-poort.jpg", "fort-nassau-mouri"),
    True,
)
check_that(
    "the stripped form is tried as well as the full one",
    recover.local_keys("fort-nassau-mouri-poort.jpg", "fort-nassau-mouri"),
    ["fortnassaumouripoort", "poort"],
)

# A filename chosen by hand can spell a word differently from the Commons title
# it was named after -- `kejetia-market-markt.jpg` for the file "Kejetia-Markt",
# because "Markt" is German for "market" and the local name says "market". No key
# can faithfully connect them, and that is correct rather than a gap: widening the
# matcher until it accepted a partial-word match is how a photograph gets credited
# to the wrong place. Such a file is reported unmatched and credited in
# IMAGE-CREDITS.md by hand instead, which is what plan_from_credits.py reads back.
check_that(
    "a hand-spelled filename does not loosely match a differently-spelled title",
    recover.slug_key("Kejetia-Markt.jpg")
    in recover.local_keys("kejetia-market-markt.jpg", "kejetia-market"),
    False,
)
check_that(
    "it is offered as keys rather than silently dropped",
    recover.local_keys("kejetia-market-markt.jpg", "kejetia-market"),
    ["kejetiamarketmarkt", "markt"],
)
check_that(
    "a filename with no entity prefix is offered once, not twice",
    recover.local_keys("osu-castle.jpg", "osu-castle"),
    ["osucastle"],
)
check_that(
    "a different entity's prefix is not stripped",
    recover.local_keys("kejetia-market-markt.jpg", "bonwire-kente-village"),
    ["kejetiamarketmarkt"],
)

# ---------------------------------------------------------------------------
# the real filenames this bug shipped on, as a regression net
# ---------------------------------------------------------------------------
_REAL_PAIRS = [
    ("Cape Coast Castle 09 05 2025.jpg", "cape-coast-castle-09-05-2025.jpg", "cape-coast-castle"),
    (
        "Barack Obama in Cape Coast Castle.jpg",
        "cape-coast-castle-barack-obama-in-cape-coast-castle.jpg",
        "cape-coast-castle",
    ),
    ("Cape Coast Castle, Cape Coast, Ghana.JPG", "cape-coast-castle-cape-coast-ghana.jpg", "cape-coast-castle"),
]
for _title, _local, _entity in _REAL_PAIRS:
    check_that(
        f"real pair matches: {_title}",
        recover.slug_key(_title) in recover.local_keys(_local, _entity),
        True,
    )

# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
print()
for _failure in FAILED:
    print(f"  FAIL  {_failure}")
print(f"\n{len(_REAL_PAIRS) * 0 + PASSED + len(FAILED)} assertions, {PASSED} pass, {len(FAILED)} fail")
raise SystemExit(1 if FAILED else 0)