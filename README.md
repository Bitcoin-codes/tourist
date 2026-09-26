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

## Layout

- `index.html`, `planner.html`, `regions.html` — load `frontend/js/app.bundle.js`
- `booking.html` — loads `app.js` (root) plus the payment UI in its inline script
- `backend/app.py` — Flask API, run on Vercel as a serverless function
- `backend/payments.py` — the pricing authority (`SERVICE_PRICING`) and the
  Paystack adapter
- `assets/images/` — site photography, see [IMAGE-CREDITS.md](IMAGE-CREDITS.md)
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
