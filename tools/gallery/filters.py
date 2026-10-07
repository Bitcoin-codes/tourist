#!/usr/bin/env python3
"""Decide whether a Commons file may be shown as a photograph of a given place.

The hard part of building an image gallery for a travel site is not finding
pretty pictures of Ghana. It is refusing the ones that merely *mention* the place.
A search for "Cape Coast Castle" returns the castle, a bronze sculpture of a
castle, a 1790 engraving of a castle, a Dutch archive photograph captioned "the
Netherlands and the world", and a photograph of the Dutch town called Cape
Coast. All five match the query. Only one is a photograph of Cape Coast Castle.

Nothing here looks at the picture. Composition scoring is deliberately not used
to decide *what* a photo shows, because a rendering-based score cannot tell a
fort from a plate of food -- a picture of the wrong subject scores as perfectly
as a picture of the right one. Every rule below reads only the title, the
categories and the description, which is why they can be unit-tested exhaustively
against the known bad answers.

The bias throughout is toward false acceptance, never false rejection. A rule
that is unsure lets the file through to a human. The cost of a wrong photo in a
gallery is a visitor being told Cape Coast Castle looks like something else; the
cost of an over-strict rule is a gallery that stays empty, and an empty gallery
is indistinguishable from "this place has no photographs on Commons".

Vocabulary and stemming
-----------------------
All matching is done on stems, because "castles" and "castle" must be the same
token. The vocabulary sets below are written in their natural, readable form
("colobus", not "colobu") and stemmed once at import into the `_STEMS` lookup.
Writing them pre-stemmed by hand is how "colobus" ends up silently failing to
match: the set looks right and the comparison never fires.

Rule entry points, all pure functions of (record, entity) -> reason string:

    is_photograph      is this a photograph at all?
    location_verdict   is it in the right country and the right place?
    distinctive_tokens which words of a place's name actually identify it
    other_subject      is the file about something other than the place
    place_conflicts    does a word in the metadata name more than one place
    screen             all of the above, in the order they must run

`test_filters.py` pins each rule to the specific wrong photograph that motivated
it, and is the only place that knows the intended behaviour.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable

# --------------------------------------------------------------------------
# text normalisation
# --------------------------------------------------------------------------
_WORD_RE = re.compile(r"[a-z0-9]+")

_PLURAL_SUFFIXES = ("sses", "shes", "ches", "xes", "zes", "ses")


def _words(text: str) -> list[str]:
    """Lowercase word tokens, accent-folded, punctuation dropped.

    Commons titles and categories are dense with punctuation -- commas, brackets,
    full stops -- and that punctuation never carries meaning for matching while
    carrying a great deal for false positives.
    """
    if not text:
        return []
    folded = unicodedata.normalize("NFKD", text)
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    return _WORD_RE.findall(folded.lower())


def _stems(words: Iterable[str]) -> set[str]:
    """Crude, deliberately shallow stemming, case-insensitive.

    Not Porter, and that is a decision rather than a shortcut: the only job here
    is to make "castles" and "castle" one token. A real stemmer would also merge
    words that genuinely differ, and every one of those merges is a rejection
    that cannot be explained to the person looking at the picture.

    Lowercasing here rather than at each call site is deliberate. Vocabulary is
    written in the case that reads best -- "Ghanaian", "CC BY-SA" -- and a
    vocabulary set that is not folded to the same case as the text it is matched
    against produces a rule that silently never fires. That is exactly what
    happened to the country list: "Guyana" and "guyana" are different strings,
    the country check passed everything, and the suite caught it.
    """
    out: set[str] = set()
    for word in words:
        word = word.lower()
        if len(word) > 4 and word.endswith(_PLURAL_SUFFIXES):
            word = word[:-2]
        elif len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]
        # Single characters are dropped. They come from possessives and
        # abbreviations -- "Chief's Palace" and "St. George's Castle" both yield
        # a bare "s" -- and a one-letter token that happens to appear in two
        # names is a coin flip, not evidence.
        if len(word) > 1:
            out.add(word)
    return out


def _keys(text: str) -> set[str]:
    """Stemmed word tokens of a string, for phrase matching."""
    return _stems(_words(text))


def _norm(text: str) -> str:
    """Lowercase, accent-folded, single-spaced, for phrase matching.

    A phrase list cannot be matched by intersecting token sets. FOREIGN_PLACES
    holds whole phrases, and "cape coast guyana" stems to {cape, coast, guyana} --
    so intersecting it against the text of a photograph of Cape Coast Castle
    matches on "cape" and rejects the right photograph. Likewise "coat of arms"
    matches every caption containing the word "of". Phrases are therefore matched
    as phrases; only single words are matched by token intersection.
    """
    if not text:
        return ""
    folded = unicodedata.normalize("NFKD", text)
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    return " ".join(_WORD_RE.findall(folded.lower()))


def _has_phrase(haystack: str, phrase: str) -> bool:
    """Whole-word containment of a phrase in text.

    Both sides are normalised. Normalising only the needle searches a
    capitalised title for a lowercase pattern and finds nothing, which looks
    exactly like "the phrase is absent" and quietly turns the rule off.
    """
    text = _norm(haystack)
    needle = _norm(phrase)
    if not needle:
        return False
    return re.search(rf"\b{re.escape(needle)}\b", text) is not None


def _stem_set(words: Iterable[str]) -> set[str]:
    """Stem a vocabulary list once, at import, so lookups are exact."""
    return _stems(words)


# --------------------------------------------------------------------------
# vocabulary
# --------------------------------------------------------------------------

# Words that describe a *kind* of thing rather than a particular one. "Fort
# William" must not be satisfied by the word "fort", and a photograph of any
# botanical garden is not a photograph of Aburi Botanical Gardens.
GENERIC = set(
    """
    adventure africa attraction beach bridge building castle center centre
    church city climate college corporation culture dam district estate
    factory farm forest fort gallery garden gate hall historic historical
    hospital hotel house island lake library lighthouse market memorial monument
    mosque museum national nature office palace park place port region resort
    restaurant river road rock school square stadium state statue store street
    temple tour town tower university valley village waterfall west zoo
    botanical harbour harbor creek bay hill hills grove gardens beaches
    castles forts ruins site sites view photo photos picture pictures
    reserve reserves resource entrance
    """.split()
)

# The site is a guide to Ghana. A caption naming any other country is a different
# place, however strongly it also names ours -- "Cape Coast, Guyana" and "Cape
# Coast, Ghana" differ by one word and by an ocean.
#
# Written as a block of text rather than a set literal purely so it can be read
# and diffed; it is stemmed at import like every other vocabulary. It is a
# complete country and demonym list, not a curated selection, because the
# selection approach is what let Guyana through -- see FOREIGN_PLACES below.
#
# Two rules govern what goes in here.
#
#  * This block is DATA, not code. It is one triple-quoted string split on
#    whitespace, so a '#' line inside it is not a comment: it is vocabulary.
#    A comment written inside these quotes once made "Accra" a foreign country
#    and "National" one too, and rejected every correct photograph in the file.
#
#  * Name each country in the form a caption uses. Most entries are demonyms
#    ("Thai", "Togolese", "Scottish"), and a demonym does not match the country
#    it belongs to -- so the country form is listed as well: Thailand, Togo,
#    Scotland. Half of the list was missing both forms entirely, which is why
#    "National Theatre Budapest" was checked against "Hungarian" and passed,
#    and "Isle of Wight, England" was checked against nothing at all, because
#    England was not here and neither was Japan.
#
# Single words only. A country spelled as two words is matched as a phrase in
# FOREIGN_PLACES instead: "United Kingdom" reduced to tokens makes "united"
# foreign, and every United Nations photograph taken in Accra is then a
# photograph of somewhere else.
_COUNTRIES = """
    Afghanistan Albania Algeria Andorra Angola Argentina Armenia Australia
    Austria Azerbaijan Bahamas Bahrain Bangladesh Barbados Belarus Belgium
    Belize Benin Bhutan Bolivia Bosnia Botswana Brazil Brunei Bulgaria
    Burkina Burundi Cambodia Cameroon Canada Chad Chile China Colombia
    Comoros Congo Croatia Cuba Cyprus Czechia Czech Denmark Djibouti Dominica Ecuador
    Egypt Eritrea Estonia Eswatini Ethiopia Fiji Finland France Gabon Gambia
    Georgia Germany Ghanaian Greece Grenada Guatemala Guyana Haitian
    Honduras Hungary Iceland India Indonesian Iran Iraq Ireland Israel Italy
    Laos Latvia Lebanon Lesotho Liberian Libya Liechtenstein Lithuania
    Luxembourg Madagascar Malawi Malaysia Maldives Mali Malta Mauritania
    Mauritius Mexico Micronesia Moldova Monaco Mongolia Montenegro Morocco
    Mozambique Myanmar Namibia Nauru Nepal Netherlands Nicaraguan Niger
    Nigeria Norwegian Oman Pakistan Palau Palestinian Panama Paraguayan Peru
    Philippine Poland Portuguese Qatar Romanian Russian Rwandan Salvadoran
    Samoan Saudi Scottish Senegal Serbian Seychelles Singapore Slovak Slovenia
    Solomon Somali Spanish Sudanese Suriname Swedish Swiss Syrian Taiwanese
    Tajik Tanzanian Thai Togolese Tonga Tunisian Turkish Turkmenian Tuvaluan
    Ugandan Ukrainian Uruguayan Uzbek Vanuatu Venezuelan Vietnamese Yemen
    Zambian Zimbabwean
    England Scotland Wales Japan Korea Thailand Togo Jamaica Jordan Kazakhstan
    Kenya Kuwait Haiti Indonesia Liberia Nicaragua Paraguay Portugal Romania
    Russia Rwanda Samoa Serbia Slovakia Somalia Spain Sweden Switzerland Syria
    Taiwan Tanzania Trinidad Tunisia Turkey Turkmenistan Tuvalu Uganda Ukraine
    Uruguay Uzbekistan Vatican Venezuela Vietnam Zambia Zimbabwe Norway
