"""Online deposits for bookings — Paystack + Flutterwave.

Three rules this module exists to enforce:

1. The browser is never trusted with an amount. `quote()` recomputes the total
   from SERVICE_PRICING, the server's own copy of the prices shown in
   booking.html. The `data-price` attributes in the HTML are display only;
   /api/payments/methods ships this list so the form renders from it and the
   two can't drift into under-charging someone. If you change a price here,
   the form updates itself on the next page load.

2. Secret keys never leave the server. The guest is redirected to the
   provider's hosted checkout, so no card or MoMo detail ever reaches this
   site, and there is nothing to keep PCI-scoped.

3. Nothing is "paid" until the provider says so. Payment is confirmed only by
   re-reading the transaction from Paystack/Flutterwave's own verification
   API (the webhook calls the same code), never from the browser's return URL
   alone, which a guest could edit.
"""

import hashlib
import hmac
import json
import logging
import math
import os
import urllib.error
import urllib.parse
import urllib.request

log = logging.getLogger(__name__)

PAYSTACK_API = 'https://api.paystack.co'
FLW_API = 'https://api.flutterwave.com/v3'

# ── Pricing (server is the authority) ──────────────────────────────────
SERVICE_PRICING = {
    'airport-transfer': {'name': 'Airport VIP Transfer', 'price': 350},
    'tour-guide': {'name': 'Certified Local Tour Guide', 'price': 500},
    'car-rental': {'name': 'Private 4x4 Chauffeur Rental', 'price': 900},
    'monkey-pass': {'name': 'Tafi Atome & Wildlife Fast-Pass', 'price': 400},
    'festival-pass': {'name': 'Royal Cultural Festival VIP Pass', 'price': 600},
}

# ── Gateways ───────────────────────────────────────────────────────────
# `currencies` is what the merchant account can actually charge. A Ghana
# Paystack account settles in cedis only, so USD is Flutterwave's job; that is
# also the account that can be granted PayPal.
PROVIDERS = {
    'paystack': {
        'name': 'Paystack',
        'label': 'Visa / Mastercard card or Ghana Mobile Money',
        'currencies': ['GHS'],
        'methods': [
            {'id': 'card', 'label': 'Card — Visa, Mastercard, Verve'},
            {'id': 'momo', 'label': 'Mobile Money — MTN, Telecel, AirtelTigo'},
        ],
    },
    'flutterwave': {
        'name': 'Flutterwave',
        'label': 'Card, PayPal, Apple Pay, Google Pay or Mobile Money',
        'currencies': ['GHS', 'USD'],
        'methods': [
            {'id': 'card', 'label': 'Card — Visa, Mastercard'},
            {'id': 'paypal', 'label': 'PayPal'},
            {'id': 'applepay', 'label': 'Apple Pay'},
            {'id': 'googlepay', 'label': 'Google Pay'},
            {'id': 'momo', 'label': 'Mobile Money — MTN, Telecel, AirtelTigo'},
        ],
    },
}


class PaymentError(Exception):
    """A payment could not be set up or verified. The message is guest-safe."""


# ── Config ─────────────────────────────────────────────────────────────

def _num_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name) or default)
    except (TypeError, ValueError):
        return float(default)


def deposit_percent() -> int:
    pct = _num_env('DEPOSIT_PERCENT', 30)
    return max(1, min(100, int(pct)))


def usd_ghs_rate() -> float:
    rate = _num_env('USD_GHS_RATE', 12.5)
    return rate if rate > 0 else 12.5


def paystack_key() -> str:
    return (os.environ.get('PAYSTACK_SECRET_KEY') or '').strip()


def flutterwave_key() -> str:
    return (os.environ.get('FLW_SECRET_KEY')
            or os.environ.get('FLUTTERWAVE_SECRET_KEY') or '').strip()


def flw_webhook_secret() -> str:
    return (os.environ.get('FLW_WEBHOOK_SECRET') or '').strip()


def provider_ready(provider: str) -> bool:
    if provider == 'paystack':
        return bool(paystack_key())
    if provider == 'flutterwave':
        return bool(flutterwave_key())
    return False


def supports(provider: str, currency: str, method: str) -> bool:
    conf = PROVIDERS.get(provider)
    if not conf or not provider_ready(provider):
        return False
    if currency not in conf['currencies']:
        return False
    return any(m['id'] == method for m in conf['methods'])


def describe_methods() -> dict:
    """What the booking form is allowed to offer right now."""
    providers = []
    for pid, conf in PROVIDERS.items():
        configured = provider_ready(pid)
        providers.append({
            'id': pid,
            'name': conf['name'],
            'label': conf['label'],
            'configured': configured,
            'currencies': conf['currencies'] if configured else [],
            'methods': conf['methods'] if configured else [],
        })
    return {
        'depositPercent': deposit_percent(),
        'usdGhsRate': usd_ghs_rate(),
        'currency': 'GHS',
        'currencies': ['GHS'] + (['USD'] if provider_ready('flutterwave') else []),
        'providers': providers,
        'services': [
            {'value': v, 'name': s['name'], 'price': s['price']}
            for v, s in SERVICE_PRICING.items()
        ],
    }


