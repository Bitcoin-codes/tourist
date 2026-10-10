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
import json
import sys
import tempfile
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

# -- the official name of a place known by its short one -----------------------
#
# "A guy making hand beads at the National Centre for Culture and Arts in Accra,
# Ghana" describes the craft bazaar this site lists as the Accra Arts Centre;
# that centre's official name is the Centre for National Culture, Accra. The
# file's title is "Beads maker 3", which names nothing, and a distinctive word
# in a description alone scores 1 -- below MIN_SPECIFICITY -- so thirty-six
# photographs of the market itself were dropped as naming no destination.
#
# The alias carries "Accra" because the data also lists the Kumasi Centre for
# National Culture. These phrases are matched as token sets, so without the
# city a Kumasi caption would score for the Accra market and take it over.
check_that(
    "the Centre for National Culture, Accra is the Accra Arts Centre",
    select.specificity(
        {
            "title": "File:Beads maker 3.jpg",
            "categories": [],
            "extmetadata": {
                "ImageDescription": {
                    "value": "A guy making hand beads at the National Centre for Culture and Arts in Accra, Ghana"
                }
            },
        },
        entity("accra-arts-centre"),
    ),
    2,
)
check_that(
    "a Kumasi caption scores nothing for the Accra market",
    select.specificity(
        {
            "title": "File:Kente seller 2.jpg",
            "categories": [],
            "extmetadata": {
                "ImageDescription": {
                    "value": "Craft stalls at the Centre for National Culture, Kumasi"
                }
            },
        },
        entity("accra-arts-centre"),
    ),
    0,
)
check_that(
    "the Kumasi centre still scores on its own name",
    select.specificity(
        {
            "title": "File:Kente seller 2.jpg",
            "categories": [],
            "extmetadata": {
                "ImageDescription": {
                    "value": "Craft stalls at the Centre for National Culture, Kumasi"
                }
            },
        },
        entity("centre-for-national-culture"),
    )
    >= 2,
    True,
)

# -- search terms include the rituals ------------------------------------------
_terms = select.search_terms(entity("aboakyer-festival"))
check_that(
    "the festival name leads the search",
    _terms[0],
    f"Aboakyer Festival {select.GHANA_ANCHOR}",  # parenthetical dropped
)
check_that(
    "a parenthetical is never sent to Commons",
    all("(" not in t for t in _terms),
    True,
)
check_that(
    "every query is anchored to the country",
    all(t.endswith(f" {select.GHANA_ANCHOR}") for t in _terms),
    True,
)
check_that(
    "the anchor is one word, so it cannot discard the name it qualifies",
    select.GHANA_ANCHOR,
    "Ghana",
)
check_that(
    "ritual phrases are searched, not just the festival name",
    any(t.startswith("Asafo Warrior Deer Hunt") for t in _terms),
    True,
)
check_that(
    "ritual phrases come after the name-derived terms",
    next(i for i, t in enumerate(_terms) if t.startswith("Asafo Warrior Deer Hunt")) >= 3,
    True,
)
check_that("search terms are capped", len(_terms) <= 6, True)
check_that(
    "a destination searches without rituals",
    select.search_terms(DESTINATIONS[0]),
    [t for t in select.search_terms(DESTINATIONS[0]) if len(t) > 3][:6],
)
check_that(
    "a destination's first query is its own name in Ghana",
    select.search_terms(DESTINATIONS[0])[0],
    f"{DESTINATIONS[0]['name'].split(' (')[0]} {select.GHANA_ANCHOR}",
)
check_that("ritual_terms returns nothing for a destination", select.ritual_terms(DESTINATIONS[0]), [])

