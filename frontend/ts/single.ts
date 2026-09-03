/**
 * vistaGHANA — Complete Application (Single File)
 * TypeScript + Flask REST API
 */
export {};

// ── Types ─────────────────────────────────────────────────────────────
interface Destination {
  id: string; name: string; category: string; categoryName: string;
  region: string; location: string; image: string; rating: number;
  reviews: number; fee: string; hours: string; bestTime: string;
  accessibility: string; lat: number; lng: number; shortDesc: string;
  fullDesc: string; highlights: string[]; nearbyHotels: string[];
  guideContact: string;
}

interface Festival {
  id: string; name: string; culture: string; month: string;
  duration: string; location: string; region: string; image: string;
  shortDesc: string; fullDesc: string; keyRituals: string[];
}

interface PracticalInfo { title: string; badge: string; content: string; }
interface ItineraryDay { day: string; title: string; activities: string[]; }
interface ItineraryResponse { days: number; style: string; plan: ItineraryDay[]; }
interface ApiResponse<T> { success: boolean; count?: number; data: T; }

interface Region {
  id: string; name: string; capital: string; abbreviation: string;
  grid: [number, number]; span: [number, number]; blurb: string;
  destinations: string[]; festivals: string[];
}
interface ResolvedRegion {
  id: string; name: string; capital: string; abbreviation: string;
  grid: [number, number]; span: [number, number]; blurb: string;
  destinations: Destination[]; festivals: Festival[]; hasContent: boolean;
}

type Theme = 'light' | 'dark';
type Category = 'all' | 'national-parks' | 'historical' | 'waterfalls' | 'cultural';

// ── API Client ────────────────────────────────────────────────────────
const API_BASE = 'http://localhost:5000/api';

async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      headers: { 'Content-Type': 'application/json' }, ...options,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error(`API Error [${endpoint}]:`, err);
    throw err;
  }
}

async function getDestinations(cat: string = 'all', q: string = ''): Promise<ApiResponse<Destination[]>> {
  const p = new URLSearchParams();
  if (cat !== 'all') p.append('category', cat);
  if (q) p.append('search', q);
  const query = p.toString() ? `?${p}` : '';
  return apiFetch<Destination[]>(`/destinations${query}`);
}

async function getFestivals(): Promise<ApiResponse<Festival[]>> {
  return apiFetch<Festival[]>('/festivals');
}

async function getInfo(type: string): Promise<ApiResponse<PracticalInfo>> {
  return apiFetch<PracticalInfo>(`/info/${type}`);
}

async function getRegions(): Promise<ApiResponse<Region[]>> {
  return apiFetch<Region[]>('/regions');
}

async function getRegion(id: string): Promise<ApiResponse<ResolvedRegion>> {
  return apiFetch<ResolvedRegion>(`/regions/${id}`);
}

async function apiItinerary(days: number, style: string): Promise<ApiResponse<ItineraryResponse>> {
  return apiFetch<ItineraryResponse>('/itinerary', {
    method: 'POST', body: JSON.stringify({ days, style }),
  });
}

// ── UI Helpers ────────────────────────────────────────────────────────
function $(s: string): HTMLElement | null { return document.querySelector(s); }
function $$(s: string): HTMLElement[] { return Array.from(document.querySelectorAll(s)); }

function esc(s: string): string {
  const d = document.createElement('div'); d.textContent = s; return d.innerHTML;
}

function openModal(id: string): void {
  const el = document.getElementById(id);
  if (el) { el.classList.add('active'); document.body.style.overflow = 'hidden'; }
}

function closeModal(id: string): void {
  const el = document.getElementById(id);
  if (el) { el.classList.remove('active'); document.body.style.overflow = ''; }
}

