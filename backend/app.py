"""Flask REST API Backend for vistaGHANA Tourism Platform"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json
import os
import uuid

app = Flask(__name__)
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def load_json(filename: str) -> list | dict:
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filename: str, data: list | dict) -> None:
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


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

    bookings = load_json('bookings.json')
    bookings.append(booking)
    save_json('bookings.json', bookings)

    return jsonify({
        'success': True,
        'message': 'Booking confirmed!',
        'data': {
            'reference': booking_ref,
            'booking': booking
        }
    }), 201


@app.route('/api/bookings/<ref>', methods=['GET'])
def get_booking(ref: str):
    bookings = load_json('bookings.json')
    booking = next((b for b in bookings if b['reference'] == ref), None)

    if not booking:
        return jsonify({'success': False, 'error': 'Booking not found'}), 404

    return jsonify({'success': True, 'data': booking})


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
