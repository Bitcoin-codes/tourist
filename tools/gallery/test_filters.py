#!/usr/bin/env python3
"""The known-bad photographs, kept as executable assertions.

Every rule in filters.py exists because a specific wrong photograph got through
without it. This file is that list. If a rule is deleted or loosened and this
suite still passes, the rule was never doing anything; if the suite is edited to
make a failing case pass, the case was wrong to begin with.

The shape of each case is a real Commons record -- the title, categories,
description and licence metadata the filters actually read -- and the verdict
that record should get for one destination. Cases marked REJECT only assert that
*some* rule fires, because the exact wording of a reason is not behaviour
anyone depends on. Cases marked ACCEPT assert the empty string, which is a much
stronger claim: the photograph is right and nothing may reject it.

The ACCEPT cases carry the most weight. An over-strict filter does not fail
loudly; it empties a gallery, and an empty gallery looks identical to "this place
has no photographs on Commons". Three of these exist because that is exactly
what happened when the rules were first written.

Usage
-----
    venv/bin/python tools/gallery/test_filters.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from filters import (  # noqa: E402
    S_ANIMAL_SUBJECT,
    S_FOREIGN,
    S_GENERIC,
    S_NOT_A_PHOTO,
    S_SATELLITE,
    S_SUBJECT_MISMATCH,
    S_VESSEL_SUBJECT,
    distinctive_tokens,
    load_sibling_map,
    location_verdict,
    place_conflicts,
    screen,
)

DUTCH_ARCHIVE = "The Netherlands and the world"


def rec(
    title: str,
    categories: list[str] | None = None,
    description: str = "",
    licence: str = "CC BY-SA 4.0",
    licence_url: str = "https://creativecommons.org/licenses/by-sa/4.0",
    restrictions: str = "",
    mime: str = "image/jpeg",
) -> dict[str, Any]:
    """A Commons record shaped the way `commons.Commons.info` returns one.

    `extmetadata` is flat here, as `Commons.info` leaves it: the raw API nests
    every value as `{"value": ...}` and the client flattens it. `commons.field`
    accepts either shape, so a caller cannot silently read an empty licence.
    """
    ext: dict[str, str] = {
        "LicenseShortName": licence,
        "ImageDescription": description,
    }
    if licence_url:
        ext["LicenseUrl"] = licence_url
    if restrictions:
        ext["Restrictions"] = restrictions
        ext["Attribution"] = restrictions
    return {
        "title": f"File:{title}",
        "mime": mime,
        "width": 3000,
        "height": 2000,
        "categories": [f"Category:{c}" for c in (categories or [])],
        "extmetadata": ext,
    }


# --------------------------------------------------------------------------
# the cases
# --------------------------------------------------------------------------
# (label, record, entity, expect_accept)
CASES: list[tuple[str, dict[str, Any], str, bool]] = [
    # -- before photography -------------------------------------------------
    (
        "an 1836 engraving of the fort is not a photograph of it",
        rec("Cape Coast Castle, 1836", ["Castles in Ghana"], "Engraving of the castle"),
        "Cape Coast Castle",
        False,
    ),
    (
        "a 1790 map of the Gold Coast is not a photograph",
        rec("Map of the Gold Coast 1790", ["Maps of Ghana"]),
        "Cape Coast Castle",
        False,
    ),

    # -- not a photograph ---------------------------------------------------
    (
        "a coat of arms in SVG form is rejected on format alone",
        rec("Coat of arms of the Fante Confederacy.svg", ["Fante"], mime="image/svg+xml"),
        "Cape Coast Castle",
        False,
    ),
    (
        "a PNG map is rejected: vector and lossless are not photographs",
        rec("Cape Coast castle map.png", ["Maps of Ghana"], mime="image/png"),
        "Cape Coast Castle",
        False,
    ),
    (
        "a photograph of a plaque about the fort is not a photograph of the fort",
        rec("Plaque at Cape Coast Castle", ["Cape Coast Castle"]),
        "Cape Coast Castle",
        False,
    ),

    # -- the categories that must NOT be excluded --------------------------
    # These three are the ones that emptied real galleries when they were in the
    # deny list. Fort Apollonia, the National Museum and the International Slavery
    # Museum are all photographed from the inside and Commons files those
    # photographs under museum and archive categories.
    (
        "a photograph taken inside a museum is still a photograph of the place",
        rec("Interior of the National Museum", ["Museums in Ghana", "Accra"]),
        "National Museum of Ghana",
        True,
    ),
    (
        "an archive-sourced photograph of a fort is a photograph of the fort",
        rec(
            "Kaapstad, Gouverneur's Kasteel (2).jpg",
            ["Dutch colonial architecture", DUTCH_ARCHIVE, "Fort Amsterdam"],
            "Gezicht op de kasteel te Kaapstad",
        ),
        "Fort Amsterdam",
        True,
    ),

    # -- satellite and maps -------------------------------------------------
    (
        "satellite imagery is not a photograph of a place",
        rec("Lake Volta Sentinel-2 image", ["Rivers of Ghana"], "Landsat composite"),
        "Lake Volta",
        False,
    ),

    # -- contradictions -----------------------------------------------------
    (
        "a caption naming two different forts is not either of them",
        rec("Cape Coast Castle and Elmina Castle from the sea", ["Castles in Ghana"]),
        "Cape Coast Castle",
        False,
    ),

    # -- the right fort in the wrong country --------------------------------
    (
        "a Dutch archive photo stamped with a foreign country is still Ghana's fort",
        rec(
            "Kaapstad, Gouverneur's Kasteel (2).jpg",
            [DUTCH_ARCHIVE, "Fort Amsterdam"],
            "Kasteel van Kaapstad, ongetekend",
        ),
        "Fort Amsterdam",
        True,
    ),
    (
        "a photo of Paramaribo is not a photo of a Ghanaian fort",
        rec("Kasteel Paramaribo", ["Suriname", "Fort Zeelandia"]),
        "Fort Amsterdam",
        False,
    ),
    (
        "Cape Coast in Guyana is not Cape Coast in Ghana",
        rec("Cape Coast, Guyana", ["Cities in Guyana"]),
        "Cape Coast Castle",
        False,
    ),
    # "National Theatre" is three words a hundred theatres share, so a title
    # containing the phrase scores 3 anywhere on earth. This one was the only
    # photograph the National Theatre had: an illustration of the Prague theatre
    # reprinted in an American student magazine, catalogued in a category about
    # Prague's National Theatre and captioned "Czech National Theatre".
    (
        "the National Theatre in Prague is not Accra's",
        rec(
            "Czech National Theatre (1927)",
            ["History of National Theatre in Prague"],
            "Czech National Theatre as depicted in the Student Life, vol. 17, no. 5",
        ),
        "National Theatre",
        False,
    ),
    # The control that matters: the rule must not take the right theatre with it.
    (
        "Accra's National Theatre is still accepted",
        rec(
            "National Theatre, Accra",
            ["Theatres in Ghana"],
            "The National Theatre in Accra, Ghana",
        ),
        "National Theatre",
        True,
        "Greater Accra",
    ),

    # -- alternative names --------------------------------------------------
    # "Accra" is Osu Castle's city and also appears in three other destination
    # names, so this case needs the region passed in to survive. That is the
    # honest shape of the problem: the filters cannot know where a place is, so
    # the caller has to say.
    (
        "Osu Castle is also called Fort Christiansborg",
        rec("Fort Christiansborg, Accra", ["Forts in Ghana", "Osu"]),
        "Osu Castle",
        True,
        "Accra",
    ),

    # -- the name lives outside the title -----------------------------------
    (
        "the Navrongo basilica never says Navrongo in its title",
        rec(
            "Basilica of Our Lady of Seven Sorrows",
            ["Navrongo", "Churches in Ghana"],
            "The basilica at Navrongo, Upper West Region",
        ),
        "Navrongo",
        True,
    ),

    # The Centre for National Culture, Accra is the Accra Arts Centre, and
    # Commons describes the craft market's files in those words.
    (
        "the Centre for National Culture, Accra is the Accra Arts Centre",
        rec(
            "Beads maker 3",
            [],
            "A guy making hand beads at the National Centre for Culture and Arts in Accra, Ghana",
        ),
        "Accra Arts Centre",
        True,
    ),
    # The same phrase with a different city is the Ashanti one, which the data
    # lists separately. The aliases are token sets, so the city has to be in them.
    (
        "the Kumasi centre's caption is not the Accra market",
        rec(
            "Kente seller 2",
            ["Centre for National Culture"],
            "Craft stalls at the Centre for National Culture, Kumasi",
        ),
        "Accra Arts Centre",
        False,
    ),

    # -- the subject is not the place ---------------------------------------
    (
        "a colobus monkey is not the monkey sanctuary's building",
        rec("Colobus monkey at Boabeng Fiema", ["Boabeng Fiema Monkey Sanctuary"]),
        "Boabeng Fiema Monkey Sanctuary",
        False,
    ),
    (
        "the man-of-war Fort William is not Fort William the fort",
        rec("HMS Fort William at anchor", ["Ships of the United Kingdom"]),
        "Fort William Anomabu",
        False,
    ),

    # -- a word the place is named after must not disqualify it --------------
    (
        "a market is a market: Kejetia Market survives the word market",
        rec("Kejetia Market, Kumasi", ["Kumasi", "Markets in Ghana"]),
        "Kejetia Market",
        True,
        "Kumasi Central",
    ),

    # -- licences -----------------------------------------------------------
    (
        "a restriction note overrides a free licence tag",
        rec(
            "Cape Coast Castle from the sea",
            ["Cape Coast Castle"],
            restrictions="Contact me before any commercial use",
        ),
        "Cape Coast Castle",
        False,
    ),
    (
        "an all-rights-reserved file is not usable",
        rec("Cape Coast Castle", ["Cape Coast Castle"], licence="All rights reserved"),
        "Cape Coast Castle",
        False,
    ),
    (
        "a free tag with no licence deed is not evidence of anything",
        rec("Cape Coast Castle", ["Cape Coast Castle"], licence="CC BY-SA 4.0", licence_url=""),
        "Cape Coast Castle",
        False,
    ),

    # -- the plain happy path ----------------------------------------------
    (
        "an ordinary photograph of the right place passes",
        rec("Cape Coast Castle courtyard", ["Cape Coast Castle", "Cape Coast"]),
        "Cape Coast Castle",
        True,
    ),
]

ALL_PLACE_NAMES = [
    "Fort William Anomabu",
    "Fort William Cape Coast",
    "Cape Coast Castle",
    "Elmina Castle",
    "Ada Foah Beach",
    "Keta",
    "Bole",
    "Ada",
    "Boabeng Fiema Monkey Sanctuary",
    "Osu Castle",
    "Aburi Botanical Gardens",
    "Lake Bosomtwe",
    "Kejetia Market",
    "National Museum of Ghana",
    "Fort Amsterdam",
    "Fort Batenstein",
    # Three Accra destinations and two Kumasi ones. These are what made "Osu
    # Castle, Accra" look ambiguous before the host-word exemption existed.
    "James Fort (Accra)",
    "Accra Arts Centre",
    "Accra International Conference Centre",
    "Kumasi Fort",
    "Kumasi Cultural Centre",
]
KNOWN_PLACES = set(ALL_PLACE_NAMES)

AMBIGUOUS_CASES: list[tuple[str, dict[str, Any], str, bool]] = [
    # "william" is in the name of two destinations, so for anything that is not
    # a Fort William, a caption offering only "william" could be either one.
    # This is the case that matters: Fort William in the data and HMS Fort
    # William both exist, and they are different places.
    (
        "a token naming more than one destination is ambiguous",
        rec("Fort William, 1890", ["Forts in Ghana"]),
        "Keta",
        False,
    ),
    (
        "a token naming only this destination is not a conflict",
        rec("Ada Foah Beach at sunset", ["Ada Foah Beach"]),
        "Ada Foah Beach",
        True,
    ),
    (
        "a token naming several places including this one is merely uninformative",
        rec("Fort William, 1890", ["Forts in Ghana"]),
        "Fort William Anomabu",
        True,
    ),
    (
        "the town that distinguishes two Fort Williams is not a conflict",
        rec("Fort William at Anomabu", ["Fort William (Anomabu)", "Anomabu"]),
        "Fort William Anomabu",
        True,
    ),
    (
        "a city in the title that is also in two other destinations' names is a conflict",
        rec("Osu Castle, Accra", ["Osu Castle"]),
        "Osu Castle",
        False,
    ),
    (
        "a possessive fragment is too short to count as evidence",
        rec("Chief's Palace", ["Sefwi Wiawso Paramount Chief's Palace", "Kumasi Fort"]),
        "Fort William Anomabu",
        True,
    ),
    (
        "a real town in the title is still a conflict without the region",
        rec("Osu Castle, Kumasi", ["Osu Castle"]),
        "Osu Castle (Fort Christiansborg)",
        False,
    ),
]

# Cases where the entity's own region rescues the title. Tested separately because
# the exemption has to be passed in: the filters deliberately do not look up
# region data themselves, so a caller that forgets it gets a rejection rather
# than a wrong answer, which is the safe direction to fail in.
HOST_CASES: list[tuple[str, dict[str, Any], str, str, bool]] = [
    (
        "Osu Castle in Accra is not ambiguous because Accra is its city",
        rec("Osu Castle, Accra", ["Osu Castle"]),
        "Osu Castle (Fort Christiansborg)",
        "Greater Accra",
        True,
    ),
    (
        "the region exemption does not rescue an unrelated city",
        rec("Osu Castle, Kumasi", ["Osu Castle"]),
        "Osu Castle (Fort Christiansborg)",
        "Greater Accra",
        False,
    ),
]


def run() -> int:
    # Every destination name in the data. Words shared by two of them -- "fort",
    # "william" -- cannot identify a place on their own, so distinctive_tokens
    # must stop counting on them. This is the real shape of the problem: two
    # different buildings are both called Fort William.
    load_sibling_map(ALL_PLACE_NAMES)

    failures: list[str] = []
    passed = 0

    for case in CASES:
        label, record, entity, expect_accept = case[:4]
        hosts = [case[4]] if len(case) > 4 else []
        reason = screen(record, entity, KNOWN_PLACES, hosts)
        accepted = reason == ""
        if accepted == expect_accept:
            passed += 1
        elif expect_accept:
            failures.append(f"  REJECTED but should pass: {label}\n      reason: {reason}")
        else:
            failures.append(f"  ACCEPTED but should fail: {label}")

    for label, record, entity, expect_accept in AMBIGUOUS_CASES:
        reason = place_conflicts(record, entity, KNOWN_PLACES)
        accepted = reason == ""
        if accepted == expect_accept:
            passed += 1
        else:
            failures.append(
                f"  place_conflicts: {label} -> got {reason or 'accepted'!r}, "
                f"wanted {'accept' if expect_accept else 'reject'}"
            )

    for label, record, entity, region, expect_accept in HOST_CASES:
        reason = place_conflicts(record, entity, KNOWN_PLACES, [region])
        accepted = reason == ""
        if accepted == expect_accept:
            passed += 1
        else:
            failures.append(
                f"  host words: {label} -> got {reason or 'accepted'!r}, "
                f"wanted {'accept' if expect_accept else 'reject'}"
            )

    # distinctive_tokens: the words that actually identify a place.
    token_cases = [
        (
            "Fort William Anomabu",
            {"anomabu"},
            "fort and william are shared with the other Fort William",
        ),
        (
            "Aburi Botanical Gardens",
            {"aburi"},
            "botanical and garden are kinds, not identities",
        ),
        (
            "Lake Bosomtwe",
            {"bosomtwe"},
            "a lake whose location field repeats its name is still identified",
        ),
        (
            "Kejetia Market",
            {"kejetia"},
            "a market is identified by its own name, not by 'market'",
        ),
    ]
    for name, want, why in token_cases:
        got = distinctive_tokens(name)
        if got == want:
            passed += 1
        else:
            failures.append(f"  distinctive_tokens({name!r}) = {got}, wanted {want} ({why})")

    # A destination that shares every one of its words with something else in the
    # data must not be matched on those words alone.
    # A destination that shares only generic words with everything else of its
    # kind must not be matched by those words alone.
    record = rec("Fort William", ["Forts in Ghana"])
    if location_verdict(record, "Fort William Anomabu") == "":
        failures.append(
            "  a bare 'Fort William' was accepted for Fort William Anomabu: "
            "the shared words 'fort william' identify neither town"
        )
    else:
        passed += 1

    # A structural guard, because the same mistake was made three times.
    #
    # Every vocabulary that gets compared by token intersection must contain
    # only single words. A multi-word entry contributes its function words to the
    # stemmed set, and "coat of arms" contributes "of" -- which then matches every
    # caption that says "of", rejecting correct photographs for no reason. Phrases
    # belong in the *_PHRASES lists, which are matched as phrases.
    #
    # This is worth a test because the failure is silent. A rule that never fires
    # and a rule that never should fire look identical from the outside.
    function_words = {"of", "the", "and", "in", "a", "an", "at", "on", "for", "to"}
    token_sets = {
        "GENERIC": S_GENERIC,
        "FOREIGN": S_FOREIGN,
        "NOT_A_PHOTO": S_NOT_A_PHOTO,
        "ANIMAL_SUBJECT": S_ANIMAL_SUBJECT,
        "SUBJECT_MISMATCH": S_SUBJECT_MISMATCH,
        "VESSEL_SUBJECT": S_VESSEL_SUBJECT,
        "SATELLITE": S_SATELLITE,
    }
    for name, tokens in token_sets.items():
        intruders = tokens & function_words
        if intruders:
            failures.append(
                f"  {name} contains function word(s) {sorted(intruders)}: it is being "
                f"matched by token intersection, so a multi-word entry leaks these. "
                f"Move multi-word terms to a *_PHRASES list."
            )
        else:
            passed += 1

    # A vocabulary written in the wrong case silently matches nothing. The
    # country list was "Guyana" while the text keys were "guyana", so the
    # foreign-country rule passed every file it was given.
    for name, tokens in token_sets.items():
        cased = {t for t in tokens if t != t.lower()}
        if cased:
            failures.append(f"  {name} holds non-lowercase tokens {sorted(cased)[:3]}")
        else:
            passed += 1

    total = passed + len(failures)
    for line in failures:
        print(line)
    print(f"\n{total} assertions, {passed} pass, {len(failures)} fail")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(run())
