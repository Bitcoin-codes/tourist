"""Flask REST API Backend for vistaGHANA Tourism Platform"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json
import os
import re
import io
import base64
import uuid
import smtplib
import urllib.request
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import parseaddr
from html import escape

try:  # package import - Vercel does `from backend.app import app`
    from . import payments
except ImportError:  # direct run - `python3 app.py` from backend/
    import payments

# Load secrets from a local .env file. Real environment variables always win
# (load_dotenv does not override), so Vercel's env vars take precedence in
# production and this is effectively a no-op there.
try:
    from dotenv import load_dotenv
    _here = os.path.dirname(os.path.abspath(__file__))
    for _candidate in (
        os.path.join(_here, '.env'),            # backend/.env
        os.path.join(_here, '..', '.env'),      # project root .env
        os.path.join(os.getcwd(), '.env'),      # wherever we were started
    ):
        if os.path.isfile(_candidate):
            load_dotenv(_candidate, override=False)
except Exception:
    pass

try:
    import qrcode
    from qrcode.image.svg import SvgPathImage
    QR_AVAILABLE = True
except Exception:
    QR_AVAILABLE = False

app = Flask(__name__)
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# The site's Supabase project (same public client key already shipped in the
# HTML). The `bookings` table intentionally allows public insert/read via RLS,
# so the anon key works for the one row per request. Override with the
# SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY) env vars.
SUPABASE_URL = os.environ.get('SUPABASE_URL') or 'https://efyiskwpdqqmgghdtppq.supabase.co'
SUPABASE_KEY = (
    os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    or os.environ.get('SUPABASE_ANON_KEY')
    or 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVmeWlza3dwZHFxbWdnaGR0cHBxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg0NjIzMjksImV4cCI6MjEwNDAzODMyOX0.o3-p5w8Or0EhsE0xhVXc36ahTNsIiErMyLuK00ReiCA'
)


def load_json(filename: str) -> list | dict:
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filename: str, data: list | dict) -> None:
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Columns the payments migration adds to `bookings`. Kept in one place so a
# deployment that hasn't run the migration yet still saves bookings: the insert
# is retried without them, and the payment is always re-readable from the
# gateway itself, which is the real source of truth.
PAYMENT_COLUMNS = (
    'paymentStatus', 'paymentProvider', 'paymentMethod', 'paymentRef',
    'amountPaid', 'currency', 'balanceDueGHS', 'paidAt', 'paymentMeta',
)

SUPABASE_HEADERS = {
    'Content-Type': 'application/json',
    'apikey': SUPABASE_KEY,
    'Authorization': 'Bearer ' + SUPABASE_KEY,
}


def _supabase_booking_row(booking: dict) -> dict:
    row = {
        'id': booking['id'],
        'reference': booking['reference'],
        'fullName': booking['fullName'],
        'email': booking['email'],
        'phone': booking['phone'],
        'arrivalDate': booking['arrivalDate'],
        'arrivalTime': booking['arrivalTime'],
        'airport': booking['airport'],
        'flightNumber': booking['flightNumber'],
        'travelers': booking['travelers'],
        'services': booking['services'],
        'totalGHS': booking['totalGHS'],
        'totalUSD': booking['totalUSD'],
        'paymentMethod': booking['paymentMethod'],
        'specialRequests': booking['specialRequests'],
        'status': booking['status'],
        'createdAt': booking['createdAt'],
    }
    row.update({k: v for k, v in booking.items() if k in PAYMENT_COLUMNS})
    return row


def _insert_booking_row(row: dict) -> bool:
    try:
        endpoint = SUPABASE_URL.rstrip('/') + '/rest/v1/bookings'
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(row).encode(),
            headers=dict(SUPABASE_HEADERS, **{'Prefer': 'return=minimal'}))
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.status in (200, 201, 204)
    except Exception:
        return False


def persist_booking(booking: dict) -> bool:
    """Persist a booking to Supabase Postgres (serverless-friendly), falling
    back to the local JSON file. Never raises."""
    if SUPABASE_URL and SUPABASE_KEY:
        row = _supabase_booking_row(booking)
        attempts = [row]
        if any(col in row for col in PAYMENT_COLUMNS):
            # The payments migration may not have been applied yet. A booking
            # must never fail to save over a missing payment column.
            attempts.append({k: v for k, v in row.items() if k not in PAYMENT_COLUMNS})
        for attempt in attempts:
            if _insert_booking_row(attempt):
                return True

    try:
        bookings = load_json('bookings.json')
        bookings.append(booking)
        save_json('bookings.json', bookings)
        return True
    except Exception:
        return False


def update_booking_payment(ref: str, fields: dict) -> bool:
    """Best-effort write of a booking's payment state. Never raises and never
    blocks: the gateway is the source of truth, so a pass still reads correctly
    when this can't be written (e.g. the UPDATE policy isn't in place yet)."""
    body = {k: v for k, v in (fields or {}).items() if k in PAYMENT_COLUMNS}
    if not body or not ref:
        return False

    if SUPABASE_URL and SUPABASE_KEY:
        try:
            endpoint = (SUPABASE_URL.rstrip('/') + '/rest/v1/bookings?reference=eq.'
                        + urllib.parse.quote(str(ref), safe=''))
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(body).encode(),
                method='PATCH',
                headers=dict(SUPABASE_HEADERS, **{'Prefer': 'return=minimal'}))
            with urllib.request.urlopen(req, timeout=15) as res:
                if res.status in (200, 201, 204):
                    return True
        except Exception:
            pass

    try:
        bookings = load_json('bookings.json')
        for booking in bookings:
            if booking.get('reference') == ref:
                booking.update(body)
                save_json('bookings.json', bookings)
                return True
    except Exception:
        pass
    return False


def find_booking(ref: str) -> dict | None:
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            endpoint = (SUPABASE_URL.rstrip('/') + '/rest/v1/bookings?reference=eq.'
                        + urllib.parse.quote(ref) + '&select=*')
            req = urllib.request.Request(endpoint, headers={
                'apikey': SUPABASE_KEY,
                'Authorization': 'Bearer ' + SUPABASE_KEY
            })
            with urllib.request.urlopen(req, timeout=15) as res:
                rows = json.loads(res.read().decode('utf-8'))
                if rows:
                    return rows[0]
        except Exception:
            pass
    try:
        bookings = load_json('bookings.json')
        return next((b for b in bookings if b['reference'] == ref), None)
    except Exception:
        return None


def site_url() -> str:
    url = os.environ.get('SITE_URL')
    if url:
        return url.rstrip('/')
    vercel_url = (os.environ.get('VERCEL_PROJECT_PRODUCTION_URL')
                  or os.environ.get('VERCEL_URL'))
    if vercel_url:
        return 'https://' + vercel_url.strip('/')
    return 'http://localhost:5000'


def make_qr_svg(payload: str) -> str | None:
    if not QR_AVAILABLE:
        return None
    try:
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=6, border=2)
        qr.add_data(payload)
        qr.make(fit=True)
        img = qr.make_image(image_factory=SvgPathImage)
        buf = io.BytesIO()
        img.save(buf)
        svg = buf.getvalue().decode('utf-8')
        return 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode('utf-8')).decode('ascii')
    except Exception:
        return None


def make_qr_png(payload: str) -> bytes | None:
    if not QR_AVAILABLE:
        return None
    try:
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=6, border=2)
        qr.add_data(payload)
        qr.make(fit=True)
        from qrcode.image.pure import PyPNGImage
        img = qr.make_image(image_factory=PyPNGImage)
        buf = io.BytesIO()
        img.save(buf)
        return buf.getvalue()
    except Exception:
        return None


def send_confirmation_email(booking: dict, pass_url: str, qr_png: bytes | None,
                             payment: dict | None = None) -> bool:
    """Send the arrival pass by email (free tier: any SMTP account).

    The QR is attached as a real PNG referenced via Content-ID (`cid:`), which
    renders in Gmail/Outlook/Apple Mail. Inline `data:` URIs are stripped by
    those clients, so we deliberately do not embed the image that way. A
    clickable link to the pass is included as a fallback for image blocking.

    `payment` is the verified gateway result; when present the email becomes a
    deposit receipt rather than a pay-on-arrival confirmation.
    """
    host = os.environ.get('MAIL_HOST')
    port = int(os.environ.get('MAIL_PORT', '587'))
    user = os.environ.get('MAIL_USER')
    password = os.environ.get('MAIL_PASS')
    if not (host and user and password):
        return False

    # The SMTP envelope sender must be a bare address — passing
    # "Name <address>" to sendmail() fails. MAIL_FROM may be either form;
    # MAIL_FROM_NAME supplies the human-readable From header.
    _, mail_from = parseaddr(os.environ.get('MAIL_FROM') or user or '')
    mail_from = mail_from or user
    mail_from_name = (os.environ.get('MAIL_FROM_NAME') or '').strip()

    ref = escape(str(booking.get('reference', '')))
    services = escape(', '.join(booking.get('services') or []) or 'None selected')
    safe_url = escape(str(pass_url), quote=True)

    paid_block = ''
    if payment and payment.get('paid'):
        provider_label = (payments.PROVIDERS.get(payment.get('provider') or '', {})
                          .get('name') or (payment.get('provider') or '').title())
        amount = float(payment.get('amount') or 0)
        currency = payment.get('currency') or 'GHS'
        symbol = '$' if currency == 'USD' else 'GHS '
        total = float(booking.get('totalGHS') or 0)
        paid_ghs = float(payment.get('amountGHS') or amount)
        balance = round(max(total - paid_ghs, 0.0), 2)
        paid_block = (
            '<tr><th style="text-align:left;color:#555;padding:4px 8px;">Deposit received</th>'
            f'<td><strong>{symbol}{amount:,.2f} {escape(str(currency))}</strong> via '
            f'{escape(provider_label)} &mdash; ref {escape(str(payment.get("reference") or ""))}</td></tr>'
            '<tr><th style="text-align:left;color:#555;padding:4px 8px;">Balance on arrival</th>'
            f'<td>GHS {balance:,.2f}</td></tr>'
        )

    qr_block = ''
    if qr_png:
        qr_block = ('<p style="text-align:center;margin:20px 0 6px;">'
                    '<img src="cid:arrival-pass-qr" alt="QR Arrival Pass" '
                    'width="170" height="170" '
                    'style="border-radius:12px;background:#fff;padding:6px;border:1px solid #e5e7eb;" '
                    '/></p>')

    html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;margin:auto;">
      <h2 style="color:#0066CC;">Akwaaba to Ghana &mdash; {('Deposit Received!' if paid_block else 'Booking Confirmed!')}</h2>
      <p>Hi <strong>{escape(str(booking.get('fullName', '')))}</strong>, your arrival services pass is ready.</p>
      <table style="border-collapse:collapse;width:100%;line-height:1.7;">
        <tr><th style="text-align:left;color:#555;padding:4px 8px;">Booking Ref</th><td><strong>{ref}</strong></td></tr>
        <tr><th style="text-align:left;color:#555;padding:4px 8px;">Airport Pickup</th><td>{escape(str(booking.get('airport', '')))}</td></tr>
        <tr><th style="text-align:left;color:#555;padding:4px 8px;">Arrival</th><td>{escape(str(booking.get('arrivalDate', '')))} {escape(str(booking.get('arrivalTime', '')))}</td></tr>
        <tr><th style="text-align:left;color:#555;padding:4px 8px;">Flight</th><td>{escape(str(booking.get('flightNumber', ''))) or '&mdash;'}</td></tr>
        <tr><th style="text-align:left;color:#555;padding:4px 8px;">Travelers</th><td>{escape(str(booking.get('travelers', '')))}</td></tr>
        <tr><th style="text-align:left;color:#555;padding:4px 8px;">Services</th><td>{services}</td></tr>
        <tr><th style="text-align:left;color:#555;padding:4px 8px;">Total</th><td>GHS {escape(str(booking.get('totalGHS', 0)))} (~${escape(str(booking.get('totalUSD', 0)))} USD)</td></tr>
        {paid_block}
      </table>
      {qr_block}
      <p style="text-align:center;margin:14px 0 4px;">
        <a href="{safe_url}" style="display:inline-block;background:#0066CC;color:#ffffff;text-decoration:none;padding:12px 22px;border-radius:8px;font-weight:bold;">Open your arrival pass</a>
      </p>
      <p style="text-align:center;font-size:0.82rem;color:#6b7280;margin-top:4px;">
        Or scan the QR code above with your phone camera.
      </p>
      <p style="color:#888;font-size:0.85rem;">Show this pass to your airport chauffeur upon landing. {('The balance is settled on arrival &mdash; Visa, MoMo or cash.' if paid_block else 'Payment is on arrival &mdash; Visa, MoMo or cash.')}</p>
    </div>
    """
    msg = MIMEMultipart('mixed')
    msg['Subject'] = f"Your Ghana Arrival Pass — {booking.get('reference', '')}"
    msg['From'] = f'{mail_from_name} <{mail_from}>' if mail_from_name else mail_from
    msg['To'] = booking.get('email', '')

    related = MIMEMultipart('related')
    alt = MIMEMultipart('alternative')
    alt.attach(MIMEText(
        f"Reference: {booking.get('reference', '')}\n"
        f"Open your arrival pass: {pass_url}\n"
        f"Show this pass to your airport chauffeur upon landing.", 'plain'))
    alt.attach(MIMEText(html, 'html'))
    related.attach(alt)

    if qr_png:
        img = MIMEImage(qr_png, name=f'arrival-pass-{booking.get("reference", "")}.png')
        img.add_header('Content-ID', '<arrival-pass-qr>')
        img.add_header('Content-Disposition', 'inline')
        related.attach(img)

    msg.attach(related)

    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.ehlo()
            if os.environ.get('MAIL_STARTTLS', '1') == '1':
                server.starttls()
            server.login(user, password)
            server.sendmail(mail_from, [booking.get('email', '')], msg.as_string())
        return True
    except Exception:
        return False


