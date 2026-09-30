# tools/gallery

Builds the extra photographs shown in each destination's and festival's *View
Details* window, from Wikimedia Commons, with an attribution record for every
file.

The pipeline lives in the repository rather than in a scratch directory because
it lived in one and a reboot took it. The photographs in
`assets/images/gallery/` survived; the record of which Commons file each one is
did not, and `recover.py` exists because of that.

## Order of operations

```sh
# 1. Is everything already on disk accounted for? Run this first, always.
venv/bin/python tools/gallery/recover.py

# 2. Fill the gaps: search Commons, filter, assign each photograph to one place.
venv/bin/python tools/gallery/select.py --report-only     # see what would happen
venv/bin/python tools/gallery/select.py --install

# 3. Write the result into the data files and the credits table.
venv/bin/python tools/gallery/apply.py --plan /tmp/opencode/gallery-select/select-plan.json
venv/bin/python tools/gallery/apply.py --plan /tmp/opencode/gallery-select/select-plan.json --alt-review

# 4. Build the served derivatives, then check everything.
venv/bin/python tools/build_image_variants.py
venv/bin/python tools/gallery/check.py
```

Downloaded images, API caches and intermediate plans all live in
`/tmp/opencode/`. Nothing in this directory is a cache, and nothing here should
be: `/tmp/opencode` is assumed to be lost at any time, and every script there
can be rebuilt from what is in the repository.

`apply.py` accepts the plan from either `recover.py` (a dict keyed by entity) or
`select.py` (a flat list), and the two can be combined by concatenating them —
which is the situation the site is actually in, since 29 destinations have files
on disk and the rest do not.

## The scripts

| File | What it decides |
| --- | --- |
| `commons.py` | Cached, throttled Commons API client. `licence_of()` returns a verdict, not a string, and an uploader's restriction note beats their self-declared free tag. |
| `filters.py` | Whether a file may be shown as a photograph of a given place. Titles, categories and descriptions only. |
| `select.py` | Search, filter, and then give each photograph to exactly one destination. Downloads and installs. |
| `recover.py` | Match the files already installed back to their Commons sources. |
| `apply.py` | Write `images` arrays into the data files and regenerate the credits table. |
| `check.py` | Verify the data and the files: sizes, alt text, credits, one-gallery-per-photograph. |
| `pixels.py` | Whether two image files are the same picture. |
| `test_filters.py` | 49 assertions on the filter rules. |
| `test_pixels.py` | 23 assertions on the picture matcher. |

Run both test files directly; they need no network and finish in seconds.

## Things that are decided, and why

**Nothing crops or retouches an installed file.** Installs are byte-identical to
the Commons 1920px downscale of the original. An earlier version cropped to 16:10
and white-balanced by hand, which was defensible when images went straight into
a hero tile with a fixed aspect and is wrong for 3:2 thumbnails that
`object-fit: cover` already handles. It also made the files unrecoverable: the
pixel signature can prove a local file is the same image as a Commons thumbnail
and cannot prove it is the same image as a *cropped* one.

**A photograph belongs to exactly one gallery.** "Fort Batenstein" photographs
usually mention Keta, and so do "Fort Good Hope" photographs, so without a global
step both galleries fill with the same picture of a Keta street. `select.py`
scores how specifically each file's metadata names each destination — full name in
a title beats full name in a category beats a distinctive word in a description —
and gives each file to the best one.

**The filters are biased toward false acceptance.** An over-strict filter does
not fail loudly, it empties a gallery, and an empty gallery is indistinguishable
from "this place has no photographs on Commons". Every rule that was loosened
because it was rejecting correct photographs is listed in the `filters.py`
comments, and the reason is always a file that was thrown out wrongly.

**Alt text is the place name plus whatever the file name added.** Commons
descriptions are catalogue entries, not descriptions of views: five photographs of
Osu Castle all carry the same "located in Osu, Ghana, on the coast of the Gulf of
Guinea". `apply.py --alt-review` lists the ones that fell back to a bare
"Photograph of {place}", which is most of them. Writing them properly needs
someone looking at the photographs.

## What has not been verified

- **No photograph has been looked at.** There is no browser attached to the
  environment these scripts were built in. Every rule here was derived from
  Commons metadata and from measurement, and every photograph is an unmodified
  copy of a Commons thumbnail whose title names the place — but sharpness,
  exposure and "is this actually a picture of that place" have not been checked
  by eye. The filters are a substitute for looking, not a replacement for it.
- **`assets/images/slavetrade.jpeg` has no established provenance.** Its author,
  licence and subject are unknown. It is the one image on the site whose right to
  display has not been confirmed, and `IMAGE-CREDITS.md` says so.
