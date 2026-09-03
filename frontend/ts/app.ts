/**
 * vistaGHANA — Main Application Entry Point
 * TypeScript + Flask REST API Architecture
 */

import { initThemeToggle, initMobileNav, initHeaderScroll, initModalClose, openModal, closeModal, showToast } from './ui';
import { initDestinations, toggleBookmark, openDestinationModal, clearSearch, renderDestinations } from './destinations';
import { initFestivals, openFestivalModal } from './festivals';
import { initChat, initGlobalChatFunctions } from './chat';
import { getPracticalInfo, generateItinerary } from './api';
import { escapeHTML } from './ui';

// ── DOMContentLoaded ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  initMobileNav();
  initHeaderScroll();
  initModalClose();
  initDestinations();
  initFestivals();
  initChat();
  initGlobalChatFunctions();
  initGlobalFunctions();
  initHeroSearch();
});

// ── Global Window Functions (for inline handlers) ─────────────────────
function initGlobalFunctions(): void {
  window.toggleBookmark = toggleBookmark;
  window.openDestinationModal = openDestinationModal;
  window.openFestivalModal = openFestivalModal;
  window.closeModal = closeModal;
  window.showToast = showToast;
  window.clearSearch = clearSearch;
  window.renderDestinations = renderDestinations;
  window.openInfoModal = openInfoModal;
  window.generateItineraryUI = generateItineraryUI;
}

// ── Practical Info Modal ──────────────────────────────────────────────
async function openInfoModal(type: string): Promise<void> {
  const overlay = document.getElementById('info-modal-overlay');
  const card = document.getElementById('info-modal-card');
  if (!overlay || !card) return;

  try {
    const response = await getPracticalInfo(type);
    const info = response.data;

    card.innerHTML = `
      <button class="modal-close-btn" onclick="window.closeModal('info-modal-overlay')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
      <div class="modal-content-body" style="padding:32px;">
        <span class="card-badge" style="position:static;margin-bottom:14px;display:inline-block;">${escapeHTML(info.badge)}</span>
        <h2 style="font-size:1.5rem;margin-bottom:20px;color:var(--text-heading);">${escapeHTML(info.title)}</h2>
        <div style="line-height:1.8;color:var(--text-body);font-size:0.92rem;">${info.content}</div>
        <button class="hero-pill-btn" style="margin-top:24px;width:100%;justify-content:center;font-size:0.9rem;" onclick="window.closeModal('info-modal-overlay')">Got It</button>
      </div>`;

    openModal('info-modal-overlay');
  } catch (error) {
    console.error('Failed to load info:', error);
  }
}

// ── Hero Search Bar ───────────────────────────────────────────────────
function initHeroSearch(): void {
  const checkin = document.getElementById('hero-checkin') as HTMLInputElement | null;
  if (checkin) {
    const today = new Date();
    today.setDate(today.getDate() + 7);
    checkin.value = today.toISOString().split('T')[0];
    checkin.min = new Date().toISOString().split('T')[0];
  }
}

// ── Itinerary Generator (UI only, with API data) ──────────────────────
async function generateItineraryUI(): Promise<void> {
  const daysEl = document.getElementById('planner-days') as HTMLSelectElement | null;
  const styleEl = document.getElementById('planner-style') as HTMLSelectElement | null;
  const results = document.getElementById('itinerary-results');
  if (!daysEl || !styleEl || !results) return;

  const days = parseInt(daysEl.value, 10);
  const style = styleEl.value;

  try {
    const response = await generateItinerary(days, style);
    const plan = response.data.plan;

    let html = `<h3 style="color:var(--brand-primary);font-size:1.15rem;margin-bottom:14px;">Your ${days}-Day Ghana Itinerary</h3>`;
    plan.forEach(day => {
      html += `
        <div class="day-item">
          <h4>${escapeHTML(day.day)}: ${escapeHTML(day.title)}</h4>
          <p>${day.activities.join(' &bull; ')}</p>
        </div>`;
    });

    results.innerHTML = html;
    results.classList.add('active');
    showToast('Itinerary generated!');
  } catch (error) {
    // Fallback to local generation
    generateLocalItinerary(days, results);
  }
}

function generateLocalItinerary(days: number, container: HTMLElement): void {
  let html = `<h3 style="color:var(--brand-primary);font-size:1.15rem;margin-bottom:14px;">Your ${days}-Day Ghana Itinerary</h3>`;

  if (days === 3) {
    html += `
      <div class="day-item"><h4>Day 1: Accra & Tafi Atome</h4><p>Black Star Square &bull; Tafi Atome Monkey Sanctuary &bull; Local lunch</p></div>
      <div class="day-item"><h4>Day 2: Cape Coast & Elmina</h4><p>Cape Coast Castle &bull; Kakum Canopy Walk &bull; Elmina Castle</p></div>
      <div class="day-item"><h4>Day 3: Markets & Farewell</h4><p>Accra Arts Centre &bull; Kente shopping &bull; Jollof & Highlife evening</p></div>`;
  } else if (days === 7) {
    html += `
      <div class="day-item"><h4>Days 1-2: Central Coast</h4><p>Cape Coast Castle &bull; Kakum Canopy Walk &bull; Elmina Castle</p></div>
      <div class="day-item"><h4>Days 3-4: Ashanti Region</h4><p>Boabeng-Fiema Monkeys &bull; Manhyia Palace &bull; Bonwire Kente Village</p></div>
      <div class="day-item"><h4>Days 5-7: Volta Region</h4><p>Tafi Atome Monkeys &bull; Wli Waterfalls &bull; Mount Afadjato</p></div>`;
  } else {
    html += `
      <div class="day-item"><h4>Week 1: Coast & Kumasi</h4><p>Accra &bull; Cape Coast &bull; Kakum &bull; Boabeng-Fiema &bull; Kumasi Heritage</p></div>
      <div class="day-item"><h4>Week 2: North & Volta</h4><p>Tamale Damba &bull; Mole Safari &bull; Paga Crocodiles &bull; Tafi Atome &bull; Wli</p></div>`;
  }

  container.innerHTML = html;
  container.classList.add('active');
  showToast('Itinerary generated!');
}

// ── Type Declarations for Window ──────────────────────────────────────
declare global {
  interface Window {
    toggleBookmark: (id: string, event: Event) => void;
    openDestinationModal: (id: string) => void;
    openFestivalModal: (id: string) => void;
    closeModal: (id: string) => void;
    showToast: (msg: string) => void;
    clearSearch: () => void;
    renderDestinations: () => void;
    openInfoModal: (type: string) => void;
    generateItineraryUI: () => void;
    sendQuickPrompt: (text: string) => void;
    toggleAIChat: () => void;
  }
}
