/**
 * AI Chatbot Module — Keyword-based Response Engine
 */
import { escapeHTML } from './ui';
export function initChat() {
    const form = document.getElementById('ai-chat-form');
    if (form) {
        form.addEventListener('submit', handleChatSubmit);
    }
}
function handleChatSubmit(e) {
    e.preventDefault();
    const input = document.getElementById('ai-chat-input');
    const messages = document.getElementById('ai-chat-messages');
    if (!input || !messages)
        return;
    const query = input.value.trim();
    if (!query)
        return;
    // User message
    const userDiv = document.createElement('div');
    userDiv.className = 'ai-message user';
    userDiv.innerHTML = `
    <div class="ai-msg-avatar"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div>
    <div class="ai-msg-content"><p>${escapeHTML(query)}</p></div>`;
    messages.appendChild(userDiv);
    input.value = '';
    messages.scrollTop = messages.scrollHeight;
    // Typing indicator
    const typing = document.createElement('div');
    typing.className = 'ai-message bot typing';
    typing.id = 'ai-typing';
    typing.innerHTML = `
    <div class="ai-msg-avatar"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/></svg></div>
    <div class="ai-msg-content"><p><em>Typing...</em></p></div>`;
    messages.appendChild(typing);
    messages.scrollTop = messages.scrollHeight;
    setTimeout(() => {
        typing.remove();
        const response = generateResponse(query);
        const botDiv = document.createElement('div');
        botDiv.className = 'ai-message bot';
        botDiv.innerHTML = `
      <div class="ai-msg-avatar"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/></svg></div>
      <div class="ai-msg-content">${response}</div>`;
        messages.appendChild(botDiv);
        messages.scrollTop = messages.scrollHeight;
    }, 750);
}
function generateResponse(query) {
    const q = query.toLowerCase();
    if (q.includes('monk') || q.includes('tafi') || q.includes('boabeng') || q.includes('animal')) {
        return `<p><strong>Ghana Monkey Sanctuaries:</strong></p>
      <p>1. <strong>Tafi Atome:</strong> Volta Region sacred forest where Mona monkeys feed from your hands!</p>
      <p>2. <strong>Boabeng-Fiema:</strong> Home to Mona and rare Pied Colobus monkeys.</p>
      <p><button class="btn-card-details" style="font-size:0.75rem;padding:4px 10px;margin-top:6px;" onclick="window.openDestinationModal('tafi-atome-monkey-sanctuary')">View Details &rarr;</button></p>`;
    }
    if (q.includes('airport') || q.includes('pickup') || q.includes('transfer')) {
        return `<p><strong>VIP Airport Transfers:</strong></p>
      <p>Meet & greet at Kotoka Airport with private AC transfer to your hotel.</p>
      <p><strong>Cost: GHS 350 (~$30 USD).</strong></p>`;
    }
    if (q.includes('guide') || q.includes('tour')) {
        return `<p><strong>Certified Local Tour Guides:</strong></p>
      <p>GTA-certified guides for historical sites & sanctuaries.</p>
      <p><strong>Cost: GHS 500 (~$40 USD) per day.</strong></p>`;
    }
    if (q.includes('pay') || q.includes('cash') || q.includes('card') || q.includes('arrival')) {
        return `<p><strong>Payment Options:</strong></p>
      <p>Reserve online with <strong>Zero Upfront!</strong> Pay on arrival via Visa, Mastercard, or Cedis/USD cash.</p>`;
    }
    if (q.includes('castle') || q.includes('cape coast') || q.includes('elmina') || q.includes('history')) {
        return `<p><strong>UNESCO Fortresses:</strong></p>
      <p><strong>Cape Coast Castle:</strong> World Heritage fortress with Door of No Return.</p>
      <p><strong>Elmina Castle:</strong> Africa's oldest European building (1482).</p>
      <p><button class="btn-card-details" style="font-size:0.75rem;padding:4px 10px;margin-top:6px;" onclick="window.openDestinationModal('cape-coast-castle')">Explore &rarr;</button></p>`;
    }
    if (q.includes('festiv') || q.includes('aboakyer') || q.includes('homowo') || q.includes('damba')) {
        return `<p><strong>Ghanaian Festivals:</strong></p>
      <p><strong>Aboakyer (May):</strong> Winneba warrior deer hunt.</p>
      <p><strong>Homowo (Aug):</strong> Ga harvest festival with Kpokpoi.</p>
      <p><button class="btn-card-details" style="font-size:0.75rem;padding:4px 10px;margin-top:6px;" onclick="window.openFestivalModal('aboakyer-festival')">View Festival &rarr;</button></p>`;
    }
    if (q.includes('waterfall') || q.includes('wli') || q.includes('boti')) {
        return `<p><strong>Waterfalls:</strong></p>
      <p><strong>Wli:</strong> Highest in West Africa with bat sanctuary.</p>
      <p><strong>Boti:</strong> Twin falls & Umbrella Rock.</p>
      <p><button class="btn-card-details" style="font-size:0.75rem;padding:4px 10px;margin-top:6px;" onclick="window.openDestinationModal('wli-waterfall')">View Wli &rarr;</button></p>`;
    }
    if (q.includes('itinerar') || q.includes('plan') || q.includes('day') || q.includes('trip')) {
        return `<p><strong>Itinerary Options:</strong></p>
      <p><strong>3 Days:</strong> Accra, Cape Coast, Tafi Atome.</p>
      <p><strong>7 Days:</strong> Full Ghana experience.</p>
      <p><a href="#planner" style="color:var(--brand-primary);font-weight:700;">Open Trip Planner &rarr;</a></p>`;
    }
    if (q.includes('hello') || q.includes('hi') || q.includes('akwaaba') || q.includes('food')) {
        return `<p><strong>Akwaaba! (Welcome!)</strong></p>
      <p>Ghana offers warm hospitality, UNESCO heritage, and world-class Jollof rice! How can I help?</p>`;
    }
    return `<p><strong>Akwaaba!</strong> Ghana offers sanctuaries, castles, waterfalls, and festivals.</p>
    <p>Try the suggestion chips below for quick answers!</p>`;
}
export function initGlobalChatFunctions() {
    window.sendQuickPrompt = (text) => {
        const input = document.getElementById('ai-chat-input');
        if (input) {
            input.value = text;
            handleChatSubmit(new Event('submit'));
        }
    };
    window.toggleAIChat = () => {
        const chatWindow = document.getElementById('ai-chat-window');
        if (chatWindow)
            chatWindow.classList.toggle('active');
    };
}
//# sourceMappingURL=chat.js.map