# ── Quote ──────────────────────────────────────────────────────────────

def quote(service_values, currency: str = 'GHS') -> dict:
    """Authoritative price for a set of service ids."""
    currency = (currency or 'GHS').upper()
    if currency not in ('GHS', 'USD'):
        raise PaymentError('Choose to pay in GHS or USD.')

    known = [v for v in (service_values or []) if v in SERVICE_PRICING]
    unknown = [v for v in (service_values or []) if v not in SERVICE_PRICING]
    if unknown:
        raise PaymentError('Unrecognised service in the booking.')
    if not known:
        raise PaymentError('Select at least one service before paying a deposit.')

    total_ghs = sum(SERVICE_PRICING[v]['price'] for v in known)
    pct = deposit_percent()
    deposit_ghs = int(math.ceil(total_ghs * pct / 100.0))

    rate = usd_ghs_rate()
    if currency == 'USD':
        total = round(total_ghs / rate, 2)
        deposit = round(deposit_ghs / rate, 2)
    else:
        total = float(total_ghs)
        deposit = float(deposit_ghs)

    deposit = max(deposit, 1.0)  # both gateways reject a zero charge
    return {
        'currency': currency,
        'depositPercent': pct,
        'rate': rate,
        'totalGHS': total_ghs,
        'depositGHS': deposit_ghs,
        'balanceGHS': max(total_ghs - deposit_ghs, 0),
        'total': total,
        'deposit': deposit,
        'balance': round(max(total - deposit, 0.0), 2),
        'services': [SERVICE_PRICING[v]['name'] for v in known],
    }


def parse_choice(value: str):
    """'paystack:momo' -> ('paystack', 'momo')."""
    provider, _, method = (value or '').partition(':')
    return provider.strip(), method.strip()


# ── HTTP ───────────────────────────────────────────────────────────────

# urllib sends "Python-urllib/3.x" by default, and both gateways sit behind
# Cloudflare, which rejects that signature with 403 "error code: 1010". It looks
# exactly like a bad API key, so a real card payment would fail in production
# while every stubbed test still passed. Identify the app honestly instead.
USER_AGENT = 'AkwaabaTours/1.0 (+https://tourist-ten-psi.vercel.app)'


def _request(url: str, payload=None, headers=None, timeout: int = 25) -> dict:
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json', 'User-Agent': USER_AGENT,
                 **(headers or {})},
        method='POST' if data is not None else 'GET')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            body = res.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        code = e.code
        raw = ''
        try:
            raw = e.read().decode('utf-8', 'replace')
        except Exception:
            pass
        # Gateways answer with JSON, but a WAF refusal ("error code: 1010") is
        # plain text, so fall back to the raw body rather than losing it.
        try:
            detail = json.loads(raw).get('message') or ''
        except Exception:
            detail = ''
        if code in (401, 403):
            # Either a wrong/revoked key, or an edge (Cloudflare/WAF) refusal.
            # The guest gets the same safe message for both; the raw body goes to
            # the log so a block is diagnosable instead of looking like a typo.
            log.warning('gateway %s rejected the request: HTTP %s %s', url, code,
                        (detail or raw)[:120])
            # A wrong, revoked or still-unset key. That's our mistake, not the
            # guest's, and "Invalid key" would be meaningless to them.
            raise PaymentError(
                'Card payments are temporarily unavailable. Please pay on arrival, '
                'or contact us and we will take your deposit directly.') from e
        # Provider messages are written for merchants; keep them short and
        # guest-safe, and never echo a raw status code.
        raise PaymentError((detail or 'The payment could not be started. Please try again.')[:200]) from e
    except Exception as e:
        raise PaymentError('Could not reach the payment provider. Please try again.') from e
    try:
        return json.loads(body)
    except Exception as e:
        raise PaymentError('Unreadable response from the payment provider.') from e


# ── Paystack ───────────────────────────────────────────────────────────

def initialize_paystack(*, amount_ghs: float, reference: str, email: str,
                        callback_url: str, metadata: dict) -> dict:
    data = _request(
        PAYSTACK_API + '/transaction/initialize',
        {
            'email': email,
            'amount': int(round(float(amount_ghs) * 100)),  # pesewas
            'currency': 'GHS',
            'reference': reference,
            'callback_url': callback_url,
            'metadata': metadata,
        },
        {'Authorization': 'Bearer ' + paystack_key()})
    if not data.get('status') or not (data.get('data') or {}).get('authorization_url'):
        raise PaymentError(data.get('message') or 'Paystack could not start the payment.')
    d = data['data']
    return {
        'authorizationUrl': d['authorization_url'],
        'paymentRef': d.get('reference') or reference,
        'accessCode': d.get('access_code'),
    }