def send_contact_email(name: str, contact: str, message: str, ticket: str) -> bool:
    """Email a chatbot handoff to a human agent (free: same Brevo SMTP).

    The visitor never leaves the chat — they hand the conversation off here
    and the agent reaches them on whatever they gave: a phone number or an
    address. `NOTIFY_EMAIL` decides who receives it and falls back to the
    verified sender, so this works with nothing new to configure.

    Both name and message come straight from the visitor, so they are escaped
    before they reach HTML, newlines are stripped from anything that lands in
    a header (Subject injection), and the visitor's contact only ever appears
    in Reply-To — never as From or To — so it cannot spoof the sender.
    Reply-To is set only for an address: a phone number is meaningless there,
    so it is put in the body instead where the agent can call or WhatsApp it.
    """
    host = os.environ.get('MAIL_HOST')
    port = int(os.environ.get('MAIL_PORT', '587'))
    user = os.environ.get('MAIL_USER')
    password = os.environ.get('MAIL_PASS')
    if not (host and user and password):
        return False

    _, mail_from = parseaddr(os.environ.get('MAIL_FROM') or user or '')
    mail_from = mail_from or user
    mail_from_name = (os.environ.get('MAIL_FROM_NAME') or '').strip()

    _, notify = parseaddr(os.environ.get('NOTIFY_EMAIL') or mail_from)
    notify = notify or mail_from

    # Header-safe forms: no CR/LF may survive into a header value.
    subj_name = re.sub(r'[\r\n]+', ' ', name).strip()[:80] or 'visitor'
    subj_contact = re.sub(r'[\r\n]+', ' ', contact).strip()[:120]

    # Reply-To only means something for an address.
    is_email = bool(re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]{2,}', contact))
    reply_to = contact if is_email else ''
    # `UNKNOWN` is what the chatbot substitutes when a visitor demanded an
    # immediate transfer before giving details — render it as absence, not
    # as a literal word the agent would have to decode.
    shown_contact = '' if contact.upper() == 'UNKNOWN' else contact

    safe_name = escape(name)[:120] or 'Not given'
    safe_contact = escape(shown_contact)[:254]
    safe_ticket = escape(ticket)
    safe_msg = (escape(message)[:2000]
                .replace('\r\n', '<br>')
                .replace('\n', '<br>'))

    if not safe_contact:
        reply_cell = '<em style="color:#999;">Not provided</em>'
    elif is_email:
        reply_cell = f'<a href="mailto:{safe_contact}">{safe_contact}</a>'
    else:
        reply_cell = (f'{safe_contact} '
                      '<span style="color:#888;font-size:0.85rem;">(phone — call or WhatsApp)</span>')

    footer = ('Reply to this email to reach the visitor directly.' if is_email else
              'Call or WhatsApp the number above to reach the visitor directly.' if safe_contact else
              'No reply channel was given — the visitor only wanted the request logged.')

    html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;margin:auto;">
      <h2 style="color:#0066CC;">Chat handoff {safe_ticket}</h2>
      <p>A visitor asked the chatbot to be passed to a human agent.</p>
      <table style="border-collapse:collapse;width:100%;line-height:1.7;">
        <tr><th style="text-align:left;color:#555;padding:4px 8px;">From</th><td>{safe_name}</td></tr>
        <tr><th style="text-align:left;color:#555;padding:4px 8px;">Reply to</th><td>{reply_cell}</td></tr>
        <tr><th style="text-align:left;color:#555;padding:4px 8px;">Ticket</th><td><strong>{safe_ticket}</strong></td></tr>
      </table>
      <p style="background:#f7f9fc;border-left:3px solid #0066CC;padding:10px 12px;border-radius:4px;margin:14px 0;">{safe_msg}</p>
      <p style="color:#888;font-size:0.85rem;">{footer}</p>
    </div>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'Chat handoff {ticket} - {subj_name}'
    msg['From'] = f'{mail_from_name} <{mail_from}>' if mail_from_name else mail_from
    msg['To'] = notify
    msg['Reply-To'] = f'{subj_name} <{reply_to}>' if reply_to else notify
    msg.attach(MIMEText(
        f'Chat handoff {ticket}\n'
        f'From: {subj_name}\n'
        f'Contact: {subj_contact or "not provided"}\n\n'
        f'{message}', 'plain'))
    msg.attach(MIMEText(html, 'html'))

    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.ehlo()
            if os.environ.get('MAIL_STARTTLS', '1') == '1':
                server.starttls()
            server.login(user, password)
            server.sendmail(mail_from, [notify], msg.as_string())
        return True
    except Exception:
        return False


