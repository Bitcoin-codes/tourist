/**
 * Destinations Module — Rendering, Filtering, Modals
 */

import type { Destination, Category } from './types';
import { getDestinations } from './api';
import { $, $$, openModal, closeModal, showToast, escapeHTML } from './ui';

let currentCategory: Category = 'all';
let searchQuery: string = '';
let savedBookmarks: string[] = JSON.parse(localStorage.getItem('visitGhanaBookmarks') || '[]');

export function initDestinations(): void {
  renderDestinations();
  initCategoryTabs();
  initSearch();
}

export async function renderDestinations(): Promise<void> {
  const grid = document.getElementById('destinations-grid');
  if (!grid) return;

  try {
    const response = await getDestinations(currentCategory, searchQuery);
    const destinations = response.data;

    if (destinations.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1/-1; text-align: center; padding: 48px 16px; background: var(--bg-card); border-radius: var(--radius-lg); border: 1px solid var(--border-light);">
          <h3 style="font-size: 1.2rem; margin-bottom: 6px; color: var(--text-heading);">No destinations found</h3>
          <p style="color: var(--text-muted); margin-bottom: 14px; font-size: 0.9rem;">Try "Monkey", "Waterfall", "Castle", or "Safari"</p>
          <button class="btn-card-details" onclick="window.clearSearch()">Clear Search</button>
        </div>`;
      return;
    }

    grid.innerHTML = destinations.map((item: Destination, i: number) => {
      const isSaved = savedBookmarks.includes(item.id);
      const isTopRated = item.rating >= 4.9;
      const urgencyMessages = [
        'Selling fast', 'Popular choice', 'High demand', 'Limited spots'
      ];
      const urgency = urgencyMessages[i % urgencyMessages.length];
      const scarcityNum = Math.floor(Math.random() * 8) + 2;

      return `
        <div class="destination-card" data-id="${item.id}" style="animation-delay: ${i * 50}ms">
          <div class="card-media">
            <img src="${item.image}" alt="${escapeHTML(item.name)}" loading="lazy">
            <span class="card-badge">${escapeHTML(item.categoryName)}</span>
            ${isTopRated ? '<span class="card-urgency-badge">Top Rated</span>' : ''}
            <button class="card-bookmark-btn ${isSaved ? 'saved' : ''}" onclick="window.toggleBookmark('${item.id}', event)" title="Save to wishlist">
              <svg viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
            </button>
          </div>
          <div class="card-body">
            <div class="card-location">
              <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>
              ${escapeHTML(item.location)}
            </div>
            <h3 class="card-title">${escapeHTML(item.name)}</h3>
            <p class="card-description">${escapeHTML(item.shortDesc)}</p>
            <div class="card-social-proof">
              <span class="card-rating">
                <svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                ${item.rating}
              </span>
              <span class="card-reviews">(${item.reviews.toLocaleString()} reviews)</span>
              ${isTopRated ? '<span class="card-top-rated">Top Rated</span>' : ''}
            </div>
            <div class="card-amenities">
              <span class="amenity-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg> ${escapeHTML(item.hours.split('–')[0].trim())}</span>
              <span class="amenity-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg> ${escapeHTML(item.accessibility.split(' ').slice(0, 3).join(' '))}</span>
            </div>
            <div class="card-scarcity">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
              ${urgency} &mdash; ${scarcityNum} spots booked today
            </div>
            <div class="card-meta">
              <div class="card-price-block">
                <span class="card-price-savings">Save 15%</span>
                <span class="card-price-current">${escapeHTML(item.fee)}</span>
                <span class="card-price-suffix">per person</span>
              </div>
              <button class="btn-card-details" onclick="window.openDestinationModal('${item.id}')">View Details</button>
            </div>
          </div>
        </div>`;
    }).join('');
  } catch (error) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 48px 16px;">
        <p style="color: var(--text-muted);">Unable to load destinations. Make sure the server is running.</p>
        <button class="btn-card-details" onclick="window.renderDestinations()" style="margin-top: 12px;">Retry</button>
      </div>`;
  }
}

function initCategoryTabs(): void {
  $$('.tab-btn').forEach((btn: HTMLElement) => {
    btn.addEventListener('click', (e: Event) => {
      $$('.tab-btn').forEach((b: HTMLElement) => b.classList.remove('active'));
      (e.currentTarget as HTMLElement).classList.add('active');
      currentCategory = (e.currentTarget as HTMLElement).dataset.category as Category;
      renderDestinations();
    });
  });
}

function initSearch(): void {
  const input = document.getElementById('search-input') as HTMLInputElement | null;
  if (!input) return;

  let debounce: ReturnType<typeof setTimeout>;
  input.addEventListener('input', (e: Event) => {
    clearTimeout(debounce);
    debounce = setTimeout(() => {
      searchQuery = (e.target as HTMLInputElement).value;
      renderDestinations();
    }, 300);
  });
}

export function clearSearch(): void {
  searchQuery = '';
  const input = document.getElementById('search-input') as HTMLInputElement | null;
  if (input) input.value = '';
  renderDestinations();
}

export function toggleBookmark(id: string, event: Event): void {
  event.stopPropagation();
  const index = savedBookmarks.indexOf(id);
  if (index > -1) {
    savedBookmarks.splice(index, 1);
    showToast('Removed from wishlist');
  } else {
    savedBookmarks.push(id);
    showToast('Added to wishlist!');
  }
  localStorage.setItem('visitGhanaBookmarks', JSON.stringify(savedBookmarks));
  renderDestinations();
}

export async function openDestinationModal(id: string): Promise<void> {
  const overlay = document.getElementById('destination-modal-overlay');
  const card = document.getElementById('destination-modal-card');
  if (!overlay || !card) return;

  try {
    const response = await getDestinations();
    const item = response.data.find((d: Destination) => d.id === id);
    if (!item) return;

    card.innerHTML = `
      <button class="modal-close-btn" onclick="window.closeModal('destination-modal-overlay')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
      <img src="${item.image}" class="modal-hero-img" alt="${escapeHTML(item.name)}" loading="lazy">
      <div class="modal-content-body">
        <div class="modal-header-meta">
          <span class="card-badge" style="position:static;">${escapeHTML(item.categoryName)}</span>
          <span style="font-weight:700;color:var(--brand-teal);font-size:0.85rem;display:inline-flex;align-items:center;gap:4px;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            ${escapeHTML(item.region)}
          </span>
        </div>
        <h2 class="modal-title">${escapeHTML(item.name)}</h2>
        <div class="modal-fact-grid">
          <div class="fact-item"><h5>Hours</h5><p>${escapeHTML(item.hours)}</p></div>
          <div class="fact-item"><h5>Entrance Fee</h5><p>${escapeHTML(item.fee)}</p></div>
          <div class="fact-item"><h5>Best Time</h5><p>${escapeHTML(item.bestTime)}</p></div>
          <div class="fact-item"><h5>Accessibility</h5><p>${escapeHTML(item.accessibility)}</p></div>
        </div>
        <h3 style="font-size:1.15rem;margin:20px 0 10px;color:var(--text-heading);">About</h3>
        <p style="color:var(--text-body);line-height:1.7;font-size:0.92rem;margin-bottom:20px;">${escapeHTML(item.fullDesc)}</p>
        <h4 style="font-size:0.95rem;margin-bottom:10px;color:var(--text-heading);">Key Highlights</h4>
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:24px;">
          ${item.highlights.map(h => `<span style="background:var(--brand-primary-light);color:var(--brand-primary);font-weight:600;font-size:0.8rem;padding:5px 12px;border-radius:var(--radius-pill);display:inline-flex;align-items:center;gap:4px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            ${escapeHTML(h)}
          </span>`).join('')}
        </div>
        <div style="background:var(--bg-surface-alt);border:1px solid var(--border-light);padding:16px;border-radius:var(--radius-md);margin-bottom:20px;">
          <h4 style="font-size:0.9rem;margin-bottom:6px;color:var(--text-heading);">Nearby Hotels</h4>
          <p style="font-size:0.85rem;color:var(--text-body);">${item.nearbyHotels.join(' &bull; ')}</p>
          <h4 style="font-size:0.9rem;margin:12px 0 6px;color:var(--text-heading);">Tour Guide</h4>
          <p style="font-size:0.85rem;color:var(--brand-primary);font-weight:700;">${escapeHTML(item.guideContact)}</p>
        </div>
        <div style="display:flex;gap:10px;">
          <button class="hero-pill-btn" style="flex:1;justify-content:center;font-size:0.88rem;" onclick="window.showToast('Added to your trip!')">Add to Trip</button>
          <button class="btn-card-details" style="padding:10px 20px;" onclick="window.closeModal('destination-modal-overlay')">Close</button>
        </div>
      </div>`;

    openModal('destination-modal-overlay');
  } catch (error) {
    console.error('Failed to load destination:', error);
  }
}

// Expose to window for inline handlers
declare global {
  interface Window {
    toggleBookmark: (id: string, event: Event) => void;
    openDestinationModal: (id: string) => void;
    closeModal: (id: string) => void;
    showToast: (msg: string) => void;
    clearSearch: () => void;
    renderDestinations: () => void;
  }
}