let _toastTimer: ReturnType<typeof setTimeout> | null = null;
function showToast(msg: string): void {
  let t = document.getElementById('global-toast');
  if (!t) { t = document.createElement('div'); t.id = 'global-toast'; t.className = 'toast'; document.body.appendChild(t); }
  t.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg> ${esc(msg)}`;
  t.classList.add('active');
  if (_toastTimer) clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => t?.classList.remove('active'), 3000);
}

// ── State ─────────────────────────────────────────────────────────────
let currentCategory: Category = 'all';
let searchQuery = '';
let savedBookmarks: string[] = JSON.parse(localStorage.getItem('visitGhanaBookmarks') || '[]');

// ── Theme ─────────────────────────────────────────────────────────────
function initTheme(): void {
  const saved = (localStorage.getItem('visitGhanaTheme') as Theme) || 'light';
  document.documentElement.setAttribute('data-theme', saved);
  $$('.theme-toggle-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const cur = (document.documentElement.getAttribute('data-theme') as Theme) || 'light';
      const next: Theme = cur === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('visitGhanaTheme', next);
      showToast(`Switched to ${next === 'light' ? 'Light' : 'Dark'} theme`);
    });
  });
}

// ── Mobile Nav ────────────────────────────────────────────────────────
function initMobileNav(): void {
  const toggle = document.getElementById('mobile-toggle-btn');
  const nav = document.querySelector('.nav-links');
  if (!toggle || !nav) return;
  toggle.setAttribute('aria-expanded', 'false');
  toggle.addEventListener('click', () => {
    const open = nav.classList.toggle('active');
    toggle.classList.toggle('active', open);
    toggle.setAttribute('aria-expanded', String(open));
    document.body.classList.toggle('nav-open', open);
  });
  $$('.nav-link').forEach(link => link.addEventListener('click', () => {
    nav.classList.remove('active'); toggle.classList.remove('active');
    toggle.setAttribute('aria-expanded', 'false'); document.body.classList.remove('nav-open');
  }));
  document.addEventListener('click', (e: Event) => {
    const t = e.target as HTMLElement;
    if (nav.classList.contains('active') && !nav.contains(t) && !toggle.contains(t)) {
      nav.classList.remove('active'); toggle.classList.remove('active');
      toggle.setAttribute('aria-expanded', 'false'); document.body.classList.remove('nav-open');
    }
  });
}

// ── Header Scroll ─────────────────────────────────────────────────────
function initHeaderScroll(): void {
  const h = document.getElementById('site-header');
  if (h) window.addEventListener('scroll', () => h.classList.toggle('scrolled', window.scrollY > 10), { passive: true });
}

// ── Modal Close on Overlay Click ──────────────────────────────────────
function initModalClose(): void {
  document.addEventListener('click', (e: Event) => {
    const t = e.target as HTMLElement;
    if (t.classList.contains('modal-overlay')) { t.classList.remove('active'); document.body.style.overflow = ''; }
  });
}

// ── Destinations ──────────────────────────────────────────────────────
async function renderDestinations(): Promise<void> {
  const grid = document.getElementById('destinations-grid');
  if (!grid) return;
  try {
    const res = await getDestinations(currentCategory, searchQuery);
    const items = res.data;
    if (!items.length) {
      grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:48px 16px;background:var(--bg-card);border-radius:var(--radius-lg);border:1px solid var(--border-light);">
        <h3 style="font-size:1.2rem;margin-bottom:6px;color:var(--text-heading);">No destinations found</h3>
        <p style="color:var(--text-muted);margin-bottom:14px;font-size:0.9rem;">Try "Monkey", "Waterfall", "Castle", or "Safari"</p>
        <button class="btn-card-details" onclick="clearSearch()">Clear Search</button></div>`;
      return;
    }
    const urgencyLabels = ['Selling fast', 'Popular choice', 'High demand', 'Booked today'];
    grid.innerHTML = items.map((item: Destination, i: number) => {
      const saved = savedBookmarks.includes(item.id);
      const top = item.rating >= 4.9;
      const spots = Math.floor(Math.random() * 8) + 2;
      return `<div class="destination-card" data-id="${item.id}" style="animation-delay:${i * 50}ms">
        <div class="card-media">
          <img src="${item.image}" alt="${esc(item.name)}" loading="lazy">
          <span class="card-badge">${esc(item.categoryName)}</span>
          ${top ? '<span class="card-urgency-badge">Top Rated</span>' : ''}
          <button class="card-bookmark-btn ${saved ? 'saved' : ''}" onclick="toggleBookmark('${item.id}',event)" title="Save">
            <svg viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
          </button>
        </div>
        <div class="card-body">
          <div class="card-location">
            <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>
            ${esc(item.location)}
          </div>
          <h3 class="card-title">${esc(item.name)}</h3>
          <p class="card-description">${esc(item.shortDesc)}</p>
          <div class="card-social-proof">
            <span class="card-rating"><svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg> ${item.rating}</span>
            <span class="card-reviews">(${item.reviews.toLocaleString()})</span>
            ${top ? '<span class="card-top-rated">Top Rated</span>' : ''}
          </div>
          <div class="card-amenities">
            <span class="amenity-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg> ${esc(item.hours.split('–')[0].trim())}</span>
          </div>
          <div class="card-scarcity"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg> ${urgencyLabels[i % urgencyLabels.length]} &mdash; ${spots} booked today</div>
          <div class="card-meta">
            <div class="card-price-block">
              <span class="card-price-current">${esc(item.fee)}</span>
              <span class="card-price-suffix">per person</span>
            </div>
            <button class="btn-card-details" onclick="openDestinationModal('${item.id}')">View Details</button>
          </div>
        </div></div>`;
    }).join('');
  } catch {
    grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:48px;"><p style="color:var(--text-muted);">Unable to load. Is the Flask server running on port 5000?</p></div>`;
  }
}