def normalize_phone(raw: str) -> str:
    """Format a Ghana/local number as international (+233...). Kept for the
    WhatsApp `wa.me` deep link the frontend builds and for any future SMS
    provider (Hubtel / Africa's Talking)."""
    digits = ''.join(c for c in (raw or '') if c.isdigit())
    if not digits:
        return ''
    if len(digits) == 10 and digits.startswith('0'):
        digits = '233' + digits[1:]
    return '+' + digits


# ── Destination Endpoints ──────────────────────────────────────────────

@app.route('/api/destinations', methods=['GET'])
def get_destinations():
    category = request.args.get('category', 'all')
    tour_type = request.args.get('tourType', 'all')
    search = request.args.get('search', '').lower().strip()

    destinations = load_json('destinations.json')

    if category != 'all':
        destinations = [d for d in destinations if d['category'] == category]

    # A place can be several kinds of tour at once — Kejetia Market is both a
    # market and heritage — so tourType is a membership test, not the equality
    # comparison `category` uses. `.get` keeps a record written before this
    # field existed from throwing a 500.
    if tour_type != 'all':
        destinations = [
            d for d in destinations
            if tour_type in (d.get('tourTypes') or [])
        ]

    if search:
        destinations = [
            d for d in destinations
            if search in d['name'].lower()
            or search in d['location'].lower()
            or search in d['region'].lower()
            or search in d['shortDesc'].lower()
            or search in d['fullDesc'].lower()
            or any(search in h.lower() for h in d['highlights'])
        ]

    return jsonify({
        'success': True,
        'count': len(destinations),
        'data': destinations
    })


