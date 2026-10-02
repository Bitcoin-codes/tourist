#!/usr/bin/env python3
"""Rebuild the gallery plan for the photographs already on disk.

Why this exists
---------------
The selection pipeline that produced `assets/images/gallery/` lived in a scratch
directory and was lost to a reboot. The images survived; the record of *which
Commons file each one is* did not. This reconstructs that record.

How a local file is matched back to its Commons source
------------------------------------------------------
Filename first, because it is free: the installer slugified the Commons title, so
`cape-coast-castle-coast-windows.jpg` came from a title containing "Cape Coast
Castle" and "coast windows". Both sides are reduced to a letters-and-digits-only
key, which ignores the punctuation, spacing and case that slugification is lossy
about. An exact key match is very strong evidence.

Pixels second, because filenames lie. Several Commons files per entity collapse
to the same slug (the installer disambiguated the duplicates with `-2`, `-3`),
and some slugs lost their distinguishing characters entirely. For those, each
plausible candidate's 1920px thumbnail is downloaded and compared to the local
file by a coarse grayscale signature, which tolerates the re-encode, the
white-balance and the 16:10 crop that installation applied.

The point of the pixel check is that it needs no human eyes. A wrong file
scores nowhere near a right one, so a confident pixel match is a confirmation
rather than an opinion -- which matters, because the photographs were originally
chosen by someone looking at them and that review must not be silently redone by
a heuristic.

Output
------
    gallery_plan.json   entity -> [{file, credits, match, score}]
    recover-report.txt  everything a human needs to check the uncertain cases

Usage
-----
    venv/bin/python tools/gallery/recover.py
    venv/bin/python tools/gallery/recover.py --strict   # fail on any uncertain match
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from commons import (  # noqa: E402
    CACHE_DIR,
    IMAGE_SUFFIXES,
    Commons,
    artist_of,
    cached_records,
    is_raster_image,
    licence_of,
)
import pixels  # noqa: E402

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("needs Pillow: run this with venv/bin/python")

ROOT = Path(__file__).resolve().parent.parent.parent
GALLERY = ROOT / "assets" / "images" / "gallery"
SCRATCH = Path("/tmp/opencode/gallery-recovery")
THUMBS = SCRATCH / "thumbs"
PLAN_OUT = SCRATCH / "gallery_plan.json"
REPORT_OUT = SCRATCH / "recover-report.txt"

# Mean absolute difference between two 16x16 grayscale signatures, 0-255. The
# signature itself lives in `pixels`, shared with select.py and check.py so that
# one threshold decides "same picture" everywhere. These two are looser than
# pixels.SAME because this stage is answering a different question: it is matching
# an installed file against a candidate it has not seen, where a wrong match
# attaches a photographer's name to somebody else's photograph. It is better to
# report a miss and let a person decide than to guess.
#
# Measured on this repository's own files: the same photograph, resized and
# re-encoded, scores under 1.3. Different photographs of the same place score
# above 30. The gap is wide, so the threshold is not delicate.
MATCH_THRESHOLD = 20.0

# Above this, we call it a miss and say so rather than inventing a match.
UNSURE_THRESHOLD = 26.0

# A match this good means the two images are the same photograph, so the pixel
# stage can stop as soon as every outstanding file reaches it.
PERFECT = 3.0

# How many candidates to download per entity. Search returns up to 150 titles;
# downloading all of them costs gigabytes and hours, and the tail of a search
# result list is almost never a photograph of the place.
MAX_CANDIDATES = 45

_ALNUM_RE = re.compile(r"[^a-z0-9]+")
# Trailing extension, captured so slug_key can check it against the image suffixes
# and drop only those. A title like "Fort Nassau 1990" must keep its digits.
_EXTENSION_RE = re.compile(r"\.[a-z0-9]{2,5}$")


def slug_key(text: str) -> str:
    """Letters and digits only, lowercased, accent-folded, extension dropped.

    The local filenames were slugified from Commons titles, which is lossy about
    case, spacing, underscores and punctuation. Stripping all of it maximises the
    chance that both sides reduce to the same string. `Nji Gbetkom` and
    `Nji-Gbetkom` and `Nji  Gbetkom` all become `njigbetkom`.

    The extension has to go, and dropping it here rather than in `local_key` is
    deliberate: `slug_key` is applied to a Commons *title*, which carries the
    extension, and `local_key` to a *filename*. Keeping it on one side only made
    the two keys differ by a trailing "jpg" for every single file, so the
    name-matching stage never once succeeded and all credit recovery quietly fell
    through to the pixel stage instead. Nothing errored -- an unmatched key simply
    looks like a file Commons has not heard of, which is indistinguishable from
    the truth.
    """
    folded = unicodedata.normalize("NFKD", text)
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    folded = folded.lower()
    # "j", "p" and "g" are all letters, so an extension survives the alnum filter
    # intact. It has to be removed while the dot is still there to find it.
    for suffix in _EXTENSION_RE.findall(folded):
        if suffix in IMAGE_SUFFIXES:
            folded = folded[: -len(suffix)]
            break
    return _ALNUM_RE.sub("", folded)


def local_key(filename: str) -> str:
    """The key for an installed file: its slug, with the extension dropped.

    The entity prefix is *not* removed here. See `local_keys` for why both forms
    have to be tried, and note that the docstring here used to promise the prefix
    would be stripped by this function while no caller ever passed an entity id
    for it to strip -- so the promise was not kept and nothing noticed.
    """
    stem = filename[:-4] if filename.lower().endswith(".jpg") else filename
    return slug_key(stem)


def local_keys(filename: str, entity: str) -> list[str]:
    """Both keys an installed filename could have been derived from.

    The installed names are not consistent about whether they carry the entity
    id, because they were slugified from Commons titles by more than one code
    path over the life of the project:

      `fort-nassau-mouri-poort.jpg`     Commons title "Fort Nassau poort"
      `kejetia-market-markt.jpg`        Commons title "Kejetia-Markt"

    The first repeats the entity id and the Commons title does not, so only the
    stripped key can match. The second repeats words that the Commons title also
    contains, so only the unstripped key can match. Guessing one convention loses
    half the files, which is why both are offered and the first that resolves wins.

    Order matters only for which of two equally good candidates gets reported
    first; the ambiguity handling downstream is the same either way.
    """
    full = local_key(filename)
    keys = [full]
    if filename.startswith(entity + "-"):
        stripped = local_key(filename[len(entity) + 1 :])
        if stripped and stripped != full:
            keys.append(stripped)
    return keys


def signature(path: Path) -> list[float] | None:
    """16x16 grayscale signature of an image, or None if unreadable."""
    return pixels.of_path(path)


def signature_of_ratio(path: Path, ratio: float) -> list[float] | None:
    """Signature after centre-cropping to `ratio` first.

    Installed tiles were cropped to 16:10, so comparing a cropped local file to a
    full-frame candidate head-on measures the crop, not the subject. Cropping
    both to the same shape first removes that error.
    """
    try:
        with Image.open(path) as raw:
            image = raw.convert("L")
            width, height = image.size
            if width / height > ratio:
                new_width = int(round(height * ratio))
                left = (width - new_width) // 2
                image = image.crop((left, 0, left + new_width, height))
            else:
                new_height = int(round(width / ratio))
                top = (height - new_height) // 2
                image = image.crop((0, top, width, top + new_height))
            return pixels.pixels(image)
    except Exception:
        return None


def distance(a: list[float], b: list[float]) -> float:
    """Mean absolute difference between two signatures. See `pixels.distance`."""
    return pixels.distance(a, b)


def best_score(
    local: tuple[list[float], list[float]], cand: tuple[list[float], list[float]]
) -> tuple[float, str]:
    """Best comparison of one candidate against one local file.

    Pairs by aspect form: a full-frame candidate is compared to a full-frame
    local file, and a 16:10-cropped candidate to a 16:10-cropped local file.
    Cross-pairing them would measure the crop rather than the subject.
    """
    full = distance(local[0], cand[0])
    crop = distance(local[1], cand[1])
    if crop < full:
        return crop, "crop16x10"
    return full, "full"


def rank_candidates(
    titles: set[str], records: dict[str, dict], entity: str
) -> list[str]:
    """Order candidates by how strongly their own metadata names the place.

    A Commons file that never mentions the place in its title, categories or
    description is unlikely to be a photograph of it -- but "unlikely" is not
    "impossible", which is why this only reorders the list rather than filtering
    it. Dropping candidates here would silently make a gallery smaller, and a
    smaller gallery that is missing the right photograph is worse than a larger
    one that includes a wrong one we can review.
    """
    from filters import _keys  # local import: the two modules are independent

    want = _keys(entity)
    scored: list[tuple[int, str]] = []
    for title in titles:
        if title not in records:
            continue
        record = records[title]
        text = " ".join(
            (
                title.split(":", 1)[-1],
                record.get("extmetadata", {}).get("ImageDescription", "") or "",
                " ".join(record.get("categories", []) or []),
            )
        )
        overlap = len(want & _keys(text))
        # Landscape files are what a place gallery wants; a flag or a logo is
        # not, and that is knowable from the metadata without looking.
        bonus = 0
        if record.get("width", 0) >= record.get("height", 0):
            bonus += 1
        if record.get("thumbwidth", 0) >= 1200:
            bonus += 1
        scored.append((-overlap, -bonus, title))
    scored.sort()
    return [title for _, _, title in scored]


def download(url: str, dest: Path) -> Path | None:
    """Fetch a thumbnail into the scratch dir, once."""
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        import urllib.request

        from commons import USER_AGENT

        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=90) as response:
            dest.write_bytes(response.read())
        return dest
    except Exception:
        return None


def load_entities() -> tuple[dict[str, str], dict[str, list[str]]]:
    """Map every gallery filename to its entity id, and list the originals.

    Returns (id -> human-readable name, id -> installed filenames). The name
    matters: it is by far the most productive search term, because it is what a
    Commons uploader would have typed.
    """
    data = json.loads((ROOT / "backend" / "data" / "destinations.json").read_text())
    names: dict[str, str] = {d["id"]: d.get("name") or d["id"] for d in data}
    festivals = json.loads((ROOT / "backend" / "data" / "festivals.json").read_text())
    names.update({f["id"]: f.get("name") or f["id"] for f in festivals})

    ids = sorted(names, key=len, reverse=True)

    by_entity: dict[str, list[str]] = {}
    for path in sorted(GALLERY.glob("*.jpg")):
        name = path.name
        if VARIANT_RE.search(name):
            continue  # a generated derivative, not an installed original
        for entity in ids:
            if name == f"{entity}.jpg" or name.startswith(f"{entity}-"):
                by_entity.setdefault(entity, []).append(name)
                break
        else:
            print(f"  warning: {name} matches no destination id", file=sys.stderr)
    return names, by_entity


VARIANT_RE = re.compile(r"-(400|800)\.jpg$", re.IGNORECASE)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strict", action="store_true", help="exit 1 if any file matched only by pixels or not at all")
    parser.add_argument("--limit", type=int, default=0, help="stop after N entities (debugging)")
    parser.add_argument(
        "--offline",
        action="store_true",
        help=(
            "answer only from the on-disk API cache and fail on a miss, so this "
            "can run alongside select.py without spending Commons' rate limit"
        ),
    )
    parser.add_argument(
        "--from-cache",
        action="store_true",
        help=(
            "match against every Commons file the pipeline has already fetched "
            "instead of searching again; implies no network traffic"
        ),
    )
    args = parser.parse_args()
    if args.from_cache:
        args.offline = True  # the whole point is that nothing here needs the network

    names_by_id, by_entity = load_entities()
    total = sum(len(v) for v in by_entity.values())
    print(f"{total} installed originals across {len(by_entity)} entities\n")

    client = Commons(CACHE_DIR, throttle=0.4, offline=args.offline)
    pool = cached_records(CACHE_DIR) if args.from_cache else {}
    if pool:
        print(
            f"  candidate pool from cache: {len(pool)} Commons files, "
            f"{sum(1 for r in pool.values() if is_raster_image(r))} of them photographs\n"
        )
    plan: dict[str, list[dict]] = {}
    report: list[str] = []
    stats = {"name": 0, "pixels": 0, "unmatched": 0, "non_image": 0}

    entities = sorted(by_entity)
    if args.limit:
        entities = entities[: args.limit]

    for entity in entities:
        names = sorted(by_entity[entity])
        print(f"{entity}")

        # Every local file's signature, in both aspect forms.
        local: dict[str, tuple[list[float], list[float]]] = {}
        for name in names:
            path = GALLERY / name
            full = signature(path)
            if full is None:
                report.append(f"{entity}/{name}: unreadable locally")
                stats["unmatched"] += 1
                continue
            local[name] = (full, signature_of_ratio(path, 16 / 10) or full)

        # Candidate Commons titles. The entity's real name is the best search
        # term -- "Cape Coast Castle" finds far more than "cape coast castle"
        # does through a slug. After that, the distinctive words of each local
        # filename: for "cape-coast-castle-coast-windows.jpg" the words "coast"
        # and "windows" are what separate it from the entity's other files.
        terms: list[str] = [names_by_id.get(entity, entity.replace("-", " "))]
        extras: list[str] = []
        for name in names:
            tail = name[: -len(".jpg")]
            if tail.startswith(entity + "-"):
                tail = tail[len(entity) + 1 :]
            words = [w for w in re.split(r"[-_]+", tail) if len(w) > 2 and not w.isdigit()]
            if len(words) >= 2:
                extras.append(" ".join(words))
        seen: set[str] = set()
        for term in [terms[0]] + sorted(set(extras), key=len, reverse=True):
            if term and term.lower() not in seen:
                seen.add(term.lower())
                terms.append(term)
        terms = terms[:3]

        if args.from_cache:
            # No search: match against every title the pipeline has ever fetched.
            #
            # The search index is the one thing the cache does not hold, because
            # every search this session was answered with a 429 that outlasted the
            # retry budget and so was never written down. What the cache does hold
            # is metadata for 390-odd candidate files, and a name match against
            # those is the whole of what stage 1 needs. Anything still unmatched
            # falls through to the pixel comparison below, which uses the same
            # pool and also needs no network.
            records = dict(pool)
        else:
            titles: set[str] = set()
            for term in terms:
                titles.update(client.search(term, limit=50))
            if not titles:
                report.append(f"{entity}: no Commons candidates at all")
                continue
            records = client.info(sorted(titles))

        by_key: dict[str, list[str]] = {}
        for title in records:
            stem = title.split(":", 1)[-1]
            by_key.setdefault(slug_key(stem), []).append(title)

        # Stage 1: exact slug match, no download needed.
        matched: dict[str, str] = {}
        for name in names:
            cands: list[str] = []
            for key in local_keys(name, entity):
                cands = by_key.get(key, [])
                if cands:
                    break
            if len(cands) == 1:
                matched[name] = cands[0]
            elif len(cands) > 1:
                report.append(
                    f"{entity}/{name}: {len(cands)} Commons files share this slug -- "
                    + "; ".join(c.rsplit(":", 1)[-1] for c in cands)
                    + "  -> falling back to pixels"
                )

        # Stage 2: pixel comparison for whatever is left. `still` holds only
        # names not already settled, so nothing is overwritten here.
        #
        # This is the expensive stage, so it is bounded three ways. Candidates
        # are ranked by how closely their own text mentions the place, since a
        # file that never mentions it is very unlikely to be a photograph of it;
        # only the top MAX_CANDIDATES are downloaded; and the scan stops as soon
        # as every remaining file has a near-identical match, because a score
        # under PERFECT cannot be improved on.
        still = [n for n in names if n not in matched and n in local]
        if still and args.from_cache:
            # Stage 2 is not available in this mode, and pretending otherwise
            # would be the exact bug this flag exists to prevent.
            #
            # `Commons.offline` covers the API only. Stage 2 fetches thumbnails
            # over plain HTTP, which never touches the cache, so "offline" as a
            # promise about network traffic would simply be untrue if stage 2
            # ran. Downloading dozens of images while the selection search is
            # being throttled is also the thing most likely to make the throttling
            # worse for both jobs.
            #
            # So this mode is name-match only. Anything left over is reported as
            # uncredited and needs a networked run to resolve -- which is the
            # honest outcome, rather than a claim of coverage the run did not have.
            for name in still:
                report.append(
                    f"{entity}/{name}: not in the cache pool by name -- needs a "
                    f"networked run to confirm by pixels"
                )
            still = []
        if still:
            ranked = rank_candidates(titles, records, entity)
            # Widen the download window rather than giving up. A first pass over
            # the best-ranked candidates resolves the common case cheaply; only
            # when a file is still unmatched do we pay for the rest of the list.
            # Search order is a popularity ranking, not a relevance ranking, so
            # the right file is often well down it.
            start, width = 0, MAX_CANDIDATES
            while still and start < len(ranked):
                batch = ranked[start : start + width]
                start += width
                for title in batch:
                    record = records[title]
                    if not record.get("thumburl"):
                        continue
                    # Before it is downloaded, and before it can be compared to
                    # anything. See commons.is_raster_image for why this has to be
                    # a separate test rather than something the matcher notices.
                    if not is_raster_image(record):
                        stats["non_image"] += 1
                        continue
                    cache_name = f"{record.get('sha1', 'x')[:16]}_{slug_key(title)[:40]}.jpg"
                    path = download(record["thumburl"], THUMBS / cache_name)
                    if path is None:
                        continue
                    cand_full = signature(path)
                    if cand_full is None:
                        continue
                    cand_crop = signature_of_ratio(path, 16 / 10) or cand_full
                    for name in list(still):
                        score, how = best_score(local[name], (cand_full, cand_crop))
                        prior = matched.get(name)
                        if prior is None or score < prior["score"]:
                            matched[name] = {"title": title, "score": score, "form": how}
                        if matched[name]["score"] < PERFECT:
                            still.remove(name)  # identical; cannot do better
                width = min(width * 2, 512)

        rows: list[dict] = []
        for name in names:
            hit = matched.get(name)
            if hit is None:
                report.append(f"{entity}/{name}: NO MATCH -- needs a human decision")
                stats["unmatched"] += 1
                continue
            if isinstance(hit, dict):
                title, score, kind = hit["title"], hit["score"], "pixels"
            else:
                title, score, kind = hit, 0.0, "filename"
            record = records.get(title, {})
            if score > UNSURE_THRESHOLD:
                report.append(
                    f"{entity}/{name}: weak pixel match to {title.rsplit(':', 1)[-1]} "
                    f"(score {score:.1f} > {UNSURE_THRESHOLD}) -- needs a human decision"
                )
                stats["unmatched"] += 1
                continue
            if kind == "filename":
                stats["name"] += 1
            else:
                stats["pixels"] += 1
                report.append(
                    f"{entity}/{name}: matched by pixels to {title.rsplit(':', 1)[-1]} "
                    f"(score {score:.1f}, {hit['form']})"
                )
            lic = licence_of(record)
            if not lic["free"]:
                report.append(f"  !! {name} licence: {lic['reason']}")
            rows.append(
                {
                    "entity": entity,
                    "file": f"gallery/{name}",
                    "title": title,
                    "description": record.get("extmetadata", {}).get("ImageDescription", ""),
                    "match": kind,
                    "score": round(score, 2),
                    "author": artist_of(record),
                    "licence": lic["label"],
                    "licence_url": record.get("extmetadata", {}).get("LicenseUrl", ""),
                    "source": record.get("descriptionurl", ""),
                    "width": record.get("width", 0),
                    "height": record.get("height", 0),
                }
            )
        plan[entity] = rows
        # Written after every entity, not once at the end.
        #
        # This run died partway through on a DNS failure, after matching 19 of 29
        # destinations, and the plan was only ever written at the end -- so the
        # matches existed in the log and nowhere else, and recovering them meant
        # re-running the whole thing. An hour of throttled API calls to reconstruct
        # a file that had already been computed is exactly the failure this whole
        # pipeline moved into the repository to avoid. Each entity's rows are
        # complete on the line after its print, so the write is safe to repeat.
        PLAN_OUT.parent.mkdir(parents=True, exist_ok=True)
        PLAN_OUT.write_text(json.dumps(plan, indent=2, sort_keys=True))
        write_report(plan, report, stats, client)
        print(f"  {len(rows)}/{len(names)} matched")

    PLAN_OUT.parent.mkdir(parents=True, exist_ok=True)
    PLAN_OUT.write_text(json.dumps(plan, indent=2, sort_keys=True))
    write_report(plan, report, stats, client)

    print(
        f"\nby filename {stats['name']}, by pixels {stats['pixels']}, "
        f"unmatched {stats['unmatched']}\n"
        f"api calls {client.calls} ({client.cache_hits} cached)\n"
        f"plan    {PLAN_OUT}\nreport  {REPORT_OUT}"
    )
    return 1 if args.strict and stats["unmatched"] else 0


def write_report(
    plan: dict[str, list[dict[str, Any]]],
    report: list[str],
    stats: dict[str, int],
    client: Any,
) -> None:
    """Write the human-readable half of the run: what matched, and what did not."""
    lines = [
        "GALLERY RECOVERY REPORT",
        "=" * 60,
        "",
        f"matched by filename : {stats['name']}",
        f"matched by pixels   : {stats['pixels']}",
        f"UNMATCHED           : {stats['unmatched']}",
        f"refused as non-image: {stats['non_image']}   (PDF, DjVu, scan -- not photographs)",
        f"API calls           : {client.calls} ({client.cache_hits} cache hits)",
        "",
        "Entries needing a human decision, and every pixel-only match:",
        "-" * 60,
        "",
    ]
    lines += report or ["  (none -- every file matched by name with no ambiguity)"]
    REPORT_OUT.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