function initCategoryTabs(): void {
  $$('.tab-btn').forEach(btn => btn.addEventListener('click', (e: Event) => {
    $$('.tab-btn').forEach(b => b.classList.remove('active'));
    (e.currentTarget as HTMLElement).classList.add('active');
    currentCategory = (e.currentTarget as HTMLElement).dataset.category as Category;
    renderDestinations();
  }));
}

function initSearch(): void {
  const input = document.getElementById('search-input') as HTMLInputElement | null;
  if (!input) return;
  let timer: ReturnType<typeof setTimeout>;
  input.addEventListener('input', (e: Event) => {
    clearTimeout(timer);
    timer = setTimeout(() => { searchQuery = (e.target as HTMLInputElement).value; renderDestinations(); }, 300);
  });
}

function clearSearch(): void {
  searchQuery = '';
  const input = document.getElementById('search-input') as HTMLInputElement | null;
  if (input) input.value = '';
  renderDestinations();
}

function toggleBookmark(id: string, event: Event): void {
  event.stopPropagation();
  const idx = savedBookmarks.indexOf(id);
  if (idx > -1) { savedBookmarks.splice(idx, 1); showToast('Removed from wishlist'); }
  else { savedBookmarks.push(id); showToast('Added to wishlist!'); }
  localStorage.setItem('visitGhanaBookmarks', JSON.stringify(savedBookmarks));
  renderDestinations();
}