@app.route('/api/destinations/<dest_id>', methods=['GET'])
def get_destination(dest_id: str):
    destinations = load_json('destinations.json')
    destination = next((d for d in destinations if d['id'] == dest_id), None)

    if not destination:
        return jsonify({'success': False, 'error': 'Destination not found'}), 404

    return jsonify({'success': True, 'data': destination})


# ── Festival Endpoints ─────────────────────────────────────────────────

@app.route('/api/festivals', methods=['GET'])
def get_festivals():
    festivals = load_json('festivals.json')
    return jsonify({
        'success': True,
        'count': len(festivals),
        'data': festivals
    })


@app.route('/api/festivals/<festival_id>', methods=['GET'])
def get_festival(festival_id: str):
    festivals = load_json('festivals.json')
    festival = next((f for f in festivals if f['id'] == festival_id), None)

    if not festival:
        return jsonify({'success': False, 'error': 'Festival not found'}), 404

    return jsonify({'success': True, 'data': festival})


# ── Practical Info Endpoint ────────────────────────────────────────────

@app.route('/api/info/<info_type>', methods=['GET'])
def get_practical_info(info_type: str):
    info_data = load_json('practical_info.json')
    info = info_data.get(info_type)

    if not info:
        return jsonify({'success': False, 'error': 'Info not found'}), 404

    return jsonify({'success': True, 'data': info})