def verify_paystack(reference: str) -> dict:
    url = PAYSTACK_API + '/transaction/verify/' + urllib.parse.quote(str(reference), safe='')
    data = _request(url, headers={'Authorization': 'Bearer ' + paystack_key()})
    if not data.get('status'):
        raise PaymentError(data.get('message') or 'Paystack could not verify that payment.')
    d = data.get('data') or {}
    amount = round((d.get('amount') or 0) / 100.0, 2)
    return {
        'provider': 'paystack',
        'reference': d.get('reference') or reference,
        'status': d.get('status') or 'unknown',
        'paid': d.get('status') == 'success',
        'amount': amount,
        'amountGHS': amount,
        'currency': d.get('currency') or 'GHS',
        'channel': d.get('channel'),
        'paidAt': d.get('paid_at'),
    }


# ── Flutterwave ────────────────────────────────────────────────────────

def initialize_flutterwave(*, amount: float, currency: str, reference: str,
                           email: str, name: str, phone: str,
                           redirect_url: str, metadata: dict) -> dict:
    payload = {
        'tx_ref': reference,
        'amount': float(amount),
        'currency': currency,
        'redirect_url': redirect_url,
        'customer': {'email': email, 'name': name, 'phone_number': phone},
        'custom': metadata,
        'meta': metadata,
    }
    data = _request(FLW_API + '/payments', payload,
                    {'Authorization': 'Bearer ' + flutterwave_key()})
    d = data.get('data') or {}
    if not d.get('link'):
        raise PaymentError(data.get('message') or 'Flutterwave could not start the payment.')
    return {
        'authorizationUrl': d['link'],
        'paymentRef': str(d.get('id') or reference),
        'txRef': reference,
    }


def verify_flutterwave(reference: str, transaction_id: str | None = None) -> dict:
    headers = {'Authorization': 'Bearer ' + flutterwave_key()}

    if not transaction_id:
        # No stored transaction id (the booking row may predate it, or the
        # update policy isn't in place yet) — look the transaction up by the
        # tx_ref we sent, then verify that one properly.
        qs = urllib.parse.urlencode({'tx_ref': reference, 'per_page': 1})
        listed = _request(FLW_API + '/transactions?' + qs, headers=headers)
        rows = listed.get('data') or []
        if not rows:
            return {'provider': 'flutterwave', 'reference': reference,
                    'status': 'not_found', 'paid': False, 'amount': 0, 'amountGHS': 0,
                    'currency': 'GHS', 'transactionId': None, 'paidAt': None}
        transaction_id = str(rows[0].get('id') or '')

    data = _request(FLW_API + '/transactions/' + urllib.parse.quote(str(transaction_id), safe='') + '/verify',
                    headers=headers)
    d = data.get('data') or {}
    status = d.get('status') or 'unknown'
    amount = float(d.get('amount') or 0)
    currency = d.get('currency') or 'GHS'
    return {
        'provider': 'flutterwave',
        'reference': d.get('tx_ref') or reference,
        'transactionId': str(d.get('id') or transaction_id),
        'status': status,
        'paid': status == 'successful',
        'amount': amount,
        # Normalised to cedis so a balance is comparable whatever was charged.
        'amountGHS': round(amount * usd_ghs_rate(), 2) if currency == 'USD' else amount,
        'currency': currency,
        'channel': d.get('payment_method'),
        'paidAt': d.get('created_at'),
    }


def check_flw_webhook_hash(header: str) -> bool:
    """Flutterwave signs each webhook with `verif-hash`: the sha256 of the
    secret in FLW_WEBHOOK_SECRET. With no secret configured there is nothing
    to compare against, so the caller still verifies the transaction against
    Flutterwave's own API - this hash is a second lock, never the only one."""
    secret = flw_webhook_secret()
    if not secret:
        return True
    expected = hashlib.sha256(secret.encode('utf-8')).hexdigest().lower()
    return hmac.compare_digest((header or '').strip().lower(), expected)


def verify(provider: str, reference: str, transaction_id: str | None = None) -> dict:
    provider = (provider or '').strip().lower()
    if not provider_ready(provider):
        raise PaymentError(f'{provider.title() or "That"} payments are not set up on this site yet.')
    if provider == 'paystack':
        return verify_paystack(reference)
    if provider == 'flutterwave':
        return verify_flutterwave(reference, transaction_id)
    raise PaymentError('Unknown payment provider.')


def initialize(provider: str, *, amount: float, currency: str, reference: str,
                email: str, name: str, phone: str, callback_url: str,
                metadata: dict) -> dict:
    provider = (provider or '').strip().lower()
    if not provider_ready(provider):
        raise PaymentError(f'{provider.title() or "That"} payments are not set up on this site yet.')
    if currency not in PROVIDERS[provider]['currencies']:
        raise PaymentError(
            f'{PROVIDERS[provider]["name"]} cannot charge in {currency} on this account. '
            'Pay in GHS, or choose Flutterwave for USD.')
    if provider == 'paystack':
        return initialize_paystack(amount_ghs=amount, reference=reference, email=email,
                                   callback_url=callback_url, metadata=metadata)
    return initialize_flutterwave(amount=amount, currency=currency, reference=reference,
                                  email=email, name=name, phone=phone,
                                  redirect_url=callback_url, metadata=metadata)
