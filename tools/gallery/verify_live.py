#!/usr/bin/env python3
"""Verify every photograph the site currently shows against the filters.

The gallery was assembled one search at a time, and a filter tightened later
cannot retroactively reject what is already published. This closes that gap:
for each row of IMAGE-CREDITS.md it fetches the file's real Commons record
(title, description, categories, licence) and runs filters.screen() exactly
as select.py does, with the same known-names and host arguments.

It has already earned its place. The first run found two photographs that were
live and wrong -- an aerial view of Cape Three Points in New South Wales filed
as Ghana's, and Fort Amsterdam in Ambon filed as the one in Abandzi -- both of
which passed every filter at the time they were chosen because no filter yet
knew the words "Wales" or "Indonesia".

Records already held in the selection checkpoint are reused rather than
re-fetched; only the rest reach the API, 50 titles per request, and the merged
set is written to .gallery-state/live-records.json so test_live.py can assert
against real metadata without a network.

Usage
-----
    venv/bin/python tools/gallery/verify_live.py
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from commons import Commons  # noqa: E402
from filters import screen  # noqa: E402

STATE = ROOT / ".gallery-state"
CHECKPOINT = STATE / "select" / "select-checkpoint.jsonl"
OUT = STATE / "live-records.json"


def live_rows() -> list[tuple[str, str]]:
    """(entity name, commons file title) for every published photograph."""
    credits = (ROOT / "IMAGE-CREDITS.md").read_text(encoding="utf-8")
    block = credits.split("<!-- gallery-credits:start -->")[1].split(
        "<!-- gallery-credits:end -->"
    )[0]
    out: list[tuple[str, str]] = []
    for line in block.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5:
            continue
        match = re.search(r"commons\.wikimedia\.org/wiki/File:(.+)\)", cells[4])
        if not match:
            continue
        title = "File:" + urllib.parse.unquote(match.group(1)).replace("_", " ")
        out.append((cells[0], title))
    return out


def checkpoint_records() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if not CHECKPOINT.exists():
        return out
    for line in CHECKPOINT.open(encoding="utf-8"):
        if not line.strip():
            continue
        row = json.loads(line)
        for rec in (row.get("kept") or []) + (row.get("rejected") or []):
            out[rec.get("title", "")] = rec
    return out


def load_records(fetch: bool = True) -> dict[str, dict[str, Any]]:
    """Real Commons records for every published photograph, fetching what is
    missing. Returns {file title: record}."""
    rows = live_rows()
    titles = sorted({t for _, t in rows})
    have = checkpoint_records()
    # A checkpoint record with no metadata at all is not evidence of anything --
    # four live photographs were being judged "no licence declared" purely
    # because their cached row predated the licence fields. Such a record is
    # treated as absent so the real one is fetched.
    usable = {t: r for t, r in have.items() if r.get("extmetadata")}
    known = {t: usable[t] for t in titles if t in usable}
    todo = [t for t in titles if t not in known]
    if todo and fetch:
        client = Commons(cache_dir=STATE / "api-cache")
        known.update(client.info(todo))
    return known


def main() -> int:
    rows = live_rows()
    records = load_records()
    print(f"  live photographs : {len(rows)}")
    print(f"  records available: {len(records)}")
    OUT.write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  written          : {OUT.relative_to(ROOT)}")

    data = json.loads((ROOT / "backend" / "data" / "destinations.json").read_text("utf-8"))
    fests = json.loads((ROOT / "backend" / "data" / "festivals.json").read_text("utf-8"))
    by_name = {r.get("name", ""): r for r in data + fests}
    known_names = [r.get("name", "") for r in data + fests]

    failures: dict[str, list[str]] = defaultdict(list)
    uncovered: list[str] = []
    for place, title in rows:
        entity = by_name.get(place)
        record = records.get(title)
        if entity is None or record is None:
            uncovered.append(f"{place}: {title}")
            continue
        hosts = f"{entity.get('region', '')} {entity.get('location', '')}".split()
        reason = screen(record, entity.get("name", ""), known_names, hosts)
        if reason:
            key = re.sub(r"'[^']*'", "'...'", reason)
            failures[key].append(f"{entity.get('name')}: {title}")

    total = sum(len(v) for v in failures.values())
    print(f"\n  REJECTED by the current filters: {total}/{len(rows)}")
    for key in sorted(failures, key=lambda k: -len(failures[k])):
        print(f"    {len(failures[key]):4}  {key}")
        for line in failures[key][:40]:
            print(f"           {line}")
    if uncovered:
        print(f"\n    {len(uncovered)} had no record to test")
        for line in uncovered[:10]:
            print(f"           {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
