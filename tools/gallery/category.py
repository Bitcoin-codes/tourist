#!/usr/bin/env python3
"""Gather candidates from Commons categories, where text search cannot reach.

Why this exists
---------------
`select.search` matches words in titles, captions and descriptions, and asks
every word of a query at once. A village's photographs are frequently filed
under the village's *category* while saying nothing about it in any caption:
"Smoky kitchen in Daboya.jpg" does not answer a search for "Daboya Fugu
Weaving Village Ghana" -- four words at once -- and twenty-two destinations
returned nothing under every query while Commons plainly holds photographs of
some of them, filed under the place's category.

A category is a place claim by Commons itself, not our inference, and
`specificity` already reads a file's categories as evidence: membership of
"Category:Daboya" is the uploader's filing and scores exactly like the word
appearing in a title. So a category harvest is held to every gate a search
result meets -- `is_raster_image`, licence, subject, location, place-conflict,
`MIN_WIDTH`, `specificity` -- and nothing here installs a photograph. This
widens the checkpoint pool; assignment, contact-sheet inspection and
`apply.py` are unchanged downstream, so a wrong photograph cannot slip in
through the back.

Category search is not anchored to GHANA_ANCHOR the way file search is. The
anchor exists to stop a file search being answered by the rest of the world,
but a category is named for what it contains -- "Category:Axim" is not
ambiguous with anything -- and appending the country would zero out the very
categories that exist without it, since Commons writes "Category:Princes
Town", not "Category:Princes Town, Ghana". The foreign-category risk lands
instead on `relevant_category`, and beyond that on the same `screen` every
other candidate faces.

Usage:
    venv/bin/python tools/gallery/category.py            # every destination with no strip
    venv/bin/python tools/gallery/category.py --entity daboya-fugu-weaving-village
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from commons import (  # noqa: E402
    CACHE_DIR,
    Commons,
    CommonsError,
    is_raster_image,
)
from filters import (  # noqa: E402
    _keys,
    distinctive_tokens,
    load_sibling_map,
    screen,
)

# `select` is a C builtin extension module, so `import select` finds that one
# and not the pipeline's select.py, whatever the path says. Loading by file
# path is what the test harnesses already do, and a module that shares its
# pipeline state must share the loaded instance rather than exec it again --
# the sibling and ritual maps this file builds live in filters/select module
# globals, and a second exec would be maps built in one copy and read in
# another.
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "gallery_select", Path(__file__).resolve().parent / "select.py"
)
assert _spec.loader is not None
_select = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_select)

CHECKPOINT_OUT = _select.CHECKPOINT_OUT
MIN_WIDTH = _select.MIN_WIDTH
MIN_WANT = _select.MIN_WANT
_non_image_title = _select._non_image_title
_parses = _select._parses
host_words = _select.host_words
load_entities = _select.load_entities
load_ritual_map = _select.load_ritual_map

# Category searches per entity, categories swept, and subcategories descended.
#
# Three of each was the original budget, and it is what a healthy rate limit
# affords. Under a hard one it does not work: each destination then costs six
# to ten separate API calls, Commons answers nearly every one with a 429 and
# orders a twenty-to-forty second wait, and twenty entities spent twenty-six
# minutes doing nothing but honouring those waits -- seventy-seven idle seconds
# each. Eight of those twenty had no category at all, so the budget bought
# nothing but the knowledge that there was nothing to buy.
#
# So the sweep is now breadth-first: one search, one category, no descent. The
# town's own category is where a place's files actually sit, and that is the
# single most productive request there is; the second and third searches and
# the subcategory walk earn far less per request than they cost in waiting.
# Raise these again when Commons is serving normally -- nothing downstream
# depends on the numbers, they only bound the requests this run makes.
TERMS_PER_ENTITY = 1
CATEGORIES_PER_ENTITY = 1
SUBCATS_PER_ENTITY = 0


def category_terms(
    entity: dict[str, Any], limit: int | None = None
) -> list[str]:
    """What to search the category namespace for, most specific first.

    The town leads because that is the category a place's files are filed
    under when they are filed under anything -- "Category:Daboya" holds the
    village's photographs however they are titled. The bare name follows for
    destinations whose attraction has a category of its own
    ("Category:Nchiraa Falls"), and the distinctive words last, because a
    category is sometimes filed under the trade rather than the place
    ("Category:Fugu" -- though see `relevant_category` for why the fish is
    usually filtered out downstream).

    `limit` overrides TERMS_PER_ENTITY. The default is the live tuning, which
    moves with the rate limit, so a test that cares about the ordering passes
    its own number rather than asserting whatever the constant happens to be.
    """
    bare = entity["name"].split(" (")[0].strip() or entity["name"]
    town = (entity.get("location") or "").split(",")[0].strip()
    out: list[str] = []
    seen: set[str] = set()
    for candidate in (town, bare, " ".join(sorted(distinctive_tokens(bare)))):
        term = candidate.strip()
        key = term.lower()
        if len(term) > 3 and key not in seen:
            seen.add(key)
            out.append(term)
    return out[: TERMS_PER_ENTITY if limit is None else limit]


def relevant_category(category: str, entity: dict[str, Any]) -> bool:
    """Keep only categories that could actually be about this entity.

    A one-word category search returns the whole neighbourhood -- searching
    "Wa" in the file namespace returned categories beginning "Water", and in
    the category namespace it is worse. The gate is containment of the town, or
    of at least two of the name's own words: the same containment rule
    `alias_terms` applies to aliases, for the same reason -- one shared word
    ("fort", "palace") names a hundred categories that are not this one.
    """
    cat = category.removeprefix("Category:").lower()
    town = (entity.get("location") or "").split(",")[0].strip().lower()
    if len(town) > 3 and town in cat:
        return True
    words = {w for w in _keys(entity["name"].split(" (")[0]) if len(w) > 3}
    return sum(1 for w in words if w in cat) >= 2


def write_checkpoint_row(
    checkpoint: Path, entity_id: str, kept: list[dict], why: list[dict], tried: list[str]
) -> None:
    """Append one entity's row, in the exact shape `select` resumes from.

    Later lines win on load (`collect` overwrites as it reads), so appending a
    row -- rather than editing one in place -- keeps a killed run's partial
    write harmless: the unreadable line is skipped and the previous row for the
    same entity still describes a complete state.
    """
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    lines = (
        [
            line
            for line in checkpoint.read_text().splitlines()
            if line.strip() and _parses(line)
        ]
        if checkpoint.exists()
        else []
    )
    lines.append(
        json.dumps(
            {"id": entity_id, "kept": kept, "rejected": why, "tried": tried},
            sort_keys=True,
        )
    )
    checkpoint.write_text("\n".join(lines) + "\n")


def load_checkpoint(path: Path) -> dict[str, dict[str, Any]]:
    """Last row per entity -- the state `select.collect` would resume from."""
    rows: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return rows
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue  # a partial final line from a killed process
        rows[row["id"]] = row
    return rows


def harvest(
    client: Commons,
    entities: list[dict[str, Any]],
    known_names: list[str],
    checkpoint: Path = CHECKPOINT_OUT,
    *,
    categories_per_entity: int | None = None,
    subcats_per_entity: int | None = None,
    terms_per_entity: int | None = None,
) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
    """Sweep each entity's categories and merge survivors into its pool.

    Returns (passing, rejected) keyed by entity id. Merges, never replaces:
    the pool already holds what an earlier search found, and a photograph is
    the same photograph whether it arrived through a query or a category.
    Rejections accumulate too -- a file refused once for being Japanese does
    not become acceptable because it turned up again under "Category:Fugu".

    The three keyword arguments override TERMS_PER_ENTITY,
    CATEGORIES_PER_ENTITY and SUBCATS_PER_ENTITY. Those constants are live
    rate-limit tuning and move with how Commons is serving today, so a test
    that cares about the sweep *mechanism* -- one descent level, markers
    recorded, nothing swept twice -- passes its own budget instead of
    asserting whatever the constant happens to be this week. The same is true
    of a deliberate deep pass over a handful of entities: raising the budget
    on the command line asks the questions the lean run skipped, and every
    one it already answered is still skipped by its marker.
    """
    if categories_per_entity is None:
        categories_per_entity = CATEGORIES_PER_ENTITY
    if subcats_per_entity is None:
        subcats_per_entity = SUBCATS_PER_ENTITY
    if terms_per_entity is None:
        terms_per_entity = TERMS_PER_ENTITY
    prior = load_checkpoint(checkpoint)
    passing: dict[str, list[dict]] = {}
    rejected: dict[str, list[dict]] = {}

    for entity in entities:
        row = prior.get(entity["id"]) or {}
        carried = list(row.get("kept") or [])
        why = list(row.get("rejected") or [])
        tried = list(row.get("tried") or [])
        # Categories already answered on. Recorded in `tried` alongside the
        # queries so a retry sweeps nothing twice, and every marker shares one
        # `category:` prefix -- the earlier version mixed `category-search:`
        # with `category:`, and because `"category-search:X".startswith(
        # "category:")` is False (the ninth character is a hyphen, not a colon)
        # the swept-set missed the search and subcat markers and a re-run
        # re-searched every term. A marker is never a query: queries always end
        # in the country anchor, so the prefix cannot collide.
        swept = {t for t in tried if t.startswith("category:")}

        # -- discover categories ------------------------------------------
        categories: list[str] = []
        seen: set[str] = set()
        for term in category_terms(entity, limit=terms_per_entity):
            if f"category:search:{term}" in swept:
                continue
            tried.append(f"category:search:{term}")
            try:
                hits = client.search_categories(term)
            except CommonsError as exc:
                print(f"  {entity['id']}: category search {term!r} failed: {exc}", flush=True)
                continue
            for cat in hits:
                key = cat.lower()
                if key in seen or not relevant_category(cat, entity):
                    continue
                seen.add(key)
                categories.append(cat)

        # -- list members --------------------------------------------------
        titles: set[str] = set()
        for cat in categories[:categories_per_entity]:
            if f"category:files:{cat}" in swept:
                continue
            tried.append(f"category:files:{cat}")
            try:
                titles.update(client.category_members(cat, kind="file"))
            except CommonsError as exc:
                print(f"  {entity['id']}: members of {cat} failed: {exc}", flush=True)
        # One level of subcategories, from the most specific category only.
        #
        # Guarded on the budget as well as on the marker: with the descent cut
        # to zero this block must not even ask for the subcategory list, or the
        # request is spent to learn nothing -- which is the whole thing the
        # reduced budget is there to avoid.
        if (
            subcats_per_entity > 0
            and categories
            and f"category:subcats:{categories[0]}" not in swept
        ):
            primary = categories[0]
            tried.append(f"category:subcats:{primary}")
            try:
                subs = client.category_members(primary, kind="subcat", limit=subcats_per_entity)
            except CommonsError:
                subs = []
            for sub in subs[:subcats_per_entity]:
                if f"category:files:{sub}" in swept:
                    continue
                tried.append(f"category:files:{sub}")
                try:
                    titles.update(client.category_members(sub, kind="file"))
                except CommonsError as exc:
                    print(f"  {entity['id']}: members of {sub} failed: {exc}", flush=True)

        # -- the same gates `select.collect` applies -----------------------
        kept: list[dict] = []
        if titles:
            for title in sorted(t for t in titles if _non_image_title(t)):
                why.append({"title": title, "reason": "not a photograph (PDF, DjVu or scan)"})
            titles = {t for t in titles if not _non_image_title(t)}
            try:
                records = client.info(sorted(titles))
            except CommonsError as exc:
                print(f"  {entity['id']}: metadata fetch failed: {exc}", flush=True)
                records = {}
            seen_sha = {r.get("sha1") for r in carried if r.get("sha1")}
            hosts = host_words(entity)
            for title in sorted(records):
                record = records[title]
                if not is_raster_image(record):
                    why.append({"title": title, "reason": "not a photograph (PDF, DjVu or scan)"})
                    continue
                if record.get("sha1"):
                    if record["sha1"] in seen_sha:
                        continue
                    seen_sha.add(record["sha1"])
                reason = screen(record, entity["name"], known_names, hosts)
                if reason:
                    why.append({"title": title, "reason": reason})
                    continue
                if record.get("width", 0) < MIN_WIDTH:
                    why.append({"title": title, "reason": f"too small: {record.get('width')}px"})
                    continue
                kept.append(record)

        seen_titles = {r.get("title") for r in carried}
        kept = carried + [r for r in kept if r.get("title") not in seen_titles]
        passing[entity["id"]] = kept
        rejected[entity["id"]] = why
        write_checkpoint_row(checkpoint, entity["id"], kept, why, tried)

        # A file is worth more to read than a count, but the count says whether
        # this sweep changed anything at all: "0 new" over "0 kept" tells the
        # operator the categories were empty rather than that the gates refused.
        fresh = len(kept) - len(carried)
        cats_swept = sum(1 for t in tried if t.startswith("category:") and not t.startswith("category-subcats:") and "Category:" in t)
        print(
            f"  {entity['id']}: {len(kept)} in pool (+{fresh} from "
            f"{cats_swept} categories, {len(titles)} files seen)",
            flush=True,
        )
    return passing, rejected


def stripless_destination_ids() -> set[str]:
    """Destination ids with no installed gallery strip.

    Read from the raw JSON rather than from `load_entities()`, which projects
    each row down to the fields selection reads and drops `images` -- filtering
    on a field that is not there matched all 156 entities and swept the
    finished destinations too, spending rate limit on galleries that already
    exist. A category sweep is only for the places that still need one.
    """
    rows = json.loads(
        (Path(__file__).resolve().parents[2] / "backend" / "data" / "destinations.json").read_text()
    )
    return {row["id"] for row in rows if not row.get("images")}


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--entity", action="append", default=[], help="limit to these entity ids")
    parser.add_argument(
        "--limit", type=int, default=0, help="stop after this many entities this run"
    )
    parser.add_argument(
        "--terms",
        type=int,
        default=None,
        metavar="N",
        help=f"category searches per entity (default {TERMS_PER_ENTITY})",
    )
    parser.add_argument(
        "--categories",
        type=int,
        default=None,
        metavar="N",
        help=f"file categories swept per entity (default {CATEGORIES_PER_ENTITY})",
    )
    parser.add_argument(
        "--subcats",
        type=int,
        default=None,
        metavar="N",
        help=f"subcategory levels descended per entity (default {SUBCATS_PER_ENTITY})",
    )
    args = parser.parse_args()

    all_entities = load_entities()
    if args.entity:
        entities = [e for e in all_entities if e["id"] in set(args.entity)]
    else:
        # Destinations with no installed strip. Computed from the raw JSON, not
        # from a field on `load_entities()`'s projection -- see
        # stripless_destination_ids. Destinations only: a festival pass is its
        # own run, once the owner has asked for it.
        need = stripless_destination_ids()
        entities = [e for e in all_entities if e["kind"] == "destination" and e["id"] in need]
    known_names = [e["name"] for e in all_entities]
    # Same full-set maps `select.main` builds, for the same reasons: a word is
    # only distinctive relative to every other name, and a ritual word only
    # distinctive relative to every other claim on it.
    load_sibling_map(known_names)
    load_ritual_map(all_entities)

    if args.limit:
        entities = entities[: args.limit]
    print(f"{len(entities)} entities to sweep\n", flush=True)
    client = Commons(CACHE_DIR, throttle=1.5)

    passing, _rejected = harvest(
        client,
        entities,
        known_names,
        terms_per_entity=args.terms,
        categories_per_entity=args.categories,
        subcats_per_entity=args.subcats,
    )

    ready = [eid for eid, pool in passing.items() if len(pool) >= MIN_WANT]
    print(
        f"\n{len(ready)} of {len(passing)} pools now hold >= {MIN_WANT} candidates; "
        f"API calls: {client.calls} ({client.cache_hits} cached, {client.throttled} throttled)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
