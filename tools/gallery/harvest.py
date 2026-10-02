#!/usr/bin/env python3
"""Turn the selection checkpoint into a plan, without waiting for the search.

`select.py --install` does its search, then `assign`, then `install` in one
process, so nothing reaches disk until all 156 entities have been searched.
Under Wikimedia's rate limiter that is hours, and the checkpoint the process
writes at each entity would sit unused the whole time.

The checkpoint already holds everything `assign` needs: the candidate records
for every entity it has finished. This runs the same `assign` and `install`
those records are destined for, so the harvest is the pipeline's own decision
and not a second, different one. Run it after any number of entities and the
galleries installed so far are usable; run it again later and it picks up the
new ones.

Only `assign`'s inputs change, not its behaviour: photographs are still given to
the destination they name most strongly, and still need to name one at all.

Usage:

    python3 tools/gallery/harvest.py                  # install from the checkpoint
    python3 tools/gallery/harvest.py --report-only    # say what it would do
    python3 tools/gallery/harvest.py --out plan.json  # write the plan rows
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

# select.py runs its own side effects on import, so load it the same way the
# tests do: by spec, which keeps `if __name__ == "__main__"` from firing.
_spec = importlib.util.spec_from_file_location("select", HERE / "select.py")
select = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(select)

MIN_WANT = select.MIN_WANT


def read_checkpoint(path: Path) -> dict[str, dict]:
    """Entity id -> {"kept": [...], "rejected": [...]} for everything searched.

    Trailing lines are tolerated: a run killed mid-write leaves a partial JSON
    line at the end of the file, and that must not cost us the entities that
    completed before it. Skipping a corrupt line is safe because the entity it
    belonged to will be searched again on resume, so it costs a repeat rather
    than a result.
    """
    out: dict[str, dict] = {}
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            print(f"  skipping an unreadable checkpoint line ({len(line)} chars)")
            continue
        entity_id = row.get("id")
        if entity_id:
            out[entity_id] = row
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--checkpoint", default=str(select.CHECKPOINT_OUT), help="checkpoint to harvest"
    )
    parser.add_argument("--out", default="/tmp/opencode/harvest-plan.json")
    parser.add_argument("--install", action="store_true", help="download the chosen files")
    parser.add_argument("--report-only", action="store_true", help="choose but write nothing")
    args = parser.parse_args()

    entities = select.load_entities()
    # The sibling map has to be built over all 156 names, not over the searched
    # subset: it is what makes a shared word look non-distinctive, and computing
    # it on 8 would call "Castle" distinctive and hand every castle its neighbours'
    # photographs.
    select.load_sibling_map([e["name"] for e in entities])

    searched = read_checkpoint(Path(args.checkpoint))
    passing = {i: r["kept"] for i, r in searched.items() if r.get("kept")}
    rejected = {i: r.get("rejected", []) for i, r in searched.items() if r.get("rejected")}
    print(f"{len(entities)} entities, {len(searched)} searched, {len(passing)} with candidates\n")

    galleries, unassigned = select.assign(passing, entities)
    rows, notes = select.install(
        galleries, write=args.install, report_only=args.report_only
    )
    for note in notes[:20]:
        print(f"  note: {note}")
    if len(notes) > 20:
        print(f"  ... and {len(notes) - 20} more")

    ready = {k: v for k, v in galleries.items() if len(v) >= MIN_WANT}
    thin = {k: v for k, v in galleries.items() if 0 < len(v) < MIN_WANT}
    not_searched = [e["id"] for e in entities if e["id"] not in searched]
    not_reached = [e["id"] for e in entities if e["id"] in searched and e["id"] not in passing]

    print(
        f"\nphotographs chosen : {len(rows)}\n"
        f"  with a row (>= {MIN_WANT}) : {len(ready)} {sorted(ready)}\n"
        f"  too thin          : {len(thin)} {sorted(thin)}\n"
        f"  searched, none usable : {len(not_reached)}\n"
        f"  not yet searched  : {len(not_searched)}\n"
        f"  named no place strongly enough : {len(unassigned)}"
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
    print(f"\nplan  {out}")
    if not args.install and not args.report_only:
        print("\nnothing was downloaded -- pass --install to write files to disk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
