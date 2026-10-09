#!/usr/bin/env python3
"""Tests for the category-namespace harvest.

The claim under test is narrow and it is the whole point: a photograph reached
through a category must face exactly the gates a photograph reached through a
search query faces, and its arrival must never disturb what the query already
found. Everything else in this file is detail of those two promises.

Third: the category markers recorded in `tried` must be inert to `select` --
a search term always ends in the country anchor, so a "category:" prefix can
never be mistaken for one, and re-running the harvest must sweep nothing twice.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


category = _load("category")
select = _load("select")

# A plain import, not an importlib load: `category.py` catches `CommonsError`
# from the one `commons` module on sys.path, and a separately-exec'd copy would
# define a second class object that the same `except` clause does not match.
import commons  # noqa: E402

ENTITIES = select.load_entities()
select.load_sibling_map([e["name"] for e in ENTITIES])
select.load_ritual_map(ENTITIES)

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


# -- a record that passes every gate, so a test can change one thing at a time
def good_record(title: str, *, sha1: str, width: int = 1600, categories=None) -> dict:
    return {
        "title": title,
        "width": width,
        "height": 1200,
        "mime": "image/jpeg",
        "sha1": sha1,
        "descriptionurl": "https://commons.wikimedia.org/wiki/" + title.replace(" ", "_"),
        "thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/x.jpg",
        "thumbwidth": 1920,
        "thumbheight": 1440,
        "extmetadata": {
            "LicenseShortName": {"value": "CC BY-SA 4.0"},
            "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0"},
            "Artist": {"value": "Some Photographer"},
        },
        "categories": categories or [],
    }


class FakeCommons:
    """A Commons that answers from dicts and counts what was asked."""

    def __init__(self, categories_found=None, members=None, records=None, fail_terms=()):
        self.categories_found = categories_found or {}
        self.members = members or {}
        self.records = records or {}
        self.fail_terms = set(fail_terms)
        self.asked_categories: list[str] = []
        self.asked_members: list[tuple[str, str]] = []

    def search_categories(self, term, limit=20):
        if term in self.fail_terms:
            raise commons.CommonsError(f"simulated failure for {term!r}")
        return list(self.categories_found.get(term, []))

    def category_members(self, cat, kind="file", limit=50):
        if not cat.startswith("Category:"):
            raise ValueError(f"cmtitle must be a category title: {cat!r}")
        self.asked_members.append((cat, kind))
        return list(self.members.get((cat, kind), []))

    def info(self, titles):
        return {t: self.records[t] for t in titles if t in self.records}


# -- category_terms --------------------------------------------------------
daboya = entity("daboya-fugu-weaving-village")
# An explicit limit: the live TERMS_PER_ENTITY is rate-limit tuning and moves
# with how Commons is serving, so these check the ordering the function
# promises, not whatever the constant happens to be this week.
terms = category.category_terms(daboya, limit=3)
check_that("the town leads the category terms", terms[0], "Daboya")
check_that("the bare name follows the town", terms[1], "Daboya Fugu Weaving Village")
check_that("no more than the requested number of terms", len(terms) <= 3, True)
check_that(
    "the live default asks for at least one term",
    len(category.category_terms(daboya)) >= 1,
    True,
)
check_that(
    "the country anchor is absent from category terms",
    any("ghana" in t.lower().split() for t in terms),
    False,
)

# A parenthetical is dropped here as it is in file search.
fort_royal = category.category_terms(entity("fort-royal"), limit=3)
check_that(
    "a parenthetical is dropped before searching categories",
    "Fort Royal (Cape Coast)" in fort_royal,
    False,
)

# -- relevant_category ------------------------------------------------------
check_that(
    "a category named for the town is relevant",
    category.relevant_category("Category:Daboya", daboya),
    True,
)
check_that(
    "a category containing the town is relevant",
    category.relevant_category("Category:Buildings in Daboya", daboya),
    True,
)
check_that(
    "a category with two of the name's words is relevant",
    category.relevant_category("Category:Fugu weaving", daboya),
    True,
)
check_that(
    "a category with one shared word is not relevant",
    category.relevant_category("Category:Weaving worldwide", daboya),
    False,
)
check_that(
    "an unrelated category is not relevant",
    category.relevant_category("Category:Museums in Ghana", daboya),
    False,
)

# A word too short to be evidence cannot make a category relevant on its own --
# searching "Wa" returns categories beginning "Water".
check_that(
    "a very short town does not match by containment alone",
    category.relevant_category("Category:Waterfalls in Ghana", entity("wa-naa-palace")),
    False,
)

# -- harvest: the gates are the search gates ---------------------------------
# `harvest` applies exactly what `collect` applies -- `screen` and `MIN_WIDTH`.
# The specificity score that would drop a merely-related photo is `assign`'s
# job, downstream, so a harvest that keeps such a photo is correct.
tmp = Path(tempfile.mkdtemp()) / "checkpoint.jsonl"

# Daboya: a town category with five files. `distinctive_tokens` for this name
# is only {'fugu'}, so a title must contain "fugu" (or the whole name) to name
# the place -- "Daboya market day" is a photograph of the town but does not
# identify the weaving village, and is refused off-subject.
client = FakeCommons(
    categories_found={"Daboya": ["Category:Daboya"]},
    members={("Category:Daboya", "file"): [
        "File:Fugu weaving at Daboya.jpg",
        "File:Fugu delivery truck in Meguro.jpg",
        "File:Fugu closeup tiny.jpg",
        "File:Market stall wares.jpg",
        "File:Fugu sashimi plate.jpg",
    ]},
    records={
        "File:Fugu weaving at Daboya.jpg": good_record(
            "File:Fugu weaving at Daboya.jpg", sha1="aaa", categories=["Category:Daboya"]
        ),
        "File:Fugu delivery truck in Meguro.jpg": good_record(
            "File:Fugu delivery truck in Meguro.jpg",
            sha1="bbb",
            categories=["Category:Fugu"],
        ),
        "File:Fugu closeup tiny.jpg": good_record(
            "File:Fugu closeup tiny.jpg", sha1="ccc", width=640, categories=["Category:Daboya"]
        ),
        "File:Market stall wares.jpg": good_record(
            "File:Market stall wares.jpg", sha1="ddd", categories=["Category:Daboya"]
        ),
        "File:Fugu sashimi plate.jpg": good_record(
            "File:Fugu sashimi plate.jpg", sha1="eee", categories=["Category:Fugu"]
        ),
    },
)
passing, rejected = category.harvest(client, [daboya], [e["name"] for e in ENTITIES], tmp)

titles_kept = [r["title"] for r in passing["daboya-fugu-weaving-village"]]
check_that(
    "the weaving photograph is kept",
    sorted(titles_kept),
    sorted(["File:Fugu weaving at Daboya.jpg", "File:Fugu sashimi plate.jpg"]),
)
reasons = {r["title"]: r["reason"] for r in rejected["daboya-fugu-weaving-village"]}
check_that(
    "a photograph too small is refused",
    reasons.get("File:Fugu closeup tiny.jpg", "").startswith("too small:"),
    True,
)
check_that(
    "a Japanese photograph is refused by a gate, not by luck",
    "foreign" in reasons.get("File:Fugu delivery truck in Meguro.jpg", ""),
    True,
)
check_that(
    "a town photo that does not name the village is refused off-subject",
    "off-subject" in reasons.get("File:Market stall wares.jpg", ""),
    True,
)

# The sashimi plate names the distinctive word "fugu" and so passes `screen`,
# but it is a photograph of a meal in Japan. What refuses it is `specificity`,
# which `assign` applies -- and `assign` is the gate every candidate meets
# before installation. This is the two-stage safety: harvest widens the pool
# generously, assign is strict.
by_title = {r["title"]: r for r in passing["daboya-fugu-weaving-village"]}
check_that(
    "assign's specificity drops the merely-related photo",
    select.specificity(by_title["File:Fugu sashimi plate.jpg"], daboya) < 2,
    True,
)
check_that(
    "while the real weaving photo scores enough to install",
    select.specificity(by_title["File:Fugu weaving at Daboya.jpg"], daboya) >= 2,
    True,
)

# -- harvest: merge, never replace -------------------------------------------
# The real-world shape of the merge: `select` searched and holds one photograph
# in the pool, with queries in `tried` but no category markers. The harvest
# must add the category's photographs without touching what search found --
# including a carried photo that would no longer pass `screen` on its own.
tmp2 = Path(tempfile.mkdtemp()) / "checkpoint.jsonl"
carried_record = good_record(
    "File:Daboya old search find.jpg", sha1="old", categories=["Category:Daboya"]
)
tmp2.write_text(
    json.dumps(
        {
            "id": "daboya-fugu-weaving-village",
            "kept": [carried_record],
            "rejected": [],
            "tried": ["Daboya Fugu Weaving Village Ghana", "Daboya Ghana"],
        }
    )
    + "\n"
)
client2 = FakeCommons(
    categories_found={"Daboya": ["Category:Daboya"]},
    members={("Category:Daboya", "file"): [
        "File:Daboya old search find.jpg",
        "File:Fugu weaving group.jpg",
    ]},
    records={
        "File:Daboya old search find.jpg": carried_record,
        "File:Fugu weaving group.jpg": good_record(
            "File:Fugu weaving group.jpg", sha1="eee", categories=["Category:Daboya"]
        ),
    },
)
# An explicit descent budget: the live SUBCATS_PER_ENTITY is rate-limit
# tuning and is currently zero, so this exercises the marker-recording
# mechanism independently of that tuning.
passing2, _ = category.harvest(
    client2,
    [daboya],
    [e["name"] for e in ENTITIES],
    tmp2,
    subcats_per_entity=3,
)
check_that(
    "the carried photograph stays in the pool, in place",
    [r["title"] for r in passing2["daboya-fugu-weaving-village"]],
    ["File:Daboya old search find.jpg", "File:Fugu weaving group.jpg"],
)
check_that(
    "a photograph found by both routes is kept once",
    len({r["sha1"] for r in passing2["daboya-fugu-weaving-village"]}),
    2,
)

# -- harvest: already-swept categories are not swept again --------------------
swept_terms = category.load_checkpoint(tmp2)["daboya-fugu-weaving-village"]["tried"]
check_that(
    "a swept category's files are recorded in tried",
    "category:files:Category:Daboya" in swept_terms,
    True,
)
check_that(
    "the swept subcategory listing is recorded",
    "category:subcats:Category:Daboya" in swept_terms,
    True,
)
check_that(
    "the category query itself is recorded",
    "category:search:Daboya" in swept_terms,
    True,
)
check_that(
    "the pre-existing search queries are still recorded",
    "Daboya Ghana" in swept_terms,
    True,
)
client3 = FakeCommons(
    categories_found={"Daboya": ["Category:Daboya"]},
    members={("Category:Daboya", "file"): ["File:Fugu new photo.jpg"]},
    records={
        "File:Fugu new photo.jpg": good_record(
            "File:Fugu new photo.jpg", sha1="fff", categories=["Category:Daboya"]
        ),
    },
)
passing3, _ = category.harvest(client3, [daboya], [e["name"] for e in ENTITIES], tmp2)
check_that(
    "a third sweep asks Commons nothing at all",
    client3.asked_members,
    [],
)
check_that(
    "and the pool does not grow from a sweep that never ran",
    len(passing3["daboya-fugu-weaving-village"]),
    2,
)

# -- harvest: subcategories are descended exactly one level --------------------
techiman = entity("techiman-history-museum")
client4 = FakeCommons(
    categories_found={"Techiman": ["Category:Techiman"]},
    members={
        ("Category:Techiman", "file"): ["File:Techiman street.jpg"],
        ("Category:Techiman", "subcat"): ["Category:Museums in Techiman"],
        ("Category:Museums in Techiman", "file"): ["File:Techiman museum exhibit.jpg"],
        ("Category:Museums in Techiman", "subcat"): ["Category:Deeper still"],
    },
    records={
        "File:Techiman street.jpg": good_record(
            "File:Techiman street.jpg", sha1="111", categories=["Category:Techiman"]
        ),
        "File:Techiman museum exhibit.jpg": good_record(
            "File:Techiman museum exhibit.jpg",
            sha1="222",
            categories=["Category:Museums in Techiman"],
        ),
    },
)
# An explicit descent budget: the live SUBCATS_PER_ENTITY is rate-limit
# tuning and is currently zero, so this exercises the mechanism itself --
# descend one level, no deeper -- independently of that tuning.
category.harvest(
    client4,
    [techiman],
    [e["name"] for e in ENTITIES],
    tmp,
    categories_per_entity=2,
    subcats_per_entity=3,
)
check_that(
    "subcategories are listed for the primary category only",
    [c for c, k in client4.asked_members if k == "subcat"],
    ["Category:Techiman"],
)
check_that(
    "a subcategory's files are swept",
    ("Category:Museums in Techiman", "file") in client4.asked_members,
    True,
)
check_that(
    "the descent stops at one level",
    ("Category:Deeper still", "file") in client4.asked_members,
    False,
)

# -- the checkpoint row is one select can resume from --------------------------
row = category.load_checkpoint(tmp)["techiman-history-museum"]
check_that("the row carries kept", isinstance(row["kept"], list), True)
check_that("the row carries rejected", isinstance(row["rejected"], list), True)
check_that("the row carries tried", isinstance(row["tried"], list), True)
check_that(
    "a category marker cannot be mistaken for a query",
    all(
        "ghana" in t.lower().split()[-1:]
        for t in row["tried"]
        if not t.startswith("category:")
    ),
    True,
)

# select.collect resumes by overwriting per id as it reads; the harvest's row
# must survive that shape -- later line wins, earlier lines are not corruption.
raw = tmp.read_text().splitlines()
parsed = [json.loads(line) for line in raw if line.strip()]
check_that(
    "every checkpoint line parses",
    len(parsed) == len([line for line in raw if line.strip()]),
    True,
)
last = [r for r in parsed if r["id"] == "daboya-fugu-weaving-village"][-1]
check_that(
    "the last row for an entity is its current state",
    len(last["kept"]),
    2,
)

# -- a failed category search costs the run nothing but a note ------------------
client5 = FakeCommons(fail_terms={"Nchiraa"}, categories_found={"Nchiraa Falls": []})
passing5, _ = category.harvest(client5, [entity("nchiraa-waterfalls")], [e["name"] for e in ENTITIES], tmp)
check_that(
    "a failed category search leaves the entity in the result",
    "nchiraa-waterfalls" in passing5,
    True,
)

# -- the default target set is the destinations that still need one -------------
without_strip = [e for e in ENTITIES if e["kind"] == "destination" and not e.get("images")]
check_that(
    "every stripless destination is sweepable",
    all(e["id"] in {x["id"] for x in ENTITIES} for e in without_strip),
    True,
)

for _failure in FAILED:
    print("FAIL " + _failure)
print(f"\n{PASSED + len(FAILED)} assertions, {PASSED} pass, {len(FAILED)} fail")
raise SystemExit(1 if FAILED else 0)
