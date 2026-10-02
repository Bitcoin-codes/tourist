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
    USER_AGENT,
    Commons,
    artist_of,
    is_raster_image,
    licence_of,
)
import pixels  # noqa: E402
from filters import (  # noqa: E402
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
SCRATCH = Path("/tmp/opencode/gallery-select")
PLAN_OUT = SCRATCH / "select-plan.json"
REPORT_OUT = SCRATCH / "select-report.txt"
# Appended one line per entity as it finishes, so a run interrupted by a 429 or a
# killed shell resumes instead of starting over. See collect().
CHECKPOINT_OUT = SCRATCH / "select-checkpoint.jsonl"

# At most this many photographs in one gallery. The UI shows a hero plus a
# scrolling strip; more than six is unreachable behind a swipe.
MAX_PHOTOS = 6

# A gallery strip renders only when a destination has a hero plus at least two
# more, so a second photograph is the point at which it is worth building.
MIN_WANT = 2

# A photograph must name a destination at least this specifically to be used.
# The scale, from weakest to strongest, is built by `specificity` below.
MIN_SPECIFICITY = 2

# A photograph needs a real licence and a real size. Anything narrower than this
# cannot fill a thumbnail at 2x on a phone without upscaling.
MIN_WIDTH = 1200


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


def search_terms(entity: dict[str, Any]) -> list[str]:
    """What to ask Commons for, most productive first.

    The display name leads, because that is what an uploader would have typed.
    The name plus its region catches a caption that names the district instead.
    The bare distinctive words catch the cases where the destination's own name is
    a Commons category nobody searched -- "Fort Batenstein" is filed under
    "Princes Town" as often as under its own name.
    """
    terms = [entity["name"]]
    if entity["region"] and entity["region"] != entity["name"]:
        terms.append(f"{entity['name']} {entity['region']}")
    distinctive = distinctive_tokens(entity["name"])
    if distinctive:
        terms.append(" ".join(sorted(distinctive)))
    seen: set[str] = set()
    out: list[str] = []
    for term in terms:
        key = term.lower()
        if len(term) > 3 and key not in seen:
            seen.add(key)
            out.append(term)
    return out[:3]


# --------------------------------------------------------------------------
# scoring
# --------------------------------------------------------------------------
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
    if distinctive & _keys(title):
        return 2
    if distinctive & _keys(categories):
        return 2
    if distinctive & _keys(description):
        return 1
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
    """Search and filter. Returns (passing, rejected) keyed by entity id.

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
        if passing:
            print(f"  resuming: {len(passing)} entities already searched\n", flush=True)

    def checkpoint_entity(entity_id: str, kept: list[dict], why: list[dict]) -> None:
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
        lines.append(json.dumps({"id": entity_id, "kept": kept, "rejected": why}, sort_keys=True))
        checkpoint.write_text("\n".join(lines) + "\n")

    for entity in entities:
        if entity["id"] in passing:
            continue

        titles: set[str] = set()
        for term in search_terms(entity):
            titles.update(client.search(term, limit=50))
        if not titles:
            rejected[entity["id"]] = [{"title": "", "reason": "no candidates found"}]
            checkpoint_entity(entity["id"], [], rejected[entity["id"]])
            continue

        records = client.info(sorted(titles))
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
            kept.append(record)

        passing[entity["id"]] = kept
        checkpoint_entity(entity["id"], kept, rejected.get(entity["id"], []))
        print(
            f"  {entity['id']}: {len(kept)} of {len(records)} pass"
            + (f" ({counts.get('rejected', 0)} filtered)" if counts.get("rejected") else ""),
            flush=True,
        )
    return passing, rejected


def _parses(line: str) -> bool:
    try:
        json.loads(line)
        return True
    except json.JSONDecodeError:
        return False


def assign(
    passing: dict[str, list[dict]], entities: list[dict[str, Any]]
) -> tuple[dict[str, list[dict]], list[dict]]:
    """Give every photograph to exactly one destination: its strongest match.

    A photograph is used only where it names the destination at least
    `MIN_SPECIFICITY`, and only if it names *this* destination more strongly
    than any other. That second condition is what stops a Keta street appearing
    in both fort galleries, and it is why `specificity` is compared rather than
    thresholded on its own.
    """
    by_id = {entity["id"]: entity for entity in entities}
    best_for_file: dict[str, tuple[int, str, dict]] = {}

    for entity_id, records in passing.items():
        entity = by_id[entity_id]
        for record in records:
            score = specificity(record, entity)
            if score < MIN_SPECIFICITY:
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
            if twin is not None:
                notes.append(
                    f"{entity_id}/{name}: the same picture is already installed as "
                    f"{twin}, from {record['title'].rsplit(':', 1)[-1]}"
                )
                continue
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

    print(f"{len(entities)} entities, {len(known_names)} known names\n")
    client = Commons(SCRATCH / "api-cache", throttle=1.5)

    print("searching and filtering")
    if args.fresh:
        CHECKPOINT_OUT.unlink(missing_ok=True)
    # `--limit` bounds one invocation rather than the whole entity set, so a run
    # can be topped up over several sittings without ever starting over.
    batch = entities[: args.limit] if args.limit else entities
    passing, rejected = collect(
        client, batch, known_names, checkpoint=CHECKPOINT_OUT, resume=not args.fresh
    )
    galleries, unassigned = assign(passing, entities)
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
        f"galleries with >= {MIN_WANT} : {len(ready)}",
        f"photographs chosen    : {len(rows)}",
        f"too thin to show      : {len(thin)}",
        f"no usable photograph : {len(entities) - len(ready) - len(thin)}",
        f"API calls             : {client.calls} ({client.cache_hits} cached, {client.throttled} throttled)",
        "",
        "Why an entity has no gallery. This is the honest gap: it is what",
        "Wikimedia coverage looks like, not a failure of the pipeline.",
        "-" * 60,
    ]
    for entity in entities:
        if entity["id"] in ready:
            continue
        found = len(galleries.get(entity["id"], []))
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
    failed = [note for note in notes if note.startswith("  ") is False and "REPLACED" not in note and "same picture" not in note]
    lines += [
        "",
        "Installation notes",
        "-" * 60,
        f"  already present and identical : {sum('identical' in n for n in notes)}",
        f"  written                        : {sum('identical' not in n for n in notes if 'REPLACED' not in n and 'same picture' not in n)}",
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