async function openDestinationModal(id: string): Promise<void> {
  const overlay = document.getElementById('destination-modal-overlay');
  const card = document.getElementById('destination-modal-card');
  if (!overlay || !card) return;
  try {
    const res = await getDestinations();
    const item = res.data.find((d: Destination) => d.id === id);
    if (!item) return;
    card.innerHTML = `
      <button class="modal-close-btn" onclick="closeModal('destination-modal-overlay')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
      <img src="${item.image}" class="modal-hero-img" alt="${esc(item.name)}" loading="lazy">
      <div class="modal-content-body">
        <div class="modal-header-meta">
          <span class="card-badge" style="position:static;">${esc(item.categoryName)}</span>
          <span style="font-weight:700;color:var(--brand-teal);font-size:0.85rem;">${esc(item.region)}</span>
        </div>
        <h2 class="modal-title">${esc(item.name)}</h2>
        <div class="modal-fact-grid">
          <div class="fact-item"><h5>Hours</h5><p>${esc(item.hours)}</p></div>
          <div class="fact-item"><h5>Fee</h5><p>${esc(item.fee)}</p></div>
          <div class="fact-item"><h5>Best Time</h5><p>${esc(item.bestTime)}</p></div>
          <div class="fact-item"><h5>Access</h5><p>${esc(item.accessibility)}</p></div>
        </div>
        <h3 style="font-size:1.1rem;margin:18px 0 8px;color:var(--text-heading);">About</h3>
        <p style="color:var(--text-body);line-height:1.7;font-size:0.9rem;margin-bottom:18px;">${esc(item.fullDesc)}</p>
        <h4 style="font-size:0.9rem;margin-bottom:8px;color:var(--text-heading);">Highlights</h4>
        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:20px;">
          ${item.highlights.map(h => `<span style="background:var(--brand-primary-light);color:var(--brand-primary);font-weight:600;font-size:0.78rem;padding:4px 10px;border-radius:var(--radius-pill);">${esc(h)}</span>`).join('')}
        </div>
        <div style="background:var(--bg-surface-alt);border:1px solid var(--border-light);padding:14px;border-radius:var(--radius-md);margin-bottom:18px;">
          <p style="font-size:0.85rem;color:var(--text-body);margin-bottom:4px;"><strong>Hotels:</strong> ${item.nearbyHotels.join(' · ')}</p>
          <p style="font-size:0.85rem;color:var(--brand-primary);font-weight:700;"><strong>Guide:</strong> ${esc(item.guideContact)}</p>
        </div>
        <div style="display:flex;gap:8px;">
          <button class="hero-pill-btn" style="flex:1;justify-content:center;font-size:0.85rem;" onclick="showToast('Added to your trip!')">Add to Trip</button>
          <button class="btn-card-details" style="padding:8px 18px;" onclick="closeModal('destination-modal-overlay')">Close</button>
        </div>
      </div>`;
    openModal('destination-modal-overlay');
  } catch (e) { console.error(e); }
}

// ── Festivals ─────────────────────────────────────────────────────────
async function renderFestivals(): Promise<void> {
  const c = document.getElementById('festivals-grid-container');
  if (!c) return;
  try {
    const res = await getFestivals();
    c.innerHTML = res.data.map((f: Festival) => `
      <div class="festival-card-expanded">
        <div class="festival-card-img">
          <img src="${f.image}" alt="${esc(f.name)}" loading="lazy">
          <span class="festival-month-badge">${esc(f.month.split('(')[0].trim())}</span>
        </div>
        <div class="festival-card-content">
          <div class="festival-culture-tag">${esc(f.culture)}</div>
          <h3 class="festival-card-title">${esc(f.name)}</h3>
          <div class="festival-meta-row">
            <span><strong>Location:</strong> ${esc(f.location)}, ${esc(f.region)}</span>
            <span><strong>Duration:</strong> ${esc(f.duration)}</span>
          </div>
          <p class="festival-card-desc">${esc(f.shortDesc)}</p>
          <button class="btn-card-details" onclick="openFestivalModal('${f.id}')" style="width:100%;text-align:center;">View Details</button>
        </div>
      </div>`).join('');
  } catch { c.innerHTML = `<p style="color:var(--text-muted);text-align:center;padding:40px;">Unable to load festivals.</p>`; }
}

async function openFestivalModal(id: string): Promise<void> {
  const overlay = document.getElementById('destination-modal-overlay');
  const card = document.getElementById('destination-modal-card');
  if (!overlay || !card) return;
  try {
    const res = await getFestivals();
    const f = res.data.find((x: Festival) => x.id === id);
    if (!f) return;
    card.innerHTML = `
      <button class="modal-close-btn" onclick="closeModal('destination-modal-overlay')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
      <img src="${f.image}" class="modal-hero-img" alt="${esc(f.name)}" loading="lazy">
      <div class="modal-content-body">
        <div class="modal-header-meta">
          <span class="card-badge" style="position:static;background:var(--accent-coral);color:var(--text-inverse);border:none;">${esc(f.culture)}</span>
          <span style="font-weight:700;color:var(--brand-teal);font-size:0.85rem;">${esc(f.location)}, ${esc(f.region)}</span>
        </div>
        <h2 class="modal-title">${esc(f.name)}</h2>
        <div class="modal-fact-grid">
          <div class="fact-item"><h5>Month</h5><p>${esc(f.month)}</p></div>
          <div class="fact-item"><h5>Duration</h5><p>${esc(f.duration)}</p></div>
          <div class="fact-item"><h5>Location</h5><p>${esc(f.location)}</p></div>
          <div class="fact-item"><h5>Region</h5><p>${esc(f.region)}</p></div>
        </div>
        <h3 style="font-size:1.1rem;margin:18px 0 8px;color:var(--text-heading);">Cultural History</h3>
        <p style="color:var(--text-body);line-height:1.7;font-size:0.9rem;margin-bottom:18px;">${esc(f.fullDesc)}</p>
        <h4 style="font-size:0.9rem;margin-bottom:8px;color:var(--text-heading);">Key Rituals</h4>
        <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:20px;">
          ${f.keyRituals.map(r => `<span style="background:var(--accent-orange-light);color:var(--accent-orange);font-weight:600;font-size:0.78rem;padding:4px 10px;border-radius:var(--radius-pill);">${esc(r)}</span>`).join('')}
        </div>
        <div style="display:flex;gap:8px;">
          <button class="hero-pill-btn" style="flex:1;justify-content:center;font-size:0.85rem;" onclick="showToast('Festival added to trip!')">Add to Trip</button>
          <button class="btn-card-details" style="padding:8px 18px;" onclick="closeModal('destination-modal-overlay')">Close</button>
        </div>
      </div>`;
    openModal('destination-modal-overlay');
  } catch (e) { console.error(e); }
}

