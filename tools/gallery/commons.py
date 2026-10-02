#!/usr/bin/env python3
"""A polite, cached client for the Wikimedia Commons API.

Everything the gallery pipeline needs from Commons goes through here: searching
for candidate files, reading their categories, and pulling author/licence/source
metadata plus a display-sized thumbnail URL.

Two things this module is careful about
---------------------------------------
1. **We never write a `w` descriptor we cannot honour.** Commons is asked for a
   thumbnail at `THUMB_WIDTH`; the returned `thumburl` is the file we install.
   Anything narrower than that would be a lie in the `srcset`.
2. **Metadata is preserved raw and parsed separately.** `extmetadata` values are
   HTML fragments that vary wildly between uploads. `licence_of()` and
   `artist_of()` normalise them, but the untouched original is kept in the cache
   so a parsing change never means re-downloading anything.

Every response is cached on disk keyed by the request, so re-running the
pipeline after a code change costs no API traffic. Delete the cache directory to
start over.

Licence rules this module implements
------------------------------------
Commons' own `LicenseShortName` is not enough to trust. A file can be tagged
CC BY-SA 4.0 and still carry an uploader note restricting commercial use, and
tagging is not moderated. `licence_of()` therefore returns a verdict, not just a
string, and `RESTRICTED` wins over any free tag -- see `FREE_LICENCE_RE` and
`RESTRICTION_HINTS`.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

# A descriptive User-Agent is required by the Wikimedia API etiquette policy and
# is the only way to get into the cache. Keep it identifiable and contactable.
USER_AGENT = (
    "GhanaTourSiteGallery/1.0 "
    "(build-time image selection for a tourism site; "
    "https://github.com/ ; contact: site owner via repository issues)"
)

API = "https://commons.wikimedia.org/w/api.php"

# The width we ask Commons to render thumbnails at. Everything installed is this
# wide or narrower, which is what lets the frontend promise an 800w hero and a
# 1920w full-size viewer without a single request 404ing.
THUMB_WIDTH = 1920

# One API cache, shared by every script in this pipeline.
#
# It used to be one directory per script -- `gallery-select/api-cache` and
# `gallery-recovery/api-cache` -- which quietly split the cache in half. Search
# fetched 39 responses into its own directory; recovery, run afterwards, opened
# an empty one, found nothing, and reported every installed file as unmatched
# when in fact the metadata for most of them was sitting on disk a few folders
# away. The two never shared what they had learned from Commons, and neither
# could tell that the other had already paid for it.
#
# Cache filenames are the SHA-256 of the request, so the same question always
# lands on the same filename and merging two directories is a plain file copy
# with no possibility of one run's answer overwriting another's.
CACHE_DIR = Path("/tmp/opencode/gallery-cache")

# Licences we are willing to publish under. Anything outside this set is treated
# as unusable, including "no known copyright restrictions" style placeholders
# which in practice usually mean the uploader did not check.
FREE_LICENCE_RE = re.compile(
    r"^(cc[\s\-_]?(by|by[\s\-_]?sa|0|sa)[\s\-_]?\d?\.?0?|public\s*domain|pd[\s\-_]?\w*|gfdl)"
    r"\s*(attribution)?",
    re.IGNORECASE,
)

# Licences that look free but are not, and so must never match the above.
NON_FREE_HINTS = re.compile(
    r"(fair\s*use|non[\s\-_]?free|copyright(?!ed\s+free)|all\s+rights\s+reserved"
    r"|\bnc\b|non[\s\-_]?commercial|no[\s\-_]?derivat|\bnc[\s\-_]?nd\b)",
    re.IGNORECASE,
)

# Uploader notes that restrict a nominally free licence. Checked against the
# free-form metadata fields, because this is where "I give permission for
# non-commercial use only" actually lives.
RESTRICTION_HINTS = re.compile(
    r"(non[\s\-_]?commercial|commercial\s+use|permission\s+(is\s+)?(only|required)"
    r"|contact\s+(me|the\s+(author|uploader|photographer))"
    r"|not\s+free\s+to\s+reproduce|educational\s+use\s+only"
    r"|no\s+derivat|attribution\s+required|ask\s+me\s+first|credit\s+me)",
    re.IGNORECASE,
)

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


class CommonsError(RuntimeError):
    """The API refused us, or answered with something unusable."""


def _plain(value: str) -> str:
    """Strip tags and collapse whitespace, for a human-readable one-liner."""
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", value or "")).strip()


# Wikimedia Commons holds scanned books, manuscripts and archival documents next
# to photographs, and it renders a PDF or DjVu to a perfectly ordinary JPEG of its
# first page. The pixel matcher cannot tell that rendered book page from a
# photograph -- it compares grey levels, and a page of nineteenth-century text is
# grey levels like anything else.
#
# That is not hypothetical. Two photographs installed for Cape Coast Castle were
# matched by pixels to "Studies of nature on the coast of Arran" and "A Voyage
# Round the Coasts of Scotland and the Isles", both PDFs of books about Scotland,
# and one of them was credited to them and displayed. The grey-level distance was
# small because the local files were themselves page-shaped, not because the
# matcher understood anything.
#
# So the candidate's file type has to be checked before it is downloaded, in every
# path that can reach a match. This is the check that says no.
NON_IMAGE_SUFFIXES = frozenset(
    {".pdf", ".djvu", ".djv", ".djt", ".djvu.xml", ".chm", ".epub", ".pages"}
)

# The raster formats this project will install. Used by slug_key to drop a
# trailing extension before reducing a title to letters and digits, so that a
# Commons title and the filename derived from it reduce to the same string.
IMAGE_SUFFIXES = frozenset(
    {
        ".jpg",
        ".jpeg",
        ".jpe",
        ".png",
        ".webp",
        ".tif",
        ".tiff",
        ".gif",
        ".bmp",
        ".apng",
        ".avif",
    }
)


def is_raster_image(record: dict[str, Any]) -> bool:
    """True when a Commons file is a photograph we could legitimately show.

    Checked in this order, and the reason is that each later test is weaker than
    the one before it:

    1. the extension of the file's own title, which is what Commons itself uses to
       decide how to render it;
    2. the MIME type from imageinfo, which catches a `.tif` or `.svg` that is a
       scan or a diagram rather than a photograph;
    3. as a last resort, the format of the thumbnail URL, because a `.jpg`
       thumbnail is served for a PDF too and that is precisely the trap.
    """
    title = str(record.get("title", ""))
    suffix = ("." + title.rsplit(".", 1)[-1].lower()) if "." in title else ""
    if suffix in NON_IMAGE_SUFFIXES:
        return False

    mime = str(record.get("mime", "")).lower()
    if mime:
        if not mime.startswith("image/"):
            return False
        # image/tiff is a scan or a raw camera file, not a displayable photograph.
        if mime in {"image/tiff", "image/svg+xml", "image/x-icon"}:
            return False

    thumb = str(record.get("thumburl", "")).lower()
    if thumb:
        if any(thumb.endswith(s) for s in NON_IMAGE_SUFFIXES):
            return False
        # Commons renders page 1 of a multi-page document as "page1.jpg" or
        # "page1-1920px.jpg" whatever the original's type claims, so the file name
        # of the thumbnail is the remaining tell.
        basename = thumb.rsplit("/", 1)[-1]
        if re.match(r"page\d+([-_.]|$)", basename):
            return False
    return True


def field(ext: dict[str, Any], key: str, default: str = "") -> str:
    """Read one `extmetadata` value, tolerating both shapes it arrives in.

    The raw API nests values as `{"LicenseShortName": {"value": "CC BY-SA 4.0",
    "source": "..."}}`, while `Commons.info` flattens that to a plain string.
    Accepting either means callers cannot silently read an empty licence -- which
    is the kind of bug that shows up as "no licence declared" on every single
    file, and is easy to misread as "Commons has no licences".
    """
    value = ext.get(key, default)
    if isinstance(value, dict):
        value = value.get("value", default)
    return value if isinstance(value, str) else default


def records_of(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Flatten one API response into `{title: record}`.

    Split out of `Commons.info` so the identical shape can be rebuilt from a
    cache file without making a request. See `cached_records`.
    """
    out: dict[str, dict[str, Any]] = {}
    for page in payload.get("query", {}).get("pages", {}).values():
        if "missing" in page or not page.get("imageinfo"):
            continue
        info = page["imageinfo"][0]
        ext = {k: v.get("value", "") for k, v in info.get("extmetadata", {}).items()}
        out[page["title"]] = {
            "title": page["title"],
            "width": info.get("width", 0),
            "height": info.get("height", 0),
            "mime": info.get("mime", ""),
            "sha1": info.get("sha1", ""),
            "descriptionurl": info.get("descriptionurl", ""),
            "thumburl": info.get("thumburl") or info.get("url", ""),
            "thumbwidth": info.get("thumbwidth", 0),
            "thumbheight": info.get("thumbheight", 0),
            "extmetadata": ext,
            "categories": [c["title"] for c in page.get("categories", [])],
        }
    return out


