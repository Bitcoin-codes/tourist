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

import importlib.util
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

# ---------------------------------------------------------------------------
print()
for _failure in FAILED:
    print(f"  FAIL  {_failure}")
print(f"\n{PASSED + len(FAILED)} assertions, {PASSED} pass, {len(FAILED)} fail")
raise SystemExit(1 if FAILED else 0)
