# Taking online deposits (Paystack + Flutterwave)

Guests can now reserve with a **30% deposit** paid online, and settle the balance
on arrival. Nothing about pay-on-arrival has changed: it is still the default,
and it still works if no payment keys are set at all.

## How it works

1. The guest picks "pay a deposit now". The form only offers the gateways the
   server actually has keys for (`GET /api/payments/methods`).
2. The server recomputes the total from its own price list, takes 30%, and
   creates the payment with the gateway.
3. The guest is redirected to the gateway's hosted checkout — card or MoMo
   details never touch this site.
4. The gateway confirms payment two ways: a webhook, and a live check when the
   guest returns. **The gateway is the source of truth**; the database is a
   cache of it, so a pass always shows the right state even if a write failed.
5. The pass/booking email is sent only once money has actually arrived.

Card data never reaches the server, so there is nothing PCI-scoped to worry about.

## 1. Get your keys

**Paystack** — dashboard.paystack.com → Settings → API Keys.
**Flutterwave** — dashboard.flutterwave.com → Settings → API Keys (a *test*
secret key while you are trying this out).

Start with the **test** keys. They open a real sandbox checkout and move no
money. Only switch to the live keys when you are ready to take real payments.

## 2. Add them to Vercel

Vercel → your project → Settings → Environment Variables → add:

| Variable | Value |
|---|---|
| `PAYSTACK_SECRET_KEY` | `sk_test_...` then `sk_live_...` |
| `FLW_SECRET_KEY` | `FLWSECK_TEST-...` then `FLWSECK-...` |
| `FLW_WEBHOOK_SECRET` | from Flutterwave → Settings → API Keys → Webhook secret |
| `DEPOSIT_PERCENT` | optional, defaults to `30` |
| `USD_GHS_RATE` | optional, defaults to `12.5` — the rate used to show and settle USD |

Then redeploy. (For local work the same names go in `backend/.env`.)

## 3. Point the webhooks at your site

This is the part that is easy to miss, and without it a paid deposit only shows
up when the guest happens to return to the page.

- **Paystack** — Settings → API Keys & Webhooks → add
  `https://your-domain.com/api/payments/webhook/paystack`, events
  `charge.success`. Enable "Send test webhooks" while testing.
- **Flutterwave** — Settings → Webhooks → add
  `https://your-domain.com/api/payments/webhook/flutterwave`.

Both are re-verified against the gateway's own API before anything is marked
paid, so a forged callback changes nothing.

## 4. Run the database migration

```
supabase/migrations/20260925120000_add_booking_payments.sql
```

Adds the payment columns to `bookings`. Until it runs, **everything still
works** — bookings save without the payment columns and payment state is read
live from the gateway. The columns are what let a confirmed deposit persist
without another gateway call.

The migration also creates a permissive UPDATE policy, matching the table's
existing posture. The tighter option is to set `SUPABASE_SERVICE_ROLE_KEY` in
Vercel and then drop that policy:

```sql
drop policy if exists "public update bookings" on public.bookings;
```

## 5. Turn on PayPal (optional, and not guaranteed)

PayPal cannot pay a Ghana-based business account directly, so it comes through
Flutterwave: request "PayPal" under Settings → Business Preference → Payment
methods. If Flutterwave declines, the option simply never appears on your site —
the form is built from what your account can actually charge. Cards (Visa and
Mastercard, including diaspora-issued) and Mobile Money work regardless.

## Changing a price

Prices live in `backend/payments.py` (`SERVICE_PRICING`) — the server is the
authority on what anyone is charged. The booking form picks them up from
`GET /api/payments/methods`, so the figure a guest sees and the figure charged
cannot drift apart. Change it in one place.

## What is deliberately not here

- **Refunds.** A paid deposit is recorded but there is no self-service refund
  button; handle those by hand in the gateway dashboard.
- **Full online payment.** The deposit is the default. To charge the whole
  amount, set `DEPOSIT_PERCENT=100`.