# -- an entity whose own name matches nothing still gets queries that can -----
_alias_entity = entity("komfo-anokye-sword-site")
_alias_terms = select.search_terms(_alias_entity)
check_that(
    "a four-word name queries its short form as well",
    select.alias_terms(_alias_entity),
    ["anokye sword", "komfo anokye"],
)
check_that(
    "the short form reaches Commons as a query of its own",
    "komfo anokye Ghana" in _alias_terms,
    True,
)
check_that(
    "the destination's own name still leads every query",
    _alias_terms[0],
    f"Komfo Anokye Sword Site {select.GHANA_ANCHOR}",
)
check_that(
    "alias queries are pinned to the country like every other query",
    all(t.endswith(f" {select.GHANA_ANCHOR}") for t in _alias_terms),
    True,
)
check_that(
    "a destination with no recorded alias asks for none",
    select.alias_terms(DESTINATIONS[0]),
    [],
)
check_that(
    "an alias is not borrowed across two destinations sharing one word",
    select.alias_terms(entity("gushiegu-textile-centre")),
    ["gushiegu", "gushiegu market"],
)
check_that(
    "an answered alias does not crowd out one never asked",
    select.alias_terms(
        entity("komfo-anokye-sword-site"),
        asked=[
            f"anokye sword {select.GHANA_ANCHOR}",
            f"komfo anokye {select.GHANA_ANCHOR}",
        ],
    ),
    ["manhyia sword", "sword site kumasi"],
)
check_that(
    "aliases are capped with everything else",
    len(_alias_terms) <= 6,
    True,
)
check_that(
    "an alias names the place well enough to score against its own name",
    select.specificity(
        {"title": "Komfo Anokye Sword Site", "categories": [], "extmetadata": {}},
        _alias_entity,
    )
    >= select.MIN_SPECIFICITY,
    True,
)

# -- an entity that came back empty is re-asked, but only about what is new ----
#
# The alias above exists because a four-word name returns nothing at all. If a
# retry also repeated the four queries that already returned nothing, the pass
# would cost six requests where two would do -- and the rate limit answering
# bursts with 429s would spend that budget rediscovering answers it has given.
# So a row records what it asked, and an empty row is re-asked about the rest.
class _Asks:
    """Records the queries sent and finds nothing, so the entity stays empty."""

    def __init__(self) -> None:
        self.terms: list[str] = []

    def search(self, term: str, limit: int = 50) -> list[str]:
        self.terms.append(term)
        return []

    def info(self, titles: list[str]) -> dict[str, dict]:
        return {}


_retry = entity("komfo-anokye-sword-site")
_alias_queries = {f"{a} {select.GHANA_ANCHOR}" for a in select.alias_terms(_retry)}
_row = {
    "id": _retry["id"],
    "kept": [],
    "rejected": [{"title": "", "reason": "no candidates found"}],
    "tried": [t for t in select.search_terms(_retry) if t not in _alias_queries],
}
with tempfile.TemporaryDirectory() as _dir:
    _cp = Path(_dir) / "checkpoint.jsonl"
    _cp.write_text(json.dumps(_row) + "\n")

    _first = _Asks()
    with contextlib.redirect_stdout(io.StringIO()):
        select.collect(_first, [_retry], [_retry["name"]], checkpoint=_cp)
    check_that(
        "a retry does not repeat a query that already returned nothing",
        [t for t in _first.terms if t not in _alias_queries],
        [],
    )
    check_that(
        "it does ask the alias nobody has tried yet",
        sorted(_first.terms),
        sorted(_alias_queries),
    )
    _written = [json.loads(line) for line in _cp.read_text().splitlines() if line.strip()]
    check_that(
        "and the row it writes remembers every query, aliases included",
        set(_written[-1]["tried"]),
        set(_row["tried"]) | _alias_queries,
    )

    _second = _Asks()
    with contextlib.redirect_stdout(io.StringIO()):
        select.collect(_second, [_retry], [_retry["name"]], checkpoint=_cp)
    check_that(
        "a second retry asks the aliases still unasked, and only those",
        _second.terms,
        ["manhyia sword Ghana", "sword site kumasi Ghana"],
    )

    # And once even those have been answered there is nothing left to ask: the
    # checkpoint remembers every query, alias included.
    _exhausted = _Asks()
    with contextlib.redirect_stdout(io.StringIO()):
        select.collect(_exhausted, [_retry], [_retry["name"]], checkpoint=_cp)
    check_that(
        "a third retry asks nothing at all -- the question has been answered",
        _exhausted.terms,
        [],
    )

    # A pool already large enough to show is never re-asked: its screening
    # stands, and the searches for it are over.
    _with_photos = dict(
        _row, kept=[{"title": "File:One.jpg"}, {"title": "File:Two.jpg"}], tried=[]
    )
    _cp.write_text(json.dumps(_with_photos) + "\n")
    _third = _Asks()
    with contextlib.redirect_stdout(io.StringIO()):
        select.collect(_third, [_retry], [_retry["name"]], checkpoint=_cp)
    check_that(
        "an entity with photographs enough to show is left exactly as it was",
        _third.terms,
        [],
    )

    # One photograph is not a strip, so the search continues -- but only about
    # questions still unanswered, and what the entity already holds survives a
    # retry that finds nothing more (merge, never replace).
    _thin = dict(_row, kept=[{"title": "File:One.jpg"}])
    _cp.write_text(json.dumps(_thin) + "\n")
    _fourth = _Asks()
    with contextlib.redirect_stdout(io.StringIO()):
        select.collect(_fourth, [_retry], [_retry["name"]], checkpoint=_cp)
    check_that(
        "an entity holding one photograph asks only the queries never sent",
        _fourth.terms,
        sorted(_alias_queries),
    )
    _written_thin = [
        json.loads(line) for line in _cp.read_text().splitlines() if line.strip()
    ]
    check_that(
        "and the photograph it already held is still held",
        _written_thin[-1]["kept"],
        [{"title": "File:One.jpg"}],
    )

