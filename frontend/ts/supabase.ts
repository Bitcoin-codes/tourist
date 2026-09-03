// @ts-nocheck
/**
 * Supabase backend adapter for Ghana Kora Vista Tours.
 *
 * Self-contained (no ES imports) so it can be loaded as a classic <script>
 * BEFORE frontend/js/app.bundle.js. Attaches functions to window so the
 * standalone bundle can route its API calls through Supabase when configured.
 *
 * Credentials are read from window.__SUPABASE_URL__ and window.__SUPABASE_ANON_KEY__.
 */

// ── Config ────────────────────────────────────────────────────────────
function supabaseCfg() {
  const w = typeof window !== 'undefined' ? window : ({} as any);
  const url = w.__SUPABASE_URL__;
  const anonKey = w.__SUPABASE_ANON_KEY__;
  return url && anonKey ? { url: String(url).replace(/\/$/, ''), anonKey } : null;
}

// ── Low-level PostgREST ───────────────────────────────────────────────
async function sbSelect(table, params = {}) {
  const c = supabaseCfg();
  if (!c) throw new Error('Supabase not configured');
  const q = new URLSearchParams();
  q.set('select', '*');
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') q.set(k, v);
  }
  const res = await fetch(`${c.url}/rest/v1/${table}?${q.toString()}`, {
    headers: { apikey: c.anonKey, Authorization: `Bearer ${c.anonKey}` },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Supabase ${table}: HTTP ${res.status} ${body.slice(0, 200)}`);
  }
  return res.json();
}

async function sbSelectSingle(table, idField, id) {
  const rows = await sbSelect(table, { [idField]: `eq.${id}` });
  return rows.length ? rows[0] : null;
}

// ── Destinations ──────────────────────────────────────────────────────
async function sbGetDestinations(category = 'all', search = '') {
  const params = {};
  if (category !== 'all') params.category = `eq.${category}`;
  let list = await sbSelect('destinations', params);
  if (search) {
    const s = String(search).toLowerCase();
    list = list.filter((d) =>
      [d.name, d.location, d.region, d.shortDesc, d.fullDesc].filter(Boolean).some((f) => String(f).toLowerCase().includes(s)) ||
      (Array.isArray(d.highlights) && d.highlights.some((h) => String(h || '').toLowerCase().includes(s))));
  }
  return { success: true, count: list.length, data: list };
}

async function sbGetDestination(id) {
  const d = await sbSelectSingle('destinations', 'id', id);
  return d ? { success: true, data: d } : { success: false, data: null };
}

// ── Festivals ─────────────────────────────────────────────────────────
async function sbGetFestivals() {
  const list = await sbSelect('festivals');
  return { success: true, count: list.length, data: list };
}

async function sbGetFestival(id) {
  const f = await sbSelectSingle('festivals', 'id', id);
  return f ? { success: true, data: f } : { success: false, data: null };
}

// ── Practical Info ────────────────────────────────────────────────────
async function sbGetInfo(type) {
  const rows = await sbSelect('practical_info', { type: `eq.${type}` });
  const info = rows.length ? rows[0] : null;
  if (!info) return { success: false, data: null };
  return { success: true, data: { title: info.title, badge: info.badge, content: info.content } };
}

// ── Regions ───────────────────────────────────────────────────────────
async function sbGetRegions() {
  const list = await sbSelect('regions');
  return { success: true, count: list.length, data: list };
}

async function sbGetRegion(id) {
  const r = await sbSelectSingle('regions', 'id', id);
  if (!r) return { success: false, data: null };
  const dests = Array.isArray(r.destinations) ? r.destinations : [];
  const fests = Array.isArray(r.festivals) ? r.festivals : [];
  const resolvedDests = [];
  for (const did of dests) {
    const d = await sbSelectSingle('destinations', 'id', did);
    if (d) resolvedDests.push(d);
  }
  const resolvedFests = [];
  for (const fid of fests) {
    const f = await sbSelectSingle('festivals', 'id', fid);
    if (f) resolvedFests.push(f);
  }
  return {
    success: true,
    data: {
      ...r,
      destinations: resolvedDests,
      festivals: resolvedFests,
      hasContent: resolvedDests.length > 0 || resolvedFests.length > 0,
    },
  };
}

// ── Bookings ──────────────────────────────────────────────────────────
function sbUuid() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID();
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

async function sbCreateBooking(data) {
  const c = supabaseCfg();
  if (!c) throw new Error('Supabase not configured');
  const now = new Date().toISOString();
  const ref = `GH-${now.slice(0, 4)}-${Math.floor(Math.random() * 9000) + 1000}`;
  const booking = {
    id: sbUuid(),
    reference: ref,
    fullName: data.fullName,
    email: data.email,
    phone: data.phone,
    arrivalDate: data.arrivalDate || '',
    arrivalTime: data.arrivalTime || '',
    airport: data.airport || '',
    flightNumber: data.flightNumber || '',
    travelers: data.travelers ?? 2,
    services: data.services || [],
    totalGHS: data.totalGHS ?? 0,
    totalUSD: data.totalUSD ?? 0,
    paymentMethod: data.paymentMethod || 'arrival',
    specialRequests: data.specialRequests || '',
    status: 'confirmed',
    createdAt: now,
  };
  const res = await fetch(`${c.url}/rest/v1/bookings`, {
    method: 'POST',
    headers: { apikey: c.anonKey, Authorization: `Bearer ${c.anonKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(booking),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Supabase bookings insert: HTTP ${res.status} ${body.slice(0, 200)}`);
  }
  return { success: true, message: 'Booking confirmed!', data: { reference: ref, booking } };
}

async function sbGetBooking(reference) {
  const rows = await sbSelect('bookings', { reference: `eq.${reference}` });
  return rows.length ? { success: true, data: rows[0] } : { success: false, data: null };
}

// ── Wishlist ──────────────────────────────────────────────────────────
async function sbGetWishlist() {
  const rows = await sbSelect('wishlist', { order: 'id.asc' });
  return { success: true, data: (rows || []).map((r) => r.destinationId) };
}

async function sbToggleWishlist(destinationId) {
  const c = supabaseCfg();
  if (!c) throw new Error('Supabase not configured');
  const current = (await sbGetWishlist()).data;
  const action = current.includes(destinationId) ? 'removed' : 'added';
  if (action === 'added') {
    await fetch(`${c.url}/rest/v1/wishlist`, {
      method: 'POST',
      headers: { apikey: c.anonKey, Authorization: `Bearer ${c.anonKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ destinationId }),
    });
  } else {
    await fetch(`${c.url}/rest/v1/wishlist?destinationId=eq.${encodeURIComponent(destinationId)}`, {
      method: 'DELETE',
      headers: { apikey: c.anonKey, Authorization: `Bearer ${c.anonKey}`, 'Content-Type': 'application/json' },
    });
  }
  const updated = (await sbGetWishlist()).data;
  return { success: true, action, data: updated };
}

