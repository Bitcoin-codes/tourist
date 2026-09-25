# Taking online deposits (Paystack)

Guests can reserve with a **30% deposit** paid online, and settle the balance
on arrival. Pay on arrival stays the default, and if no Paystack key is set the
page behaves exactly as it did before any of this existed.

**Current setup: Paystack only.** That covers Visa and Mastercard (including
diaspora-issued cards) and Ghana Mobile Money — MTN, Telecel and AirtelTigo —
charged in cedis. Everything a guest needs to pay a deposit today.

## How it works

1. The guest picks "pay a deposit now". The form only offers the gateways the
   server actually has keys for (`GET /api/payments/methods`).
2. The server recomputes the total from its own price list, takes 30%, and
   creates the payment with Paystack.
3. The guest is redirected to Paystack's hosted checkout — card and MoMo
   details never touch this site.
4. Paystack confirms payment two ways: a webhook, and a live check when the
   guest returns. **Paystack is the source of truth**; the database is a cache
   of it, so a pass always shows the right state even if a write failed.
5. The pass/booking email is sent only once money has actually arrived.

Card data never reaches the server, so there is nothing PCI-scoped to worry about.

## 1. Get your key

dashboard.paystack.com → Settings → API Keys → **Secret Key**.

Start with the **test** key (`sk_test_…`). It opens a real sandbox checkout and
moves no money. Only switch to the live key when you are ready to take real
payments — at which point you replace the env var and redeploy.

## 2. Add it to Vercel

Vercel → your project → Settings → Environment Variables:

| Variable | Value |
|---|---|
| `PAYSTACK_SECRET_KEY` | `sk_test_…`, then `sk_live_…` |
| `DEPOSIT_PERCENT` | optional, defaults to `30` |
| `USD_GHS_RATE` | optional, defaults to `12.5` — only used to *display* a USD estimate |

Then redeploy. Env vars only apply to a fresh deployment.

Do not commit the key. `backend/.env` is safe for local work — `.gitignore:15`
covers `.env*` — but Vercel's dashboard is the better place for the live key.

## 3. Point the webhook at your site

This is the step that's easy to miss. Without it, a paid deposit only shows up
when the guest happens to return to the page.

Paystack → Settings → API Keys & Webhooks → add:

```
https://tourist-ten-psi.vercel.app/api/payments/webhook/paystack
```

Events: `charge.success`. Turn on "Send test webhooks" while testing.

Paystack webhooks carry no signature, so the endpoint believes nothing in the
body — it re-reads the transaction from Paystack's own verify API first. A
forged callback changes nothing.

## 4. Run the database migration

```
supabase/migrations/20260925120000_add_booking_payments.sql
```

Adds the payment columns to `bookings`. Until it runs, **everything still
works** — bookings save without the payment columns and payment state is read
live from Paystack. The columns are what let a confirmed deposit persist
without another Paystack call.

The migration also creates a permissive UPDATE policy, matching the table's
existing posture. The tighter option is to set `SUPABASE_SERVICE_ROLE_KEY` in
Vercel and then drop that policy:

```sql
drop policy if exists "public update bookings" on public.bookings;
```

## 5. Mobile Money

Nothing to switch on — it's part of the Paystack checkout your guests already
see. If you'd rather not show it, remove `'momo'` from the `methods` list for
`paystack` in `backend/payments.py`; the option then never appears on the form.

## International cards

In the Paystack dashboard, Settings → Preferences → tick **Accept international
payments**. Without it, only Ghana-issued cards can pay — which would block
your diaspora customers.

Paystack reviews travel agencies more closely for this, and may ask for an IATA
licence or a signed partnership agreement. Local cards and Mobile Money are
unaffected, so you're not blocked while that happens.

## Changing a price

Prices live in `backend/payments.py` (`SERVICE_PRICING`) — the server is the
authority on what anyone is charged. The booking form picks them up from
`GET /api/payments/methods`, so the figure a guest sees and the figure charged
cannot drift apart. Change it in one place.

## If you ever want USD or PayPal later

Not possible with Paystack alone: a Ghana Paystack account settles in cedis
only, and Ghana cannot receive into a PayPal business account directly. Both
need a second gateway (Flutterwave is the usual route), which is why a provider
adapter is already in `backend/payments.py`. Until you add its key it stays
completely dormant — the form is built from what is actually configured, so it
can never offer a route that would fail. See "If you ever want USD or PayPal later" above.

## What is deliberately not here

- **Refunds.** A paid deposit is recorded but there is no self-service refund
  button; handle those by hand in the Paystack dashboard.
- **Full online payment.** The deposit is the default. To charge the whole
  amount, set `DEPOSIT_PERCENT=100`.
