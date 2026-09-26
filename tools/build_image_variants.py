#!/usr/bin/env python3
"""Build right-sized JPEG derivatives of every image the site serves.

The problem this solves
-----------------------
Destination cards render at 291x180 CSS pixels (356x180 on a 390px phone) and
the tour tiles at about 305x190. The originals are 640-1920px wide and average
166 KB, so the destinations grid alone asked the browser for 23 MB to fill a grid
of thumbnails. Images trickled in so slowly that cards sat visibly empty, which
is what made the site feel broken.

The fix is to let the browser choose a right-sized file per display. This script
writes derivatives next to each original:

    <name>-400.jpg   for 1x displays
    <name>-800.jpg   for 2x (retina) displays

and the frontend selects between them with `srcset`/`sizes`.

Two rules keep this from wasting space
-------------------------------------
1. Never upscale: a source narrower than the target is left alone, since
   "resizing" it upwards only produces a bigger, blurrier file. A source of
   exactly the target width is re-encoded in place instead, because the
   original is often saved at a quality a thumbnail does not need.
2. Never write a derivative that is not smaller than its source. Re-encoding a
   330px JPEG at 800px "produces" a 330px file that is often *larger* than the
   original, so those are skipped entirely.

Because a variant may legitimately not exist, the true available widths are
written to frontend/js/image-variants.js. The frontend reads that map instead
of guessing, so every `w` descriptor it emits is truthful and no request can
404.

Originals are left untouched: they are the licence-attributed source and remain
the fallback whenever no derivative exists.

Usage
-----
    python tools/build_image_variants.py           # build what is missing/outdated
    python tools/build_image_variants.py --force   # rebuild everything
    python tools/build_image_variants.py --check   # verify only; exit 1 if stale
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent.parent
IMAGE_ROOT = ROOT / "assets" / "images"
IMAGE_PREFIX = "assets/images/"

# Output width -> JPEG quality. Quality is deliberately modest: these files are
# only ever painted into boxes 291-356 CSS pixels wide, so anything above the
# mid-70s is invisible on screen while costing real megabytes on a phone.
VARIANTS: dict[int, int] = {400: 76, 800: 76}

# Vector formats are already resolution-independent: nothing to downscale.
SKIP_SUFFIXES = {".svg"}

# Loaded by the pages before any image markup is generated.
MANIFEST = ROOT / "frontend" / "js" / "image-variants.js"

# Matches a filename this script itself produced, so a derivative is never
# mistaken for a source. Keep in step with VARIANTS.
VARIANT_NAME = re.compile(r"-(?:" + "|".join(str(w) for w in VARIANTS) + r")\.jpg$", re.IGNORECASE)

# Removes just the width from a derivative filename, leaving the extension, so
# "foo-400.jpg" recovers to "foo.jpg". VARIANT_NAME cannot be used for this
# because it also consumes ".jpg".
VARIANT_WIDTH = re.compile(r"-(?:" + "|".join(str(w) for w in VARIANTS) + r")(?=\.[a-z0-9]+$)", re.IGNORECASE)


# --------------------------------------------------------------------------
# which images the frontend actually asks for
# --------------------------------------------------------------------------
def referenced_images() -> list[Path]:
    """Every assets/images path referenced by data, markup or JS.

    Derived from real references rather than by walking the folder, so no
    derivative is ever generated for an image nothing displays.
    """
    found: set[str] = set()

    def add(value: object) -> None:
        if isinstance(value, str) and value.startswith(IMAGE_PREFIX):
            found.add(value)

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("image", "img", "photo", "thumbnail"):
                    add(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for data_file in sorted((ROOT / "backend" / "data").glob("*.json")):
        try:
            walk(json.loads(data_file.read_text()))
        except json.JSONDecodeError as exc:
            print(f"  warning: {data_file.name} is not valid JSON ({exc})", file=sys.stderr)

    pattern = re.compile(r"""["'(](assets/images/[^"')]+)["')]""")
    for html_file in sorted(ROOT.glob("*.html")):
        for match in pattern.finditer(html_file.read_text(errors="ignore")):
            add(match.group(1))
    for js_file in list(ROOT.glob("*.js")) + sorted((ROOT / "frontend" / "js").glob("*.js")):
        if js_file == MANIFEST:
            # This file lists the derivatives themselves. Scanning it would make
            # every derivative look like a fresh source and build derivatives of
            # derivatives, forever.
            continue
        for match in pattern.finditer(js_file.read_text(errors="ignore")):
            add(match.group(1))

    # The markup now contains srcset URLs, so the same applies there: a path
    # that is already a derivative is not a source.
    originals = {p for p in found if not VARIANT_NAME.search(p)}

    # Break the circularity. The markup this script reads now points at the
    # derivatives it generates, so a source can lose its last reference the
    # moment a build rewrites its `src`. Recover the original from any
    # derivative path that appears, which makes the whole thing idempotent.
    for path in list(found):
        stripped = VARIANT_WIDTH.sub("", path)
        if stripped != path and (ROOT / stripped).exists():
            originals.add(stripped)

    # Absolute paths, so this works from any working directory.
    return sorted(ROOT / p for p in originals if (ROOT / p).exists())


def repo_relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


# --------------------------------------------------------------------------
# building
# --------------------------------------------------------------------------
def variant_path(source: Path, width: int) -> Path:
    """Must stay in step with variantUrl() in frontend/js/images.js."""
    return source.with_name(f"{source.stem}-{width}.jpg")


def flatten(image: Image.Image) -> Image.Image:
    """RGB-ready copy, compositing any alpha onto white."""
    rgba = image.convert("RGBA")
    canvas = Image.new("RGB", rgba.size, (255, 255, 255))
    canvas.paste(rgba, mask=rgba.split()[3])
    return canvas


def build_variant(source: Path, width: int, quality: int, dry_run: bool = False) -> tuple[Path, int] | None:
    """Write one derivative. Returns (path, bytes), or None if it would be waste.

    Skipped when the source is already narrower than the target (that would mean
    upscaling) or when the re-encode does not beat the source on size.

    With dry_run the encode still happens, into memory, so --check reaches the
    same decision the real build would. Skipping the encode would make --check
    report as missing variants that the build deliberately declines to create,
    because the re-encode would not have been smaller than the original.
    """
    target = variant_path(source, width)
    with Image.open(source) as raw:
        source_width, source_height = raw.size
        image = flatten(raw)

    if source_width < width:
        # Narrower than the target: any "derivative" would be an upscale.
        return None

    if source_width > width:
        image = image.resize(
            (width, max(1, round(source_height * width / source_width))),
            Image.LANCZOS,
        )
    # When source_width == width this is a straight re-encode at native size.
    # Worth doing: the original is often saved at a higher quality than a
    # thumbnail needs, and without it a 2x display has only the 400w candidate
    # to choose from and gets a visibly soft image.

    original_size = source.stat().st_size

    if dry_run:
        probe = io.BytesIO()
        image.save(probe, "JPEG", quality=quality, optimize=True, progressive=True)
        if probe.tell() >= original_size:
            return None
        return target, probe.tell()

    image.save(target, "JPEG", quality=quality, optimize=True, progressive=True)

    if target.stat().st_size >= original_size:
        # Re-encoding did not pay for itself. Drop it and let the frontend use
        # the original, rather than shipping a bigger file under a smaller name.
        target.unlink()
        return None

    return target, target.stat().st_size


def is_current(source: Path, target: Path) -> bool:
    return target.exists() and target.stat().st_mtime >= source.stat().st_mtime


def write_manifest(entries: dict[str, list[int]]) -> None:
    body = "\n".join(f'    "{path}": {widths},' for path, widths in sorted(entries.items()))
    MANIFEST.write_text(
        "// GENERATED FILE - do not edit by hand.\n"
        "// Rebuild with:  python tools/build_image_variants.py\n"
        "//\n"
        "// Maps each source image to the derivative widths that actually exist, so\n"
        "// frontend/js/images.js can emit a truthful srcset. Images absent from this\n"
        "// map have no derivatives and are served as-is.\n"
        "window.IMAGE_VARIANTS = {\n"
        f"{body}\n"
        "};\n"
    )


# --------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--check", action="store_true", help="verify without writing; exit 1 if anything is missing or stale")
    parser.add_argument("--force", action="store_true", help="rebuild every variant even if it looks current")
    parser.add_argument("--prune", action="store_true", help="delete derivatives that are no longer wanted (e.g. after changing VARIANTS)")
    args = parser.parse_args()

    all_sources = referenced_images()
    if not all_sources:
        print("error: no referenced images found - has the data layout changed?", file=sys.stderr)
        return 2

    vectors = [p for p in all_sources if p.suffix.lower() in SKIP_SUFFIXES]
    sources = [p for p in all_sources if p.suffix.lower() not in SKIP_SUFFIXES]
    if vectors:
        print(f"{len(vectors)} vector image(s) need no derivatives (already scalable):")
        for path in vectors:
            print(f"  {repo_relative(path)}")

    print(f"\nraster images: {len(sources)}\n")

    manifest: dict[str, list[int]] = {}
    built_bytes = 0
    built = 0
    skipped_small = 0
    skipped_no_gain = 0
    unreadable: list[Path] = []
    stale: list[Path] = []
    on_disk_bytes = 0

    for source in sources:
        key = repo_relative(source)
        for width, quality in sorted(VARIANTS.items()):
            target = variant_path(source, width)
            try:
                with Image.open(source) as probe:
                    source_width = probe.size[0]
            except UnidentifiedImageError:
                unreadable.append(source)
                break

            if source_width < width:
                skipped_small += 1
                continue

            if not args.force and is_current(source, target):
                manifest.setdefault(key, []).append(width)
                on_disk_bytes += target.stat().st_size
                continue

            if args.check:
                # Decide whether a variant *would* be built before calling it
                # stale, otherwise --check flags variants the build
                # intentionally skips.
                if build_variant(source, width, quality, dry_run=True) is not None:
                    stale.append(target)
                continue

            result = build_variant(source, width, quality)
            if result is None:
                skipped_no_gain += 1
                continue
            _, size = result
            manifest.setdefault(key, []).append(width)
            built_bytes += size
            on_disk_bytes += size
            built += 1

    if unreadable:
        print(f"warning: {len(unreadable)} image(s) could not be read, left alone:")
        for path in unreadable:
            print(f"  {repo_relative(path)}")

    if args.check:
        problems = len(stale) + len(unreadable)
        if problems:
            if stale:
                print(f"\nSTALE: {len(stale)} derivative(s) missing or older than their source, e.g.")
                for path in stale[:8]:
                    print(f"  {repo_relative(path)}")
            print("\nrun:  python tools/build_image_variants.py")
            return 1
        print("all derivatives present and up to date")
        return 0

    write_manifest(manifest)

    if args.prune:
        wanted = {
            variant_path(ROOT / src, w).resolve()
            for src, widths in manifest.items()
            for w in widths
        }
        removed = 0
        for path in sorted(IMAGE_ROOT.rglob("*.jpg")):
            if not VARIANT_NAME.search(path.name):
                continue
            if path.resolve() not in wanted:
                path.unlink()
                removed += 1
                print(f"  pruned {repo_relative(path)}")
        print(f"pruned {removed} orphaned derivative(s)")

    original_bytes = sum(p.stat().st_size for p in sources)
    print(f"wrote {built} derivative(s) this run, {built_bytes / 1024 / 1024:.1f} MB")
    print(f"skipped: {skipped_small} too small to shrink, {skipped_no_gain} re-encode was not smaller")
    print(f"\noriginals        : {original_bytes / 1024 / 1024:6.1f} MB")
    print(f"derivatives      : {on_disk_bytes / 1024 / 1024:6.1f} MB across {len(manifest)} image(s)")
    print(f"manifest         : {repo_relative(MANIFEST)} ({len(manifest)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