// ── Itinerary (Edge Function) ─────────────────────────────────────────
async function sbGenerateItinerary(days, style) {
  const c = supabaseCfg();
  if (!c) throw new Error('Supabase not configured');
  const res = await fetch(`${c.url}/functions/v1/itinerary`, {
    method: 'POST',
    headers: { apikey: c.anonKey, Authorization: `Bearer ${c.anonKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ days, style }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Supabase itinerary fn: HTTP ${res.status} ${body.slice(0, 200)}`);
  }
  return res.json();
}

// ── Generic dispatch (mirrors Flask endpoints) ────────────────────────
async function __sbFetch(endpoint, options) {
  const method = (options?.method || 'GET').toUpperCase();
  const ep = String(endpoint).split('?')[0];
  const query = new URLSearchParams(String(endpoint).split('?')[1] || '');
  const body = options?.body;

  if (method === 'GET') {
    if (ep === '/destinations') {
      const category = query.get('category') || 'all';
      const search = query.get('search') || '';
      const { success, count, data } = await sbGetDestinations(category, search);
      return { success, count, data };
    }
    const dMatch = ep.match(/^\/destinations\/([^/?]+)/);
    if (dMatch) return sbGetDestination(decodeURIComponent(dMatch[1]));
    if (ep === '/festivals') return sbGetFestivals();
    const fMatch = ep.match(/^\/festivals\/([^/?]+)/);
    if (fMatch) return sbGetFestival(decodeURIComponent(fMatch[1]));
    const iMatch = ep.match(/^\/info\/([^/?]+)/);
    if (iMatch) return sbGetInfo(decodeURIComponent(iMatch[1]));
    if (ep === '/regions') return sbGetRegions();
    const rMatch = ep.match(/^\/regions\/([^/?]+)/);
    if (rMatch) return sbGetRegion(decodeURIComponent(rMatch[1]));
    if (ep === '/wishlist') return sbGetWishlist();
    const bMatch = ep.match(/^\/bookings\/([^/?]+)/);
    if (bMatch) return sbGetBooking(decodeURIComponent(bMatch[1]));
    if (ep === '/health') return { success: true, data: { status: 'healthy', service: 'Ghana Kora Vista Tours API' } };
  }

  if (method === 'POST') {
    if (ep === '/bookings') return sbCreateBooking(body || {});
    if (ep === '/wishlist') return sbToggleWishlist((body || {}).destinationId);
    if (ep === '/itinerary') return sbGenerateItinerary(Number((body || {}).days) || 7, (body || {}).style || 'balanced');
  }

  throw new Error(`Unsupported Supabase endpoint: ${method} ${endpoint}`);
}

// ── Attach to window for the app bundle ───────────────────────────────
(function attach() {
  const w = typeof window !== 'undefined' ? window : ({} as any);
  w.__sbFetch = __sbFetch;
  w.__sbCreateBooking = sbCreateBooking;
  w.__sbToggleWishlist = sbToggleWishlist;
  w.__sbGenerateItinerary = sbGenerateItinerary;
})();