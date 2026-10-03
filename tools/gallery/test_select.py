#!/usr/bin/env python3
"""Tests for selection's ritual awareness.

Festivals are selected partly on their own `keyRituals`, because a photograph of
Kpokpoi sprinkling is a photograph of Homowo even when the caption never says
"Homowo Festival" -- Commons is full of ritual photographs filed under the ritual
and not the festival.

Two things must hold, and the second is the one that matters:

  * a ritual that names only one festival counts as identification;
  * a ritual word shared with another festival counts as nothing.

The second is what stops a durbar being attributed to whichever festival listed
"Durbar of Paramount Chiefs" first. Four festivals mention durbars, and a gallery
of a different festival's durbar reads as perfectly plausible -- which is exactly
why it would not be caught by anyone looking at it.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

_spec = importlib.util.spec_from_file_location("select", HERE / "select.py")
select = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(select)

ENTITIES = select.load_entities()
select.load_sibling_map([e["name"] for e in ENTITIES])
select.load_ritual_map(ENTITIES)
FESTIVALS = [e for e in ENTITIES if e["kind"] == "festival"]
DESTINATIONS = [e for e in ENTITIES if e["kind"] == "destination"]

PASSED = 0
FAILED: list[str] = []


def check_that(what: str, got: object, expected: object) -> None:
    global PASSED
    if got == expected:
        PASSED += 1
    else:
        FAILED.append(f"{what}\n      expected {expected!r}\n      got      {got!r}")


def entity(entity_id: str) -> dict:
    return next(e for e in ENTITIES if e["id"] == entity_id)


def score(entity_id: str, title: str, categories: list[str] | None = None) -> int:
    record = {"title": title, "categories": categories or [], "extmetadata": {}}
    return select.specificity(record, entity(entity_id))


# -- the map covers names as well as rituals, which is what lets it see a ritual
# word colliding with some other entity's name -------------------------------
check_that("the map is built over rituals and names", len(select.RITUAL_OWNER) > 300, True)
check_that(
    "a ritual word shared by two festivals has both as owners",
    select.RITUAL_OWNER.get("durbar") == {"aboakyer-festival", "apoo-festival", "fetu-afahye-festival", "hogbetsotso-festival"},
    True,
)
check_that(
    "a word unique to one festival has that one owner",
    select.RITUAL_OWNER.get("kpokpoi"),
    {"homowo-festival"},
)

# -- the first rule: a distinctive ritual identifies its festival -------------
check_that(
    "a distinctive ritual in the title is specific enough",
    score("homowo-festival", "File:Kpokpoi sprinkling at Homowo.jpg"),
    2,
)
check_that(
    "a distinctive ritual in a category is specific enough",
    score("aboakyer-festival", "File:Hunt.jpg", categories=["Asafo Warrior Deer Hunt"]),
    2,
)
check_that(
    "a distinctive ritual in the description is specific enough",
    select.specificity(
        {
            "title": "File:Untitled.jpg",
            "categories": [],
            "extmetadata": {"ImageDescription": {"value": "Community fundraiser for the festival"}},
        },
        entity("adekyem-festival"),
    )
    == 2,
    True,
)
check_that(
    "naming the festival outright still beats naming only a ritual",
    score("homowo-festival", "File:Homowo Festival Kpokpoi.jpg"),
    3,
)

# -- the second rule: a shared word identifies nothing -------------------------
# All three of Adekyem's "Ancestral Libation Pouring" words are claimed by other
# festivals, so no combination of them can say which festival this is. Accepting
# it would attribute a photograph to one of three festivals at random.
check_that(
    "a ritual made entirely of shared words scores nothing",
    score("adekyem-festival", "File:Ancestral libation pouring.jpg"),
    0,
)
check_that(
    "one distinctive word inside a shared phrase is enough",
    score("adekyem-festival", "File:Harvest Gift Sharing.jpg"),
    2,
)
check_that(
    "a word shared with another festival's ritual is refused",
    score("adekyem-festival", "File:Drumming performance.jpg"),
    0,
)
check_that(
    "'durbar' is refused for every festival that mentions one",
    {score(f["id"], "File:Royal Durbar.jpg") for f in FESTIVALS},
    {0},
)

# -- destinations must be untouched -------------------------------------------
check_that("a destination has no ritual keys", select.distinctive_ritual_keys(DESTINATIONS[0]), set())
check_that(
    "a destination is still scored on its name alone",
    score("cape-coast-castle", "File:Cape Coast Castle 34.jpg") >= 2,
    True,
)

# -- search terms include the rituals ------------------------------------------
_terms = select.search_terms(entity("aboakyer-festival"))
check_that(
    "the festival name leads the search",
    _terms[0],
    "Aboakyer Festival",  # parenthetical dropped; see search_terms
)
check_that(
    "a parenthetical is never sent to Commons",
    all("(" not in t for t in _terms),
    True,
)
check_that(
    "ritual phrases are searched, not just the festival name",
    "Asafo Warrior Deer Hunt" in _terms,
    True,
)
check_that(
    "ritual phrases come after the name-derived terms",
    _terms.index("Asafo Warrior Deer Hunt") >= 3,
    True,
)
check_that("search terms are capped", len(_terms) <= 6, True)
check_that(
    "a destination searches without rituals",
    select.search_terms(DESTINATIONS[0]),
    [t for t in select.search_terms(DESTINATIONS[0]) if len(t) > 3][:6],
)
check_that("ritual_terms returns nothing for a destination", select.ritual_terms(DESTINATIONS[0]), [])

# -- the map is replaced, not accumulated --------------------------------------
_selective = [
    entity("homowo-festival"),
    entity("adekyem-festival"),
]
select.load_ritual_map(_selective)
check_that(
    "reloading with two festivals does not keep the other eleven",
    select.RITUAL_OWNER.get("durbar") is None,
    True,
)
check_that(
    "a word owned by an entity outside the new set is dropped",
    select.distinctive_ritual_keys(entity("aboakyer-festival")),
    set(),
)
select.load_ritual_map(ENTITIES)  # restore for any later import
check_that(
    "the map can be rebuilt and gives the same answer",
    select.RITUAL_OWNER.get("kpokpoi"),
    {"homowo-festival"},
)

# -- one local filename, three real Commons titles ---------------------------
#
# MediaWiki titles are case-insensitive only at the first letter; a slug is
# case-insensitive everywhere. Three genuine files -- "A View from the Summit",
# "A view from the Summit", "A view from the summit" -- therefore reduce to one
# local name. Before this was guarded, all three downloaded (different bytes, so
# the pixel check could not call them twins), each overwrote the same path, and
# each emitted its own row: one photograph shown three times, three credits, and
# the site agreeing with neither.
def _plain(title: str, specificity: int = 3) -> dict:
    return {
        "title": title,
        "categories": [],
        "extmetadata": {},
        "specificity": specificity,
        "width": 1600,
        "height": 1067,
        "thumbwidth": 1600,
    }


_colliding, _collision_notes = select.install(
    {
        "mount-afadjato": [
            _plain("File:A View from the Summit.jpg"),
            _plain("File:A view from the Summit.jpg"),
            _plain("File:A view from the summit.jpg"),
        ]
    },
    write=False,
    report_only=True,
)
check_that(
    "three titles that slug to one filename yield one row",
    len(_colliding),
    1,
)
check_that(
    "the first claimant keeps the photograph",
    _colliding[0]["title"] if _colliding else None,
    "File:A View from the Summit.jpg",
)
check_that(
    "the filename really is the shared slug",
    _colliding[0]["file"] if _colliding else None,
    "gallery/mount-afadjato-a-view-from-the-summit.jpg",
)
check_that(
    "a dropped collision is reported rather than silent",
    len(_collision_notes),
    2,
)
check_that(
    "nothing else in the run was affected",
    all("mount-afadjato" in note for note in _collision_notes),
    True,
)

# Titles that do *not* collide must still get one row each, or the guard would
# be quietly throwing away perfectly good photographs.
_distinct, _distinct_notes = select.install(
    {
        "mount-afadjato": [
            _plain("File:A View from the Summit.jpg"),
            _plain("File:Wild fruits on the mountain.jpg"),
            _plain("File:223m up.jpg"),
        ]
    },
    write=False,
    report_only=True,
)
check_that(
    "three distinct titles still give three rows",
    len(_distinct),
    3,
)
check_that(
    "and nothing is reported against them",
    len(_distinct_notes),
    0,
)

# -- a rate limit must stop the run, not be rediscovered a hundred times ------
#
# Commons rate limits whole clients, so a hard limit presents as a string of
# unrelated individual failures. Grinding through every remaining entity costs a
# few minutes each and buys nothing: none of them are checkpointed, so the run
# would have been restarted from exactly where it was anyway.
class _Blocked:
    """Every request fails, the way a saturated rate limit does."""

    def search(self, term: str, limit: int = 50) -> list[str]:
        raise RuntimeError("429 Too Many Requests")

    def info(self, titles: list[str]) -> dict[str, dict]:
        raise RuntimeError("429 Too Many Requests")


_block_buffer = io.StringIO()
with contextlib.redirect_stdout(_block_buffer):
    _blocked_passing, _blocked_rejected, _blocked_failed = select.collect(
        _Blocked(),
        DESTINATIONS[:10],
        [e["name"] for e in DESTINATIONS[:10]],
        checkpoint=None,
    )
_blocked_log = _block_buffer.getvalue()

check_that(
    "a saturated rate limit stops after four entities, not ten",
    len(_blocked_failed),
    select.STALL_AFTER_FAILURES,
)
check_that(
    "nothing is claimed as having been searched and found empty",
    _blocked_rejected,
    {},
)
check_that(
    "and nothing is claimed as passing",
    _blocked_passing,
    {},
)
check_that(
    "the log says why it stopped, so a stalled run is not read as a finished one",
    "cooldown" in _blocked_log,
    True,
)

# A failure that is genuinely isolated must not stop anything -- otherwise the
# guard above would turn one flaky entity into an aborted run.
class _OneBad:
    """The first entity fails; everything after it works."""

    def __init__(self) -> None:
        self.calls = 0

    def search(self, term: str, limit: int = 50) -> list[str]:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("429 Too Many Requests")
        return [f"File:Placeholder {self.calls}.jpg"]

    def info(self, titles: list[str]) -> dict[str, dict]:
        # Commons returns a mapping of title to record, not a list.
        return {
            title: {
                "title": title,
                "mime": "image/jpeg",
                "sha1": f"{self.calls}-{index}",
                "categories": [],
                "extmetadata": {},
                "width": 1600,
                "height": 1067,
                "thumbwidth": 1600,
                "thumburl": "https://upload.wikimedia.org/x.jpg",
                "descriptionurl": "https://commons.wikimedia.org/wiki/File:X",
            }
            for index, title in enumerate(titles)
        }


_one_buffer = io.StringIO()
with contextlib.redirect_stdout(_one_buffer):
    _one_passing, _one_rejected, _one_failed = select.collect(
        _OneBad(),
        DESTINATIONS[:10],
        [e["name"] for e in DESTINATIONS[:10]],
        checkpoint=None,
    )
check_that(
    "one isolated failure does not stop the run",
    len(_one_failed),
    1,
)
# An entity is recorded in `passing` whether or not anything survived screening,
# so this counts attempted entities, not successful ones.
check_that(
    "the entities after it are still attempted",
    len(_one_passing),
    9,
)
check_that(
    "and the failure was recorded as a failure, not as an empty search",
    list(_one_failed)[0],
    DESTINATIONS[0]["id"],
)

# ---------------------------------------------------------------------------
print()
for _failure in FAILED:
    print(f"  FAIL  {_failure}")
print(f"\n{PASSED + len(FAILED)} assertions, {PASSED} pass, {len(FAILED)} fail")
raise SystemExit(1 if FAILED else 0)