"""
# "Guinea" and "Ghanaian" are removed deliberately. "Ghanaian" describes our own
# photographs. "Guinea" cannot decide anything: it is a country, it is the old
# regional name for the whole Gold Coast, and it is half of "Papua New Guinea",
# so a caption using it is ambiguous rather than foreign. Dropping it recovered
# twelve candidate photographs of Osu Castle that were correct.
FOREIGN = set(_COUNTRIES.split()) - {"Ghana", "Ghanaian", "Guinea", "Guinean"}

# Places outside Ghana that turn up in real search results for Ghanaian subjects
# and that a country check alone would not catch, because the caption names a
# region or a namesake rather than a country. This is a short, observed list
# rather than a gazetteer: it catches mistakes that have actually happened, and
# a name absent from it means "no opinion", never "correct". Add to it when a
# wrong answer turns up -- that is the only way this list should ever grow.
#
# These are PHRASES and are matched as phrases. Splitting them into words and
# intersecting token sets matches "cape coast guyana" against any photograph of
# Cape Coast, on the word "cape".
FOREIGN_PLACES = [
    # Dutch colonial-era prints catalogued by their Dutch names, which mention
    # a Dutch fort rather than the Ghanaian one being photographed.
    "fort gehu", "fort gheu", "fort zuid", "fort oranje", "fort zeelandia",
    # Castles and forts in the wider Atlantic world sharing a Ghanaian name.
    "fort alfred south carolina", "fort charles south carolina",
    "fort william jamaica", "fort charles jamaica", "fort hunt jamaica",
    "morant bay", "fort den hermen", "fort goede hoop suid",
    # Suriname and Curacao, close in name to Elmina and Cape Coast.
    "paramaribo", "willemstad", "curacao", "suriname", "demerara",
    "berbice", "esseibo", "georgetown guyana",
    # Cape Coast is also a parish in Guyana; Elmina a neighbourhood in
    # Paramaribo. Both appear in captions about the wrong continent.
    "cape coast guyana", "cape coast belize",
    "elmina suriname", "elmina guyana",
    # Namesakes outside Ghana.
    "bibiani sierra leone",
    # Places that were actually installed as Ghanaian destinations and had to be
    # removed by hand, one entry per wrong answer -- "Fort Victoria" chose the
    # Isle of Wight three times and Vancouver Island once, "National Theatre"
    # chose London four times, Budapest and Bangkok, "Fort Royal" chose Lokrum,
    # and "Fuller Falls" chose Bellows Falls, Vermont. A city is matched here
    # rather than in _COUNTRIES because no city belongs to a country list, and
    # these were never going to be caught by one.
    "isle of wight", "london", "budapest", "bangkok", "lokrum",
    "vancouver island", "bristol", "leith", "bellows falls", "vanadzor",
    "meguro", "tokyo", "fiji", "fort lauderdale", "royal fort gardens",
    "sui-ho", "shing mun", "sui wo",
    "ambon", "sint eustatius", "st eustatius",
    # "Czech National Theatre (1927)" scored 3 on the national-theatre name and
    # was the only photograph that destination had: an illustration of the
    # Prague theatre reprinted in an American student magazine. "Czech" now
    # stops the title and "Prague" the category it sits in, and the two spellings
    # of the country live in _COUNTRIES alongside this.
    "prague",
    # Countries spelled as two words, so they cannot go in _COUNTRIES without
    # its single-word check swallowing half of every unrelated caption.
    "ivory coast", "sierra leone", "sri lanka", "south africa", "new zealand",
    "united kingdom", "great britain", "united states", "costa rica",
    "saudi arabia", "czech republic", "dominican republic", "south sudan",
    "north macedonia", "papua new guinea", "central african republic",
    "burkina faso", "cape verde",
]

# Markers that identify a photograph's subject as a ship rather than a building.
# A vessel word alone is not enough: "Fort William and the boats" is a
# photograph of a fort. These are the words only a ship has.
SHIP_SUBJECT = set(
    """
    hms hmss sss rms uss mv anchor anchored moored mooring mast masts sail
    sails deck decks crew captain naval navy warship dockyard shipyard afloat
    pennant rigging bowsprit stern
    """.split()
)
S_SHIP_SUBJECT = _stem_set(SHIP_SUBJECT)

# Name prefixes that only a warship carries. Checked at the start of the title
# only, because "Fort William with HMS Test astern" is a photograph of a fort.
SHIP_PREFIXES = ["hms", "hmss", "ss", "rms", "uss", "mv", "sv", "hv"]

# Categories that file a picture as a ship. Blunter than the title check, but a
# category like "Ships of the United Kingdom" is never about a building.
SHIP_CATEGORIES = [
    "ships of",
    "warships of",
    "merchant ships of",
    "naval vessels of",
    "sailboats of",
]

# Categories that describe a file's *filing* rather than its subject. The Dutch
# national archives stamp their whole collection "The Netherlands and the world",
# which contains the word "world" and nothing else useful, and which every
# Ghanaian fort photograph in their hands carries. Scanning for "netherlands"
# before stripping this rejects most of the best archive photographs of Ghana's
# forts -- the ones nobody else has.
PROVENANCE_NOISE = set(
    """
    the netherlands and the world netherlands and the world african studies
    colonial colonialism dutch colonial image from the rce rijksmuseum
    nederlands fotomuseum nationaal archief archives archive archival
    uploaded with own work own work
    """.split()
)

# A photograph has to be a photograph. Note what is absent: "museum" and
# "archives" are not here and never should be. Excluding them emptied real
# galleries -- Fort Apollonia, the National Museum and the International Slavery
# Museum are all photographed from the inside, and Commons files those
# photographs under museum and archive categories. A rule that costs a true
# photograph has gone too far.
NOT_A_PHOTO = set(
    """
    painting paintings drawing drawings sketch sketches engraving engravings
    etching lithograph lithographs woodcut map maps diagram chart
    portrait portraits poster stamp stamps banknote banknotes coin coins medal
    medals heraldry logo seal screenshot scan facsimile manuscript letter
    illustration newspaper postcard brochure advertisement blazon iconography
    sculpture sculptures bronze statue statues plaque plaques inscription
    inscriptions tablet tablets sarcophagus
    """.split()
)

# Multi-word terms that share a function word with ordinary prose, so they must
# be matched as whole phrases. "coat of arms" as a token set is {coat, of, arm}
# and matches every caption that says "of".
NOT_A_PHOTO_PHRASES = [
    "coat of arms",
    "map of",
    "plan of",
    "portrait of",
    "print of",
    "flag of",
    "photo of a photo",
    "photograph of a photograph",
    "old map",
    "old photograph",
    # Museum and library accession numbers, where the subject is an object in a
    # collection rather than a place. Six photographs were installed for
    # "Princess Town Beach" this way -- a Met Museum painting, a Mughal album
    # page, a sarcophagus, a Japanese woodblock print -- and five more for
    # "Fuller Falls", all of them carrying the same accession stem. The hash
    # after the prefix is what makes the phrase safe: a Ghanaian photograph
    # with "met" in its caption does not have "met dp" followed by a number.
    "met dp",
    "dpla",
    "folio from the",
    "from chapter ",
]

# Categories whose contents are not photographs of a place. "Museums" and
# "archives" are deliberately absent, for the reason above. Each entry is a whole
# concept: a category is rejected when it contains all the words of one of these,
# so "Paintings of the Volta Region" is caught by "paintings" and "Forts in
# Ghana" is not.
NOT_A_PHOTOGRAPH_CATEGORY = [
    "paintings",
    "sculptures",
    "statues",
    "stamps of ghana",
    "coins of ghana",
    "banknotes of ghana",
    "maps of ghana",
    "historical maps",
    "signs",
    "signage",
    "graffiti",
    "posters",
    "filmed in ghana",
]

# Subjects that are never the place, even when the caption names it. Narrower
# than GENERIC on purpose: GENERIC exists to stop *kind* words from identifying a
# place, and using it here would reject "Fort Christiansborg" as an other-subject
# "fort" for a destination called Osu Castle. A word has to be plainly about
# something else to disqualify.
SUBJECT_MISMATCH = set(
    """
    colobus colobuses monkey monkeys baboon chimpanzee gorilla lemur crocodile
    hippo lizard snakes snake butterfly beetles insect insects reptile
    portrait portraits logo logos stamp stamps banknote banknotes coin coins
    medal medals seal flags flag poster posters timetable menu menus
    brochure passport visa mural graffiti statue statues
    cake cakes scissors ribbon bunting
    pda laptop cessna glider hangglider kite kites
    """.split()
)
S_SUBJECT_MISMATCH = _stem_set(SUBJECT_MISMATCH)

# Subject matter that is never the place itself, even when the caption names it.
ANIMAL_SUBJECT = set(
    """
    monkey monkeys colobus colobuses ape apes chimpanzee baboon bird birds
    butterfly butterflies snake snakes lizard lizards fish elephant elephants
    buffalo antelope animal animals insect insects reptile reptiles flora
    fauna plant plants flower flowers tree trees fruit food dish dishes
    crocodile hippo gorilla lemur
    """.split()
)

# Word pairs that cannot both be true of one place. Catches a caption naming the
# right town and the wrong building. The check requires a *distinctive* word from
# each side -- see `_contradiction` for why that qualification is not optional.
CONTRADICTIONS: tuple[tuple[str, str], ...] = (
    ("cape coast", "elmina"),
    ("cape coast", "fort william"),
    ("fort william", "anomabu"),
    ("fort william", "cape coast"),
    ("accra", "cape coast"),
    ("kumasi", "accra"),
    ("elmina", "anomabu"),
    ("fort amsterdam", "fort batenstein"),
    ("fort nassau", "fort good hope"),
    ("fort metal cross", "fort betase"),
    ("fort brittany", "fort william"),
    ("fort william", "fort batenstein"),
    ("sekondi", "takoradi"),
    ("lake volta", "lake bosomtwe"),
    ("lake volta", "lake tano"),
    ("bui", "volta"),
)

# A building that changed its name. A photograph of Osu Castle is a photograph of
# Fort Christiansborg, and rejecting it because "Christiansborg" is not in the
# name is exactly the failure this table exists to prevent.
ALTERNATIVE_NAMES: dict[str, set[str]] = {
    "osu castle": {"christiansborg", "christiansburg"},
    "fort christiansborg": {"osu castle", "osu"},
    "fort christiansborgh": {"osu castle", "osu"},
    "fort william anomabu": {"anomabu fort", "anomabu"},
    "fort william cape coast": {"cape coast fort", "cape coast"},
    "fort st george": {"elmina castle", "st georges", "george"},
    "fort st jago": {"hill fort", "st jago", "jago"},
    "fort st anthony": {"axim fort", "anthony", "axim"},
    "fort metal cross": {"metal cross", "keta"},
    "fort betase": {"betase", "sekondi"},
    "fort brittany": {"brittany fort", "amanfei", "amanfie"},
    "fort batenstein": {"batenstein", "princes town", "princetown", "butre"},
    "fort gross friedrichsburg": {"friedrichsburg", "keta", "kwitta"},
    "fort good hope": {"good hope", "keta", "kwatta"},
    "fort nassau": {"nassau", "mouri"},
    "fort amsterdam": {"amsterdam", "abandzi", "keta"},
    "fort apollonia": {"apollonia", "benya"},
    "fort prinstenstein": {"prinstenstein", "princes town"},
    "fort patience": {"patience", "tadi", "tadu", "apam"},
    "fort orange": {"orange", "keta", "kwitta"},
    "fort indigo": {"indigo", "fetu", "fetuase"},
    "fort buffalo": {"buffalo", "tanzua"},
    "fort klapperkop": {"klapperkop", "kwamfu"},
    "fort plakot": {"plakot", "aflao"},
    "fort keta": {"keta", "kwitta", "kwatta"},
    "fort osu": {"osu", "christiansborg"},
    "castro fort": {"castro", "elmina", "shama"},
    "fort san sebastian": {"san sebastian", "shama", "lator"},
    "fort coromantee": {"coromantee", "elmina", "shama"},
    "fort don dave": {"don dave", "bibiani"},
    "fort george": {"george", "bibiani"},
    "fort sidney": {"sidney", "shama"},
    "fort st charles": {"st charles", "anco"},
    "fort carlos": {"carlos", "shama"},
    # The official name of a place known by its short one, rather than a rename.
    # The Centre for National Culture, Accra *is* the Accra Arts Centre -- the
    # craft bazaar on John Evans Atta Mills High Street -- and Commons describes
    # its files as "the National Centre for Culture and Arts in Accra", wording
    # that scores 1 on a description alone and was therefore dropped for every
    # one of thirty-six photographs of the market itself.
    #
    # "Accra" is carried in both phrases because the data also lists the Kumasi
    # Centre for National Culture. The phrases are matched as token sets, so
    # without it a Kumasi caption naming its centre would score 2 here and be
    # installed as a photograph of the Accra market.
    "accra arts centre": {
        "centre for national culture accra",
        "national centre for culture and arts accra",
    },
    # A destination named by more words than anyone typed to upload it.
    # `gsrsearch` matches every word of the query, so "Komfo Anokye Sword Site
    # Ghana" is four words that co-occur in no file description on Commons, and
    # the entity comes back with no candidate at all -- nothing judged unfit,
    # nothing even seen. The short form is the name the files carry: the sword
    # in Kumasi is "Komfo Anokye" wherever it is written, the kente village is
    # "Adanwomase", and Akwapim is spelled with a p by half the country.
    #
    # Both halves have to move together, and they do: `alias_terms` in select.py
    # queries these phrases, and the matching below accepts a file that names
    # only them. Querying without matching finds the photograph and then rejects
    # it for not naming the destination; matching without querying screens a
    # candidate that was never returned.
    #
    # The tight ones are kept tight on purpose. "bomfobiri" is the sanctuary's
    # own village; "techiman" alone would be every photograph in the district,
    # so it stays welded to "museum".
    "komfo anokye sword site": {"komfo anokye", "anokye sword"},
    "prempeh ii jubilee museum": {"prempeh ii museum", "manhyia palace museum"},
    "adanwomase kente village": {"adanwomase kente", "adanwomase"},
    "nchiraa waterfalls": {"nchiraa"},
    "ahwiaa woodcarving village": {"ahwiaa woodcarving", "ahwiaa"},
    "techiman heritage & culture museum": {"techiman museum"},
    "nania slave route": {"nania slave"},
    "bunso honey & palm wine eco-park": {"bunso eco park", "bunso"},
    "lake volta shore at dambai": {"dambai volta", "dambai"},
    "gambaga lookout & nahiley escarpment": {"gambaga escarpment", "nahiley"},
    "goaso cocoa & forest belt": {"goaso cocoa", "goaso"},
    "bomfobiri wildlife sanctuary": {"bomfobiri"},
    "akuapim ridge": {"akwapim ridge", "akwapim"},
    "gushiegu local textile centre": {"gushiegu textile", "gushiegu"},
    "tengzug shrine complex": {"tengzug"},
    "sirigu pottery centre": {"sirigu pottery", "sirigu"},
    "asumura rockfowl sanctuary": {"asumura rockfowl", "asumura"},
}

# Ships share names with the forts. "Fort William" photographs include the
# man-of-war Fort William; so do several forts' boats. If a caption's subject is
# a vessel, it is not the fort. "man of war" is deliberately absent -- it stems
# to include "of", and this list is matched by token intersection. The
# ship-prefix and ship-category checks cover the same ground.
VESSEL_SUBJECT = set(
    """
    ship ships vessel vessels boats boat schooner brig frigate galleon barge
    ferry canoe canoes yacht trawler liner steamer sloop cutter
    """.split()
)

# Satellite and aerial imagery is a map, not a photograph of a place, and it
# reads as noise beside ground-level pictures in the same strip.
SATELLITE = set(
    """
    satellite landsat sentinel modis orthophoto orthoimage nasa
    """.split()
)

# Phrases, for the same reason "aerial survey" had to leave the set above.
SATELLITE_PHRASES = ["aerial survey", "aerial imagery", "true colour", "satellite view"]

# Pre-photographic works. A four-digit year before 1839 is decisive on its own:
# no photograph of that can exist.
_BEFORE_1839_RE = re.compile(r"\b(1[0-7]\d\d|1[789]\d\d)\b")
_MEDIA_WORD_RE = re.compile(
    r"\b(daguerreotype|tintype|cabinet card|watercolou?r|"
    r"nineteenth[- ]century (?:engraving|print|drawing))\b",
    re.IGNORECASE,
)

# Collection accession numbers, which name an object in a store rather than a
# place. The Met's "DP" followed by digits is the common one; the Brooklyn
# Museum files objects as five digits, a space and three or four more.
#
# This has to be a pattern and cannot be a phrase. `_norm` breaks "DP267661"
# into the words "dp" and "267661", so a phrase of "met dp" searches for a
# boundary that does not exist between the p and the 2 -- the rule reads
# correct-looking titles as plain English and matches none of them.
_ACCESSION_RE = re.compile(r"\bdp\d{4,}\b|\b\d{5} \d{3,4}\b")

# Two countries joined by a hyphen are naming the border between them, not a
# destination: "Tagbo Falls flows from the Ghana-Togo range" is a Ghanaian
# photograph and Togo is a direction in it. Stripped before the country check,
# because adding the neighbouring countries to that check found real mistakes
# and this was the one correct photograph it took with them. A comma does not
# get the same pardon -- "Cape Coast, Guyana" is the mistake the country rule
# exists for.
_BORDER_RE = re.compile(r"\bghana\s*[-\u2010-\u2015]\s*\w+\b|\b\w+\s*[-\u2010-\u2015]\s*ghana\b", re.IGNORECASE)

# The bounding box every destination in this data sits in, generously padded
# for coastal and border slack. Coordinates are the one signal that cannot be
# argued with: a caption may name a shared place and a category may be copied
# in error, but a geotag of 66.3 N, 128.6 W is Fort Good Hope in the Northwest
# Territories and nothing else. Three live photographs were found this way --
# an aerial view of Cape Three Points in New South Wales, the Water Fort in
# Sint Eustatius, and Fort Good Hope in Canada -- none of which any wording in
# their captions would have caught.
#
# If this site ever lists somewhere other than Ghana, this has to become
# per-entity rather than global.
_GHANA_BOX = (3.5, 12.0, -4.5, 2.0)  # south, north, west, east
_COORD_CATEGORY_RE = re.compile(r"\((\d+)\s*°\s*([NS])[^)]*?(\d+)\s*°\s*([EW])")


def _coordinates(record: dict[str, Any]) -> tuple[float, float] | None:
    """Latitude and longitude, from the geotag or from the coordinate category.

    Both are read because Commons carries them in two places: EXIF-derived
    GPS fields for files that have them, and a category of the form
    "(34° S, 151° E)" for files whose coordinates were never written into
    their metadata. The wrong-place aerial photograph had only the second.
    """
    ext = record.get("extmetadata") or {}
    try:
        return float(ext["GPSLatitude"]), float(ext["GPSLongitude"])
    except (KeyError, TypeError, ValueError):
        pass
    match = _COORD_CATEGORY_RE.search(" ".join(record.get("categories") or []))
    if not match:
        return None
    lat = float(match.group(1)) * (1 if match.group(2) == "N" else -1)
    lon = float(match.group(3)) * (1 if match.group(4) == "E" else -1)
    return lat, lon

# --------------------------------------------------------------------------
# stemmed lookup tables -- built once, at import
# --------------------------------------------------------------------------
S_GENERIC = _stem_set(GENERIC)
S_FOREIGN = _stem_set(FOREIGN)
S_FOREIGN_PLACES = _stem_set(FOREIGN_PLACES)
S_PROVENANCE_NOISE = _stem_set(PROVENANCE_NOISE)
S_NOT_A_PHOTO = _stem_set(NOT_A_PHOTO)
S_NOT_A_PHOTO_CATEGORY = tuple(
    _keys(entry) for entry in NOT_A_PHOTOGRAPH_CATEGORY
)
S_ANIMAL_SUBJECT = _stem_set(ANIMAL_SUBJECT)
S_VESSEL_SUBJECT = _stem_set(VESSEL_SUBJECT)
S_SATELLITE = _stem_set(SATELLITE)

# Contradiction pairs reduced to the distinctive word of each side. Kept as a
# precomputed list of stem sets so the hot path does no set arithmetic on words.
_CONTRADICTION_KEYS: tuple[tuple[set[str], set[str]], ...] = tuple(
    (_keys(left) - S_GENERIC, _keys(right) - S_GENERIC)
    for left, right in CONTRADICTIONS
)

# Every alternative name, flattened, so a lookup does not walk the whole table.
_ALT_NAMES: dict[frozenset[str], set[frozenset[str]]] = {
    frozenset(_keys(name)): {frozenset(_keys(alt)) for alt in alternatives}
    for name, alternatives in ALTERNATIVE_NAMES.items()
}


# --------------------------------------------------------------------------
# inputs
# --------------------------------------------------------------------------
def _title(record: dict[str, Any]) -> str:
    return (record.get("title") or "").split(":", 1)[-1].rsplit(".", 1)[0]


def _description(record: dict[str, Any]) -> str:
    from commons import field

    return field(record.get("extmetadata", {}), "ImageDescription")


def _category_text(record: dict[str, Any]) -> str:
    return " ".join(record.get("categories", []) or [])


def _subject_text(record: dict[str, Any]) -> str:
    """Title and categories only.

    The description is prose written by whoever uploaded the file, and it will
    mention anything at all -- a region, a date, a related building. Reading it
    as the subject is how "The basilica at Navrongo, Upper West Region" got
    rejected for containing the word "region".
    """
    return f"{_title(record)} {_category_text(record)}"


def _all_text(record: dict[str, Any]) -> str:
    """Everything the filters may read, folded to one string."""
    return f"{_title(record)} {_description(record)} {_category_text(record)}"


def _category_key(category: str) -> set[str]:
    """'Category:Forts in Ghana' -> {'fort', 'ghana'}."""
    return _keys(category)


def _is_photo_extension(record: dict[str, Any]) -> bool:
    title = (record.get("title") or "").lower()
    # Vector and lossless formats are rejected outright: they are not
    # photographs, and every one seen on Commons for these subjects is a map, a
    # coat of arms or a logo.
    return not title.endswith(
        (".svg", ".png", ".gif", ".tif", ".tiff", ".webp", ".pdf", ".djvu", ".xcf")
    )


# --------------------------------------------------------------------------
# rule: is this a photograph at all?
# --------------------------------------------------------------------------
def is_photograph(record: dict[str, Any], entity_name: str = "") -> str:
    """Return a rejection reason, or "" if this is a usable photograph."""
    if not _is_photo_extension(record):
        return "not-a-photo: non-raster format"

    text = _all_text(record)
    keys = _keys(text)

    for word in sorted(keys & S_NOT_A_PHOTO):
        return f"not-a-photo: '{word}'"
    for word in sorted(keys & S_SATELLITE):
        return f"satellite: '{word}'"
    for phrase in SATELLITE_PHRASES:
        if _has_phrase(text, phrase):
            return f"satellite: phrase {phrase!r}"

    for phrase in NOT_A_PHOTO_PHRASES:
        if _has_phrase(text, phrase):
            return f"not-a-photo: phrase {phrase!r}"
    if _ACCESSION_RE.search(_norm(text)):
        return "not-a-photo: museum accession number"

    for category in record.get("categories", []) or []:
        category_keys = _category_key(category)
        for denied in S_NOT_A_PHOTO_CATEGORY:
            if denied and denied <= category_keys:
                return f"not-a-photo: category '{category.rsplit(':', 1)[-1]}'"

    # Contradictions are checked against the title only. A description is prose
    # and will mention related places -- an Osu Castle photograph whose
    # description links to Cape Coast is not thereby a photograph of Cape Coast,
    # and title-only checking stopped 21 of 56 correct Osu Castle candidates
    # being thrown away by the pair ("accra", "cape coast").
    title_keys = _keys(_title(record))
    for left, right in _CONTRADICTION_KEYS:
        if left & title_keys and right & title_keys:
            return "contradiction: two different places named in one title"

    if _is_pre_photographic(record):
        return "before-photography: describes a work made before photography"
    return ""


def _is_pre_photographic(record: dict[str, Any]) -> bool:
    """True when the file is about something made before photography existed."""
    text = _all_text(record)
    for year in _BEFORE_1839_RE.findall(text):
        if int(year) < 1839:
            return True
    return bool(_MEDIA_WORD_RE.search(text))


# --------------------------------------------------------------------------
# rule: is it the right place?
# --------------------------------------------------------------------------
def location_verdict(record: dict[str, Any], entity_name: str) -> str:
    """Return a rejection reason, or "" if the file is plausibly in this place.

    `entity_name` is the destination's display name, e.g. "Fort Batenstein".
    """
    if not _is_photo_extension(record):
        return "not-a-photo: non-raster format"

    point = _coordinates(record)
    if point is not None:
        lat, lon = point
        # (0, 0) is what a camera writes when it has no fix. It is an absent
        # geotag, not a photograph in the Gulf of Guinea.
        if not (abs(lat) < 0.01 and abs(lon) < 0.01):
            south, north, west, east = _GHANA_BOX
            if not (south <= lat <= north and west <= lon <= east):
                return f"geotag: {lat:.4f}, {lon:.4f} is outside Ghana"

    # The foreign-country scan must not see provenance stamps, or the Dutch
    # archive photographs of Ghanaian forts -- most of the good ones -- are
    # rejected for naming the country that photographed them.
    categories = _keys(_category_text(record)) - S_PROVENANCE_NOISE
    country_text = " ".join(
        (_title(record), _description(record), " ".join(sorted(categories)))
    )
    country_text = _BORDER_RE.sub(" ", country_text)
    keys = _keys(country_text)
    words = set(_words(country_text))

    for foreign in sorted(keys & S_FOREIGN):
        return f"foreign: '{foreign}'"
    for place in FOREIGN_PLACES:
        if _has_phrase(country_text, place):
            return f"foreign-place: {place!r}"

    # A ship that shares a fort's name is not the fort. The signal is a ship
    # prefix at the start of the title, because that is how a ship is named and
    # no building's name begins with one: "HMS Fort William at anchor" is a
    # man-of-war, while "Fort William, with HMS Test in the foreground" is a
    # fort and is left alone. A ship-filing category is the second, blunter
    # signal. A vessel word on its own is not enough -- "Fort William and the
    # boats" is a photograph of the fort.
    title_keys = _keys(_title(record))
    title_norm = _norm(_title(record))
    starts_with_prefix = any(
        title_norm == prefix or title_norm.startswith(f"{prefix} ")
        for prefix in SHIP_PREFIXES
    )
    ship_category = any(
        _has_phrase(_category_text(record), phrase) for phrase in SHIP_CATEGORIES
    )
    if starts_with_prefix or ship_category or (
        (title_keys & S_VESSEL_SUBJECT) and (title_keys & S_SHIP_SUBJECT)
    ):
        return "vessel: subject is a ship, not the place"

    if not _names_place(record, entity_name):
        return f"off-subject: no mention of {entity_name!r}"
    return ""


def _names_place(record: dict[str, Any], entity_name: str) -> bool:
    """Is the place named in the title, the categories, or the description?

    Three ways to qualify, tried in order, and all three are needed:

    1. **The whole name appears.** The strongest signal, and the only one
       available for a place whose every word is shared with something else.
    2. **An alternative name appears.** Osu Castle is Fort Christiansborg.
    3. **A distinctive word appears.** Not just any word of the name: for Fort
       William Anomabu that is "anomabu" alone, because "fort" describes every
       fort in the country and "william" is shared with the second Fort William
       in the data. A caption reading only "Fort William" therefore does not
       qualify, which is the point -- it cannot tell us which fort it shows.

    A title match alone is never sufficient, and neither is a name match alone.
    The Navrongo basilica is filed as "Basilica of Our Lady of Seven Sorrows" and
    never says "Navrongo" in its title, so the categories and description have to
    be read too.
    """
    if not _keys(entity_name):
        return True

    for text in (_title(record), _category_text(record), _description(record)):
        if _has_phrase(text, entity_name):
            return True

    everywhere = " ".join(
        (_title(record), _category_text(record), _description(record))
    )
    if _matches_alternative(_keys(everywhere), _keys(entity_name)):
        return True

    distinctive = distinctive_tokens(entity_name)
    if distinctive and (distinctive & _keys(everywhere)):
        return True
    return False


def _matches_alternative(text_keys: set[str], entity_keys: set[str]) -> bool:
    """True when `text_keys` names the place under another name.

    An entry in `ALTERNATIVE_NAMES` is only consulted when its key refers to
    *this* destination, which means one of the two key sets must be contained in
    the other. Testing for any shared token instead is far too loose: "fort william
    cape coast" shares "cape" and "coast" with "Cape Coast Castle", so a caption
    about Cape Coast would be accepted as naming Fort William Cape Coast, and any
    photograph whose text merely mentioned a cape would pass for either fort.
    """
    for name_keys, alternatives in _ALT_NAMES.items():
        if not (name_keys <= entity_keys or entity_keys <= name_keys):
            continue
        for alt in alternatives:
            if alt <= text_keys:
                return True
    return False



# --------------------------------------------------------------------------
# rule: which words of a name actually identify the place
# --------------------------------------------------------------------------
def distinctive_tokens(name: str) -> set[str]:
    """Stems from a place's name that nothing else in the data also uses.

    A word is dropped when it is generic -- every fort has "fort" -- or when some
    other destination's name contains it. "Fort William" appears twice in the
    data, once for Anomabu and once for Cape Coast, so neither can be identified
    by the words "fort william"; only the town is left, and the town is only
    usable because nothing else is called that.

    The location field is deliberately not consulted. Lake Bosomtwe's location
    is "Lake Bosomtwe", so reading it as a town name strips every word of the
    name and the lake matches nothing at all.

    Two letters is not a name. "Se Yo Cave" reduces to {se, yo} once "cave" is
    removed as generic, and both are ordinary words in a sentence -- in Spanish
    they are among the commonest there are. Six photographs were installed for
    that Ghanaian cave: a Kansas Infantry company from the American Civil War,
    and five Spanish captions, every one of them identifying the place by
    agreeing with "se" or "yo". A three-letter floor drops those two, drops the
    function words "at", "of", "st", "la" and "ii" that the same rule was
    quietly matching on, and costs no entity in the data its entire set of
    identifying words except Se Yo Cave, which had nothing but them.
    """
    tokens = _keys(name) - S_GENERIC
    return {t for t in tokens if t not in _SIBLING_WORDS and len(t) > 2}


_SIBLING_WORDS: set[str] = set()


def load_sibling_map(names: Iterable[str]) -> None:
    """Teach the module which words several destinations share.

    `names` is every destination and festival name in the data. Any word that
    turns up in more than one of them is a word that cannot identify a place on
    its own, so `distinctive_tokens` stops counting on it.

    Called once at the start of a run, before any filtering.
    """
    counts: dict[str, int] = {}
    for name in names:
        for token in _keys(name) - S_GENERIC:
            counts[token] = counts.get(token, 0) + 1
    _SIBLING_WORDS.clear()
    _SIBLING_WORDS.update(token for token, n in counts.items() if n > 1)


def _name_key(name: str) -> str:
    return "".join(sorted(_keys(name)))


# --------------------------------------------------------------------------
# rule: is the file about something else that shares the name
# --------------------------------------------------------------------------
def other_subject(record: dict[str, Any], entity_name: str) -> str:
    """Reject a file whose subject is a different thing that shares the name.

    A word only disqualifies when the destination is not named after it: "Kejetia
    Market" is a market, so the word "market" must not reject it, and neither
    must "monkey" reject the Boabeng Fiema Monkey Sanctuary. A word the
    destination's alternative name accounts for is likewise not a mismatch --
    "Fort Christiansborg" is Osu Castle, not a subject change.
    """
    subject_keys = _keys(_subject_text(record))
    category_keys = _keys(_category_text(record))
    entity_keys = _keys(entity_name)
    explained = _alternative_words(entity_keys)
    for word in sorted(subject_keys & S_SUBJECT_MISMATCH):
        if word in entity_keys or word in explained:
            continue  # the place is named after this thing
        if word in category_keys and word not in _keys(_title(record)):
            continue  # present only as a category, which sets the setting
        return f"other-subject: '{word}'"
    return ""


def _alternative_words(entity_keys: set[str]) -> set[str]:
    """Every word that appears in this entity's name or in an alias of it.

    Used so that a word the caption borrows from an alternative name is not
    mistaken for a change of subject.
    """
    words: set[str] = set()
    for name_keys, alternatives in _ALT_NAMES.items():
        if name_keys & entity_keys:
            words |= set(name_keys)
            for alt in alternatives:
                words |= set(alt)
    return words


# --------------------------------------------------------------------------
# rule: ambiguous place words
# --------------------------------------------------------------------------
def place_conflicts(
    record: dict[str, Any],
    entity_name: str,
    known_places: Iterable[str],
    host_words: Iterable[str] = (),
) -> str:
    """Reject when a word in the *title* names a place other than this one.

    Some words are place names in their own right -- "william", "ada", "keta" --
    and some belong to more than one destination in this data. Such a word is
    ambiguous exactly when it points somewhere that is not the entity being
    assembled.

    Four constraints keep this from eating the gallery, and each one was added
    after watching it reject a correct photograph:

    * **Title only.** A description is prose written by whoever uploaded the file
      and mentions anything. Run over the full text this rule rejected a
      photograph of Cape Coast Castle for the word "slave", because two
      destinations are called "Nania Slave Route" and "Assin Manso Slave River".
      A title, by contrast, names the subject, so an ambiguous title word is real
      evidence of the wrong place.
    * **The entity's own region is never ambiguous.** "Accra" is in the names of
      two Accra destinations, so "Osu Castle, Accra" was rejected as pointing
      somewhere else -- but Osu Castle is in Accra, and the word names where the
      photograph was taken, not what it shows. `host_words` carries the entity's
      region and location for exactly this.
    * **Pointing at several places including this one is not ambiguous**, it is
      merely uninformative. "william" names both Fort Williams, so a caption
      saying "william" tells us nothing about which fort it shows -- but it is not
      evidence of the wrong one either, and rejecting it would empty both
      galleries. So the test is: more than one destination matches the word, and
      this entity is not one of them.
    * **Four characters minimum.** Shorter tokens are almost always fragments
      ("chief's" and "St. George's" both yield a bare "s"), and a fragment that
      lands in two names is a coin flip rather than evidence.
    """
    places = list(known_places)
    if not places:
        return ""
    place_keys = {place: _keys(place) for place in places}
    exempt = _keys(entity_name) | _keys(" ".join(host_words))

    for word in sorted(_keys(_title(record))):
        if word in S_GENERIC or word in exempt or len(word) < 4:
            continue
        hits = [place for place, keys in place_keys.items() if word in keys]
        if len(hits) > 1:
            return f"ambiguous-place: '{word}' names {hits[0]!r} and {hits[1]!r}"
    return ""


# --------------------------------------------------------------------------
# the whole screen, in the order the rules must run
# --------------------------------------------------------------------------
def screen(
    record: dict[str, Any],
    entity_name: str,
    known_places: Iterable[str] = (),
    host_words: Iterable[str] = (),
) -> str:
    """Return the first reason to reject this file for this place, else "".

    Order is deliberate. Cheap and decisive checks first: a file rejected as "not
    a photograph" or "unusable licence" needs no further thought. Subject and
    location run next, and they run on *every* path through the pipeline -- an
    earlier version had a rescue pass that skipped them, and every bad entry
    that survived came out of that pass.

    `host_words` is the entity's region and location, used to stop the ambiguity
    rule rejecting "Osu Castle, Accra" because two other destinations also have
    Accra in their names.
    """
    from commons import licence_of  # keeps this module importable on its own

    verdict = licence_of(record)
    if not verdict["free"]:
        return f"restricted: {verdict['reason']}"

    for check in (
        lambda: is_photograph(record, entity_name),
        lambda: location_verdict(record, entity_name),
        lambda: other_subject(record, entity_name),
        lambda: place_conflicts(record, entity_name, known_places, host_words),
    ):
        reason = check()
        if reason:
            return reason
    return ""
