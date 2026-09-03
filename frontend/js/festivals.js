/**
 * Festivals Module — Rendering & Modals
 */
import { getFestivals } from './api';
import { openModal, escapeHTML } from './ui';
export function initFestivals() {
    renderFestivals();
}
async function renderFestivals() {
    const container = document.getElementById('festivals-grid-container');
    if (!container)
        return;
    try {
        const response = await getFestivals();
        const festivals = response.data;
        container.innerHTML = festivals.map((item) => `
      <div class="festival-card-expanded">
        <div class="festival-card-img">
          <img src="${item.image}" alt="${escapeHTML(item.name)}" loading="lazy">
          <span class="festival-month-badge">${escapeHTML(item.month.split('(')[0].trim())}</span>
        </div>
        <div class="festival-card-content">
          <div class="festival-culture-tag">${escapeHTML(item.culture)}</div>
          <h3 class="festival-card-title">${escapeHTML(item.name)}</h3>
          <div class="festival-meta-row">
            <span><strong>Location:</strong> ${escapeHTML(item.location)}, ${escapeHTML(item.region)}</span>
            <span><strong>Duration:</strong> ${escapeHTML(item.duration)}</span>
          </div>
          <p class="festival-card-desc">${escapeHTML(item.shortDesc)}</p>
          <button class="btn-card-details" onclick="window.openFestivalModal('${item.id}')" style="width:100%;text-align:center;margin-top:auto;">
            View Festival Details
          </button>
        </div>
      </div>
    `).join('');
    }
    catch (error) {
        container.innerHTML = `
      <div style="grid-column:1/-1;text-align:center;padding:40px;">
        <p style="color:var(--text-muted);">Unable to load festivals. Make sure the server is running.</p>
      </div>`;
    }
}
export async function openFestivalModal(id) {
    const overlay = document.getElementById('destination-modal-overlay');
    const card = document.getElementById('destination-modal-card');
    if (!overlay || !card)
        return;
    try {
        const response = await getFestivals();
        const festival = response.data.find((f) => f.id === id);
        if (!festival)
            return;
        card.innerHTML = `
      <button class="modal-close-btn" onclick="window.closeModal('destination-modal-overlay')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
      <img src="${festival.image}" class="modal-hero-img" alt="${escapeHTML(festival.name)}" loading="lazy">
      <div class="modal-content-body">
        <div class="modal-header-meta">
          <span class="card-badge" style="position:static;background:var(--accent-coral);color:var(--text-inverse);border:none;">${escapeHTML(festival.culture)}</span>
          <span style="font-weight:700;color:var(--brand-teal);font-size:0.85rem;display:inline-flex;align-items:center;gap:4px;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            ${escapeHTML(festival.location)}, ${escapeHTML(festival.region)}
          </span>
        </div>
        <h2 class="modal-title">${escapeHTML(festival.name)}</h2>
        <div class="modal-fact-grid">
          <div class="fact-item"><h5>Month</h5><p>${escapeHTML(festival.month)}</p></div>
          <div class="fact-item"><h5>Duration</h5><p>${escapeHTML(festival.duration)}</p></div>
          <div class="fact-item"><h5>Location</h5><p>${escapeHTML(festival.location)}</p></div>
          <div class="fact-item"><h5>Region</h5><p>${escapeHTML(festival.region)}</p></div>
        </div>
        <h3 style="font-size:1.15rem;margin:20px 0 10px;color:var(--text-heading);">Cultural History</h3>
        <p style="color:var(--text-body);line-height:1.7;font-size:0.92rem;margin-bottom:20px;">${escapeHTML(festival.fullDesc)}</p>
        <h4 style="font-size:0.95rem;margin-bottom:10px;color:var(--text-heading);">Key Rituals</h4>
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:24px;">
          ${festival.keyRituals.map(r => `<span style="background:var(--accent-orange-light);color:var(--accent-orange);font-weight:600;font-size:0.8rem;padding:5px 12px;border-radius:var(--radius-pill);display:inline-flex;align-items:center;gap:4px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 3v18M3 12h18"/></svg>
            ${escapeHTML(r)}
          </span>`).join('')}
        </div>
        <div style="display:flex;gap:10px;">
          <button class="hero-pill-btn" style="flex:1;justify-content:center;font-size:0.88rem;" onclick="window.showToast('Festival added to your trip!')">Add to My Trip</button>
          <button class="btn-card-details" style="padding:10px 20px;" onclick="window.closeModal('destination-modal-overlay')">Close</button>
        </div>
      </div>`;
        openModal('destination-modal-overlay');
    }
    catch (error) {
        console.error('Failed to load festival:', error);
    }
}
//# sourceMappingURL=festivals.js.map