# -- the early break must not record queries it never made ---------------------
#
# SEARCH_ENOUGH stops the loop once there is enough to choose from. The row
# used to record the whole of `todo` rather than what was actually put to
# Commons, so a term the break had skipped was written down as answered and no
# later run would ask it. Alias terms come last by construction, which is
# precisely where it bit: "Princess Town Beach" flooded on "princess Ghana",
# broke, and recorded "princes town beach" -- the alternative name it was built
# for -- as a question that had been answered.
class _Breaks:
    """Floods the first query so the loop breaks before the later terms."""

    def __init__(self) -> None:
        self.terms: list[str] = []

    def search(self, term: str, limit: int = 50) -> list[str]:
        self.terms.append(term)
        if len(self.terms) == 1:
            return [f"File:Flood {i}.jpg" for i in range(select.SEARCH_ENOUGH + 5)]
        return ["File:Alias Photograph.jpg"]

    def info(self, titles: list[str]) -> dict[str, dict]:
        return {}


_flood = entity("princess-town-beach")
_flood_terms = [
    *select.search_terms(_flood),
    *(f"{a} {select.GHANA_ANCHOR}" for a in select.alias_terms(_flood)),
]
with tempfile.TemporaryDirectory() as _dir:
    _bcp = Path(_dir) / "checkpoint.jsonl"
    _breaker = _Breaks()
    with contextlib.redirect_stdout(io.StringIO()):
        select.collect(_breaker, [_flood], [_flood["name"]], checkpoint=_bcp)
    check_that(
        "the flood trips the break before every term is asked",
        len(_breaker.terms) < len(_flood_terms),
        True,
    )
    _brow = [json.loads(line) for line in _bcp.read_text().splitlines() if line.strip()][-1]
    check_that(
        "and the row records a question only if it was actually asked",
        set(_brow["tried"]) - set(_breaker.terms),
        set(),
    )
    check_that(
        "so the alias the break skipped is still unasked next run",
        select.alias_terms(_flood, _brow["tried"]),
        select.alias_terms(_flood),
    )

# -- a retry must add what it finds, not keep only what it carried -------------
#
# The merge built its "already present" set from the new pool instead of the
# carried one, so it filtered the new records against themselves, removed every
# one, and left `carried` standing alone. Only an entity below MIN_WANT retries
# at all, so this cost precisely the entities that most needed the help: Nania
# Slave Route held one photograph, its queries found three, and it kept the one
# it started with -- while the run reported the merge as done.
class _Merges:
    """Finds one photograph the entity does not yet hold."""

    def __init__(self) -> None:
        self.terms: list[str] = []

    def search(self, term: str, limit: int = 50) -> list[str]:
        self.terms.append(term)
        return ["File:Feeding blows for slaves Nania.jpg"]

    def info(self, titles: list[str]) -> dict[str, dict]:
        return {
            title: {
                "title": title,
                "width": 1600,
                "height": 1200,
                "sha1": f"newsha-{title}",
                "mime": "image/jpeg",
                "categories": [],
                "descriptionurl": "https://commons.wikimedia.org/wiki/File:x",
                "extmetadata": {
                    "LicenseShortName": {"value": "CC BY-SA 4.0"},
                    "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0"},
                    "ImageDescription": {"value": "Feeding blows for the slaves at Nania"},
                },
            }
            for title in titles
        }


