"""Compare the generated credits table against what the site actually shows.

Two directions matter, and they fail differently:

  * shown but not credited is a licence failure -- someone's photograph on the
    site with no attribution attached;
  * credited but not shown is dead weight in a table a human has to read, and
    usually means a plan row survived its gallery.

`check.py` catches the first. This catches the second, which nothing else did.
"""

from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

text = (ROOT / "IMAGE-CREDITS.md").read_text()
match = re.search(
    r"<!-- gallery-credits:start -->(.*?)<!-- gallery-credits:end -->", text, re.S
)
if not match:
    raise SystemExit("no generated credits block found")

lines = [
    line
    for line in match.group(1).splitlines()
    if line.strip().startswith("|") and "---" not in line
]
rows = lines[1:]  # drop the header

credited: set[str] = set()
for row in rows:
    cells = [cell.strip() for cell in row.split("|")]
    # | Place | `name.jpg` | Author | Licence | Source |
    if len(cells) < 3:
        continue
    name = cells[2].strip("`").strip()
    if name.endswith((".jpg", ".jpeg", ".png", ".webp")):
        credited.add(name)

shown: set[str] = set()
for name in ("destinations.json", "festivals.json"):
    for entry in json.loads((ROOT / "backend" / "data" / name).read_text()):
        for image in entry.get("images") or []:
            shown.add(image["image"].rsplit("/", 1)[-1])

print(f"  credit rows: {len(rows)}   credited files: {len(credited)}   shown: {len(shown)}")
missing = sorted(shown - credited)
extra = sorted(credited - shown)
print(f"  shown but not credited : {len(missing)} {missing[:6]}")
print(f"  credited but not shown : {len(extra)} {extra[:6]}")
raise SystemExit(1 if missing else 0)