// ── Info Modal ────────────────────────────────────────────────────────
async function openInfoModal(type: string): Promise<void> {
  const overlay = document.getElementById('info-modal-overlay');
  const card = document.getElementById('info-modal-card');
  if (!overlay || !card) return;
  try {
    const res = await getInfo(type);
    const info = res.data;
    card.innerHTML = `
      <button class="modal-close-btn" onclick="closeModal('info-modal-overlay')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
      <div class="modal-content-body" style="padding:28px;">
        <span class="card-badge" style="position:static;margin-bottom:12px;display:inline-block;">${esc(info.badge)}</span>
        <h2 style="font-size:1.4rem;margin-bottom:16px;color:var(--text-heading);">${esc(info.title)}</h2>
        <div style="line-height:1.8;color:var(--text-body);font-size:0.9rem;">${info.content}</div>
        <button class="hero-pill-btn" style="margin-top:20px;width:100%;justify-content:center;font-size:0.88rem;" onclick="closeModal('info-modal-overlay')">Got It</button>
      </div>`;
    openModal('info-modal-overlay');
  } catch (e) { console.error(e); }
}

// ── Itinerary ─────────────────────────────────────────────────────────
async function generateItineraryUI(): Promise<void> {
  const daysEl = document.getElementById('planner-days') as HTMLSelectElement | null;
  const styleEl = document.getElementById('planner-style') as HTMLSelectElement | null;
  const results = document.getElementById('itinerary-results');
  if (!daysEl || !styleEl || !results) return;
  const days = parseInt(daysEl.value, 10);
  const style = styleEl.value;
  try {
    const res = await apiItinerary(days, style);
    let html = `<h3 style="color:var(--brand-primary);font-size:1.1rem;margin-bottom:12px;">Your ${days}-Day Ghana Itinerary</h3>`;
    res.data.plan.forEach((d: ItineraryDay) => {
      html += `<div class="day-item"><h4>${esc(d.day)}: ${esc(d.title)}</h4><p>${d.activities.join(' · ')}</p></div>`;
    });
    results.innerHTML = html;
    results.classList.add('active');
    showToast('Itinerary generated!');
  } catch {
    // Local fallback
    let html = `<h3 style="color:var(--brand-primary);font-size:1.1rem;margin-bottom:12px;">Your ${days}-Day Ghana Itinerary</h3>`;
    if (days === 3) {
      html += `<div class="day-item"><h4>Day 1: Accra & Tafi Atome</h4><p>Black Star Square · Tafi Atome Monkey Sanctuary</p></div>
        <div class="day-item"><h4>Day 2: Cape Coast</h4><p>Cape Coast Castle · Kakum Canopy Walk</p></div>
        <div class="day-item"><h4>Day 3: Markets</h4><p>Accra Arts Centre · Kente shopping</p></div>`;
    } else if (days === 7) {
      html += `<div class="day-item"><h4>Days 1-2: Central Coast</h4><p>Cape Coast Castle · Kakum · Elmina</p></div>
        <div class="day-item"><h4>Days 3-4: Ashanti</h4><p>Boabeng-Fiema · Manhyia Palace · Bonwire Kente</p></div>
        <div class="day-item"><h4>Days 5-7: Volta</h4><p>Tafi Atome · Wli Waterfalls · Mount Afadjato</p></div>`;
    } else {
      html += `<div class="day-item"><h4>Week 1: Coast & Kumasi</h4><p>Accra · Cape Coast · Kakum · Kumasi</p></div>
        <div class="day-item"><h4>Week 2: North & Volta</h4><p>Tamale · Mole Safari · Paga · Tafi · Wli</p></div>`;
    }
    results.innerHTML = html;
    results.classList.add('active');
    showToast('Itinerary generated!');
  }
}