_nania = entity("nania-slave-route")
_held = {
    "title": "File:Tower for checking the slaves at Nania.jpg",
    "width": 1920,
    "height": 2560,
    "sha1": "oldsha",
    "categories": [],
    "descriptionurl": "https://commons.wikimedia.org/wiki/File:y",
    "extmetadata": {"LicenseShortName": {"value": "CC BY-SA 4.0"}},
}
with tempfile.TemporaryDirectory() as _dir:
    _mcp = Path(_dir) / "checkpoint.jsonl"
    _mcp.write_text(
        json.dumps({"id": _nania["id"], "kept": [_held], "rejected": [], "tried": []}) + "\n"
    )
    with contextlib.redirect_stdout(io.StringIO()):
        select.collect(_Merges(), [_nania], [_nania["name"]], checkpoint=_mcp)
    _mrow = [json.loads(line) for line in _mcp.read_text().splitlines() if line.strip()][-1]
    _titles = {r["title"] for r in _mrow["kept"]}
    check_that(
        "a retry keeps the photograph the entity already held",
        "File:Tower for checking the slaves at Nania.jpg" in _titles,
        True,
    )
    check_that(
        "and keeps what the retry found, which the broken merge discarded",
        "File:Feeding blows for slaves Nania.jpg" in _titles,
        True,
    )
    check_that(
        "so the pool grows by exactly the new photograph",
        len(_mrow["kept"]),
        2,
    )

# -- a photograph condemned by eye does not come back --------------------------
#
# screen is stateless, so on any later run the same file passes again and lands
# in kept. Nothing used to notice because the broken merge discarded everything
# a retry found, condemned photographs included. With the merge fixed, a
# verdict given on a contact sheet has to be remembered or it is silently
# overturned by the next pass.
class _Condemned:
    """Returns a title the entity was already told, by eye, is the wrong place."""

    def search(self, term: str, limit: int = 50) -> list[str]:
        return ["File:Pikworo stone.jpg"]

    def info(self, titles: list[str]) -> dict[str, dict]:
        return {
            title: {
                "title": title,
                "width": 2000,
                "height": 1500,
                "sha1": f"pik-{title}",
                "mime": "image/jpeg",
                "categories": [],
                "descriptionurl": "https://commons.wikimedia.org/wiki/File:z",
                "extmetadata": {
                    "LicenseShortName": {"value": "CC BY-SA 4.0"},
                    "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0"},
                    "ImageDescription": {"value": "Feeding blows for the slaves at Nania"},
                },
            }
            for title in titles
        }


with tempfile.TemporaryDirectory() as _dir:
    _ccp = Path(_dir) / "checkpoint.jsonl"
    _ccp.write_text(
        json.dumps(
            {
                "id": _nania["id"],
                "kept": [],
                "rejected": [
                    {
                        "title": "File:Pikworo stone.jpg",
                        "reason": "wrong-place: rejected on contact-sheet review, 2026-10-08",
                    }
                ],
                "tried": [],
            }
        )
        + "\n"
    )
    with contextlib.redirect_stdout(io.StringIO()):
        select.collect(_Condemned(), [_nania], [_nania["name"]], checkpoint=_ccp)
    _crow = [json.loads(line) for line in _ccp.read_text().splitlines() if line.strip()][-1]
    check_that(
        "a photograph rejected on a contact sheet does not re-enter the pool",
        [r["title"] for r in _crow["kept"]],
        [],
    )
    check_that(
        "and the reason it was kept out is recorded, not silently applied",
        any(
            "rejected on contact-sheet review" in str(r.get("reason"))
            for r in _crow["rejected"]
        ),
        True,
    )

# But a rejection that was never a judgement of place must still be re-opened:
# raising MIN_WIDTH is only worth anything if a photograph refused as too small
# under the old floor can come back under the new one.
with tempfile.TemporaryDirectory() as _dir:
    _rcp = Path(_dir) / "checkpoint.jsonl"
    _rcp.write_text(
        json.dumps(
            {
                "id": _nania["id"],
                "kept": [],
                "rejected": [{"title": "File:Pikworo stone.jpg", "reason": "too small: 490px"}],
                "tried": [],
            }
        )
        + "\n"
    )
    with contextlib.redirect_stdout(io.StringIO()):
        select.collect(_Condemned(), [_nania], [_nania["name"]], checkpoint=_rcp)
    _rrow = [json.loads(line) for line in _rcp.read_text().splitlines() if line.strip()][-1]
    check_that(
        "a refusal for size alone is still re-opened on the next pass",
        [r["title"] for r in _rrow["kept"]],
        ["File:Pikworo stone.jpg"],
    )

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

