#!/usr/bin/env python3
"""The wrong-place photographs, and the photographs they must not cost us.

Every entry here is a real Commons file that was either published as a
photograph of a Ghanaian destination and had to be taken down again, or is
published now and is genuinely of that place. Nothing is invented: the records
carry the title, categories and licence metadata the filters actually read.

Two lists, because they fail in opposite directions and only one of them is
loud.

* ``REJECTED`` asserts that a reason comes back. A wrong photograph that slips
  through is visible to a visitor and to the rights holder whose work is being
  used for the wrong place, so it is the failure people notice.

* ``ACCEPTED`` asserts the empty string, which is the far stronger claim. An
  over-strict filter does not fail loudly -- it empties a gallery, and an empty
  gallery is indistinguishable from "this place has no photographs on
  Commons". These cases exist because that is what happened: the country list
  was missing England, Scotland, Wales, Thailand and Japan entirely, so
  tightening it found real mistakes and also took down "Tagbo Falls flows from
  the Ghana-Togo range" (a caption naming the border, not a destination), two
  Dutch archive photographs of Fort Patience and Fort Batenstein that name the
  Ghanaian towns they stand in, and one that says only "reserve". Each of
  those is in ``ACCEPTED`` now, and if one fails the fix is the filter.

The records are run through ``screen()`` -- and then ``specificity()``, the
second gate -- with the same known-names and host-word arguments select.py
uses, so this is the pipeline's own judgement and not a shortcut around it.
Production requires both, and the split between them is worth knowing: 17 of
the wrong photographs are caught by the content rules alone (a foreign
country, a foreign city, a geotag outside Ghana, a subject that is a laptop)
and four by both, while none is caught by specificity alone. The second gate
earns its place on the other side of the test -- every accepted photograph has
to name the place, because a file that says nothing about where it was taken
is one this site cannot vouch for.

Usage
-----
    venv/bin/python tools/gallery/test_wrongplace.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from filters import load_sibling_map, screen  # noqa: E402

# `select` is also the name of a standard library module, and anything that
# has imported it already has it cached -- so the repository's own is loaded
# by path, as test_select.py does, rather than by name.
_spec = importlib.util.spec_from_file_location("select", HERE / "select.py")
select = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(select)
specificity = select.specificity
load_ritual_map = select.load_ritual_map

ROOT = HERE.parents[1]


def _entities() -> list[dict[str, Any]]:
    """Every destination and festival, as the selection run sees them."""
    rows: list[dict[str, Any]] = []
    for name in ("destinations.json", "festivals.json"):
        rows += json.loads((ROOT / "backend" / "data" / name).read_text(encoding="utf-8"))
    return rows


def run() -> int:
    """Two gates, in the order the pipeline applies them.

    ``screen`` is the content filter: licence, kind, place, subject. It is not
    sufficient on its own -- a file can be a real photograph of the right
    country and still be about something else that shares a word with the
    destination, which is what ``specificity`` decides. Only together do they
    decide whether a record may be installed, so asserting on either one alone
    would test a gate the pipeline does not actually use.
    """
    rows = _entities()
    known = [r.get("name", "") for r in rows]
    by_name = {r.get("name", ""): r for r in rows}
    hosts = {
        r.get("name", ""): [r.get("region") or "", r.get("location") or ""]
        for r in rows
    }
    load_sibling_map(known)
    load_ritual_map(rows)

    failures: list[str] = []
    passed = 0

    def verdict(name: str, record: dict[str, Any]) -> tuple[str, int]:
        entity = by_name.get(name, {"name": name})
        reason = screen(record, name, known, hosts.get(name, []))
        return reason, specificity(record, entity)

    for name, record in REJECTED:
        reason, score = verdict(name, record)
        if reason or score == 0:
            passed += 1
        else:
            failures.append(
                f"  ACCEPTED but must not be: {name}: {record.get('title')} "
                f"(no screen reason, specificity {score})"
            )

    for name, record in ACCEPTED:
        reason, score = verdict(name, record)
        if not reason and score > 0:
            passed += 1
        else:
            failures.append(
                f"  REJECTED but must not be: {name}: {record.get('title')} "
                f"-> {reason or f'names nothing here (specificity {score})'}"
            )

    total = passed + len(failures)
    for line in failures:
        print(line)
    print(
        f"\n{total} assertions, {passed} pass, {len(failures)} fail "
        f"({len(REJECTED)} wrong-place records, {len(ACCEPTED)} live photographs)"
    )
    return 1 if failures else 0


REJECTED = [
    (
        'Fort Victoria',
        {'title': 'File:Derelict pier, Fort Victoria, Isle of Wight, England.jpg',
 'categories': ['Category:CC-BY-4.0',
                'Category:Piers on the Isle of Wight',
                'Category:Self-published work'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'ImageDescription': 'Derelict pier, Fort Victoria, Isle of Wight, England',
                 'License': 'cc-by-4.0',
                 'LicenseShortName': 'CC BY 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by/4.0',
                 'UsageTerms': 'Creative Commons Attribution 4.0'}},
    ),
    (
        'Fort Victoria',
        {'title': 'File:RFA Fort Victoria in Leith, August 2023.jpg',
 'categories': ['Category:CC-Zero',
                'Category:RFA Fort Victoria (ship, 1990)',
                'Category:Self-published work',
                'Category:Taken with Motorola Moto G62 5G'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'ImageDescription': 'RFA Fort Victoria in Leith, Edinburgh, Scotland in '
                                     'August 2023',
                 'License': 'cc0',
                 'LicenseShortName': 'CC0',
                 'LicenseUrl': 'http://creativecommons.org/publicdomain/zero/1.0/deed.en',
                 'UsageTerms': 'Creative Commons Zero, Public Domain Dedication'}},
    ),
    (
        'Fort Victoria',
        {'title': 'File:Exterior view of church, in the community around Fort Victoria on Vancouver '
          'Island, British Columbia.jpg',
 'categories': [],
 'extmetadata': {'LicenseShortName': 'CC BY-SA 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0'}},
    ),
    (
        'National Theatre',
        {'title': 'File:National Theatre, London.jpg',
 'categories': ['Category:CC-BY-SA-2.0',
                'Category:Files with coordinates missing SDC location of creation (51° N, 1° '
                'W)',
                'Category:Flickr images reviewed by File Upload Bot (Magnus Manske)',
                'Category:National Theatre, London',
                'Category:Taken with Canon EOS 5D Mark II'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<p><a rel="nofollow" class="external text" '
                           'href="https://www.flickr.com/photos/aguichard/5152420112/">National '
                           'Theatre</a>\n'
                           '</p>\n'
                           '<ul><li>Uploaded by <a '
                           'href="//commons.wikimedia.org/wiki/User:BaldBoris" '
                           'title="User:BaldBoris">BaldBoris</a></li></ul>',
                 'GPSLatitude': '51.507113',
                 'GPSLongitude': '-0.115538',
                 'ImageDescription': 'National Theatre',
                 'License': 'cc-by-sa-2.0',
                 'LicenseShortName': 'CC BY-SA 2.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/2.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 2.0'}},
    ),
    (
        'National Theatre',
        {'title': 'File:National Theatre Budapest.jpg',
 'categories': ['Category:CC-BY-SA-3.0',
                'Category:National Theatre (Budapest) (2000-)',
                'Category:Self-published work',
                'Category:Taken with Nikon D5100'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'ImageDescription': 'Nouveau Théâtre national (Nemzeti Színház) de Hongrie, '
                                     'Budapest. Inauguré en 2002',
                 'License': 'cc-by-sa-3.0',
                 'LicenseShortName': 'CC BY-SA 3.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/3.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 3.0'}},
    ),
    (
        'National Theatre',
        {'title': 'File:National Theatre London 2026 01.jpg',
 'categories': ['Category:Buildings in the London Borough of Lambeth photographed in 2026',
                'Category:CC-BY-4.0',
                'Category:Exposure time 1/320 sec',
                'Category:F-number f/8',
                'Category:Featured pictures by Julian Herzog',
                'Category:Featured pictures of buildings in London',
                'Category:Featured pictures on Wikimedia Commons',
                'Category:Files with Assessments template missing SDC Commons quality '
                'assessment',
                'Category:Files with coordinates missing SDC location of creation (51° N, 1° '
                'W)',
                'Category:ISO speed rating 100',
                'Category:Lens focal length 73 mm',
                'Category:London photographs taken on 2026-01-18',
                'Category:National Theatre, London',
                'Category:Photo challenge winners by Julian Herzog',
                'Category:Photos by User:Julian Herzog',
                'Category:Photos of London by Julian Herzog',
                'Category:Quality images',
                'Category:Quality images by Julian Herzog',
                'Category:Quality images missing SDC Commons quality assessment',
                'Category:Quality images missing SDC creator',
                'Category:Quality images missing SDC source of file',
                'Category:Quality images of buildings in London',
                'Category:Self-published work',
                'Category:Taken with Nikkor Z 24-120mm f/4 S',
                'Category:Taken with Nikon Z 8'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'GPSLatitude': '51.507553',
                 'GPSLongitude': '-0.115167',
                 'ImageDescription': 'The National Theatre (NT, officially the Royal National '
                                     'Theatre) on the south bank of the Thames in London, '
                                     'England.',
                 'License': 'cc-by-4.0',
                 'LicenseShortName': 'CC BY 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by/4.0',
                 'UsageTerms': 'Creative Commons Attribution 4.0'}},
    ),
    (
        'National Theatre',
        {'title': 'File:April2021 Thailand National Theatre Bangkok 01.jpg',
 'categories': [],
 'extmetadata': {'LicenseShortName': 'CC BY-SA 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0'}},
    ),
    (
        'Fort Royal',
        {'title': 'File:Fort Royal Lokrum 01.jpg',
 'categories': ['Category:CC-BY-SA-4.0',
                'Category:Fort Royal (Lokrum)',
                'Category:Self-published work'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'ImageDescription': 'Fort Royal Lokrum',
                 'License': 'cc-by-sa-4.0',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0'}},
    ),
    (
        'Fort Royal',
        {'title': 'File:Royal Fort House and Park, Bristol.jpg',
 'categories': ['Category:August 2021 in Bristol',
                'Category:Bristol photographs by 14GTR',
                'Category:CC-BY-SA-4.0',
                'Category:Royal Fort House, Bristol',
                'Category:Self-published work'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'ImageDescription': "View of Royal Fort House in the Tyndall's Park area of "
                                     'Bristol',
                 'License': 'cc-by-sa-4.0',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0'}},
    ),
    (
        'Fuller Falls',
        {'title': 'File:-Loie Fuller Dancing- MET DP206655.jpg',
 'categories': ['Category:Artworks with known accession number',
                'Category:Artworks without Wikidata item',
                'Category:CC-Zero',
                'Category:GWToolset Batch Upload',
                'Category:Gilman Collection',
                'Category:Images from Metropolitan Museum of Art',
                'Category:Loie Fuller photographs by Samuel Joshua Beckett',
                'Category:The Annenberg Foundation Gift'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': 'This file was donated to Wikimedia Commons as part of a project by '
                           'the <a href="//commons.wikimedia.org/wiki/Commons:Met" '
                           'title="Commons:Met">Metropolitan Museum of Art</a>. See the <a '
                           'rel="nofollow" class="external text" '
                           'href="https://metmuseum.org/about-the-met/policies-and-documents/image-resources">Image '
                           'and Data Resources Open Access Policy</a>',
                 'ImageDescription': '<div class="description">\n'
                                     '<dl><dt>Photograph; Photographs</dt></dl></div>',
                 'License': 'cc0',
                 'LicenseShortName': 'CC0',
                 'LicenseUrl': 'http://creativecommons.org/publicdomain/zero/1.0/deed.en',
                 'UsageTerms': 'Creative Commons Zero, Public Domain Dedication'}},
    ),
    (
        'Axim Beach',
        {'title': 'File:DELL AXIM PDA (46677558785).jpg',
 'categories': ['Category:CC-BY-SA-2.0',
                'Category:Dell Axim X5',
                'Category:Flickr images reviewed by FlickreviewR 2'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<a rel="nofollow" class="external text" '
                           'href="https://www.flickr.com/photos/winkelnkemper/46677558785/">DELL '
                           'AXIM PDA</a>',
                 'ImageDescription': 'DELL AXIM PDA',
                 'License': 'cc-by-sa-2.0',
                 'LicenseShortName': 'CC BY-SA 2.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/2.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 2.0'}},
    ),
    (
        'Accra Arts Centre',
        {'title': 'File:Art+Feminism in Vanadzor (17).jpg',
 'categories': ['Category:Art and Feminism Editathon at Vanadzor Museum of Fine Arts',
                'Category:CC-BY-SA-4.0',
                'Category:Files with coordinates missing SDC location of creation',
                'Category:Self-published work'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'GPSLatitude': '40.806667',
                 'GPSLongitude': '44.496111',
                 'ImageDescription': 'Art and Feminism Editathon at Vanadzor Museum of Fine '
                                     'Arts',
                 'License': 'cc-by-sa-4.0',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0'}},
    ),
    (
        'Daboya Fugu Weaving Village',
        {'title': 'File:Fugu delivery truck in Meguro.jpg',
 'categories': ['Category:April 2025 in transport in Tokyo',
                'Category:CC-Zero',
                'Category:Delivery trucks in Japan',
                'Category:Files with coordinates missing SDC location of creation',
                'Category:Meguro (district)',
                'Category:Pufferfish dishes of Japan',
                'Category:Self-published work',
                'Category:Tokyo photographs taken on 2025-04-05',
                'Category:Trucks in Japan photographed in 2025',
                'Category:Trucks in Meguro, Tokyo',
                'Category:Uploaded with Mobile/Android'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'GPSLatitude': '35.634678',
                 'GPSLongitude': '139.713175',
                 'ImageDescription': 'Meguro (neighborhood in Meguro-ku, Tokyo, Japan)',
                 'License': 'cc0',
                 'LicenseShortName': 'CC0',
                 'LicenseUrl': 'http://creativecommons.org/publicdomain/zero/1.0/deed.en',
                 'UsageTerms': 'Creative Commons Zero, Public Domain Dedication'}},
    ),
    (
        'Akaa Falls',
        {'title': 'File:Akaan Toijalan keskustan alue.jpg',
 'categories': [],
 'extmetadata': {'LicenseShortName': 'CC BY-SA 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0'}},
    ),
    (
        'Sui River',
        {'title': 'File:Sui-ho Dam, 22 February 1953.jpg',
 'categories': ['Category:CC-PD-Mark',
                'Category:Korean War in February 1953',
                'Category:PD US Government',
                'Category:Supung Dam'],
 'extmetadata': {'ImageDescription': '23 February 1953.  Yalu River Power Plant - Fifth Air '
                                     'Force, Korea.  The Suiho power plant, the key Communist '
                                     'industrial complex in the Yalu River in North Korea and '
                                     'Manchuria, is revealed here in an aerial reconnaissance '
                                     'photograph taken at an amazingly low altitude by an '
                                     'RF-80 pilot of the U.S. Air Force 67th Tactical '
                                     'Reconnaissance Wing.  This photo, looking northeast '
                                     '(upriver), shows the dam which holds back the Suiho '
                                     'resevoir, and the cement power house at the base of the '
                                     'dam which contains the generators that once supplied '
                                     'power for many of the major industrial centers of North '
                                     'Korea.  The shore in the right section of the photo is '
                                     'the southern bank of the Yalu, northern border of '
                                     'enemy-held North Korea.  To the left, just out of range '
                                     'of the photo, is Manchuria, the sanctuary for Communist '
                                     "MiG-15's.  Despite the nearness to the MiG bases, the "
                                     'pilot of the aircraft made this low photo run in his '
                                     'unarmed jet to get this photograph.',
                 'Credit': '<a rel="nofollow" class="external free" '
                           'href="https://media.defense.gov/2010/Jun/15/2000351844/-1/-1/0/100615-F-1234S-006.JPG">https://media.defense.gov/2010/Jun/15/2000351844/-1/-1/0/100615-F-1234S-006.JPG</a>',
                 'LicenseShortName': 'Public domain',
                 'UsageTerms': 'Public domain',
                 'Copyrighted': 'False',
                 'License': 'pd'}},
    ),
    (
        'Sui River',
        {'title': 'File:HK SuiWoCourt.JPG',
 'categories': ['Category:CC-BY-SA-3.0',
                'Category:GFDL',
                'Category:License migration redundant',
                'Category:Self-published work',
                'Category:Shing Mun River',
                'Category:Sui Wo Court'],
 'extmetadata': {'ImageDescription': '\u200b穗禾苑',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'LicenseShortName': 'CC BY-SA 3.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 3.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/3.0',
                 'Copyrighted': 'True',
                 'License': 'cc-by-sa-3.0'}},
    ),
    (
        'Cape Three Points',
        {'title': 'File:Cape Three Points from the air. - panoramio.jpg',
 'categories': ['Category:Aerial photographs of the Central Coast, New South Wales',
                'Category:CC-BY-SA-3.0',
                'Category:Files with coordinates missing SDC location of creation (34° S, 151° '
                'E)',
                'Category:Panoramio files uploaded by Panoramio upload bot',
                'Category:Panoramio images reviewed by trusted users',
                'Category:Photos from Panoramio',
                'Category:Photos from Panoramio ID 919085'],
 'extmetadata': {'Attribution': 'Ray Hayward',
                 'Copyrighted': 'True',
                 'Credit': '<a rel="nofollow" class="external free" '
                           'href="https://web.archive.org/web/20161012072324/http://www.panoramio.com/photo/12454459">https://web.archive.org/web/20161012072324/http://www.panoramio.com/photo/12454459</a>',
                 'GPSLatitude': '-33.493236',
                 'GPSLongitude': '151.432543',
                 'ImageDescription': 'Cape Three Points from the air.',
                 'License': 'cc-by-sa-3.0',
                 'LicenseShortName': 'CC BY-SA 3.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/3.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 3.0'}},
    ),
    (
        'Fort Amsterdam (Abandzi)',
        {'title': 'File:Benteng Amsterdam.jpg',
 'categories': ['Category:2016 in Ambon',
                'Category:CC-BY-SA-4.0',
                'Category:Dutch East Indies',
                'Category:Fort Amsterdam (Ambon)',
                'Category:Indonesia photographs taken on 2016-12-31',
                'Category:Self-published work'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'ImageDescription': 'Fort Amsterday in the village of Hila, Ambon, Maluku '
                                     'Islands',
                 'License': 'cc-by-sa-4.0',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0'}},
    ),
    (
        'Fort Amsterdam (Abandzi)',
        {'title': 'File:Fort Amsterdam auf Ambon.jpg',
 'categories': ['Category:Ambon',
                'Category:CC-BY-SA-4.0',
                'Category:Fort Amsterdam (Ambon)',
                'Category:Self-published work'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'ImageDescription': 'Eingangsbereich',
                 'License': 'cc-by-sa-4.0',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0'}},
    ),
    (
        'Fort Amsterdam (Abandzi)',
        {'title': 'File:Ruins of the Water Fort St. Eustatius with in the background the Godet burial '
          'ground.jpg',
 'categories': ['Category:Beaches of Sint Eustatius',
                'Category:CC-BY-SA-4.0',
                'Category:Files with coordinates missing SDC location of creation',
                'Category:Mountains of Sint Eustatius',
                'Category:Self-published work',
                'Category:Sint Eustatius in the 18th century',
                'Category:Slavery in Sint Eustatius',
                'Category:Waterfort, Sint Eustatius'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'GPSLatitude': '17.486136',
                 'GPSLongitude': '-62.992681',
                 'ImageDescription': 'Ruins of the Waterfort in Sint Eustatius, Dutch '
                                     'Caribbean (also known as Fort Amsterdam) with in the '
                                     'background the historical burial ground Godet.',
                 'License': 'cc-by-sa-4.0',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0'}},
    ),
    (
        'Fort Good Hope',
        {'title': 'File:Fort Good Hope (99536196).jpg',
 'categories': ['Category:CC-BY-SA-2.0',
                'Category:February 2006 in the Northwest Territories',
                'Category:Files with coordinates missing SDC location of creation',
                'Category:Flickr images reviewed by FlickreviewR 2',
                'Category:Fort Good Hope',
                'Category:Schools in the Northwest Territories'],
 'extmetadata': {'GPSLatitude': '66.259462',
                 'GPSLongitude': '-128.633766',
                 'ImageDescription': 'School on the hill',
                 'Credit': '<a rel="nofollow" class="external text" '
                           'href="https://www.flickr.com/photos/ntlibrarian/99536196/">Fort '
                           'Good Hope</a>',
                 'LicenseShortName': 'CC BY-SA 2.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 2.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/2.0',
                 'Copyrighted': 'True',
                 'License': 'cc-by-sa-2.0'}},
    ),
    (
        'Fort Dorothea',
        {'title': 'File:Light bush brown (Bicyclus dorothea) underside Ankasa.jpg',
  'categories': ['Category:Bicyclus dorothea',
                 'Category:CC-BY-SA-4.0',
                 'Category:Files with coordinates missing SDC location of creation',
                 'Category:Lepidoptera of Ankasa Forest Reserve',
                 'Category:Nymphalidae of Ghana',
                 'Category:Photographs by Charlesjsharp',
                 'Category:Quality images',
                 'Category:Quality images by Charlesjsharp',
                 'Category:Quality images missing SDC creator',
                 'Category:Quality images of Lepidoptera by Charlesjsharp',
                 'Category:Quality images of Lepidoptera in Ghana',
                 'Category:Quality images of Nymphalidae',
                 'Category:Quality images of Nymphalidae by Charlesjsharp',
                 'Category:Quality images of butterflies by Charlesjsharp',
                 'Category:Quality images of insects by Charlesjsharp',
                 'Category:Self-published work'],
  'extmetadata': {'Artist': '<bdi><a href="https://www.wikidata.org/wiki/Q54800218" '
                            'class="extiw" title="d:Q54800218"><span title="Scottish '
                            'wildlife photographer">Charles J. Sharp</span></a></bdi>',
                  'Assessments': 'quality',
                  'AttributionRequired': 'true',
                  'Categories': 'Bicyclus dorothea|Photographs by '
                                'Charlesjsharp|Self-published work|Files with '
                                'coordinates missing SDC location of '
                                'creation|Nymphalidae of Ghana|Lepidoptera of Ankasa '
                                'Forest Reserve',
                  'CommonsMetadataExtension': 1.2,
                  'Copyrighted': 'True',
                  'Credit': '<span class="int-own-work" lang="en">Own work</span>, from '
                            '<a rel="nofollow" class="external text" '
                            'href="https://www.sharpphotography.co.uk/">Sharp '
                            'Photography, sharpphotography.co.uk</a>',
                  'DateTime': '2023-12-08 21:15:38',
                  'DateTimeOriginal': '2023-10-05 09:10:07',
                  'GPSLatitude': '5.230000',
                  'GPSLongitude': '-2.650000',
                  'GPSMapDatum': 'WGS-84',
                  'ImageDescription': 'Light bush brown (<i>Bicyclus dorothea</i>), '
                                      'Ankasa Forest Reserve, Western Region, Ghana',
                  'License': 'cc-by-sa-4.0',
                  'LicenseShortName': 'CC BY-SA 4.0',
                  'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                  'ObjectName': 'Light bush brown (Bicyclus dorothea) underside Ankasa',
                  'Restrictions': '',
                  'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0'}}
    ),
    (
        'Fort Dorothea',
        {'title': 'File:Light bush brown (Bicyclus dorothea) underside on leaf.jpg',
  'categories': ['Category:Bicyclus dorothea',
                 'Category:CC-BY-SA-4.0',
                 'Category:Files with coordinates missing SDC location of creation',
                 'Category:Lepidoptera of Kakum National Park',
                 'Category:Nymphalidae of Ghana',
                 'Category:Photographs by Charlesjsharp',
                 'Category:Quality images',
                 'Category:Quality images by Charlesjsharp',
                 'Category:Quality images missing SDC creator',
                 'Category:Quality images of Lepidoptera by Charlesjsharp',
                 'Category:Quality images of Lepidoptera in Ghana',
                 'Category:Quality images of Nymphalidae',
                 'Category:Quality images of Nymphalidae by Charlesjsharp',
                 'Category:Quality images of butterflies by Charlesjsharp',
                 'Category:Quality images of insects by Charlesjsharp',
                 'Category:Self-published work'],
  'extmetadata': {'Artist': '<bdi><a href="https://www.wikidata.org/wiki/Q54800218" '
                            'class="extiw" title="d:Q54800218"><span title="Scottish '
                            'wildlife photographer">Charles J. Sharp</span></a></bdi>',
                  'Assessments': 'quality',
                  'AttributionRequired': 'true',
                  'Categories': 'Bicyclus dorothea|Photographs by '
                                'Charlesjsharp|Self-published work|Files with '
                                'coordinates missing SDC location of '
                                'creation|Nymphalidae of Ghana|Lepidoptera of Kakum '
                                'National Park',
                  'CommonsMetadataExtension': 1.2,
                  'Copyrighted': 'True',
                  'Credit': '<span class="int-own-work" lang="en">Own work</span>, from '
                            '<a rel="nofollow" class="external text" '
                            'href="https://www.sharpphotography.co.uk/">Sharp '
                            'Photography, sharpphotography.co.uk</a>',
                  'DateTime': '2022-01-18 12:47:12',
                  'DateTimeOriginal': '2021-11-02 10:37:32',
                  'GPSLatitude': '5.331000',
                  'GPSLongitude': '-1.377000',
                  'GPSMapDatum': 'WGS-84',
                  'ImageDescription': 'Light bush brown (<i>Bicyclus dorothea</i>), '
                                      'Kakum National Park, Ghana',
                  'License': 'cc-by-sa-4.0',
                  'LicenseShortName': 'CC BY-SA 4.0',
                  'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                  'ObjectName': 'Light bush brown (Bicyclus dorothea) underside on leaf',
                  'Restrictions': '',
                  'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0'}}
    ),
    (
        'Fort Dorothea',
        {'title': 'File:Light bush brown (Bicyclus dorothea) underside.jpg',
  'categories': ['Category:Bicyclus dorothea',
                 'Category:CC-BY-SA-4.0',
                 'Category:Files with coordinates missing SDC location of creation',
                 'Category:Lepidoptera of Kakum National Park',
                 'Category:Nymphalidae of Ghana',
                 'Category:Photographs by Charlesjsharp',
                 'Category:Self-published work',
                 'Category:Valued images by Charlesjsharp',
                 'Category:Valued images missing SDC creator',
                 'Category:Valued images missing SDC depicts',
                 'Category:Valued images of Ghana',
                 'Category:Valued images of Lepidoptera by Charlesjsharp',
                 'Category:Valued images of Nymphalidae',
                 'Category:Valued images of Nymphalidae by Charlesjsharp',
                 'Category:Valued images of butterflies by Charlesjsharp',
                 'Category:Valued images of insects by Charlesjsharp',
                 'Category:Valued images promoted 2022-01',
                 'Category:Valued images sorted by promotion date'],
  'extmetadata': {'Artist': '<bdi><a href="https://www.wikidata.org/wiki/Q54800218" '
                            'class="extiw" title="d:Q54800218"><span title="Scottish '
                            'wildlife photographer">Charles J. Sharp</span></a></bdi>',
                  'Assessments': 'valued',
                  'AttributionRequired': 'true',
                  'Categories': 'Bicyclus dorothea|Photographs by '
                                'Charlesjsharp|Self-published work|Files with '
                                'coordinates missing SDC location of '
                                'creation|Nymphalidae of Ghana|Lepidoptera of Kakum '
                                'National Park',
                  'CommonsMetadataExtension': 1.2,
                  'Copyrighted': 'True',
                  'Credit': '<span class="int-own-work" lang="en">Own work</span>, from '
                            '<a rel="nofollow" class="external text" '
                            'href="https://www.sharpphotography.co.uk/">Sharp '
                            'Photography, sharpphotography.co.uk</a>',
                  'DateTime': '2022-01-18 12:47:12',
                  'DateTimeOriginal': '2021-11-02 10:37:32',
                  'GPSLatitude': '5.331000',
                  'GPSLongitude': '-1.377000',
                  'GPSMapDatum': 'WGS-84',
                  'ImageDescription': 'Light bush brown (<i>Bicyclus dorothea</i>), '
                                      'Kakum National Park, Ghana',
                  'License': 'cc-by-sa-4.0',
                  'LicenseShortName': 'CC BY-SA 4.0',
                  'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                  'ObjectName': 'Light bush brown (Bicyclus dorothea) underside',
                  'Restrictions': '',
                  'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0'}}
    ),
    (
        'Atiwa Forest Reserve',
        {'title': 'File:Atiwa - tiwa (Ngaben) - Ubud, Giantar, Bali.jpg',
  'categories': ['Category:CC-BY-SA-4.0',
                 'Category:Cremations in Ubud',
                 'Category:Images from WikiKaleidoskop',
                 'Category:Self-published work',
                 'Category:Uploaded via Campaign:wmid-wikikaleidoskop-2021'],
  'extmetadata': {'Artist': '<a '
                            'href="//commons.wikimedia.org/w/index.php?title=User:Gede_Agunata_Wiryatama&amp;action=edit&amp;redlink=1" '
                            'class="new" title="User:Gede Agunata Wiryatama (page does '
                            'not exist)">Gede Agunata Wiryatama</a>',
                  'Assessments': '',
                  'AttributionRequired': 'true',
                  'Categories': 'Self-published work|Images from '
                                'WikiKaleidoskop|Cremations in Ubud|Uploaded via '
                                'Campaign:wmid-wikikaleidoskop-2021',
                  'CommonsMetadataExtension': 1.2,
                  'Copyrighted': 'True',
                  'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                  'DateTime': '2021-08-04 04:46:31',
                  'DateTimeOriginal': '2017-08-16 13:35:26',
                  'ImageDescription': 'Atiwa - tiwa (Ngaben) sebuah tradisi yang sangat '
                                      'terkenal di Bali.Upacara Ngaben sendiri '
                                      'sebenarnya adalah prosesi pembakaran mayat atau '
                                      'kremasi bagi penganut Hindu Bali. Ritual '
                                      'pembakaran mayat tersebut ditujukan sebagai '
                                      'simbol untuk menyucikan roh orang yang telah '
                                      'meninggal. ngaben terdiri dari beberapa '
                                      'tingkatan dari tingkat Nista (terbawah), sampai '
                                      'tingkatan tertinggi (Utama)',
                  'License': 'cc-by-sa-4.0',
                  'LicenseShortName': 'CC BY-SA 4.0',
                  'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                  'ObjectName': 'Atiwa - tiwa (Ngaben) - Ubud, Giantar, Bali',
                  'Restrictions': '',
                  'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0'}}
    ),
]

ACCEPTED = [
    # Koczkodan liberyjski was removed in an earlier pass on the strength of
    # its Polish title, which read as a foreign photograph. It was wrong. The
    # file is the uploader's own work, taken 1.0 km from the sanctuary's own
    # coordinates, and carries Category:Boabeng-Fiema Monkey Sanctuary and
    # Category:Monkeys in Ghana. A title in the uploader's language is not
    # evidence of another place, and every other signal in the record says
    # Ghana. This case is the reason the ACCEPTED list exists: the two rules
    # that caught the real mistakes here could not tell this one apart.
    (
        'Boabeng-Fiema Monkey Sanctuary',
        {'title': 'File:Koczkodan liberyjski.jpg',
 'categories': ['Category:Boabeng-Fiema Monkey Sanctuary',
                'Category:CC-BY-SA-4.0',
                'Category:Files with coordinates missing SDC location of creation',
                'Category:Monkeys in Ghana',
                'Category:Self-published work'],
 'extmetadata': {'GPSLatitude': '7.708646',
                 'GPSLongitude': '-1.695770',
                 'ImageDescription': 'Koczkodan liberyjski',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                 'Copyrighted': 'True',
                 'License': 'cc-by-sa-4.0'}},
    ),
    (
        'Tagbo Falls',
        {'title': 'File:Tagbo Falls flows from the Ghana-Togo range.jpg',
 'categories': ['Category:CC-BY-SA-4.0',
                'Category:Images from Wiki Loves Earth 2024',
                'Category:Images from Wiki Loves Earth 2024 in Ghana',
                'Category:Images from Wiki Loves Earth missing SDC depicts',
                'Category:Images from Wiki Loves Earth missing SDC location of creation',
                'Category:Self-published work',
                'Category:Uploaded via Campaign:wle-gh',
                'Category:Waterfalls in Ghana'],
 'extmetadata': {'ImageDescription': 'Lush vegetation by the Tagbo falls',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                 'Copyrighted': 'True',
                 'License': 'cc-by-sa-4.0'}},
    ),
    (
        'Fort Patience',
        {'title': 'File:Overzicht achterzijde vanaf buitenmuur - Apam - 20375239 - RCE.jpg',
 'categories': ['Category:Buildings with addresses',
                'Category:Buildings with addresses - country not yet supported',
                'Category:CC-BY-SA-4.0',
                'Category:Cultural heritage monuments in Ghana with known IDs',
                'Category:Defensive walls in Ghana',
                'Category:Fort Apam',
                'Category:Images from the Rijksdienst voor het Cultureel Erfgoed',
                'Category:January 2000 Ghana photographs',
                'Category:Photographs by Loek Tangel in Ghana (2000)',
                'Category:Photographs uploaded by User:Vysotsky'],
 'extmetadata': {'ImageDescription': 'This is a photo of <a '
                                     'href="https://en.wikipedia.org/wiki/Ghana%E2%80%99s_material_cultural_heritage" '
                                     'class="extiw" title="en:Ghana’s material cultural '
                                     'heritage">Ghana\'s material cultural heritage</a> number',
                 'Credit': '<a rel="nofollow" class="external text" '
                           'href="http://beeldbank.cultureelerfgoed.nl/alle-afbeeldingen/?mode=gallery&amp;view=horizontal&amp;q=20375239">Rijksdienst '
                           'voor het Cultureel Erfgoed</a>',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0',
                 'Attribution': '<a rel="nofollow" class="external text" '
                                'href="https://www.cultureelerfgoed.nl/">Rijksdienst voor het '
                                'Cultureel Erfgoed</a>',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                 'Copyrighted': 'True',
                 'License': 'cc-by-sa-4.0'}},
    ),
    (
        'Fort Batenstein',
        {'title': 'File:Overzicht met ruïne bovenop heuvel - Butre - 20375423 - RCE.jpg',
 'categories': ['Category:Buildings with addresses',
                'Category:Buildings with addresses - country not yet supported',
                'Category:CC-BY-SA-4.0',
                'Category:Children of Ghana',
                'Category:Cultural heritage monuments in Ghana with known IDs',
                'Category:Fort Boutrie',
                'Category:Headcarrying in Ghana',
                'Category:Housing in Boutrie',
                'Category:Images from the Rijksdienst voor het Cultureel Erfgoed',
                'Category:January 2000 Ghana photographs',
                'Category:Photographs by Loek Tangel in Ghana (2000)'],
 'extmetadata': {'Attribution': '<a rel="nofollow" class="external text" '
                                'href="https://www.cultureelerfgoed.nl/">Rijksdienst voor het '
                                'Cultureel Erfgoed</a>',
                 'Copyrighted': 'True',
                 'Credit': '<a rel="nofollow" class="external text" '
                           'href="http://beeldbank.cultureelerfgoed.nl/alle-afbeeldingen/?mode=gallery&amp;view=horizontal&amp;q=20375423">Rijksdienst '
                           'voor het Cultureel Erfgoed</a>',
                 'ImageDescription': 'This is a photo of <a '
                                     'href="https://en.wikipedia.org/wiki/Ghana%E2%80%99s_material_cultural_heritage" '
                                     'class="extiw" title="en:Ghana’s material cultural '
                                     'heritage">Ghana\'s material cultural heritage</a> number',
                 'License': 'cc-by-sa-4.0',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0'}},
    ),
    (
        'Bia National Park',
        {'title': 'File:Entrance to Bia Forest reserve.jpg',
 'categories': ['Category:Bia National Park',
                'Category:CC-BY-SA-3.0',
                'Category:Images from Wiki Loves Earth 2014',
                'Category:Images from Wiki Loves Earth 2014 in Ghana',
                'Category:Images from Wiki Loves Earth missing SDC depicts',
                'Category:Images from Wiki Loves Earth missing SDC location of creation',
                'Category:People of Ghana in 2010',
                'Category:Self-published work',
                'Category:Taken with Olympus FE-46 / X-41 / X-42',
                'Category:Uploaded via Campaign:wle-gh'],
 'extmetadata': {'ImageDescription': 'Entrance to Bia Forest reserve in the Western Region',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'LicenseShortName': 'CC BY-SA 3.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 3.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/3.0',
                 'Copyrighted': 'True',
                 'License': 'cc-by-sa-3.0'}},
    ),
    (
        'Kete Krachi Museum',
        {'title': 'File:Dusty Roads Kete Krachi.JPG',
 'categories': ['Category:2011 in Ghana',
                'Category:Bus passengers in Ghana',
                'Category:CC-BY-SA-3.0',
                'Category:Dirt roads in Ghana',
                'Category:Images from Wiki Loves Earth 2014',
                'Category:Images from Wiki Loves Earth 2014 in Ghana',
                'Category:Images from Wiki Loves Earth missing SDC depicts',
                'Category:Images from Wiki Loves Earth missing SDC location of creation',
                'Category:Minibuses in Ghana',
                'Category:People of Ghana in 2011',
                'Category:Photographs of Volta Region',
                'Category:Self-published work',
                'Category:Uploaded via Campaign:wle-gh',
                'Category:Volkswagen LT (1st generation)'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'ImageDescription': 'This is a file of Ghanaian Natural Heritage with ID:',
                 'License': 'cc-by-sa-3.0',
                 'LicenseShortName': 'CC BY-SA 3.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/3.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 3.0'}},
    ),
    (
        'Kyabobo National Park',
        {'title': 'File:A large tree trunk in the kyabobo forest.jpg',
 'categories': ['Category:CC-BY-SA-4.0',
                'Category:Images from Wiki Loves Earth 2025',
                'Category:Images from Wiki Loves Earth 2025 Human Rights and Environment '
                'Special Nomination',
                'Category:Images from Wiki Loves Earth 2025 in Ghana',
                'Category:Images from Wiki Loves Earth missing SDC location of creation',
                'Category:Kyabobo National Park',
                'Category:Self-published work',
                'Category:Uploaded via Campaign:wle-gh'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'ImageDescription': 'A large tree trunk heavy with moss, and behind it, is  '
                                     'cave.',
                 'License': 'cc-by-sa-4.0',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0'}},
    ),
    (
        "Elmina Castle (St. George's Castle)",
        {'title': 'File:Elmina Castle 11.jpg',
 'categories': ['Category:CC-BY-SA-4.0',
                'Category:Elmina Castle',
                'Category:Self-published work'],
 'extmetadata': {'ImageDescription': 'Elmina Castle or St. George’s Castle, in the town of '
                                     'Elmina in the Central Region of Ghana',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                 'Copyrighted': 'True',
                 'License': 'cc-by-sa-4.0'}},
    ),
    (
        'Cape Three Points',
        {'title': 'File:DSC01739 (15318781703).jpg',
 'categories': ['Category:CC-BY-2.0',
                'Category:Cape Three Points',
                'Category:Flickr images reviewed by FlickreviewR 2',
                'Category:Lighthouses in Ghana'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<a rel="nofollow" class="external text" '
                           'href="https://www.flickr.com/photos/tinimaier/15318781703/">DSC01739</a>',
                 'ImageDescription': 'Lighthouse - Cape Three Points Village, Ghana',
                 'License': 'cc-by-2.0',
                 'LicenseShortName': 'CC BY 2.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by/2.0',
                 'UsageTerms': 'Creative Commons Attribution 2.0'}},
    ),
    (
        'Fort Amsterdam (Abandzi)',
        {'title': 'File:Fort Amsterdam, uitzicht vanaf fort - 20651813 - RCE.jpg',
 'categories': ['Category:CC-BY-SA-4.0',
                'Category:Fort Kormantin',
                'Category:Images from the Rijksdienst voor het Cultureel Erfgoed',
                'Category:Photographs by Coen Temminck Groll in Ghana',
                'Category:Temminck Groll Collection',
                'Category:The Netherlands and the world',
                'Category:Uploaded with pattypan'],
 'extmetadata': {'Attribution': '<a rel="nofollow" class="external text" '
                                'href="https://www.cultureelerfgoed.nl/">Rijksdienst voor het '
                                'Cultureel Erfgoed</a>',
                 'Copyrighted': 'True',
                 'Credit': '<a rel="nofollow" class="external text" '
                           'href="http://beeldbank.cultureelerfgoed.nl/alle-afbeeldingen/?mode=gallery&amp;view=horizontal&amp;q=20651813">Rijksdienst '
                           'voor het Cultureel Erfgoed</a>',
                 'ImageDescription': 'Fort Amsterdam, uitzicht vanaf fort<br><i>Onderwerp:</i> '
                                     'forten, landschap',
                 'License': 'cc-by-sa-4.0',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0'}},
    ),
    (
        'Aburi Botanical Gardens',
        {'title': 'File:Aburi Botanical Gardens 08.jpg',
 'categories': ['Category:Aburi Botanical Gardens',
                'Category:CC-BY-SA-4.0',
                'Category:Self-published work'],
 'extmetadata': {'GPSLatitude': '6.059121',
                 'GPSLongitude': '-0.255229',
                 'ImageDescription': 'Pictures of Aburi Botanical Gardens, Ghana',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                 'Copyrighted': 'True',
                 'License': 'cc-by-sa-4.0'}},
    ),
    (
        'Kakum National Park Canopy Walk',
        {'title': 'File:A section of kakum.jpg',
 'categories': ['Category:CC-BY-SA-4.0',
                'Category:Canopy walkways in the Kakum National Park (Ghana)',
                'Category:Ghana photographs taken on 2021-07-18',
                'Category:Images from Wiki Loves Earth 2022',
                'Category:Images from Wiki Loves Earth 2022 in Ghana',
                'Category:Images from Wiki Loves Earth 2022 in Ghana - landscape',
                'Category:Images from Wiki Loves Earth missing SDC inception',
                'Category:Self-published work',
                'Category:Trees',
                'Category:Uploaded via Campaign:wle-gh'],
 'extmetadata': {'ImageDescription': 'A stage where tourist on the walkway can rest and '
                                     'continue the walk',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                 'Copyrighted': 'True',
                 'License': 'cc-by-sa-4.0'}},
    ),
    (
        'Manhyia Palace Museum',
        {'title': 'File:An image baes of the artifacts at the Manhyia Palace Museum.jpg',
 'categories': ['Category:Africa Wiki Challenge 2025',
                'Category:CC-BY-4.0',
                'Category:Files with coordinates missing SDC location of creation',
                'Category:Ghana',
                'Category:Self-published work'],
 'extmetadata': {'GPSLatitude': '6.704311',
                 'GPSLongitude': '-1.615994',
                 'ImageDescription': 'Africa culture',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'LicenseShortName': 'CC BY 4.0',
                 'UsageTerms': 'Creative Commons Attribution 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by/4.0',
                 'Copyrighted': 'True',
                 'License': 'cc-by-4.0'}},
    ),
    (
        'Homowo Festival',
        {'title': 'File:Homowo Festival 50.jpg',
 'categories': ['Category:CC-BY-SA-4.0',
                'Category:Images from Wiki Loves Festival 2021 in Ghana',
                'Category:Self-published work',
                'Category:Teshie Homowo Festival'],
 'extmetadata': {'ImageDescription': 'Homowo Festival Celebrated by the Youth',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                 'Copyrighted': 'True',
                 'License': 'cc-by-sa-4.0'}},
    ),
    (
        'Mole National Park Elephant Safari',
        {'title': 'File:Safari in Mole (191042526).jpg',
 'categories': ['Category:CC-BY-2.0',
                'Category:Files from Stig Nygaard Flickr stream',
                'Category:Flickr images reviewed by FlickreviewR 2'],
 'extmetadata': {'ImageDescription': '<p>This is a "crop" of the &lt;a href="<a rel="nofollow" '
                                     'class="external free" '
                                     'href="https://www.flickr.com/photos/stignygaard/191042524/">https://www.flickr.com/photos/stignygaard/191042524/</a>"&gt;previous '
                                     'picture&lt;/a&gt;.\n'
                                     '</p>\n'
                                     'I like the heron between the elephants legs.',
                 'Credit': '<a rel="nofollow" class="external text" '
                           'href="https://www.flickr.com/photos/stignygaard/191042526/">Safari '
                           'in Mole</a>',
                 'LicenseShortName': 'CC BY 2.0',
                 'UsageTerms': 'Creative Commons Attribution 2.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by/2.0',
                 'Copyrighted': 'True',
                 'License': 'cc-by-2.0'}},
    ),
    (
        'Accra Arts Centre',
        {'title': 'File:National Cultural Center of Ghana, Korle-Klottey (IMG 20230201 162214).jpg',
 'categories': ['Category:Accra Arts Centre',
                'Category:CC-BY-SA-2.0+',
                'Category:Files with coordinates missing SDC location of creation',
                'Category:GFDL',
                'Category:Ghana photographs taken on 2023-02-01',
                'Category:License migration redundant',
                'Category:Pictures by MB-one rejected',
                'Category:Self-published work',
                'Category:Taken with Xiaomi Mi 11 5G',
                'Category:Uploaded with LrMediaWiki',
                'Category:User MB-one supported by Wikimedia Deutschland/Lightroom'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'GPSLatitude': '5.543030',
                 'GPSLongitude': '-0.202369',
                 'ImageDescription': 'Dance rehearsal of Folkloric Selamta at National '
                                     'Cultural Center of Ghana\xa0<span '
                                     'class="mw-valign-text-top noprint" '
                                     'typeof="mw:File/Frameless"><a '
                                     'href="//commons.wikimedia.org/wiki/File:National_Cultural_Center_of_Ghana,_Korle-Klottey_(IMG_20230201_162214).jpg#ooui-php-4" '
                                     'title="Edit this at Structured Data on Commons"><img '
                                     'alt="Edit this at Structured Data on Commons" '
                                     'src="https://thumb.wikimedia.org/wikipedia/commons/thumb/8/8a/OOjs_UI_icon_edit-ltr-progressive.svg/20px-OOjs_UI_icon_edit-ltr-progressive.svg.png?utm_source=commons.wikimedia.org&amp;utm_campaign=parser&amp;utm_content=thumbnail" '
                                     'decoding="async" loading="lazy" width="10" height="10" '
                                     'class="mw-file-element" data-file-width="20" '
                                     'data-file-height="20"></a></span>',
                 'License': 'cc-by-sa-4.0',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0/deed.en',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0'}},
    ),
    (
        'Shai Hills Resource Reserve',
        {'title': 'File:Shai Hills, Shai-Osudoku (P1100033).jpg',
 'categories': ['Category:2023 photographs of Greater Accra Region',
                'Category:CC-BY-SA-2.0+',
                'Category:GFDL',
                'Category:Ghana photographs taken on 2023-02-05',
                'Category:Kobus kob in Ghana',
                'Category:License migration redundant',
                'Category:Pictures by MB-one rejected',
                'Category:Self-published work',
                'Category:Shai Hills Resource Reserve',
                'Category:Taken with Panasonic Lumix DMC-G5 and Panasonic Lumix G Vario HD '
                '14-140mm F4.0-5.8 Asph Mega OIS',
                'Category:Uploaded with LrMediaWiki',
                'Category:User MB-one supported by Wikimedia Deutschland/Lightroom'],
 'extmetadata': {'GPSLatitude': '5.937567',
                 'GPSLongitude': '0.070225',
                 'ImageDescription': 'Shai Hills Resource Reserve\xa0<span '
                                     'class="mw-valign-text-top noprint" '
                                     'typeof="mw:File/Frameless"><a '
                                     'href="//commons.wikimedia.org/wiki/File:Shai_Hills,_Shai-Osudoku_(P1100033).jpg#ooui-php-4" '
                                     'title="Edit this at Structured Data on Commons"><img '
                                     'alt="Edit this at Structured Data on Commons" '
                                     'src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/OOjs_UI_icon_edit-ltr-progressive.svg/20px-OOjs_UI_icon_edit-ltr-progressive.svg.png?utm_source=commons.wikimedia.org&amp;utm_campaign=parser&amp;utm_content=thumbnail" '
                                     'decoding="async" loading="lazy" width="10" height="10" '
                                     'class="mw-file-element" data-file-width="20" '
                                     'data-file-height="20"></a></span>',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0/deed.en',
                 'Copyrighted': 'True',
                 'License': 'cc-by-sa-4.0'}},
    ),
    (
        'National Museum of Ghana',
        {'title': 'File:Colonial cannon in Ghana.jpg',
 'categories': ['Category:CC-BY-SA-3.0',
                'Category:Cannons in Ghana',
                'Category:Images from Wiki Loves Earth 2014',
                'Category:Images from Wiki Loves Earth 2014 in Ghana',
                'Category:Images from Wiki Loves Earth missing SDC depicts',
                'Category:Images from Wiki Loves Earth missing SDC location of creation',
                'Category:National Museum of Ghana',
                'Category:Self-published work',
                'Category:Taken with Samsung Galaxy Tab 2 10.1',
                'Category:Uploaded via Campaign:wle-gh'],
 'extmetadata': {'ImageDescription': 'This colonial canon gun is found at the Ghana national '
                                     'museum in Accra. It has been placed there since the '
                                     'opening of the national museum in 1957.',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'LicenseShortName': 'CC BY-SA 3.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 3.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/3.0',
                 'Copyrighted': 'True',
                 'License': 'cc-by-sa-3.0'}},
    ),
    (
        'Butre Beach',
        {'title': 'File:Butre, seen from Fort Batenstein.jpg',
 'categories': ['Category:Boutrie', 'Category:CC-BY-SA-4.0', 'Category:Self-published work'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'ImageDescription': 'The village of Butre, seen from Fort Batenstein. Picture '
                                     'taken in April 2017.',
                 'License': 'cc-by-sa-4.0',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0'}},
    ),
    (
        'Fort Apollonia',
        {'title': 'File:Fort Apollonia 001.jpg',
 'categories': ['Category:CC-BY-SA-4.0',
                'Category:Cultural heritage monuments in Ghana with known IDs',
                'Category:Fort Apollonia (Ghana)',
                'Category:Fort Kormantin',
                'Category:Images from Wiki Loves Monuments 2017',
                'Category:Images from Wiki Loves Monuments 2017 in Ghana',
                'Category:Images from Wiki Loves Monuments missing SDC depicts',
                'Category:Images from Wiki Loves Monuments missing SDC location of creation',
                'Category:Nominated pictures for Wiki Loves Monuments International',
                'Category:Self-published work',
                'Category:Uploaded via Campaign:wlm-gh',
                'Category:Winners of Wiki Loves Monuments 2017 in Ghana'],
 'extmetadata': {'Copyrighted': 'True',
                 'Credit': '<span class="int-own-work" lang="en">Own work</span>',
                 'ImageDescription': 'This is a photo of <a '
                                     'href="https://en.wikipedia.org/wiki/Ghana%E2%80%99s_material_cultural_heritage" '
                                     'class="extiw" title="en:Ghana’s material cultural '
                                     'heritage">Ghana\'s material cultural heritage</a> number',
                 'License': 'cc-by-sa-4.0',
                 'LicenseShortName': 'CC BY-SA 4.0',
                 'LicenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0',
                 'UsageTerms': 'Creative Commons Attribution-Share Alike 4.0'}},
    ),
]

# The two lists above are read by run(); the records themselves live below so
# that the assertions stay readable.

if __name__ == "__main__":
    raise SystemExit(run())