def cached_records(cache_dir: Path) -> dict[str, dict[str, Any]]:
    """Every file record ever fetched, rebuilt from the on-disk cache alone.

    The cache is a record of what the pipeline has already asked Commons, and
    after a run it holds the metadata for every candidate that run saw --
    including the ones it went on to reject. That makes it a search-free
    candidate pool: a photograph already sitting on disk can be credited by
    matching its filename against the titles in the cache, with no network
    traffic whatsoever.

    That matters because Commons rate-limits by client, and the selection search
    is currently throttled hard enough to stall for minutes at a time. Running
    a second job against the same limit in that state makes it worse. Reading
    the cache costs nothing and cannot earn a 429.

    Records are keyed by title, so a file fetched by more than one run collapses
    to a single entry. Later files win, and that is deliberate: these are the
    same Commons file, so if the metadata ever did differ the newer fetch is the
    one to trust.
    """
    out: dict[str, dict[str, Any]] = {}
    if not cache_dir.exists():
        return out
    for path in sorted(cache_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            # A truncated write from a run that was killed mid-response. Skipping
            # is safe: a record is only ever a bonus here, never a requirement.
            continue
        if "query" not in payload:
            continue
        out.update(records_of(payload))
    return out


class Commons:
    """Cached wrapper over the few Commons API calls this project needs."""

    def __init__(
        self, cache_dir: Path, *, throttle: float = 1.5, offline: bool = False
    ) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # Commons asks anonymous clients to stay well under 1 request/second and
        # answers a burst with HTTP 429. 1.5s is slow but the pipeline is a
        # build-time job that runs once; being a good citizen costs minutes.
        self.throttle = throttle
        # Offline means "the cache is the whole world, and a miss is an error".
        #
        # This is how credit recovery runs safely alongside the selection search.
        # Both talk to Commons, and two clients sharing an anonymous rate limit
        # is what earns the 429s that stall the search for minutes at a time. But
        # recovery only needs metadata for files already downloaded, and every
        # earlier run cached the metadata for exactly those files. So recovery can
        # be answered entirely from disk -- and making that a hard failure rather
        # than a silent fallback is the point: if offline were allowed to fall
        # through to the network, it would be a slower way of doing the thing it
        # was switched on to prevent, and the throttling would come back with no
        # obvious cause.
        self.offline = offline
        self._last_call = 0.0
        self.calls = 0
        self.cache_hits = 0
        self.throttled = 0

    # -- transport ---------------------------------------------------------
    def _cache_path(self, params: dict[str, Any]) -> Path:
        # Hash the whole request, never a prefix of it. A truncated key silently
        # merges different requests: json.dumps sorts keys, and in an imageinfo
        # request the only field that varies ("titles") sorts last, so every
        # call hashed the same and every one after the first read that first
        # response. Silent, and wrong answers rather than errors.
        key = json.dumps(params, sort_keys=True)
        return self.cache_dir / f"{hashlib.sha256(key.encode()).hexdigest()[:32]}.json"

    def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        path = self._cache_path(params)
        if path.exists():
            self.cache_hits += 1
            return json.loads(path.read_text())

        if self.offline:
            raise CommonsError(
                "offline: not in the cache, and refusing to touch the network: "
                f"{params.get('titles') or params}"
            )

        url = f"{API}?{urllib.parse.urlencode(params)}"
        last_error: Exception | None = None

        for attempt in range(6):
            wait = self.throttle - (time.monotonic() - self._last_call)
            if wait > 0:
                time.sleep(wait)

            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            try:
                with urllib.request.urlopen(request, timeout=45) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                self._last_call = time.monotonic()
                self.calls += 1
                break
            except urllib.error.HTTPError as exc:
                self._last_call = time.monotonic()
                if exc.code not in (429, 503, 500):
                    raise CommonsError(f"HTTP {exc.code} for {url}") from exc
                # Too many requests / temporarily unavailable. Back off hard and
                # say so: silently retrying at the same speed is what got us
                # throttled in the first place.
                self.throttled += 1
                delay = min(120.0, 8.0 * (2**attempt))
                print(f"  {exc.code} from Commons; waiting {delay:.0f}s", file=sys.stderr)
                self.throttle = min(self.throttle * 1.5, 8.0)
                time.sleep(delay)
                last_error = exc
            except urllib.error.URLError as exc:
                self._last_call = time.monotonic()
                last_error = exc
                time.sleep(min(60.0, 4.0 * (2**attempt)))
        else:
            raise CommonsError(f"gave up on {url}: {last_error}")

        if "error" in payload:
            raise CommonsError(f"API error for {url}: {payload['error']}")

        path.write_text(json.dumps(payload))
        return payload

    # -- queries -----------------------------------------------------------
    def search(self, term: str, limit: int = 50) -> list[str]:
        """Commons file-namespace search. Returns titles like 'File:Foo.jpg'."""
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": term,
            "gsrnamespace": 6,
            "gsrlimit": min(limit, 500),
            "gsrprop": "snippet",
            "format": "json",
            "formatversion": 1,
        }
        payload = self._get(params)
        pages = payload.get("query", {}).get("pages", {})
        return [page["title"] for page in pages.values() if page.get("title")]

    def info(self, titles: list[str]) -> dict[str, dict[str, Any]]:
        """File metadata for up to 50 titles at a time.

        Returns a mapping of title -> {
            width, height, descriptionurl, thumburl, thumbwidth,
            extmetadata, categories, sha1
        }
        """
        out: dict[str, dict[str, Any]] = {}
        for start in range(0, len(titles), 50):
            chunk = titles[start : start + 50]
            params = {
                "action": "query",
                "titles": "|".join(chunk),
                "prop": "imageinfo|categories",
                "iiprop": "url|size|sha1|extmetadata|mime",
                "iiurlwidth": THUMB_WIDTH,
                "cllimit": "max",
                "format": "json",
                "formatversion": 1,
            }
            payload = self._get(params)
            out.update(records_of(payload))
        return out

    def categories(self, titles: list[str]) -> dict[str, list[str]]:
        """Category list per file. Separate from `info` so it can be cached
        independently -- the filter rules read categories, and re-deriving them
        should not re-download the image metadata too."""
        out: dict[str, list[str]] = {}
        for start in range(0, len(titles), 50):
            chunk = titles[start : start + 50]
            payload = self._get(
                {
                    "action": "query",
                    "titles": "|".join(chunk),
                    "prop": "categories",
                    "cllimit": "max",
                    "format": "json",
                    "formatversion": 1,
                }
            )
            for page in payload.get("query", {}).get("pages", {}).values():
                out[page["title"]] = [c["title"] for c in page.get("categories", [])]
        return out