# -- the file found on disk by its own name is the file, not a twin ----------
#
# `seen` is seeded from everything already installed, so a photograph the search
# downloaded a moment earlier is in there. When install reaches it, the pixels it
# just fetched match the file at the path it is about to write -- and that was
# read as "somebody else already has this photograph", so the row was dropped.
#
# Every record that had already been installed was dropped the same way, the
# plan came back empty, and a full batch reported "nothing new to apply" while
# 130 chosen photographs waited. It hid until now because select.py used to stop
# at assign() before ever reaching its own install; once that was fixed, the
# search started finishing and was always first to the files.
import tempfile as _tempfile

_SRC_BYTES = next(
    existing.read_bytes()
    for existing in sorted(select.GALLERY.glob("*.jpg"))
    if not existing.stem.endswith(("-400", "-800"))
)
_REPRO = "mount-afadjato-a-view-from-the-summit.jpg"

with _tempfile.TemporaryDirectory() as _td:
    _td_path = Path(_td)
    (_td_path / _REPRO).write_bytes(_SRC_BYTES)
    _gallery_real, _fetch_real = select.GALLERY, select.fetch
    select.GALLERY = _td_path
    select.fetch = lambda _record: _SRC_BYTES  # bytes identical to what is on disk
    try:
        _reinstall, _reinstall_notes = select.install(
            {"mount-afadjato": [_plain("File:A View from the Summit.jpg")]},
            write=True,
            report_only=False,
        )
    finally:
        select.GALLERY, select.fetch = _gallery_real, _fetch_real

check_that(
    "a photograph already installed still earns its row",
    len(_reinstall),
    1,
)
check_that(
    "and is recorded as already installed, not as a duplicate",
    _reinstall_notes,
    [f"mount-afadjato/{_REPRO}: already installed, identical"],
)