# ── Region Endpoints ───────────────────────────────────────────────────

def _resolve_region(region: dict) -> dict:
    destinations = load_json('destinations.json')
    festivals = load_json('festivals.json')

    resolved = dict(region)
    resolved['destinations'] = [
        d for d in destinations if d['id'] in region.get('destinations', [])
    ]
    resolved['festivals'] = [
        f for f in festivals if f['id'] in region.get('festivals', [])
    ]
    resolved['hasContent'] = bool(resolved['destinations'] or resolved['festivals'])
    return resolved


@app.route('/api/regions', methods=['GET'])
def get_regions():
    regions = load_json('regions.json')
    return jsonify({
        'success': True,
        'count': len(regions),
        'data': regions
    })


@app.route('/api/regions/<region_id>', methods=['GET'])
def get_region(region_id: str):
    regions = load_json('regions.json')
    region = next((r for r in regions if r['id'] == region_id), None)

    if not region:
        return jsonify({'success': False, 'error': 'Region not found'}), 404

    return jsonify({'success': True, 'data': _resolve_region(region)})


# ── Booking Endpoints ──────────────────────────────────────────────────

REQUIRED_BOOKING_FIELDS = ['fullName', 'email', 'phone', 'arrivalDate', 'airport']


def _new_booking(data: dict, payment_fields: dict | None = None) -> dict:
    """Build a booking record. `payment_fields` marks it as awaiting a deposit
    rather than a confirmed pay-on-arrival reservation."""
    booking = {
        'id': str(uuid.uuid4()),
        'reference': f"GH-{datetime.now().year}-{uuid.uuid4().int % 9000 + 1000}",
        'fullName': data['fullName'],
        'email': data['email'],
        'phone': data['phone'],
        'arrivalDate': data['arrivalDate'],
        'arrivalTime': data.get('arrivalTime', ''),
        'airport': data['airport'],
        'flightNumber': data.get('flightNumber', ''),
        'travelers': data.get('travelers', 2),
        'services': data.get('services', []),
        'totalGHS': data.get('totalGHS', 0),
        'totalUSD': data.get('totalUSD', 0),
        'paymentMethod': data.get('paymentMethod', 'arrival'),
        'specialRequests': data.get('specialRequests', ''),
        'status': 'confirmed',
        'createdAt': datetime.now().isoformat()
    }
    if payment_fields:
        booking['status'] = 'awaiting_payment'
        booking.update(payment_fields)
    return booking


@app.route('/api/bookings', methods=['POST'])
def create_booking():
    data = request.get_json(silent=True) or {}

    for field in REQUIRED_BOOKING_FIELDS:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400

    booking = _new_booking(data)
    booking_ref = booking['reference']

    persist_booking(booking)

    # Free delivery channels: email (SMTP) + the wa.me share link the frontend
    # builds. No paid messaging provider required.
    pass_url = f"{site_url()}/booking.html?ref={booking_ref}"
    pass_qr = make_qr_svg(pass_url)
    pass_png = make_qr_png(pass_url)
    email_sent = send_confirmation_email(booking, pass_url, pass_png)

    return jsonify({
        'success': True,
        'message': 'Booking confirmed!',
        'data': {
            'reference': booking_ref,
            'booking': booking,
            'passQr': pass_qr,
            'passUrl': pass_url,
            'emailSent': email_sent,
            'whatsappSent': False
        }
    }), 201