// ── Chatbot ───────────────────────────────────────────────────────────
function initChat(): void {
  const form = document.getElementById('ai-chat-form') as HTMLFormElement | null;
  if (form) form.addEventListener('submit', handleChat);
}

function handleChat(e: Event): void {
  e.preventDefault();
  const input = document.getElementById('ai-chat-input') as HTMLInputElement | null;
  const msgs = document.getElementById('ai-chat-messages');
  if (!input || !msgs) return;
  const q = input.value.trim();
  if (!q) return;
  msgs.innerHTML += `<div class="ai-message user"><div class="ai-msg-avatar"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div><div class="ai-msg-content"><p>${esc(q)}</p></div></div>`;
  input.value = '';
  msgs.scrollTop = msgs.scrollHeight;
  setTimeout(() => {
    msgs.innerHTML += `<div class="ai-message bot"><div class="ai-msg-avatar"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/></svg></div><div class="ai-msg-content">${chatResponse(q)}</div></div>`;
    msgs.scrollTop = msgs.scrollHeight;
  }, 750);
}

function chatResponse(q: string): string {
  const l = q.toLowerCase();
  if (l.includes('monk') || l.includes('tafi')) return `<p><strong>Monkey Sanctuaries:</strong> Tafi Atome (Volta) and Boabeng-Fiema (Bono East) let you feed Mona monkeys by hand!</p>`;
  if (l.includes('castle') || l.includes('cape') || l.includes('elmina')) return `<p><strong>UNESCO Castles:</strong> Cape Coast Castle (Door of No Return) and Elmina Castle (1482, oldest in Africa).</p>`;
  if (l.includes('festiv') || l.includes('aboakyer') || l.includes('homowo')) return `<p><strong>Festivals:</strong> Aboakyer (May, deer hunt), Homowo (Aug, harvest), Damba (Jul-Aug, horse dances).</p>`;
  if (l.includes('waterfall') || l.includes('wli')) return `<p><strong>Waterfalls:</strong> Wli (highest in West Africa), Boti (twin falls + Umbrella Rock).</p>`;
  if (l.includes('airport') || l.includes('pickup')) return `<p><strong>Airport Transfer:</strong> VIP meet & greet at Kotoka (ACC), GHS 350 (~$30).</p>`;
  if (l.includes('pay') || l.includes('card')) return `<p><strong>Payment:</strong> Zero upfront! Pay on arrival via Visa, MoMo, or cash.</p>`;
  if (l.includes('itinerar') || l.includes('plan')) return `<p><strong>Itineraries:</strong> 3-day express, 7-day essential, or 14-day grand explorer. Use the Trip Planner below!</p>`;
  if (l.includes('hello') || l.includes('hi') || l.includes('akwaaba')) return `<p><strong>Akwaaba!</strong> Welcome! I can help with destinations, castles, festivals, bookings, and itineraries.</p>`;
  return `<p><strong>Akwaaba!</strong> I can help with Ghana's sanctuaries, castles, waterfalls, festivals, and travel planning. Try the chips below!</p>`;
}

// ── Hero Search ───────────────────────────────────────────────────────
function initHeroSearch(): void {
  const ci = document.getElementById('hero-checkin') as HTMLInputElement | null;
  if (ci) {
    const d = new Date(); d.setDate(d.getDate() + 7);
    ci.value = d.toISOString().split('T')[0];
    ci.min = new Date().toISOString().split('T')[0];
  }
}

