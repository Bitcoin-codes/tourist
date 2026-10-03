#!/usr/bin/env python3
"""One cycle of the fill loop: harvest the checkpoint, apply, rebuild, report.

The loop is: search, harvest, apply, verify, push -- then repeat until every
destination has a gallery. Doing that by hand is five commands each time and an
easy way to apply a plan against stale data, which has already bitten once: a
base plan saved before some rows were written silently dropped those rows and
only `check.py` noticed.

So this always rebuilds the base from the credits table as it stands now, and
only ever *adds* rows for entities that have no gallery yet. An entity whose
gallery already works is never churned -- re-selecting it risks replacing
verified photographs with a marginally better candidate for no gain, and the
regenerated credits and alt text would move underneath it.

Usage:
    python3 tools/gallery/batch.py            # one cycle
    python3 tools/gallery/batch.py --quiet    # only print the final count
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SCRATCH = Path("/tmp/opencode")
PLAN_OUT = SCRATCH / "batch-plan.json"


def counts() -> tuple[int, int, int]:
    """(destinations with a row, destinations, photographs) for both data files."""
    rows = []
    for f in ("destinations.json", "festivals.json"):
        rows += json.loads((ROOT / "backend" / "data" / f).read_text())
    with_row = [r for r in rows if r.get("images")]
    dest = [r for r in json.loads((ROOT / "backend" / "data" / "destinations.json").read_text())]
    dest_row = [r for r in dest if r.get("images")]
    return len(dest_row), len(dest), sum(len(r["images"]) for r in with_row)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    say = (lambda *a: None) if args.quiet else print

    before = counts()
    say(f"before: {before[0]}/{before[1]} destinations, {before[2]} photographs")

    # 1. Rebuild the base from the credits table as it stands.
    base_path = SCRATCH / "batch-base.json"
    rc = subprocess.run(
        [sys.executable, str(HERE / "plan_from_credits.py"), "--out", str(base_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if rc.returncode:
        print(rc.stdout + rc.stderr, file=sys.stderr)
        return 1
    base_rows = json.loads(base_path.read_text())

    # Drop duplicate rows before anything else touches them.
    #
    # The credits table is generated from the plan, so when install() emitted one
    # row three times for the same local file, the table faithfully recorded three
    # identical rows -- and this base is read back from that table. Re-applying it
    # would keep all three forever: nothing downstream compares against what is
    # already written, so a bad plan round-trips through the credits into a bad
    # plan again. First occurrence wins, matching install()'s own first-claimant
    # rule for colliding filenames.
    seen_files: set[str] = set()
    deduped: list[dict] = []
    dropped = 0
    for row in base_rows:
        key = f"{row.get('entity','')}:{row.get('file','')}"
        if key in seen_files:
            dropped += 1
            continue
        seen_files.add(key)
        deduped.append(row)
    base_rows = deduped
    if dropped:
        say(f"  dropped {dropped} duplicate row(s) from the credits table")

    # 2. Harvest whatever the checkpoint has that is not credited yet.
    rc = subprocess.run(
        [sys.executable, str(HERE / "harvest.py"), "--install", "--out", str(SCRATCH / "batch-harvest.json")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if rc.returncode:
        print(rc.stdout + rc.stderr, file=sys.stderr)
        return 1
    harvest_path = SCRATCH / "batch-harvest.json"
    if not harvest_path.exists():
        say("  no harvest produced (nothing new in the checkpoint)")
        harvest_rows: list[dict] = []
    else:
        harvest_rows = json.loads(harvest_path.read_text())

    # 3. Add for anything whose photo strip does not render yet.
    rows = []
    for f in ("destinations.json", "festivals.json"):
        rows += json.loads((ROOT / "backend" / "data" / f).read_text())
    # Not simply "has no images array": an entity credited with a single
    # photograph has a row in the credits table, so testing for that froze it at
    # one forever -- Fort Apollonia had fifty candidates pass screening and still
    # could not reach the two photographs the strip needs. The condition is
    # whether the strip will actually render, and duplicates against the base are
    # excluded by file rather than by entity, so a partial gallery can grow.
    MIN_WANT = 2
    rendered = {r["id"] for r in rows if len(r.get("images") or []) >= MIN_WANT}
    base_keys = {f"{r.get('entity','')}:{r.get('file','')}" for r in base_rows}
    new_rows = [
        r
        for r in harvest_rows
        if r["entity"] not in rendered
        and f"{r['entity']}:{r['file']}" not in base_keys
    ]

    if not new_rows:
        say("  nothing new to apply")
        print(f"{before[0]}/{before[1]}")
        return 0

    final = base_rows + new_rows
    PLAN_OUT.write_text(json.dumps(final, indent=2, ensure_ascii=False) + "\n")
    say(f"  adding {len(new_rows)} photograph(s) for {sorted({r['entity'] for r in new_rows})}")

    # 4. Apply, rebuild derivatives, verify.
    for cmd, label in (
        ([str(HERE / "apply.py"), "--plan", str(PLAN_OUT)], "apply"),
        (["tools/build_image_variants.py"], "variants"),
        ([str(HERE / "check.py")], "check"),
    ):
        target = cmd[0] if cmd[0].startswith("/") else str(ROOT / cmd[0])
        rc = subprocess.run([sys.executable, target, *cmd[1:]], cwd=ROOT, capture_output=True, text=True)
        if rc.returncode:
            print(f"\n{label} FAILED:\n{rc.stdout}\n{rc.stderr}", file=sys.stderr)
            return 1
        if label == "apply":
            for line in rc.stdout.splitlines():
                if "places given" in line or "too thin" in line:
                    say(f"    {line.strip()}")

    after = counts()
    say(f"after: {after[0]}/{after[1]} destinations, {after[2]} photographs")
    print(f"{after[0]}/{after[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