@app.route('/api/bookings/<ref>', methods=['GET'])
def get_booking(ref: str):
    booking = find_booking(ref)

    if not booking:
        return jsonify({'success': False, 'error': 'Booking not found'}), 404

    return jsonify({'success': True, 'data': booking})


# ── Payments ───────────────────────────────────────────────────────────
# A guest reserves with a deposit (DEPOSIT_PERCENT, 30% by default); the rest
# is settled on arrival. The provider is never trusted and neither is the
# browser: the amount is recomputed from SERVICE_PRICING here, and a payment
# only counts once Paystack/Flutterwave confirms it on a server-side verify.

@app.route('/api/payments/methods', methods=['GET'])
def payment_methods():
    """What the form may offer: only gateways that have keys configured, each
    with the currencies and methods that account can actually charge."""
    return jsonify({'success': True, 'data': payments.describe_methods()})


def _record_payment(provider: str, reference: str, result: dict) -> dict:
    """Fold a verified gateway result into the booking and, the first time it
    succeeds, send the pass/receipt by email."""
    booking = find_booking(reference)
    if not booking:
        return {'recorded': False, 'booking': None}

    was_paid = str(booking.get('paymentStatus') or '') in ('deposit_paid', 'paid')
    fields = {
        'paymentStatus': 'deposit_paid' if result.get('paid') else str(result.get('status') or 'unpaid'),
        'paymentProvider': provider,
        'paymentRef': str(result.get('transactionId') or result.get('reference') or ''),
        'amountPaid': result.get('amount') or 0,
        'currency': result.get('currency') or 'GHS',
        'paidAt': str(result.get('paidAt') or ''),
    }
    if result.get('paid') and not was_paid:
        total = float(booking.get('totalGHS') or 0)
        fields['balanceDueGHS'] = round(max(total - float(result.get('amountGHS') or 0), 0.0), 2)

    update_booking_payment(reference, fields)
    booking.update(fields)

    if result.get('paid') and not was_paid and booking.get('email'):
        pass_url = f"{site_url()}/booking.html?ref={reference}"
        send_confirmation_email(booking, pass_url, make_qr_png(pass_url), payment=result)

    return {'recorded': True, 'booking': booking}


@app.route('/api/payments/initialize', methods=['POST'])
def payment_initialize():
    data = request.get_json(silent=True) or {}

    for field in REQUIRED_BOOKING_FIELDS:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400

    provider, method = payments.parse_choice(data.get('paymentMethod'))
    currency = (data.get('currency') or 'GHS').upper()

    if not provider or not method:
        return jsonify({'success': False, 'error': 'Choose how you would like to pay.'}), 400
    if not payments.provider_ready(provider):
        label = payments.PROVIDERS.get(provider, {}).get('name', provider.title())
        return jsonify({'success': False, 'error': f'{label} payments are not set up on this site yet.'}), 402
    if not payments.supports(provider, currency, method):
        label = payments.PROVIDERS[provider]['name']
        # Point at the route that does work rather than just refusing.
        hint = ' Pay in GHS, or choose Flutterwave for USD.' if currency == 'USD' else ''
        return jsonify({'success': False,
                        'error': f'{label} cannot take {method.upper()} in {currency}.{hint}'}), 400

    try:
        q = payments.quote(data.get('serviceValues'), currency)
    except payments.PaymentError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

    # Names/prices for the record come from the quote, not the browser.
    booking = _new_booking({
        **data,
        'services': q['services'],
        'totalGHS': q['totalGHS'],
        'totalUSD': int(round(q['totalGHS'] / q['rate'])),
        'paymentMethod': f'{provider}:{method}',
    }, payment_fields={
        'paymentStatus': 'pending',
        'paymentProvider': provider,
        'paymentMethod': method,
        'paymentRef': '',
        'amountPaid': 0,
        'currency': currency,
        'balanceDueGHS': q['balanceGHS'],
    })
    reference = booking['reference']

    callback = (f"{site_url()}/booking.html?payment=return&ref={urllib.parse.quote(reference)}"
                f"&provider={provider}")
    metadata = {
        'bookingRef': reference,
        'services': ', '.join(q['services']),
        'depositPercent': q['depositPercent'],
        'balanceDueGHS': q['balanceGHS'],
    }

    try:
        session = payments.initialize(
            provider, amount=q['deposit'], currency=currency, reference=reference,
            email=data.get('email'), name=data.get('fullName'), phone=data.get('phone'),
            callback_url=callback, metadata=metadata)
    except payments.PaymentError as e:
        # Nothing was charged, and no booking row is written: this is a failed
        # attempt, not a reservation.
        return jsonify({'success': False, 'error': str(e)}), 502

    persist_booking(booking)
    if session.get('paymentRef'):
        update_booking_payment(reference, {'paymentRef': session['paymentRef']})

    return jsonify({
        'success': True,
        'data': {
            'reference': reference,
            'provider': provider,
            'paymentRef': session.get('paymentRef'),
            'authorizationUrl': session['authorizationUrl'],
            'amount': q['deposit'],
            'currency': currency,
            'depositPercent': q['depositPercent'],
            'totalGHS': q['totalGHS'],
            'balanceGHS': q['balanceGHS'],
        }
    }), 201