declare global {
  interface Window {
    toggleBookmark: (id: string, event: Event) => void;
    openDestinationModal: (id: string) => void;
    openFestivalModal: (id: string) => void;
    openInfoModal: (type: string) => void;
    closeModal: (id: string) => void;
    showToast: (msg: string) => void;
    clearSearch: () => void;
    generateItinerary: () => void;
    toggleAIChat: () => void;
    sendQuickPrompt: (text: string) => void;
    handleAIChatSubmit: (e: Event) => void;
    openRegionModal: (id: string) => void;
  }
}

// ── Regions Map ───────────────────────────────────────────────────────
async function renderRegions(): Promise<void> {
  const index = document.getElementById('regions-index');
  const svg = document.querySelector('.ghana-map') as SVGSVGElement | null;
  if (!svg) return;
  try {
    const res = await getRegions();
    const regions = res.data;

    // Determine which regions have content
    const detailResults = await Promise.all(
      regions.map(r => getRegion(r.id).then(res => ({ region: r, data: res.data })).catch(() => ({ region: r, data: null as unknown as ResolvedRegion })))
    );

    detailResults.forEach(({ region, data }) => {
      const path = svg.getElementById(`region-${region.id}`);
      if (!path) return;
      if (data && data.hasContent) {
        path.classList.add('has-content');
        const count = (data.destinations?.length || 0) + (data.festivals?.length || 0);
        path.setAttribute('data-count', `${count}`);
      } else {
        path.classList.add('no-content');
        path.setAttribute('aria-disabled', 'true');
      }
    });

    // Build the quick index list
    if (index) {
      index.innerHTML = regions.map(r =>
        `<button class="region-chip" data-region="${r.id}" onclick="openRegionModal('${r.id}')">
          <span class="region-chip-abbr">${esc(r.abbreviation)}</span>
          ${esc(r.name)}
        </button>`).join('');
    }

    // Make each SVG region path clickable
    const paths = Array.from(svg.querySelectorAll('.region-path')) as SVGPathElement[];
    paths.forEach(p => {
      const rid = (p.getAttribute('data-region') || '').replace('region-', '');
      if (rid) {
        p.addEventListener('click', () => { openRegionModal(rid); });
        p.style.cursor = 'pointer';
      }
    });
  } catch (e) {
    console.error(e);
    const hint = document.querySelector('.regions-hint');
    if (hint) (hint as HTMLElement).textContent = 'Unable to load region data.';
    document.querySelectorAll('.region-path').forEach(p => p.classList.add('no-content'));
  }
}

function escRegionContent(html: string): string {
  const d = document.createElement('div'); d.textContent = html; return d.innerHTML;
}