# The guard it must not lose: a genuinely different file holding these same
# pixels really is a second name for one photograph, and is still dropped.
check_that(
    "a real duplicate under a different name is still rejected",
    select.pixels.first_duplicate(
        select.pixels.of_bytes(_SRC_BYTES),
        [("somewhere-else.jpg", select.pixels.of_bytes(_SRC_BYTES))],
    ),
    "somewhere-else.jpg",
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

# -- the checkpoint is a superset of any one run's scope ----------------------
#
# `--install --entity a --entity b` searches two entities but resumes from a
# checkpoint that every earlier run wrote to, so `passing` arrives holding
# festivals as well as destinations. Indexing straight by id raised KeyError --
# after all 113 entities had been searched, which is why it cost only the
# install step rather than the search.
_partial = {DESTINATIONS[0]["id"]: [], "homowo-festival": []}
_galleries, _unassigned = select.assign(_partial, DESTINATIONS[:3])
check_that(
    "entities outside this run's scope are skipped, not raised on",
    _galleries is not None,
    True,
)
check_that(
    "and the in-scope entities are still all present",
    [eid for eid in (DESTINATIONS[0]["id"], DESTINATIONS[1]["id"], DESTINATIONS[2]["id"]) if eid in _galleries],
    [DESTINATIONS[0]["id"], DESTINATIONS[1]["id"], DESTINATIONS[2]["id"]],
)
check_that(
    "the out-of-scope entity gets no gallery of its own",
    "homowo-festival" in _galleries,
    False,
)

# -- the width floor must stay above the widest derivative ---------------------
#
# The floor and VARIANTS in build_image_variants.py are one decision expressed
# twice. Above the widest derivative, a photograph is upscaled to fill it -- the
# thing MIN_WIDTH exists to prevent. Below it, and a photograph that can serve
# every size the site renders is refused anyway. Neither is visible from the
# number alone, so the relationship is what gets pinned.
_vend = importlib.util.spec_from_file_location(
    "_variants", Path(__file__).resolve().parents[1] / "build_image_variants.py"
)
_variants = importlib.util.module_from_spec(_vend)
assert _vend.loader is not None
_vend.loader.exec_module(_variants)
_widest = max(_variants.VARIANTS)
check_that(
    "the width floor clears the widest derivative the site renders",
    select.MIN_WIDTH > _widest,
    True,
)
check_that(
    "and is not so far above it that real photographs are lost for nothing",
    select.MIN_WIDTH <= _widest * 1.5,
    True,
)

# -- lowering the threshold surfaces candidates, it does not ship them ---------
#
# A photograph can pass every image gate -- raster, minimum width, the screen --
# and still score 1, because the uploader wrote "Cape Coast" for a fort in Cape
# Coast and nothing more. `install` dropped such a file before anyone saw it,
# which is the one way this pipeline can lose a real photograph it already holds.
# The threshold is therefore a knob for *looking*, never for shipping: apply
# still runs only on pairs that survive the contact sheet.
_record_one = {
    "title": "File:Monkeys 4.jpg",
    "categories": [],
    "extmetadata": {"ImageDescription": {"value": "Troop near the Atome gate"}},
    "sha1": "aaaa",
}
_TAFI = "tafi-atome-monkey-sanctuary"
check_that(
    "the record under inspection really is below the shipping threshold",
    select.specificity(_record_one, entity(_TAFI)) < select.MIN_SPECIFICITY,
    True,
)
check_that(
    "at the default threshold it is dropped, as before",
    select.assign({_TAFI: [_record_one]}, DESTINATIONS[:3])[0][_TAFI],
    [],
)
check_that(
    "lowering the threshold brings it up for inspection",
    len(
        select.assign({_TAFI: [_record_one]}, DESTINATIONS[:3], min_specificity=1)[
            0
        ][_TAFI]
    ),
    1,
)
check_that(
    "and it is still assigned to exactly one destination",
    select.assign({_TAFI: [_record_one]}, DESTINATIONS[:3], min_specificity=1)[1],
    [],
)

# -- a distinctive name word must not be enough on its own --------------------
#
# "Daboya Fugu Weaving Village" is the only destination in the data with
# "fugu" in its name, which makes "fugu" a distinctive token -- and Commons
# holds a century of Japanese pufferfish under exactly that word. The search
# returned "Fugu delivery truck in Meguro", "Fugu and lamb restaurant" and
# "Fugu sashimi (32738795990)" for a weaving village in Ghana's Northern
# Region, all scoring 2, all ready to install as photographs of that village.
#
# The word was identifying a fish, not a place. It now needs the record to also
# say where the photograph was taken.
check_that(
    "a Japanese pufferfish truck is not a photograph of a Ghanaian village",
    score("daboya-fugu-weaving-village", "Fugu delivery truck in Meguro.jpg"),
    0,
)
check_that(
    "nor a plate of sashimi",
    score("daboya-fugu-weaving-village", "Fugu sashimi (32738795990).jpg"),
    0,
)
check_that(
    "nor a Tokyo restaurant",
    score("daboya-fugu-weaving-village", "Fugu and lamb restaurant.jpg"),
    0,
)
check_that(
    "and not rescued by categories alone either",
    score(
        "daboya-fugu-weaving-village",
        "Dress 12.jpg",
        ["Fugu", "Pufferfish", "Japan"],
    ),
    0,
)

# The guard must not simply block everything, so the controls matter as much as
# the rejections: a photograph that says where it was taken still scores, and a
# photograph that gives the full name still scores highest of all.
check_that(
    "a photograph naming the park scores on the park",
    score("kyabobo-national-park", "Bushbuck at Kyabobo National Park.jpg") >= 2,
    True,
)
check_that(
    "a photograph naming the town scores on the town",
    score("kete-krachi-museum", "Ferry carrying passengers at Kete Krachi in Ghana.jpg") >= 2,
    True,
)
check_that(
    "the full name in a title still outranks everything",
    score("daboya-fugu-weaving-village", "Daboya Fugu Weaving Village loom.jpg"),
    3,
)

# And why festivals are unaffected: a name word that fails the location check
# does not return zero, it falls through to the ritual rules below it. Only a
# *description* carrying a distinctive name word still returns early, at the
# weaker score of 1 -- unchanged from before this guard existed.
check_that(
    "a ritual still scores for the festival that owns it",
    score("homowo-festival", "Kpokpoi sprinkling by the family head.jpg") >= 2,
    True,
)

# ---------------------------------------------------------------------------
print()
for _failure in FAILED:
    print(f"  FAIL  {_failure}")
print(f"\n{PASSED + len(FAILED)} assertions, {PASSED} pass, {len(FAILED)} fail")
raise SystemExit(1 if FAILED else 0)