@app.route('/api/payments/status', methods=['GET'])
def payment_status():
    """Live payment state for a booking, read back from the gateway.

    Called when the guest returns from checkout, and by the pass view: the
    gateway, not our database, is what decides whether money arrived, so this
    stays correct even if a write failed or the webhook is delayed.
    """
    reference = (request.args.get('ref') or '').strip()
    if not reference:
        return jsonify({'success': False, 'error': 'Missing booking reference'}), 400

    booking = find_booking(reference) or {}
    provider = (request.args.get('provider') or booking.get('paymentProvider') or '').strip().lower()

    stored = {
        'status': booking.get('paymentStatus') or ('unpaid' if booking else 'unknown'),
        'amountPaid': booking.get('amountPaid') or 0,
        'currency': booking.get('currency') or 'GHS',
        'balanceDueGHS': booking.get('balanceDueGHS') or 0,
        'paidAt': booking.get('paidAt') or '',
        'totalGHS': booking.get('totalGHS') or 0,
    }
    if not provider or not payments.provider_ready(provider):
        return jsonify({'success': True, 'data': dict(stored, provider=provider, live=False)})

    try:
        result = payments.verify(provider, reference, booking.get('paymentRef') or None)
    except payments.PaymentError as e:
        return jsonify({'success': True,
                        'data': dict(stored, provider=provider, live=False, note=str(e))})

    _record_payment(provider, reference, result)
    return jsonify({'success': True, 'data': dict(
        stored,
        provider=provider,
        live=True,
        status='deposit_paid' if result.get('paid') else str(result.get('status') or 'unpaid'),
        amountPaid=result.get('amount') or 0,
        amountGHS=result.get('amountGHS') or 0,
        currency=result.get('currency') or stored['currency'],
        channel=result.get('channel') or '',
        paidAt=str(result.get('paidAt') or ''),
        balanceDueGHS=round(max(float(stored['totalGHS'] or 0) - float(result.get('amountGHS') or 0), 0.0), 2),
    )})


@app.route('/api/payments/webhook/paystack', methods=['POST'])
def paystack_webhook():
    """Paystack webhooks carry no signature, so nothing in the body is believed:
    the transaction is re-read from Paystack's verify API first."""
    payload = request.get_json(silent=True) or {}
    reference = (payload.get('data') or {}).get('reference')
    if not reference:
        return jsonify({'success': False, 'error': 'No reference'}), 400

    try:
        result = payments.verify_paystack(reference)
    except payments.PaymentError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

    _record_payment('paystack', reference, result)
    return jsonify({'success': True})


@app.route('/api/payments/webhook/flutterwave', methods=['POST'])
def flutterwave_webhook():
    if not payments.check_flw_webhook_hash(request.headers.get('verif-hash', '')):
        return jsonify({'success': False, 'error': 'Invalid signature'}), 401

    payload = request.get_json(silent=True) or {}
    d = payload.get('data') or {}
    reference = d.get('tx_ref')
    if not reference:
        return jsonify({'success': False, 'error': 'No reference'}), 400

    try:
        result = payments.verify_flutterwave(reference, str(d.get('id') or '') or None)
    except payments.PaymentError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

    _record_payment('flutterwave', reference, result)
    return jsonify({'success': True})


@app.route('/api/pass-qr/<ref>', methods=['GET'])
def pass_qr(ref: str):
    """Public QR pass image (PNG) for a booking reference. Served so email
    clients, share links and any future provider can fetch the receipt image."""
    from flask import Response, send_file
    booking = find_booking(ref)
    if not booking:
        return jsonify({'success': False, 'error': 'Booking not found'}), 404

    payload = f"{site_url()}/booking.html?ref={ref}"
    png = make_qr_png(payload)
    if not png:
        return jsonify({'success': False, 'error': 'QR generation failed'}), 500

    return Response(png, mimetype='image/png', headers={
        'Cache-Control': 'public, max-age=3600'
    })


# ── Wishlist Endpoints ─────────────────────────────────────────────────

@app.route('/api/wishlist', methods=['GET'])
def get_wishlist():
    wishlist = load_json('wishlist.json')
    return jsonify({'success': True, 'data': wishlist})


