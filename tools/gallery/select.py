#!/usr/bin/env python3
"""Choose which photographs belong in each destination's gallery.

The pipeline
------------
    search  ->  filter  ->  score  ->  assign  ->  install

Search pulls candidates from Commons for each destination. Filter runs the
subject, location and licence rules from `filters.py`, which is the only thing
standing between a search result and a gallery slot. Score then asks a question
the filters deliberately do not: of all the destinations this photograph could
belong to, which one does it belong to *most*? Assign gives every photograph to
exactly one destination. Install writes the winners to disk.

Why a photograph belongs to exactly one gallery
-----------------------------------------------
"Fort Batenstein" photographs usually mention Keta, and "Fort Good Hope"
photographs usually mention Keta too. Left alone, both galleries would show the
same photograph of a Keta street, and a visitor browsing either would see
somewhere they had not been. So a photograph goes to the destination its own
metadata names *most specifically*, and nowhere else. A photograph that clearly
belongs to Keta goes to the Keta gallery, not to both forts.

Scoring is a small ordered scale rather than a score, because the ordering is
what matters and the magnitudes are not real: a full-name match in a title beats
a full-name match in a description, because whoever wrote the title was talking
about the thing in the picture. `MIN_SPECIFICITY` then refuses the photographs
that name no destination convincingly, which is what keeps a generic "Beach in
Ghana" out of every beach gallery at once.

Nothing here crops or colour-corrects
-------------------------------------
The earlier version of this pipeline cropped installs to 16:10 and white-balanced
them by hand. That was defensible when the images went straight into a hero tile
with a fixed aspect, and it is wrong for a gallery strip whose thumbnails are 3:2,
where `object-fit: cover` already handles the crop. Worse, an unviewable edit
cannot be checked: the pixel-signature check in `recover.py` can prove a local
file is the same image as a Commons thumbnail, and it cannot prove a file is the
same image as a *cropped* one. Installs are therefore byte-identical to the
Commons thumbnail, which makes the plan recoverable at any time.

Usage
-----
    venv/bin/python tools/gallery/select.py --report-only
    venv/bin/python tools/gallery/select.py --install
    venv/bin/python tools/gallery/select.py --entity cape-coast-castle
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
    NON_IMAGE_SUFFIXES,
    STATE_DIR,
    USER_AGENT,
    Commons,
    artist_of,
    is_raster_image,
    licence_of,
)
import pixels  # noqa: E402
from filters import (  # noqa: E402
    ALTERNATIVE_NAMES,
    _description,
    _category_text,
    _keys,
    _matches_alternative,
    _title,
    _has_phrase,
    distinctive_tokens,
    load_sibling_map,
    screen,
)

ROOT = Path(__file__).resolve().parent.parent.parent
GALLERY = ROOT / "assets" / "images" / "gallery"
# Under the repository, not /tmp: this is the file a restart used to destroy.
# Everything a re-run would have to ask Commons again is here, so the directory
# is created on the way past rather than at the point of first append -- a
# checkpoint written into a parent that does not exist fails at the moment it
# should be succeeding, which is the worst possible time to find out.
SCRATCH = STATE_DIR / "select"
SCRATCH.mkdir(parents=True, exist_ok=True)
PLAN_OUT = SCRATCH / "select-plan.json"
REPORT_OUT = SCRATCH / "select-report.txt"
# Appended one line per entity as it finishes, so a run interrupted by a 429 or a
# killed shell resumes instead of starting over. See collect().
CHECKPOINT_OUT = SCRATCH / "select-checkpoint.jsonl"

# At most this many photographs in one gallery. The UI shows a hero plus a
# scrolling strip three at a time, so nine is three swipes -- as far as anyone
# reads before deciding they have seen the place, and further than that the
# strip is longer than it is useful.
#
# It was six until a destination turned up with nine usable photographs on
# Commons and six of them showing, which is a shortage in the data rather than
# a property of the design. Almost every destination has fewer than this
# either way, so raising the ceiling costs nothing where there is nothing to
# add. Must match apply.py and check.py.
MAX_PHOTOS = 9
# A gallery strip renders only when a destination has a hero plus at least two
# more, so a second photograph is the point at which it is worth building.
MIN_WANT = 2

# How many plausible candidates to stop searching at.
#
# Not how many to keep -- MAX_PHOTOS does that, and it is nine. This is the point
# at which another search term is judged unlikely to change what selection ends
# up with. screen() rejects a large share for licence, subject and location, and
# then assign() ranks what is left, so a pool of forty photographs is already far
# more than enough to yield nine that survive. It has to be generous for the same
# reason: stopping early with a pool that filtering then empties would show up as
# a destination with no gallery and no explanation.
SEARCH_ENOUGH = 40

# A photograph must name a destination at least this specifically to be used.
# The scale, from weakest to strongest, is built by `specificity` below.
MIN_SPECIFICITY = 2

# A photograph needs a real licence and a real size.
#
# The width that matters is the one the site actually renders: `build_image_variants`
# emits 400w and 800w, and the tour tile is about 305px wide. A source of 1000px
# therefore produces every derivative by downscaling, which is what "no upscaling"
# has always meant here -- the number is a floor on where quality is lost, not a
# taste in photographs.
#
# It was 1200, fifty percent above anything the site asks for, and that floor cost
# galleries rather than sharpness. "Feeding blows for slaves Nania.jpg" and "Tano
# Sacred Rock - rock climbing.jpg" are photographs of exactly the right places --
# the titles say so, and every other gate passed them -- and both were refused for
# being 1008px and 960px wide. A destination whose only fault is that its
# photographs are a little small is a destination with a gallery, not one without.
# Accuracy outranks sharpness, and a soft hero is visible in a way an empty gallery
# is not: `check.py` already reports gomoa-wonderland shipping soft at 1280px for
# exactly this reason.
#
# Raise it again only alongside VARIANTS in build_image_variants.py, and never past
# the smallest derivative the site renders -- above 800 the floor starts asking for
# resolution nothing displays. 900 is where it now stands: above the 800w it has to
# clear, and low enough to admit the 960px and 1008px photographs that were the
# whole reason for moving it.
MIN_WIDTH = 900

# How many entities in a row must fail to fetch before the run stops entirely.
#
# One failed entity means one failed entity. Four in a row does not mean four
# bad entities: Commons rates limits whole clients, so a hard limit looks
# exactly like a string of unrelated individual failures. Under the old
# behaviour the run would discover this again on every remaining entity -- a few
# minutes each, times a hundred -- while the thing actually needed was a wait.
# Four is the point at which "coincidence" stops being a reasonable reading:
# the independent failure rate here is well under one in ten, and four
# consecutive is comfortably past that.
#
# Nothing is checkpointed for a failed entity, so a stopped run loses no work
# and restarting resumes from the last entity that did succeed.
STALL_AFTER_FAILURES = 4


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------
def load_entities() -> list[dict[str, Any]]:
    """Every destination and festival, with the fields selection needs."""
    out: list[dict[str, Any]] = []
    for filename, kind in (
        ("destinations.json", "destination"),
        ("festivals.json", "festival"),
    ):
        for row in json.loads((ROOT / "backend" / "data" / filename).read_text()):
            out.append(
                {
                    "id": row["id"],
                    "name": row.get("name") or row["id"],
                    "kind": kind,
                    "description": row.get("description") or "",
                    "region": row.get("region") or "",
                    "location": row.get("location") or "",
                    # What a festival is *made of*. Selection needs these because
                    # a photograph of a festival's own ritual is a photograph of
                    # that festival even when the caption never says the festival's
                    # name -- "Kpokpoi sprinkling" is Homowo, and a Commons
                    # uploader filing that picture almost never repeats the word
                    # Homowo when the ritual itself is better known.
                    "keyRituals": list(row.get("keyRituals") or []),
                }
            )
    return out


def host_words(entity: dict[str, Any]) -> list[str]:
    """Words naming where the place is, as opposed to what it is called.

    "Osu Castle, Accra" says where the photograph was taken, not what it shows.
    Two other destinations have "Accra" in their names, so without this the
    ambiguity rule would reject the correct photograph for naming the right city.
    """
    return [entity.get("region") or "", entity.get("location") or ""]


# Which festival each ritual word belongs to. Built over every festival, in the
# same way the sibling map is built over every name, and for the same reason:
# on its own a word looks identifying that is not identifying anywhere.
#
# "Durbar", "chiefs", "royal" and "drumming" appear in several festivals'
# rituals. Counting any of them would accept a photograph for the wrong festival,
# which is exactly the wrong-place photograph this pipeline exists to prevent --
# and unlike a mismatched place name it would read as plausible, because a durbar
# really is what a festival gallery is supposed to show.
#
# 111 of the 134 ritual words are unique to one festival, so the loss from
# ignoring shared words is small and the loss from trusting them is not.
RITUAL_OWNER: dict[str, set[str]] = {}

RITUAL_STOP = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "their",
        "his",
        "her",
        "onto",
        "into",
        "are",
        "was",
        "not",
        "its",
    }
)


def load_ritual_map(entities: list[dict[str, Any]]) -> None:
    """Map every word to the entities that claim it, rituals and names alike.

    Names go in as well as rituals, because `specificity` is about to accept a
    photograph for naming this festival's ritual while naming no festival at all,
    and that has to be weighed against every other entity that *does* claim the
    word -- in a name as well as in a ritual. Registering only rituals would let
    a word through that another festival's own title uses.

    Replaces rather than extends, so calling it twice with different sets leaves
    the map describing the latest one. A map that silently accumulated would
    survive a filtered run and then mark a word as shared with an entity that
    was never in scope.
    """
    RITUAL_OWNER.clear()
    for entity in entities:
        for token in _keys(entity["name"]):
            if len(token) < 4 or token in RITUAL_STOP:
                continue
            RITUAL_OWNER.setdefault(token, set()).add(entity["id"])
        for phrase in entity.get("keyRituals") or []:
            for token in _keys(phrase):
                if len(token) < 4 or token in RITUAL_STOP:
                    continue
                RITUAL_OWNER.setdefault(token, set()).add(entity["id"])


def ritual_terms(entity: dict[str, Any]) -> list[str]:
    """The festival's own rituals, as Commons search phrases.

    Kept separate from `search_terms`' name-derived terms and ranked after them:
    the festival name is what an uploader would have typed first, and only if
    that comes up thin do the rituals add reach. Capped rather than unrestricted
    because each phrase is another request against an anonymous rate limit that
    is already returning 429s.
    """
    out: list[str] = []
    for phrase in entity.get("keyRituals") or []:
        phrase = " ".join(phrase.split())
        if len(phrase) > 3 and phrase.lower() not in {t.lower() for t in out}:
            out.append(phrase)
    return out[:3]


def distinctive_ritual_keys(entity: dict[str, Any]) -> set[str]:
    """Ritual words that identify this festival and only this festival.

    Empty for a destination: places have no rituals, and treating a name that
    happens to look like one as if it did would just widen the gate.
    """
    if entity.get("kind") != "festival":
        return set()
    if not RITUAL_OWNER:
        return set()
    mine: set[str] = set()
    for phrase in entity.get("keyRituals") or []:
        for token in _keys(phrase):
            if len(token) < 4 or token in RITUAL_STOP:
                continue
            if RITUAL_OWNER.get(token) == {entity["id"]}:
                mine.add(token)
    return mine


# What every search query is pinned to. See search_terms -- a query of the
# destination's name alone is answered by every namesake on earth, and the
# fifty results it returns are fifty that a Ghanaian photograph did not get.
#
# A richer anchor was tried and is wrong: `Fort McCarthy (Ghana OR "Gold Coast")`
# does not return the fort and the Gold Coast together, it discards the name and
# returns Chicago's Gold Coast neighbourhood -- the same six street photographs
# for three different destinations. The country is one word, so it is one word.
GHANA_ANCHOR = "Ghana"


def alias_terms(
    entity: dict[str, Any], asked: list[str] | tuple[str, ...] = ()
) -> list[str]:
    """The destination's other documented names, as Commons search phrases.

    A `gsrsearch` query matches every word it contains, and a destination's name
    is routinely longer than the phrase its photographs were filed under:
    "Komfo Anokye Sword Site Ghana" appears in no description on Commons, while
    "Komfo Anokye Ghana" describes the monument itself. Such an entity comes back
    with no candidate at all -- which is the one failure the filters cannot
    report, because there is nothing to reject: no candidate, no rejection, no
    row in the checkpoint saying anything went wrong. Seventeen destinations
    failed exactly this way.

    The key is matched by containment, not by a shared word, for the reason
    `_matches_alternative` gives: "accra arts centre" shares "centre" with
    "Gushiegu Local Textile Centre", and a photograph of the Accra market is not
    a photograph of Gushiegu. One of the two key sets has to be contained in the
    other, the same test the matching side already applies, so that querying and
    accepting can never disagree about which entity an alias belongs to.

    Placed after the name terms and after a festival's rituals, and capped at
    two: they are the second attempt at finding what the name failed to find,
    and every extra phrase is another request against a rate limit that answers
    bursts with 429s.

    `asked` is the checkpoint's `tried`: queries this destination has already
    been answered on. They are dropped *before* the cap, not after, because the
    cap is about requests this run makes and the alternative is a destination
    that can never ask anything new -- sorted alphabetically, "asumura" and
    "asumura rockfowl" are both answered and "asumura sanctuary" would sit in
    third place forever, never queried and never able to fail.
    """
    keys = _keys(entity["name"])
    answered = set(asked)
    out: list[str] = []
    for name, alternatives in ALTERNATIVE_NAMES.items():
        name_keys = _keys(name)
        if not (name_keys <= keys or keys <= name_keys):
            continue
        for phrase in sorted(alternatives):
            if (
                len(phrase) > 3
                and phrase not in out
                and f"{phrase} {GHANA_ANCHOR}" not in answered
            ):
                out.append(phrase)
    return out[:2]


def _asked_terms(row: dict[str, Any]) -> list[str]:
    """Which queries this checkpoint row has already been answered on.

    A row without the field is treated as having asked nothing, which is the
    conservative direction: a query repeated costs a request, a query skipped
    because we assumed it had been made costs the photograph it would have
    found. Rows written from now on always carry `tried`, so the unknown case
    shrinks to the rows that exist today -- and those are backfilled by the run
    that needs them, not guessed at here.
    """
    return list(row.get("tried") or [])


def search_terms(
    entity: dict[str, Any], asked: list[str] | tuple[str, ...] = ()
) -> list[str]:
    """What to ask Commons for, most productive first.

    The display name leads, because that is what an uploader would have typed.
    The name plus its region catches a caption that names the district instead.
    The bare distinctive words catch the cases where the destination's own name is
    a Commons category nobody searched -- "Fort Batenstein" is filed under
    "Princes Town" as often as under its own name.

    A festival then adds its rituals, behind the name terms rather than mixed in
    with them: photographs of "Asafo Warrior Deer Hunt" are filed under those
    words far more often than under "Aboakyer Festival", so searching only the
    name would find the durbar and miss the hunt. Two caps, not one -- three of
    each, because every extra phrase is another request against an anonymous rate
    limit that is already returning 429s, and six is where this stops being a
    search and starts being a crawl.
    """
    # The name, with any parenthetical dropped.
    #
    # The parenthetical is a search aid in the data -- "Aboakyer Festival (Deer
    # Hunting Festival)" -- but Commons matches it literally, and a query
    # containing it returns nothing at all where the bare name returns dozens:
    #
    #     "Aboakyer Festival (Deer Hunting Festival)"  ->  0 results
    #     "Aboakyer Festival"                          ->  36 results
    #
    # This is not a narrow edge case. Seven of the thirteen festivals carry a
    # parenthetical, and because the name leads the term list, a festival with one
    # spent its first search on a query guaranteed to find nothing -- and then the
    # second search on the same name plus its region, which also finds nothing.
    # Two guaranteed-zero searches against an anonymous rate limit that answers
    # bursts with 429s, before the searches that could have worked were reached.
    # The town, ahead of the region. A region narrows a search far less than a
    # town does, and for a name that is not unique to Ghana the difference is
    # the whole result set: "National Theatre" returns London, Budapest and
    # Bangkok, and "National Theatre Greater Accra" narrows that to Accra only
    # if the uploader happened to write the region. "National Theatre Accra" is
    # what a person photographing it would have typed, and six galleries were
    # lost to not asking it -- along with "Fort Victoria Cape Coast", which
    # found the Isle of Wight instead, and "Axim Beach Axim", which found a
    # Dell handheld computer.
    bare = entity["name"].split(" (")[0].strip() or entity["name"]
    terms = [bare]
    town = (entity.get("location") or "").split(",")[0].strip()
    if town and town.lower() != bare.lower() and town not in terms:
        terms.append(f"{bare} {town}")
    if entity["region"] and entity["region"] != bare:
        terms.append(f"{bare} {entity['region']}")
    distinctive = distinctive_tokens(entity["name"])
    if distinctive:
        terms.append(" ".join(sorted(distinctive)))

    # Every query is pinned to the country, which is what stops a search for a
    # Ghanaian place being answered by the rest of the world.
    #
    # The terms above are the name and parts of the name, and Commons matches
    # them anywhere: "Fort McCarthy" returned seventeen American Navy
    # photographs of a ship named after the same man, "National Theatre"
    # returned Prague, "Se Yo Cave" returned a Kansas Infantry company, "Axim"
    # returned a Dell handheld and "Daboya Fugu" a Japanese pufferfish. A
    # filter catches each of those afterwards, but the filter is what the
    # fifty-result budget is spent on -- every foreign file that has to be
    # rejected is a slot a Ghanaian one did not get.
    #
    # The anchor is one word and is deliberately not an alternation; see
    # GHANA_ANCHOR for the query that quietly discarded the destination's own
    # name. It costs the photographs that say only "Gold Coast", which are the
    # older ones, and that trade is the reason this is a comment rather than an
    # assumption: if a fort's gallery comes back thin, this is where to look.
    out: list[str] = []
    seen: set[str] = set()
    for term in terms + ritual_terms(entity) + alias_terms(entity, asked):
        key = term.lower()
        if len(term) > 3 and key not in seen:
            seen.add(key)
            out.append(f"{term} {GHANA_ANCHOR}")
    return out[:6]


# --------------------------------------------------------------------------
# scoring
# --------------------------------------------------------------------------
def _located_here(text: str, entity: dict[str, Any]) -> bool:
    """Does this text place the photograph at this destination?

    Only consulted when a distinctive name word is the *only* evidence, because
    that is where a name word can be wrong about the subject rather than about
    the place.

    "Daboya Fugu Weaving Village" has one distinctive word -- no other destination
    in the data uses "fugu" -- and Commons holds a century of Japanese pufferfish
    under exactly that word. A search returned "Fugu delivery truck in Meguro",
    "Fugu and lamb restaurant" and "Fugu Sashi Feb 07 2020" for a village in the
    Northern Region of Ghana, each scoring 2 on one shared token, each ready to
    be installed as that village's photograph. The word was not identifying the
    place; it was identifying a fish.

    So the word now has to be corroborated by the record saying where it was
    taken. The entity's own `region` and `location` are the two fields that name
    a place rather than a thing -- "Northern Region", "Daboya, near Tamale" --
    and a photograph of the village will say one of them. A photograph of a truck
    in Tokyo says neither.

    Where it is has to mean somewhere *other than the name*. "Princess Town
    Beach" has "Princess Town" for a location, so its own name appears in its
    own corroboration, and one shared word -- "princess" -- passed a Japanese
    woodblock print, two Metropolitan Museum paintings, a sarcophagus, a Mughal
    album page and a photograph of a cake, six times over. The alternatives are
    a word from the region or town that the name does not already contain, or
    naming the place properly: two of the name's words in the title, not one.
    "Kete Krachi" still passes that way; "Princess Entertaining a Visitor" does
    not.

    It never overrules a stronger signal: this runs only on the single-word path,
    so a file whose title contains the full name scores 3 first, and a file
    about the right town scores here. An entity carrying no region and no
    location has no location to corroborate with, and returning True keeps it
    exactly as permissive as it was before.
    """
    name = {t for t in _keys(entity["name"]) if len(t) > 2}
    host = {
        t
        for t in _keys(" ".join(part for part in host_words(entity) if part))
        if len(t) > 2
    }
    if not host:
        return True
    text_keys = _keys(text)
    if (host - name) & text_keys:
        return True
    return len(name & text_keys) >= 2


def specificity(record: dict[str, Any], entity: dict[str, Any]) -> int:
    """How specifically does this file's metadata name this destination?

    Ordered, not numeric, in the sense that the gaps are large enough that no
    two steps are comparable in value: a full name in a title is worth more than
    everything below it put together, and one distinctive word in a description
    is worth more than nothing. Returns 0 when the file does not name this
    destination at all, which is the common case and the cheap one to detect.
    """
    name = entity["name"]
    entity_keys = _keys(name)
    if not entity_keys:
        return 0

    title, categories, description = _title(record), _category_text(record), _description(record)

    if _has_phrase(title, name):
        return 3
    if _has_phrase(categories, name):
        return 3
    if _has_phrase(description, name):
        return 2

    distinctive = distinctive_tokens(name)
    if _matches_alternative(_keys(f"{title} {categories} {description}"), entity_keys):
        return 2
    # Corroborated by where the record says it was taken. See _located_here --
    # one distinctive word is enough to be a word that means something else
    # entirely, and nothing downstream re-checks it.
    if distinctive & _keys(title) and _located_here(title, entity):
        return 2
    if distinctive & _keys(categories) and _located_here(categories, entity):
        return 2
    if distinctive & _keys(description):
        return 1

    # A festival's own ritual, named when the festival is not.
    #
    # This is the case a festival gallery exists for and the name rules cannot
    # reach: Commons is rich in photographs of Kpokpoi sprinkling, Asafo deer
    # hunts and stool consecrations, and their captions and categories say those
    # things -- not "Homowo Festival", which the uploader had no reason to repeat
    # when the ritual itself is the better known label. Without this they all
    # score 0, which is indistinguishable from having nothing.
    #
    # Scored 2 rather than 3, so a file that names the festival outright still
    # beats one that names only a ritual, and a shared word cannot win at all:
    # `distinctive_ritual_keys` only returns words no other entity claims,
    # whether in a ritual or in a name of its own. "Durbar" therefore scores
    # nothing here, while "Kpokpoi" scores 2 for Homowo and for Homowo alone.
    ritual = distinctive_ritual_keys(entity)
    if ritual & _keys(title):
        return 2
    if ritual & _keys(categories):
        return 2
    if ritual & _keys(description):
        return 2
    return 0


# --------------------------------------------------------------------------
# the run
# --------------------------------------------------------------------------
def collect(
    client: Commons,
    entities: list[dict[str, Any]],
    known_names: list[str],
    checkpoint: Path | None = None,
    resume: bool = True,
) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
    """Search and filter. Returns (passing, rejected, failed) keyed by entity id.

    `rejected` keeps one representative reason per entity, because "no
    candidates" and "every candidate filtered out" call for different responses
    and the site owner needs to be able to tell them apart.

    Results are appended to `checkpoint`, one JSON object per entity, the moment
    each entity finishes. A full run over 156 entities is hours of throttled
    requests against a service that answers 429 under any burst, so it will
    eventually hit an exception, and losing everything at that point is what
    happened to the recovery run -- it died at entity 19 of 29 having written
    nothing. Re-running resumes from the checkpoint instead.

    The last line is truncated away before each append, so a process killed
    mid-write leaves a short final line rather than a corrupt one, and the
    unreadable line is skipped on load.
    """
    passing: dict[str, list[dict]] = {}
    rejected: dict[str, list[dict]] = {}
    # The raw row behind `passing`, so a retry can see which queries the entity
    # has already been answered on. See `_asked_terms`.
    prior: dict[str, dict[str, Any]] = {}
    # Entities whose search or metadata fetch failed. Kept apart from `rejected`
    # on purpose: we never found out whether Commons has photographs here.
    failed: dict[str, str] = {}
    # Consecutive fetch failures, so one rate limit reads as one rate limit
    # instead of as many unrelated broken entities. See STALL_AFTER_FAILURES.
    stalled = 0

    if checkpoint is not None and resume and checkpoint.exists():
        good = checkpoint.read_text().splitlines()
        for line in good:
            if not line.strip():
                continue
            try:
                done = json.loads(line)
            except json.JSONDecodeError:
                continue  # a partial final line from a killed process
            passing[done["id"]] = done["kept"]
            rejected[done["id"]] = done["rejected"]
            prior[done["id"]] = done
        if passing:
            print(f"  resuming: {len(passing)} entities already searched\n", flush=True)

        # A verdict given by eye has to hold for every pool, including those
        # this run will not touch.
        #
        # An entity whose pool already meets MIN_WANT is skipped outright, so a
        # condemned photograph inside a pool large enough to ship would never be
        # reconsidered. Princess Town Beach holds eighteen photographs, one of
        # them condemned on a contact sheet, and was skipped precisely because
        # it had enough -- which is the one condition under which the
        # condemnation could never be applied. Purging here, for every entity,
        # makes the verdict independent of whether the entity gets re-searched.
        for _eid, _pool in list(passing.items()):
            _bad = {
                r.get("title")
                for r in rejected.get(_eid, [])
                if str(r.get("reason", "")).startswith(
                    "wrong-place: rejected on contact-sheet review"
                )
            }
            if _bad:
                passing[_eid] = [r for r in _pool if r.get("title") not in _bad]

    def checkpoint_entity(
        entity_id: str, kept: list[dict], why: list[dict], tried: list[str]
    ) -> None:
        if checkpoint is None:
            return
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        # Not `checkpoint.read_text()`: mkdir has created the directory but not
        # the file, and the very first entity of the very first run is exactly
        # when that matters.
        lines = [
            line
            for line in checkpoint.read_text().splitlines()
            if line.strip() and _parses(line)
        ] if checkpoint.exists() else []
        lines.append(
            json.dumps(
                {"id": entity_id, "kept": kept, "rejected": why, "tried": tried},
                sort_keys=True,
            )
        )
        checkpoint.write_text("\n".join(lines) + "\n")

    for entity in entities:
        asked = _asked_terms(prior.get(entity["id"]) or {})
        terms = search_terms(entity, asked)
        if entity["id"] in passing:
            # Enough to show means the searching is done: the strip needs two
            # photographs and a pool of two is already more than selection
            # keeps. Below that, ask again -- but only about queries the entity
            # has not already been answered on. "Komfo Anokye Sword Site Ghana"
            # returned nothing the first time and will return nothing again, and
            # under a rate limit answering with 429s those four requests are the
            # difference between a retry that costs two calls and one that costs
            # six. The bare town, never yet tried, is what the retry is for.
            if len(passing[entity["id"]]) >= MIN_WANT:
                continue
            todo = [t for t in terms if t not in set(asked)]
            if not todo:
                continue
        else:
            todo = terms
        # What already survived an earlier run stays surviving. A retry that
        # started from an empty pool loses nothing, but Akaa Falls searched once
        # and holding one photograph must not have that photograph discarded
        # because a second query found four more.
        carried = list(passing.get(entity["id"]) or [])

        # A verdict given by eye is not re-opened by a later automated pass.
        #
        # `screen` is stateless and cannot know that a photograph was downloaded,
        # put on a contact sheet, and found to be of the wrong place -- so on any
        # later run the same file passes again and lands in `kept`. Nothing used
        # to notice, because the pool merge discarded everything a retry found,
        # condemned photographs included; with that fixed, a photograph a person
        # rejected on sight would walk straight back into the pool and out to the
        # site. "This stone serve as grinding. Mail at pikworo slaves..." is a
        # Pikworo photograph, not Nania's, and its description names both towns,
        # so it scores well and is still not of this place.
        #
        # Only the visual verdicts are remembered. Every other rejection is
        # provisional and deliberately re-asked -- a photograph refused as too
        # small under an older floor is exactly what raising MIN_WIDTH is meant
        # to recover -- but "a person looked at this and it is not the place" is
        # not a threshold that moves.
        condemned = {
            r.get("title")
            for r in rejected.get(entity["id"], [])
            if str(r.get("reason", "")).startswith("wrong-place: rejected on contact-sheet review")
        }
        # Carried too, not only what this pass finds. A condemned photograph
        # reaches the pool from the checkpoint as readily as from a query --
        # Princess Town Beach's "Blick auf Princess Town" was condemned on
        # 2026-10-08 and still sat in `kept`, because the rule was only applied
        # to records the current pass produced. A verdict that survives the
        # checkpoint has to survive the merge as well.
        if condemned:
            carried = [r for r in carried if r.get("title") not in condemned]

        # One entity must never end the run.
        #
        # A 429 is not a per-entity condition: Commons hands them out to whole
        # clients, and a batch of fifty titles asking about "Black Star Square"
        # came back with a dozen PDFs about American independence in it, which made
        # the request URL several kilobytes long and helped earn the 429 that
        # killed the run at entity 6 of 156. `Commons._get` exhausts its backoff
        # and raises, and an exception there propagated out of collect() and took
        # every unvisited entity with it.
        #
        # So an entity that cannot be fetched is recorded as such and the run moves
        # on. It is recorded in `failed` rather than in `rejected`, because "we
        # could not ask" is not the same claim as "we asked and there was nothing",
        # and collapsing the two would quietly under-report how much of Commons was
        # actually searched.
        try:
            # Stop as soon as there is enough to choose from.
            #
            # Every term is another request, and the run is spending six of them
            # per entity even when the first came back with fifty candidates.
            # Under an anonymous rate limit answering bursts with 429s, five of
            # those six were buying nothing -- and two entities in a row failed
            # outright because the budget had already been spent on terms whose
            # results were never going to be needed.
            #
            # The threshold is deliberately well above what selection keeps:
            # MAX_PHOTOS is 6, and screen() rejects a large share for licence,
            # subject or location, so a pool of 40 photographs is already more
            # than enough to leave 6 that survive. A term that returns little
            # still falls through to the next one, so a thinly-covered place
            # searches just as deeply as it did before.
            # Only the terms actually put to Commons. The break below exists to
            # stop paying for results selection will not use, and it used to leave
            # the whole of `todo` recorded as asked -- so a term the loop never
            # reached was recorded as a term that had been answered, and no later
            # run would ever ask it. Alias terms come last by construction, which
            # is precisely where it bit: "Princess Town Beach" searched four name
            # terms, broke on "princess Ghana" returning forty-five usable titles,
            # and never asked "princes town beach" -- the alternative name it was
            # built for -- while recording that it had.
            asked_now: list[str] = []
            titles: set[str] = set()
            for term in todo:
                found = client.search(term, limit=50)
                asked_now.append(term)
                titles.update(found)
                if _count_usable(titles) >= SEARCH_ENOUGH:
                    break
        except Exception as error:  # noqa: BLE001 - any failure is this entity's
            failed[entity["id"]] = f"{type(error).__name__}: {error}"
            print(f"  {entity['id']}: FETCH FAILED -- {type(error).__name__}", flush=True)
            stalled += 1
            if stalled >= STALL_AFTER_FAILURES:
                print(
                    f"\n  {stalled} entities in a row could not be fetched. That is not "
                    f"eleven bad entities, that is one rate limit, and the run is "
                    f"spending its time discovering that over and over. Stopping here "
                    f"so the wait is a cooldown rather than a queue; nothing was "
                    f"checkpointed for these, so restarting picks them all back up.",
                    flush=True,
                )
                break
            continue

        if not titles:
            if carried:
                # This query found nothing, and that is all it means. The
                # photograph from the earlier search is still the entity's.
                checkpoint_entity(entity["id"], carried, rejected.get(entity["id"], []), asked + asked_now)
            else:
                rejected[entity["id"]] = [{"title": "", "reason": "no candidates found"}]
                checkpoint_entity(entity["id"], [], rejected[entity["id"]], asked + asked_now)
            continue

        # Drop the documents by title before asking about them.
        #
        # This is the same judgement `is_raster_image` makes, applied one step
        # earlier because the extension is in the title and the MIME type is not
        # available until the request that is trying to fail. A search for a place
        # with a common word in its name returns a shelf of 19th-century books --
        # searching "Black Star Square" returned thirty PDFs, most of them about
        # the Declaration of Independence -- and fetching metadata for those costs
        # the request several kilobytes and earns rate-limit pressure for documents
        # that were going to be refused anyway.
        non_image_titles = sorted(t for t in titles if _non_image_title(t))
        titles = {t for t in titles if not _non_image_title(t)}

        try:
            records = client.info(sorted(titles))
        except Exception as error:  # noqa: BLE001
            failed[entity["id"]] = f"{type(error).__name__}: {error}"
            print(f"  {entity['id']}: FETCH FAILED -- {type(error).__name__}", flush=True)
            stalled += 1
            if stalled >= STALL_AFTER_FAILURES:
                print(
                    f"\n  {stalled} entities in a row could not be fetched -- the rate "
                    f"limit has escalated, not the corpus. Stopping so this waits out "
                    f"one cooldown instead of eleven; none of these were checkpointed.",
                    flush=True,
                )
                break
            continue

        # A whole entity fetched cleanly. Whatever was wrong was specific to it.
        stalled = 0

        for title in non_image_titles:
            rejected.setdefault(entity["id"], []).append(
                {"title": title, "reason": "not a photograph (PDF, DjVu or scan)"}
            )

        kept: list[dict] = []
        seen: set[str] = set()
        counts: dict[str, int] = {}
        hosts = host_words(entity)
        for title in sorted(records):
            record = records[title]

            # Before the sha1 dedupe and before any content screening, because a
            # scanned book is not a photograph of anywhere and no amount of reading
            # its title, categories or description will establish that it is. A
            # PDF of a book about Scotland has a title, categories and a
            # description, and passes all of them.
            if not is_raster_image(record):
                counts["non-image"] = counts.get("non-image", 0) + 1
                rejected.setdefault(entity["id"], []).append(
                    {"title": title, "reason": "not a photograph (PDF, DjVu or scan)"}
                )
                continue

            if record.get("sha1"):
                if record["sha1"] in seen:
                    continue
                seen.add(record["sha1"])

            reason = screen(record, entity["name"], known_names, hosts)
            bucket = "kept" if not reason else "rejected"
            counts[bucket] = counts.get(bucket, 0) + 1
            if reason:
                rejected.setdefault(entity["id"], []).append({"title": title, "reason": reason})
                continue
            if record.get("width", 0) < MIN_WIDTH:
                rejected.setdefault(entity["id"], []).append(
                    {"title": title, "reason": f"too small: {record.get('width')}px"}
                )
                continue
            if title in condemned:
                rejected.setdefault(entity["id"], []).append(
                    {
                        "title": title,
                        "reason": "wrong-place: rejected on contact-sheet review; not re-opened",
                    }
                )
                continue
            kept.append(record)

        # Merge, never replace: the two pools describe the same entity from two
        # different queries, and a title is the same title in either.
        #
        # The set of titles to drop is the one the entity already holds, taken
        # from `carried`. Built from `kept` instead -- as it was -- it filtered
        # the new pool against itself, which removes every new record and leaves
        # `carried` standing alone. A retry then found photographs and discarded
        # all of them while reporting the merge as done, and because only an
        # entity below MIN_WANT retries at all, it cost precisely the entities
        # that most needed the help: Nania Slave Route held one photograph, found
        # three, and kept the one it started with.
        if carried:
            seen_titles = {r.get("title") for r in carried}
            kept = carried + [r for r in kept if r.get("title") not in seen_titles]

        passing[entity["id"]] = kept
        checkpoint_entity(entity["id"], kept, rejected.get(entity["id"], []), asked + asked_now)
        print(
            f"  {entity['id']}: {len(kept)} of {len(records)} pass"
            + (f" ({counts.get('rejected', 0)} filtered)" if counts.get("rejected") else ""),
            flush=True,
        )
    return passing, rejected, failed


def _parses(line: str) -> bool:
    try:
        json.loads(line)
        return True
    except json.JSONDecodeError:
        return False


def _non_image_title(title: str) -> bool:
    """True when a Commons file title alone says this is a document.

    The extension is what Commons itself uses to decide how to render a file, so
    this is not a guess. It is the same test `commons.is_raster_image` makes on
    the full record, available before the record has been fetched.
    """
    name = title.rsplit(":", 1)[-1] if ":" in title else title
    if "." not in name:
        return False
    return ("." + name.rsplit(".", 1)[-1].lower()) in NON_IMAGE_SUFFIXES


def _count_usable(titles: set[str]) -> int:
    """How many of a result set could be photographs at all.

    Counts by title only, because it is consulted between search terms and the
    metadata has not been fetched yet. A search for a place with a common word in
    its name returns shelves of 19th-century books, and counting those as
    candidates would stop the search early on a pool of things that were always
    going to be refused -- which is exactly the failure the threshold exists to
    avoid.
    """
    return sum(1 for t in titles if not _non_image_title(t))


def assign(
    passing: dict[str, list[dict]],
    entities: list[dict[str, Any]],
    min_specificity: int = MIN_SPECIFICITY,
) -> tuple[dict[str, list[dict]], list[dict]]:
    """Give every photograph to exactly one destination: its strongest match.

    A photograph is used only where it names the destination at least
    `min_specificity`, and only if it names *this* destination more strongly
    than any other. That second condition is what stops a Keta street appearing
    in both fort galleries, and it is why `specificity` is compared rather than
    thresholded on its own.

    `min_specificity` defaults to `MIN_SPECIFICITY` and is only ever lowered
    by hand, to bring sub-threshold candidates up for inspection. Those files
    have already passed every image gate -- raster, minimum width, the screen
    -- and are held back solely by an automated score that says the caption
    does not name the place strongly enough. A caption is a poor witness: an
    uploader who photographed Fort Royal often writes "Cape Coast" and nothing
    more, and the score then reads 1 for a photograph that is entirely correct.
    Dropping such a file without ever showing it to anyone is the one way this
    pipeline can lose a real photograph it already has in hand.

    So the number may be lowered to *see* a candidate, never to ship one: every
    file that reaches a plan is inspected on a contact sheet, and `apply` is
    still run only for the pairs that survive that inspection. The default is
    unchanged, so an ordinary run behaves exactly as before.
    """
    by_id = {entity["id"]: entity for entity in entities}

    # The checkpoint holds every entity any run ever searched, and `main`
    # resumes into `passing` from it while `entities` is only this invocation's
    # `--entity` subset. A destination-only run therefore arrives here also
    # holding festival results, and `by_id[entity_id]` raised KeyError on the
    # first one -- after all 113 entities had been searched and checkpointed, so
    # it cost the install step and nothing else.
    #
    # Scope is set by `entities`, not by what happens to be in the checkpoint.
    # An entity outside it was not searched by this run, and its photographs
    # belong to whichever run does search it; assigning them here would both
    # crash and, worse, silently install files under a selection this run never
    # made.
    passing = {eid: records for eid, records in passing.items() if eid in by_id}

    best_for_file: dict[str, tuple[int, str, dict]] = {}

    for entity_id, records in passing.items():
        entity = by_id[entity_id]
        for record in records:
            score = specificity(record, entity)
            if score < min_specificity:
                continue
            key = record.get("sha1") or record["title"]
            current = best_for_file.get(key)
            if current is None or score > current[0]:
                best_for_file[key] = (score, entity_id, record)

    galleries: dict[str, list[dict]] = {e: [] for e in by_id}
    unassigned: list[dict] = []
    for score, entity_id, record in best_for_file.values():
        galleries[entity_id].append({**record, "specificity": score})
    for entity_id, records in passing.items():
        for record in records:
            key = record.get("sha1") or record["title"]
            if key not in best_for_file:
                unassigned.append({"title": record["title"], "near": entity_id})

    for rows in galleries.values():
        rows.sort(key=lambda r: (-r["specificity"], -r.get("width", 0)))
        del rows[MAX_PHOTOS:]
    return galleries, unassigned


def local_name(entity_id: str, record: dict[str, Any], index: int) -> str:
    """A local filename that says which destination it belongs to.

    The slug of the Commons title keeps the filename recognisable when a human
    is looking at the directory, and the destination prefix keeps the gallery
    reconstructible from the filenames alone if this script is ever lost again --
    which it was, once.

    The title slug is trimmed where it merely repeats the prefix. "Cape Coast
    Castle 34" under a `cape-coast-castle-` prefix is 45 characters of which 16
    say nothing, and a directory of 200 photographs should be readable.
    """
    stem = record["title"].split(":", 1)[-1].rsplit(".", 1)[0]
    slug = "".join(c if c.isalnum() else "-" for c in stem.lower()).strip("-")
    slug = "-".join(part for part in slug.split("-") if part)[:60].strip("-")

    # Commons titles carry their own "File:" prefix stripped, but the destination
    # name often appears in the title as well. Cut it once, at the start.
    for _ in range(2):
        if slug.startswith(entity_id + "-"):
            slug = slug[len(entity_id) + 1 :]
    slug = slug.strip("-")

    if not slug:
        suffix = f"-{index + 1}" if index else ""
        return f"{entity_id}{suffix}.jpg"
    return f"{entity_id}-{slug}.jpg"


def fetch(record: dict[str, Any]) -> bytes:
    """Download one Commons thumbnail."""
    import urllib.request

    request = urllib.request.Request(
        record["thumburl"], headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def install(
    galleries: dict[str, list[dict]], *, write: bool, report_only: bool
) -> tuple[list[dict], list[str]]:
    """Download and write each chosen photograph.

    Returns (plan rows, notes). Three things are checked on the way, all of which
    matter more than they look:

    * **A file already on disk is verified, not trusted.** The name is derived from
      the Commons title, so a re-run after the search results changed finds a file
      of the same name holding a different photograph. Trusting the name means the
      plan says one thing and the site shows another, and the credit in
      IMAGE-CREDITS.md is then attached to the wrong picture -- a licence failure
      that reads as a filename convention.
    * **A photograph already claimed is dropped.** `assign` gives one photograph to
      one gallery using metadata alone, which cannot see that two Commons files are
      the same frame. This is the second line of defence, and the only one that
      looks at the picture.
    * **A file that is not the thumbnail byte-for-byte is rewritten.** Installs are
      meant to be unmodified Commons downscales, which is what lets
      `recover.py`'s pixel signature prove what a local file is.
    """
    if write and not report_only:
        GALLERY.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    notes: list[str] = []
    # Filenames already taken this run, mapped to the title that took them.
    #
    # `local_name` slugs the Commons title, which is case-insensitive about
    # everything except its first letter -- and Commons is not. Three real files
    # called "A View from the Summit.jpg", "A view from the Summit.jpg" and
    # "A view from the summit.jpg" reduce to one local name. All three downloaded
    # (different bytes, so the pixel check below could not call them twins), each
    # overwrote the same path, and each emitted its own row.
    #
    # The site then showed one photograph three times while the plan and the
    # credits claimed three photographs from three sources -- with the credit
    # belonging to whichever file was written last. check.py caught it only
    # because the same path appearing twice makes a mark compare against itself,
    # which reads as a duplicate rather than as a collision.
    #
    # The first claimant wins: `galleries` is sorted by specificity, so the
    # record that kept the name is the one that named the place best.
    claimed: dict[str, str] = {}
    # Signatures of what is already installed, labelled by the file holding them.
    # Seeded from disk as well as from this run, so a photograph already installed
    # for one destination is not installed again for another on a later run.
    seen: list[tuple[str, list[float]]] = []
    for existing in sorted(GALLERY.glob("*.jpg")):
        if existing.stem.endswith(("-400", "-800")):
            continue
        mark = pixels.of_path(existing)
        if mark is not None:
            seen.append((existing.name, mark))

    for entity_id, records in sorted(galleries.items()):
        for index, record in enumerate(records):
            name = local_name(entity_id, record, index)
            target = GALLERY / name
            # Colliding with a name already used in this run. Checked before the
            # download, because nothing about it is worth fetching: the file is
            # about to be overwritten by whichever record lands last, and the row
            # would claim a source the bytes no longer match.
            if name in claimed:
                notes.append(
                    f"{entity_id}/{name}: another Commons file slugs to this name "
                    f"({claimed[name].rsplit(':', 1)[-1]!r} vs "
                    f"{record['title'].rsplit(':', 1)[-1]!r}) -- dropped, keeping the first"
                )
                continue
            claimed[name] = record["title"]
            row = {
                "entity": entity_id,
                "file": f"gallery/{name}",
                "title": record["title"],
                "description": record.get("extmetadata", {}).get("ImageDescription", ""),
                "width": record.get("width", 0),
                "height": record.get("height", 0),
                "thumbwidth": record.get("thumbwidth", 0),
                "specificity": record["specificity"],
                "author": artist_of(record),
                "licence": licence_of(record)["label"],
                "licence_url": record.get("extmetadata", {}).get("LicenseUrl", ""),
                "source": record.get("descriptionurl", ""),
            }

            if report_only:
                rows.append(row)
                continue

            try:
                data = fetch(record)
            except Exception as error:  # network, 429, a moved file
                notes.append(f"{entity_id}/{name}: not downloaded ({error})")
                continue

            mark = pixels.of_bytes(data)
            if mark is None:
                notes.append(f"{entity_id}/{name}: not a readable image")
                continue

            twin = pixels.first_duplicate(mark, seen)
            # A match against the name we are about to write is this file, found
            # in the disk seed by its own path -- not another photograph wearing
            # an alias. `seen` is seeded from everything already installed, and
            # the record we are installing is usually there already, because the
            # search's own install step put it there. Treating that as a
            # duplicate dropped the row for a photograph that was never
            # installed twice, which is how an entire batch reported "nothing new
            # to apply" while 130 photographs were sitting chosen and ready.
            #
            # The other direction still holds: a different file holding these
            # same pixels means the photograph is genuinely claimed elsewhere,
            # and there is only one name it can truthfully be published under.
            if twin is not None and twin != name:
                notes.append(
                    f"{entity_id}/{name}: the same picture is already installed as "
                    f"{twin}, from {record['title'].rsplit(':', 1)[-1]}"
                )
                continue
            if twin != name:
                seen.append((name, mark))

            if target.exists() and target.read_bytes() == data:
                notes.append(f"{entity_id}/{name}: already installed, identical")
            else:
                if target.exists():
                    notes.append(
                        f"{entity_id}/{name}: REPLACED -- a different file was under this "
                        f"name, and the plan and the site would otherwise disagree"
                    )
                target.write_bytes(data)
            rows.append(row)
    return rows, notes


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--install", action="store_true", help="write the chosen files to disk")
    parser.add_argument("--report-only", action="store_true", help="search and filter but write nothing")
    parser.add_argument("--entity", action="append", default=[], help="limit to these entity ids")
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="ignore any checkpoint and search every entity again",
    )
    parser.add_argument(
        "--min-specificity",
        type=int,
        default=MIN_SPECIFICITY,
        metavar="N",
        help=(
            "accept photographs scoring at least N (default "
            f"{MIN_SPECIFICITY}). Lower it only to bring sub-threshold "
            "candidates up for hand inspection; it never bypasses the "
            "contact sheet or apply."
        ),
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="stop after this many entities this run"
    )
    args = parser.parse_args()

    entities = load_entities()
    if args.entity:
        entities = [e for e in entities if e["id"] in set(args.entity)]
    known_names = [e["name"] for e in load_entities()]
    # Shared words across all 156 names cannot identify a place, and this must be
    # computed over the whole set, not the filtered subset, or a word looks
    # distinctive here that is not distinctive anywhere else.
    load_sibling_map(known_names)
    # The ritual map has the same requirement, and gets a fresh full load for it
    # rather than the possibly-filtered `entities` above. A ritual word has to be
    # checked against every other claim on it -- including a destination's own
    # name, which a `--entity` festival-only run never saw. Built from 13
    # festivals instead, "deer" would look distinctive to Aboakyer and any
    # photograph mentioning a deer would be accepted for it.
    load_ritual_map(load_entities())

    print(f"{len(entities)} entities, {len(known_names)} known names\n")
    client = Commons(CACHE_DIR, throttle=1.5)

    print("searching and filtering")
    if args.fresh:
        CHECKPOINT_OUT.unlink(missing_ok=True)
    # `--limit` bounds one invocation rather than the whole entity set, so a run
    # can be topped up over several sittings without ever starting over.
    batch = entities[: args.limit] if args.limit else entities
    passing, rejected, failed = collect(
        client, batch, known_names, checkpoint=CHECKPOINT_OUT, resume=not args.fresh
    )
    galleries, unassigned = assign(passing, entities, min_specificity=args.min_specificity)
    rows, notes = install(galleries, write=args.install, report_only=args.report_only)

    ready = {k: v for k, v in galleries.items() if len(v) >= MIN_WANT}
    thin = {k: v for k, v in galleries.items() if 0 < len(v) < MIN_WANT}

    PLAN_OUT.parent.mkdir(parents=True, exist_ok=True)
    PLAN_OUT.write_text(json.dumps(rows, indent=2, sort_keys=True))

    reasons: dict[str, list[tuple[str, int]]] = {}
    for entity_id, entries in rejected.items():
        tally: dict[str, int] = {}
        for entry in entries:
            tally[entry["reason"]] = tally.get(entry["reason"], 0) + 1
        reasons[entity_id] = sorted(tally.items(), key=lambda kv: -kv[1])

    lines = [
        "GALLERY SELECTION REPORT",
        "=" * 60,
        f"entities searched     : {len(entities)}",
        f"  not reached (limit) : {max(0, len(entities) - len(batch))}",
        f"  fetch failed        : {len(failed)}",
        f"galleries with >= {MIN_WANT} : {len(ready)}",
        f"specificity threshold : {args.min_specificity}"
        + ("" if args.min_specificity == MIN_SPECIFICITY else " (lowered for inspection)"),
        f"photographs chosen    : {len(rows)}",
        f"too thin to show      : {len(thin)}",
        f"no usable photograph : {len(entities) - len(ready) - len(thin)}",
        f"API calls             : {client.calls} ({client.cache_hits} cached, {client.throttled} throttled)",
        # Surfaced because a throttle stuck at its ceiling looks exactly like
        # Commons still rate limiting us, and the two have opposite fixes.
        f"  current spacing      : {max(client.throttle, client.retry_after):.2f}s "
        f"(configured floor {client.base_throttle:.2f}s, "
        f"server asked for {client.retry_after:.0f}s)",
        "",
        "Why an entity has no gallery. This is the honest gap: it is what",
        "Wikimedia coverage looks like, not a failure of the pipeline.",
        "-" * 60,
    ]
    for entity in entities:
        if entity["id"] in ready:
            continue
        found = len(galleries.get(entity["id"], []))
        # A fetch failure is reported as its own thing, not as "nothing found".
        # Saying a place has no photographs when we were simply never allowed to
        # ask is the one way this report could lie about the state of Commons, and
        # the whole reason `failed` is a separate dict.
        if entity["id"] in failed:
            lines.append(f"  {entity['id']} FETCH FAILED, not searched: {failed[entity['id']][:90]}")
            continue
        if entity["id"] not in passing:
            lines.append(f"  {entity['id']} NOT REACHED in this run")
            continue
        top = reasons.get(entity["id"], [])[:2]
        why = "; ".join(f"{reason} x{count}" for reason, count in top) or "nothing found"
        lines.append(f"  {entity['id']} ({found} usable) {why}")
    lines += [
        "",
        "Photographs dropped as naming no destination strongly enough:",
        "-" * 60,
    ]
    lines += [f"  {u['title']} (nearest: {u['near']})" for u in unassigned[:40]] or ["  (none)"]

    replaced = [note for note in notes if "REPLACED" in note]
    duplicates = [note for note in notes if "same picture" in note]
    # Which notes mean the file never reached disk.
    #
    # Every note has the same shape, "<entity>/<file>: what happened", so the
    # outcome has to be read from the wording. The old test asked whether a note
    # failed to start with two spaces, which no note does -- so "already
    # installed, identical" was counted as a failure, and a run that verified
    # all nine of its photographs reported "9 failed to fetch" underneath
    # "9 already present and identical". A report that contradicts itself is
    # worse than no report: the next person to read it goes looking for a
    # network fault that was never there.
    failed = [
        note
        for note in notes
        if "not downloaded" in note
        or "not a readable image" in note
        or "slugs to this name" in note
    ]
    identical = [note for note in notes if "identical" in note]
    # A successful write records no note at all, so what was written is what
    # reached the plan, minus the ones that were already in place and minus the
    # ones that overwrote a different file (counted on their own line).
    written = len(rows) - len(identical) - len(replaced)
    lines += [
        "",
        "Installation notes",
        "-" * 60,
        f"  already present and identical : {len(identical)}",
        f"  written                        : {written}",
        f"  replaced a different file      : {len(replaced)}",
        f"  dropped as a duplicate picture : {len(duplicates)}",
        f"  failed to fetch                : {len(failed)}",
    ]
    for note in replaced + duplicates + failed:
        lines.append(f"    {note.strip()}")
    REPORT_OUT.write_text("\n".join(lines) + "\n")

    print(
        f"\n{len(ready)} galleries with a strip, {len(rows)} photographs, "
        f"{len(thin)} too thin, {len(unassigned)} unassigned"
    )
    if replaced:
        print(f"  {len(replaced)} file(s) replaced a different file under the same name")
    if duplicates:
        print(f"  {len(duplicates)} dropped as a duplicate picture")
    if failed:
        print(f"  {len(failed)} failed to fetch")
    print(f"plan   {PLAN_OUT}\nreport {REPORT_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
