# tourist site website

Live site: <https://tourist-ten-psi.vercel.app>

## Before you run `tsc` — read this first

**Do not run `npx tsc -p tsconfig.json`.** It will silently undo working code.

`frontend/js/*.js` is the code that actually ships: the four pages load
`app.bundle.js` directly, and there is no build step in the deploy. Those `.js`
files have been hand-edited since the last compile, so the `.ts` files in
`frontend/ts/` are **stale**.

Compiling therefore *reverts* live fixes. Confirmed examples:

| Recompiling this | Silently undoes |
| --- | --- |
| `frontend/js/ui.js` | removes `applyStoredTheme()`, breaking the shared light/dark theme |
| `frontend/js/config.js` | drops the same-origin `/api` resolution used on Vercel |
| `frontend/js/single.js` | re-enables `renderAttractionPins`, which was deliberately disabled |

`tsc --noEmit` is safe — it type-checks without writing anything. Use that for
verification.

If you do need to change a compiled `.js` file, edit it directly and, if you
want the `.ts` source to match, mirror the change there by hand. Do not
regenerate.

## Images

Destination cards paint into a 291×180 box and the tour tiles into about
305×190, but the source photographs are 640–1920px wide and averaged 166 KB. The
destinations grid was asking the browser for **23 MB** to fill a grid of
thumbnails, and images arrived so slowly that cards sat visibly empty — 20 of 143
had loaded after 50 seconds, which is what made the site look broken.

`tools/build_image_variants.py` writes two derivatives beside every image:

| file | used for |
| --- | --- |
| `<name>-400.jpg` | 1x displays |
| `<name>-800.jpg` | 2x (retina) displays |

`frontend/js/images.js` turns those into a `srcset`, so each visitor fetches one
file at the size it is about to paint. The grid is now **3.8 MB at 1x (6.2×
lighter)** and 10.7 MB at 2x, and all 143 cards load.

```bash
python tools/build_image_variants.py           # build what is missing
python tools/build_image_variants.py --prune   # also drop unused derivatives
python tools/build_image_variants.py --check   # verify only; exit 1 if stale
```

Two rules keep this from wasting space: nothing is ever upscaled, and no
derivative is written unless it is genuinely smaller than the original. Fifteen
photos are already under 400px and small enough to serve as-is, so they have no
derivative and the helper falls back to the original path.

`frontend/js/image-variants.js` is **generated** — it records which widths
actually exist, so every `w` descriptor the browser sees is truthful and no
request can 404. Do not edit it by hand; re-run the script.

If you change a card or tile size in `styles.css`, update the matching preset in
`IMAGE_SIZES` (`frontend/js/images.js`). Those values are the browser's only
clue about how wide an image will be.

## Layout

- `index.html`, `planner.html`, `regions.html` — load `frontend/js/app.bundle.js`
- `booking.html` — loads `app.js` (root) plus the payment UI in its inline script
- `backend/app.py` — Flask API, run on Vercel as a serverless function
- `backend/payments.py` — the pricing authority (`SERVICE_PRICING`) and the
  Paystack adapter
- `assets/images/` — site photography, see [IMAGE-CREDITS.md](IMAGE-CREDITS.md)
- `tools/build_image_variants.py` — generates the right-sized image derivatives
- [PAYMENTS.md](PAYMENTS.md) — how to set up online deposits

## API caching

Public catalogue endpoints (`/api/destinations`, `/api/festivals`, `/api/regions`,
`/api/info/*`, `/api/payments/methods`) are served with a short `max-age` so
Vercel's edge can reuse them. Everything else — anything per-guest, including
`/api/bookings/<ref>`, `/api/payments/status` and `/api/pass-qr/<ref>` — is sent
`no-store`.

That allowlist lives in `backend/app.py` under `PUBLIC_CACHEABLE`. It is
deliberately an allowlist rather than a denylist: **anything not named there is
private by default**, so a new endpoint cannot leak guest data by being added
without a thought. If you add a per-guest endpoint, do not add it to that list.
