"""Flask REST API Backend for vistaGHANA Tourism Platform"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json
import os
import io
import base64
import uuid
import smtplib
import urllib.request
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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


def persist_booking(booking: dict) -> bool:
    """Persist a booking to Supabase Postgres (serverless-friendly), falling
    back to the local JSON file. Never raises."""
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            endpoint = SUPABASE_URL.rstrip('/') + '/rest/v1/bookings'
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
                'createdAt': booking['createdAt']
            }
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(row).encode(),
                headers={
                    'Content-Type': 'application/json',
                    'apikey': SUPABASE_KEY,
                    'Authorization': 'Bearer ' + SUPABASE_KEY,
                    'Prefer': 'return=minimal'
                })
            with urllib.request.urlopen(req, timeout=15) as res:
                return res.status in (200, 201, 204)
        except Exception:
            pass

    try:
        bookings = load_json('bookings.json')
        bookings.append(booking)
        save_json('bookings.json', bookings)
        return True
    except Exception:
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
    return (os.environ.get('SITE_URL') or 'http://localhost:5000').rstrip('/')


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


def send_confirmation_email(booking: dict, qr_uri: str | None) -> bool:
    host = os.environ.get('MAIL_HOST')
    port = int(os.environ.get('MAIL_PORT', '587'))
    user = os.environ.get('MAIL_USER')
    password = os.environ.get('MAIL_PASS')
    mail_from = os.environ.get('MAIL_FROM') or user
    if not (host and user and password):
        return False

    services = ', '.join(booking.get('services') or []) or 'None selected'
    qr_block = f'<p><img src="{qr_uri}" alt="QR Arrival Pass" width="160" height="160" style="border-radius:10px;"/></p>' if qr_uri else ''
    html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;margin:auto;">
      <h2 style="color:#0066CC;">Akwaaba to Ghana &mdash; Booking Confirmed!</h2>
      <p>Hi <strong>{booking.get('fullName', '')}</strong>, your arrival services pass is ready.</p>
      <table style="border-collapse:collapse;width:100%;line-height:1.7;">
        <tr><th style="text-align:left;color:#555;padding:4px 8px;">Booking Ref</th><td><strong>{booking.get('reference', '')}</strong></td></tr>
        <tr><th style="text-align:left;color:#555;padding:4px 8px;">Airport Pickup</th><td>{booking.get('airport', '')}</td></tr>
        <tr><th style="text-align:left;color:#555;padding:4px 8px;">Arrival</th><td>{booking.get('arrivalDate', '')} {booking.get('arrivalTime', '')}</td></tr>
        <tr><th style="text-align:left;color:#555;padding:4px 8px;">Flight</th><td>{booking.get('flightNumber', '') or '&mdash;'}</td></tr>
        <tr><th style="text-align:left;color:#555;padding:4px 8px;">Travelers</th><td>{booking.get('travelers', '')}</td></tr>
        <tr><th style="text-align:left;color:#555;padding:4px 8px;">Services</th><td>{services}</td></tr>
        <tr><th style="text-align:left;color:#555;padding:4px 8px;">Total</th><td>GHS {booking.get('totalGHS', 0)} (~${booking.get('totalUSD', 0)} USD)</td></tr>
      </table>
      {qr_block}
      <p style="color:#888;font-size:0.85rem;">Show this pass to your airport chauffeur upon landing. Payment is on arrival &mdash; Visa, MoMo or cash.</p>
    </div>
    """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Your Ghana Arrival Pass — {booking.get('reference', '')}"
    msg['From'] = mail_from
    msg['To'] = booking.get('email', '')
    msg.attach(MIMEText(f"Reference: {booking.get('reference', '')}", 'plain'))
    msg.attach(MIMEText(html, 'html'))

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


def send_confirmation_whatsapp(booking: dict) -> bool:
    sid = os.environ.get('TWILIO_ACCOUNT_SID')
    token = os.environ.get('TWILIO_AUTH_TOKEN')
    wa_from = os.environ.get('TWILIO_WHATSAPP_FROM')
    if not (sid and token and wa_from):
        return False
    digits = ''.join(c for c in (booking.get('phone') or '') if c.isdigit())
    if not digits:
        return False
    to = '+' + digits
    body = (f"Memorra Travels — Booking Confirmed!\n"
            f"Ref: {booking.get('reference', '')}\n"
            f"Name: {booking.get('fullName', '')}\n"
            f"Airport Pickup: {booking.get('airport', '')}\n"
            f"Arrival: {booking.get('arrivalDate', '')} {booking.get('arrivalTime', '')}\n"
            f"Services: {', '.join(booking.get('services') or []) or 'None'}\n"
            f"Show this pass to your airport chauffeur upon landing. Pay on arrival.")
    endpoint = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    media_url = f"{site_url()}/api/pass-qr/{booking.get('reference', '')}"
    data = urllib.parse.urlencode({
        'From': wa_from, 'To': to, 'Body': body, 'MediaUrl': media_url
    }).encode()
    req = urllib.request.Request(endpoint, data=data)
    import base64 as b64
    req.add_header('Authorization', 'Basic ' + b64.b64encode(f"{sid}:{token}".encode()).decode())
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.status in (200, 201)
    except Exception:
        return False


# ── Destination Endpoints ──────────────────────────────────────────────

@app.route('/api/destinations', methods=['GET'])
def get_destinations():
    category = request.args.get('category', 'all')
    search = request.args.get('search', '').lower().strip()

    destinations = load_json('destinations.json')

    if category != 'all':
        destinations = [d for d in destinations if d['category'] == category]

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

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    data = request.get_json()

    required_fields = ['fullName', 'email', 'phone', 'arrivalDate', 'airport']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400

    booking_ref = f"GH-{datetime.now().year}-{uuid.uuid4().int % 9000 + 1000}"

    booking = {
        'id': str(uuid.uuid4()),
        'reference': booking_ref,
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

    persist_booking(booking)

    pass_url = f"{site_url()}/booking.html?ref={booking_ref}"
    pass_qr = make_qr_svg(pass_url)
    email_sent = send_confirmation_email(booking, pass_qr)
    whatsapp_sent = send_confirmation_whatsapp(booking)

    return jsonify({
        'success': True,
        'message': 'Booking confirmed!',
        'data': {
            'reference': booking_ref,
            'booking': booking,
            'passQr': pass_qr,
            'passUrl': pass_url,
            'emailSent': email_sent,
            'whatsappSent': whatsapp_sent
        }
    }), 201


@app.route('/api/bookings/<ref>', methods=['GET'])
def get_booking(ref: str):
    booking = find_booking(ref)

    if not booking:
        return jsonify({'success': False, 'error': 'Booking not found'}), 404

    return jsonify({'success': True, 'data': booking})


@app.route('/api/pass-qr/<ref>', methods=['GET'])
def pass_qr(ref: str):
    """Public QR pass image (PNG) for a booking reference. Served so Twilio
    (and clients) can fetch the receipt image via MediaUrl."""
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