async function openRegionModal(id: string): Promise<void> {
  const overlay = document.getElementById('region-modal-overlay');
  const card = document.getElementById('region-modal-card');
  if (!overlay || !card) return;
  card.classList.add('loading');
  card.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;padding:60px;color:var(--text-muted);">Loading region…</div>`;
  openModal('region-modal-overlay');

  try {
    const res = await getRegion(id);
    const r = res.data;

    if (!r.hasContent) {
      card.innerHTML = `
        <button class="modal-close-btn" onclick="closeModal('region-modal-overlay')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        <div class="modal-content-body" style="padding:32px;text-align:center;">
          <span class="region-modal-emoji" style="display:inline-flex;width:64px;height:64px;border-radius:50%;background:var(--bg-surface-alt);align-items:center;justify-content:center;margin-bottom:16px;">
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" style="color:var(--text-muted);"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>
          </span>
          <h2 style="font-size:1.4rem;margin-bottom:6px;color:var(--text-heading);">${escRegionContent(r.name)}</h2>
          <p style="color:var(--text-muted);font-size:0.9rem;margin-bottom:14px;">Capital: ${escRegionContent(r.capital)}</p>
          <p style="color:var(--text-body);line-height:1.7;font-size:0.92rem;margin-bottom:20px;">${escRegionContent(r.blurb)}</p>
          <p style="display:inline-block;background:var(--bg-surface-alt);color:var(--text-muted);padding:8px 16px;border-radius:var(--radius-pill);font-size:0.85rem;">No festivals or attractions listed yet — coming soon!</p>
          <div style="margin-top:20px;">
            <button class="hero-pill-btn" style="width:100%;justify-content:center;font-size:0.88rem;" onclick="closeModal('region-modal-overlay')">Got It</button>
          </div>
        </div>`;
      card.classList.remove('loading');
      return;
    }

    const festCards = r.festivals.length
      ? `<h3 class="region-modal-section-title">Cultural Festivals</h3>
         <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:20px;">
           ${r.festivals.map(f => `
             <button class="region-listing-item" onclick="openFestivalModal('${f.id}')">
               <img src="${f.image}" alt="${escRegionContent(f.name)}" loading="lazy">
               <div>
                 <strong>${escRegionContent(f.name)}</strong>
                 <span>${escRegionContent(f.month)} · ${escRegionContent(f.location)}</span>
               </div>
               <svg class="region-listing-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
             </button>`).join('')}
         </div>`
      : '';

    const destCards = r.destinations.length
      ? `<h3 class="region-modal-section-title">Top Attractions</h3>
         <div style="display:flex;flex-direction:column;gap:10px;">
           ${r.destinations.map(d => `
             <button class="region-listing-item" onclick="openDestinationModal('${d.id}')">
               <img src="${d.image}" alt="${escRegionContent(d.name)}" loading="lazy">
               <div>
                 <strong>${escRegionContent(d.name)}</strong>
                 <span>${escRegionContent(d.categoryName)} · ${escRegionContent(d.fee)}</span>
               </div>
               <svg class="region-listing-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
             </button>`).join('')}
         </div>`
      : '';

    card.innerHTML = `
      <button class="modal-close-btn" onclick="closeModal('region-modal-overlay')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
      <div class="modal-content-body" style="padding:28px;">
        <div class="modal-header-meta">
          <span class="card-badge" style="position:static;">${escRegionContent(r.abbreviation)}</span>
          <span style="font-weight:700;color:var(--brand-teal);font-size:0.85rem;">Capital: ${escRegionContent(r.capital)}</span>
        </div>
        <h2 style="font-size:1.5rem;margin-bottom:8px;color:var(--text-heading);">${escRegionContent(r.name)}</h2>
        <p style="color:var(--text-body);line-height:1.7;font-size:0.9rem;margin-bottom:18px;">${escRegionContent(r.blurb)}</p>
        ${festCards}
        ${destCards}
        <button class="hero-pill-btn" style="margin-top:22px;width:100%;justify-content:center;font-size:0.88rem;" onclick="closeModal('region-modal-overlay')">Close</button>
      </div>`;
    card.classList.remove('loading');
  } catch (e) {
    console.error(e);
    card.classList.remove('loading');
    card.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-muted);">Something went wrong loading this region.</div>`;
  }
}

// ── Global Functions ──────────────────────────────────────────────────
window.toggleBookmark = toggleBookmark;
window.openDestinationModal = openDestinationModal;
window.openFestivalModal = openFestivalModal;
window.openInfoModal = openInfoModal;
window.closeModal = closeModal;
window.showToast = showToast;
window.clearSearch = clearSearch;
window.generateItinerary = generateItineraryUI;
window.openRegionModal = openRegionModal;

function toggleAIChat(): void {
  const win = document.getElementById('ai-chat-window');
  if (win) win.classList.toggle('active');
}
window.toggleAIChat = toggleAIChat;

function sendQuickPrompt(text: string): void {
  const input = document.getElementById('ai-chat-input') as HTMLInputElement | null;
  if (input) { input.value = text; handleChat(new Event('submit')); }
}
window.sendQuickPrompt = sendQuickPrompt;

function handleAIChatSubmit(e: Event): void { e.preventDefault(); handleChat(e); }
window.handleAIChatSubmit = handleAIChatSubmit;

// ── Bootstrap ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initMobileNav();
  initHeaderScroll();
  initModalClose();
  initCategoryTabs();
  initSearch();
  initChat();
  initHeroSearch();
    renderDestinations();
    renderFestivals();
    renderRegions();
});