# --------------------------------------------------------------------------
# metadata interpretation
# --------------------------------------------------------------------------
def licence_of(record: dict[str, Any]) -> dict[str, Any]:
    """Decide whether a file may be published, and under what terms.

    Returns {free, label, reason, spdx}. `reason` is why it was rejected, so the
    selection report can say something honest instead of "no candidates".

    Order matters: a restriction note beats the licence tag, because the tag is
    self-declared by the uploader and the restriction is the condition they
    actually attached to it.
    """
    ext = record.get("extmetadata", {})
    short = _plain(field(ext, "LicenseShortName"))
    usage = _plain(field(ext, "UsageTerms"))
    licence = _plain(field(ext, "License"))
    restrictions = _plain(field(ext, "Restrictions"))

    # The fields an uploader restriction actually turns up in, in the order we
    # trust them. `Attribution` is included because "please credit me" is a
    # condition even where the licence itself is permissive.
    notes = " | ".join(
        _plain(field(ext, key))
        for key in ("Restrictions", "Attribution", "Credit", "Copyrighted")
    )

    label = short or usage or licence
    spdx = _plain(field(ext, "LicenseUrl")).rsplit("/", 1)[-1].rsplit("/", 1)[-1]

    if not label:
        return {
            "free": False,
            "label": "",
            "spdx": spdx,
            "reason": "no licence declared on the file",
        }

    if NON_FREE_HINTS.search(label):
        return {
            "free": False,
            "label": label,
            "spdx": spdx,
            "reason": f"non-free licence: {label}",
        }

    hit = RESTRICTION_HINTS.search(notes)
    if hit:
        return {
            "free": False,
            "label": label,
            "spdx": spdx,
            "reason": f"uploader restriction overrides {label}: {hit.group(0)!r}",
        }

    if not FREE_LICENCE_RE.match(label):
        return {
            "free": False,
            "label": label,
            "spdx": spdx,
            "reason": f"licence not in the free set: {label!r}",
        }

    # CC BY-SA needs the licence URL to be a real Creative Commons one before we
    # publish under it; a bare tag with no deed is not evidence of anything.
    if label.lower().startswith("cc") and not field(ext, "LicenseUrl"):
        return {
            "free": False,
            "label": label,
            "spdx": spdx,
            "reason": f"{label} declared with no licence URL",
        }

    return {"free": True, "label": label, "spdx": spdx, "reason": ""}


def artist_of(record: dict[str, Any]) -> str:
    """The human-readable author, for the credits table.

    Commons' `Artist` field is an HTML fragment that is often just a linked
    username, which is useless to a reader who has never heard of Commons. When
    that is all there is, we fall back to the `Credit` field, which uploader-
    supplied prose usually names properly.
    """
    ext = record.get("extmetadata", {})
    artist = _plain(field(ext, "Artist"))
    credit = _plain(field(ext, "Credit"))
    if artist and not re.fullmatch(r"\s*(see below|unknown|self|own work)\s*", artist, re.I):
        return artist
    if credit:
        return credit
    return artist or "unattributed on Commons"