@app.route('/api/wishlist', methods=['POST'])
def toggle_wishlist():
    data = request.get_json()
    dest_id = data.get('destinationId')

    if not dest_id:
        return jsonify({'success': False, 'error': 'Missing destinationId'}), 400

    wishlist = load_json('wishlist.json')

    if dest_id in wishlist:
        wishlist.remove(dest_id)
        action = 'removed'
    else:
        wishlist.append(dest_id)
        action = 'added'

    save_json('wishlist.json', wishlist)

    return jsonify({
        'success': True,
        'action': action,
        'data': wishlist
    })


# ── Itinerary Endpoint ─────────────────────────────────────────────────

@app.route('/api/itinerary', methods=['POST'])
def generate_itinerary():
    data = request.get_json()
    days = data.get('days', 7)
    style = data.get('style', 'balanced')

    destinations = load_json('destinations.json')

    itinerary = {
        'days': int(days),
        'style': style,
        'plan': []
    }

    if str(days) == '3':
        itinerary['plan'] = [
            {'day': 'Day 1', 'title': 'Accra Heritage & Tafi Atome',
             'activities': ['Black Star Square', 'Tafi Atome Monkey Sanctuary', 'Local lunch in Hohoe']},
            {'day': 'Day 2', 'title': 'Winneba & Cape Coast',
             'activities': ['Aboakyer Festival traditions', 'Cape Coast Castle tour', 'Ocean sunset']},
            {'day': 'Day 3', 'title': 'Crafts & Markets',
             'activities': ['Accra Arts Centre', 'Kente cloth shopping', 'Farewell Jollof & Highlife evening']}
        ]
    elif str(days) == '7':
        itinerary['plan'] = [
            {'day': 'Days 1-2', 'title': 'Accra & Central Coast Fortresses',
             'activities': ['Accra monuments', 'Cape Coast Castle', 'Kakum Canopy Walk', "Elmina Castle"]},
            {'day': 'Days 3-4', 'title': 'Boabeng-Fiema & Ashanti Culture',
             'activities': ['Boabeng-Fiema Monkey Sanctuary', 'Manhyia Palace Museum', 'Bonwire Kente Village']},
            {'day': 'Days 5-7', 'title': 'Volta Region Adventures',
             'activities': ['Tafi Atome Monkeys', 'Wli Waterfalls', 'Mount Afadjato summit']}
        ]
    else:
        itinerary['plan'] = [
            {'day': 'Week 1', 'title': 'Coastal Fortresses & Kumasi Heritage',
             'activities': ['Accra', 'Cape Coast', 'Kakum', 'Boabeng-Fiema', 'Kumasi Royal Heritage']},
            {'day': 'Week 2', 'title': 'Northern Safaris & Volta Waterfalls',
             'activities': ['Tamale Damba', 'Mole Elephant Safari', 'Paga Crocodiles', 'Tafi Atome', 'Wli Waterfalls']}
        ]

    return jsonify({'success': True, 'data': itinerary})


# ── Agent Handoff ──────────────────────────────────────────────────────

@app.route('/api/contact', methods=['POST'])
def contact_agent():
    """Chatbot → human agent handoff.

    The visitor types a question, the bot admits it cannot help, and hands
    the conversation over here. No paid provider: this is the same free
    Brevo SMTP the booking confirmations already use.
    """
    data = request.get_json(silent=True) or {}

    name = str(data.get('name') or '').strip()[:120]
    # The chatbot collects "phone number / email", so this may be either.
    # `email` is still read so an older caller keeps working unchanged.
    contact = str(data.get('contact') or data.get('email') or '').strip()[:254]
    message = str(data.get('message') or '').strip()[:2000]

    if not message:
        return jsonify({'success': False, 'error': 'Message is required.'}), 400

    # `UNKNOWN` is what the frontend sends when a visitor demanded an immediate
    # transfer before giving details. Worth logging, but it has no reply channel.
    # Anything else must be a real address or a real number: whitespace and
    # newlines are excluded so this value can never be smuggled into a header.
    if contact and contact.upper() != 'UNKNOWN':
        is_email = bool(re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]{2,}', contact))
        digits = re.sub(r'\D', '', contact)
        is_phone = (bool(re.fullmatch(r'\+?[\d\s().-]{7,25}', contact))
                    and 7 <= len(digits) <= 15)
        if not (is_email or is_phone):
            return jsonify({'success': False,
                            'error': 'Please enter a valid email address or phone number.'}), 400

    ticket = f"MSG-{datetime.now().year}-{uuid.uuid4().int % 9000 + 1000}"
    sent = send_contact_email(name, contact, message, ticket)

    # `contact` is the mailbox the agent actually reads. The frontend shows it
    # only when `emailSent` is false, so a refused send still leaves the
    # visitor with a real way to reach a person instead of a dead end.
    _, fallback = parseaddr(os.environ.get('NOTIFY_EMAIL')
                            or os.environ.get('MAIL_FROM') or '')

    # There is no `contacts` table, so nothing is persisted — SMTP is the
    # delivery channel. Report the truth rather than claiming success.
    return jsonify({
        'success': True,
        'ticket': ticket,
        'emailSent': sent,
        'contact': fallback
    }), 201


# ── Health Check ───────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'vistaGHANA API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
