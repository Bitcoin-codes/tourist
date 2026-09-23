/**
 * Akwaaba AI Assistant — the shared chat brain for Memorra Travels.
 *
 * A luxury digital tourism gateway for Ghana. Encoded as keyword logic (no
 * model, no API key, no per-message cost) but following the behaviour spec:
 *
 *   1. Greet warmly with authentic Ghanaian hospitality ("Akwaaba!").
 *   2. Answer questions about destinations (Cape Coast Castle, Mole National
 *      Park, Tafi Atome Sanctuary), festivals (Homowo, Aboakyer, Damba),
 *      trip planning and booking — concise and focused on tourism.
 *   3. Never invent a booking guarantee and never claim to process payment.
 *
 * HANDOFF — three details are gathered before a human is reached:
 *
 *   1. Full Name          2. Phone Number / Email        3. Reason for contact
 *
 * ...and the transfer is announced with the <HANDOFF> trigger tag at the very
 * end of the response text:
 *
 *   <HANDOFF>
 *   {
 *     "transfer": true,
 *     "userName": "GATHERED_NAME_OR_UNKNOWN",
 *     "contact":  "GATHERED_CONTACT_OR_UNKNOWN",
 *     "topic":    "SUMMARY_OF_ISSUE"
 *   }
 *   </HANDOFF>
 *
 * The same tag is what this file parses back out to POST /api/contact, so the
 * thing shown to the visitor and the thing sent to the agent are one artifact.
 *
 * ARCHITECTURE. The responder itself is forked between pages (app.bundle.js
 * `chatResponse` for index/planner/regions vs app.js `generateAIResponse` for
 * booking) and this deliberately does not merge them — it sits in front of
 * both, exported under the original `agentHandoff` name so neither responder
 * needed a single line changed:
 *
 *     responder(q)
 *       -> agentHandoff(q)             persona/knowledge/handoff HTML, or
 *                                       null to let keyword logic answer
 *       -> ... keyword branches ...
 *       -> fallback + agentHandoffCTA()   "Talk to a human agent" button
 *
 * Running in front is also what gives every page identical answers: the
 * homepage's copy of the responder is 19 intents, booking's is 35, so without
 * this layer the same question about Damba was answered richly on booking and
 * thinly on index.
 */
(function () {
  'use strict';

  var PERSONA_NAME = 'Akwaaba AI Assistant';
  var BRAND = 'Memorra Travels';

  // ── Where a handoff lands ─────────────────────────────────────────────
  // Digits only, international format: '233241234567' opens
  // https://wa.me/233241234567?text=<the whole handoff, already written>.
  //
  // LEFT EMPTY DELIBERATELY. There is no verified agency number anywhere in
  // this repository — only `tel:112` and fictional guide numbers inside seed
  // data — and guessing one would walk real customers up to a stranger. Until
  // a number is pasted here, every transfer falls back to WhatsApp's own
  // share picker (`wa.me/?text=`) with the summary already written, so the
  // handoff works today and becomes a direct chat the moment this is filled
  // in. Nothing else in the file needs to change.
  var AGENT_WHATSAPP = '';

  var BOT_AVATAR =
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
    '<rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/></svg>';

  // ── State ─────────────────────────────────────────────────────────────
  // 'idle'       = persona + knowledge + normal keyword answering
  // 'collecting' = a handoff is in progress; the next message is one of the
  //                three details (name, then contact, then reason)
  var state = 'idle';
  var asked = '';                       // which detail the last prompt wanted

  var lead = {
    userName: '',                       // 1. Full Name
    contact: '',                        // 2. Phone Number / Email
    topic: '',                          // 3. Reason for contacting an agent
    detail: '',                         // their raw words, for the inbox only
    question: '',                       // carried across from before the handoff
    quick: false                        // two-field path: name + WhatsApp only
  };

  // The unanswered question to forward, captured from the previous message so
  // a visitor who asks "is Mole safe in August?" and *then* demands a human
  // still gets their actual question carried across.
  var lastQuestion = '';

  // ── Detection ─────────────────────────────────────────────────────────
  // Human detection needs BOTH a person-word and an action-word. Requiring
  // the pair (rather than either alone) is what keeps "your booking agent"
  // or "is there someone?" from yanking a visitor out of a normal Q&A.
  // Word boundaries matter: without them "person" matches inside
  // "personalised itinerary" and "agent" inside "agency", both of which are
  // ordinary travel questions that must fall through to the knowledge base.
  // Deliberately no `book`/`plan`/`arrange` in here: "Who is your booking
  // agent?" would then match person-word + "booking" and hijack a plain
  // information request into a handoff. `support` is in — bare "I need
  // support" is an unmistakable cry for a person — but it still has to be
  // paired with an action-word, so "support for my visa question" does not
  // fire on its own.
  var HUMAN_WORD = /\b(humans?|agents?|person|representatives?|somebody|someone|support)\b|\blive\s+support\b/i;
  var ACTION_WORD = /(talk|speak|chat|connect|transfer|reach|contact|want|need|give|put|call)/i;

  // "book custom complex tours" is its own trigger, independent of asking for
  // a person: someone commissioning a bespoke itinerary is by definition
  // talking to a human, not reading canned answers. Still needs an
  // action-word so "do you do custom tours?" is an inquiry, not a handoff.
  var CUSTOM_TOUR_WORD = /\b(custom|bespoke|tailor-?made|private|special)\s*(?:\w+\s+){0,3}\b(tours?|trips?|itinerar(?:y|ies)|safaris?|packages?|group)\b|\bcomplex\s+(?:tours?|trips?|itinerar(?:y|ies))\b|\bgroup\s+safari\b/i;

  // Escape hatch. Without this a visitor who declines the prompt (or was
  // pulled in by a false positive) is reprompted forever and never gets back
  // to normal answering. Anchored: a refusal must LEAD the message, so
  // "connect me now" is never mistaken for one. Checked only after the
  // demand test, and after any detail has been extracted from the message.
  var ABORT_RE = /^(?:ok\s*,?\s*|actually\s*,?\s*)?(?:no\b|nope\b|nah\b|naw\b|cancel\b|stop\b|never\s*mind\b|nevermind\b|forget\s+(?:it|that)\b|not\s+now\b|go\s+back\b|exit\b|skip\b|leave\s+it\b|change\s+my\s+mind\b)/i;

  // "if the user explicitly demands an agent immediately" — transfer now with
  // UNKNOWN for whatever has not been gathered yet, rather than reprompting.
  // A refusal that LEADS the message cancels the demand, so "no thanks, not
  // now" still declines instead of firing a transfer nobody wanted.
  var URGENT = /\b(now|immediately|instantly|right\s+now|right\s+away|hurry|stop\s+(?:asking|prompting|questioning)|enough|just\s+(?:connect|transfer|put)|connect\s+me|transfer\s+me|put\s+me\s+through|pass\s+me\s+(?:on|through))\b/i;
  var REFUSE_FIRST = /^(?:\s*(?:ok\s*,?\s*|actually\s*,?\s*))?(?:no\b|nope\b|nah\b|naw\b|never\b|not\s+now\b|cancel\b)/i;

  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;      // whole message is an address
  var EMAIL_FIND = /[^\s@,;]+@[^\s@,;]+\.[^\s@,;]{2,}/; // an address inside a message
  var PHONE_FIND = /\+?\d[\d\s().-]{6,}\d/;             // 8+ digits of run
  var NAME_FIND = /\b(?:my\s+name\s+is|i\s+am|i'm|im|call\s+me|name\s+is|name:|this\s+is)\s+([A-Za-z][A-Za-z .'’\u2013-]{1,48})/i;

  // ── Knowledge base ────────────────────────────────────────────────────
  // Checked in order, before the responders' own branches, so index and
  // booking give the same answer. Concise and tourism-focused by design.
  var KNOWLEDGE = [
    // Who am I — the persona, stated plainly.
    { re: /\b(who\s+are\s+you|what\s+are\s+you|your\s+name|introduce\s+yourself|are\s+you\s+(?:a\s+)?(?:human|bot|ai))\b/i,
      html: '<p><strong>Akwaaba!</strong> I\'m the ' + PERSONA_NAME + ' — your travel support guide for ' + BRAND +
            ', a luxury digital tourism gateway for Ghana. I can help with destinations, festivals, trip planning and booking details.</p>' +
            '<p style="color:var(--text-muted);font-size:0.9rem;">Anything I can\'t answer, or if you\'d rather talk to a person, ' +
            'just type <strong>agent</strong> — or I\'ll offer to pass you over.</p>' },

    // Payment honesty. Spec: do NOT claim to handle direct payment
    // processing and do NOT invent booking guarantees. This deliberately
    // runs ahead of the responders' canned "Zero upfront! Pay on arrival"
    // line, which is exactly the kind of promise that must not be made by
    // an automated guide.
    { re: /\b(pay|paying|payment|payments|paid|price|prices|pricing|cost|costs|deposit|refund|refundable|guarantee|guaranteed|guarantees|card|cards|momo|mobile\s+money|invoice|receipt)\b/i,
      html: '<p>I can\'t take payments or promise bookings from the chat — I don\'t process payments directly. ' +
            'Our agents confirm availability, pricing and payment with you personally.</p>' +
            '<p style="color:var(--text-muted);font-size:0.9rem;">Want me to pass you to one now?</p>' +
            '<button type="button" onclick="startAgentHandoff()" ' +
            'style="background:var(--brand-primary);color:#fff;border:none;border-radius:6px;' +
            'padding:7px 14px;font-size:0.85rem;font-weight:600;cursor:pointer;margin-top:6px;' +
            'display:inline-block;">Talk to a human agent &rarr;</button>' },

    // ── Festivals ──────────────────────────────────────────────────────
    { re: /\bhomowo\b/i,
      html: '<p><strong>Homowo (August)</strong> — the Ga people of Greater Accra, and the most celebrated festival in the region. ' +
            'The name means "hooting at hunger", marking the famine the Ga ancestors survived before a miraculous harvest. ' +
            'Family heads sprinkle <em>Kpokpoi</em> (steamed cornmeal with palm oil soup) across homes and streets, with drumming and dancing.</p>' },
    { re: /\baboakyer\b|\bwinneba\b|\bdeer\s+hunt\b/i,
      html: '<p><strong>Aboakyer (first Saturday in May)</strong> — the Effutu people of Winneba, Central Region. ' +
            'Two Asafo warrior groups, the Dentsefo and Tuafo, race to capture a live deer using only their bare hands. ' +
            'The first to bring back an uninjured deer wins the year\'s prestige.</p>' },
    { re: /\bdamba\b|\btamale\b|\btalking\s+drum\b|\bhorse\s+danc/i,
      html: '<p><strong>Damba (July–August)</strong> — Northern Ghana, celebrated by the Dagbamba, Gonja, Mamprusi and Waala. ' +
            'A display of chieftaincy, horse-riding choreography, traditional smocks (Batakari) and intricate talking-drum (Dondo) dancing.</p>' },
    { re: /\bfestivals?\b|\bcultural\s+(?:events?|celebrations?)\b/i,
      html: '<p><strong>Ghana\'s festivals:</strong></p>' +
            '<p>&bull; <strong>Aboakyer</strong> (May) — Winneba Asafo warrior deer hunt, bare hands only.</p>' +
            '<p>&bull; <strong>Homowo</strong> (Aug) — Ga harvest, Kpokpoi sprinkled through the streets.</p>' +
            '<p>&bull; <strong>Damba</strong> (Jul–Aug) — Northern royal horse dances and talking drums.</p>' +
            '<p style="color:var(--text-muted);font-size:0.9rem;">Ask me about any of them for the full story.</p>' },

    // ── Destinations ───────────────────────────────────────────────────
    { re: /\bmole\b|\belephant\b|\bwalking\s+safari\b|\bsafari\b/i,
      html: '<p><strong>Mole National Park</strong> — Ghana\'s premier wildlife destination, nearly 5,000 km² of savannah and river forest in the north.</p>' +
            '<p>&bull; <strong>Walking safaris</strong> with armed rangers — you approach elephant herds on foot.</p>' +
            '<p>&bull; <strong>Drive safaris (4x4)</strong> and the Mole Motel pool outlook.</p>' +
            '<p>&bull; <strong>Larabanga Mosque</strong> is a short stop away.</p>' +
            '<p style="color:var(--text-muted);font-size:0.9rem;">Stay at Zaina Lodge (luxury) or Mole Motel.</p>' },
    { re: /\bcape\s+coast\b|\bcastles?\b|\belmina\b|\bdoor\s+of\s+no\s+return\b|\bunesco\b|\bslave\s+dungeon\b/i,
      html: '<p><strong>Cape Coast Castle</strong> — a UNESCO World Heritage fortress on the Atlantic coast, built by the Swedes in 1653 and later British.</p>' +
            '<p>&bull; Guided tours through the historic dungeons and the <strong>Door of No Return</strong>.</p>' +
            '<p>&bull; The upper museum covers West African maritime history.</p>' +
            '<p>&bull; Pair it with <strong>Elmina Castle (1482)</strong>, the oldest European building in West Africa, and the Kakum Canopy Walk.</p>' },
    { re: /\btafi\b|\batome\b|\bmonkeys?\b|\bsanctuar(?:y|ies)\b|\bboabeng\b/i,
      html: '<p><strong>Tafi Atome Monkey Sanctuary</strong> — a community eco-tourism project in the Volta Region.</p>' +
            '<p>For over 200 years the sacred Mona monkeys have been protected by local traditional belief as divine messengers of the gods. ' +
            'You feed them bananas straight from your hand, then walk the forest with community guides.</p>' +
            '<p style="color:var(--text-muted);font-size:0.9rem;">Also nearby: <strong>Boabeng-Fiema</strong> (Mona and Black-and-White Pied Colobus).</p>' },

    // ── Bespoke enquiries are a handoff in waiting. Sits ABOVE trip
    //    planning so "plan me a custom trip" offers a person rather than a
    //    canned itinerary — commissioning something bespoke is the spec's own
    //    handoff trigger, not a request for a fixed route. ────────────────
    { re: CUSTOM_TOUR_WORD,
      html: '<p>We build <strong>bespoke itineraries</strong> across Ghana — private groups, multi-region safaris, weddings and corporate trips.</p>' +
            '<p style="color:var(--text-muted);font-size:0.9rem;">To scope one properly you\'ll want a person, not a bot:</p>' +
            '<button type="button" onclick="startAgentHandoff()" ' +
            'style="background:var(--brand-primary);color:#fff;border:none;border-radius:6px;' +
            'padding:7px 14px;font-size:0.85rem;font-weight:600;cursor:pointer;margin-top:6px;' +
            'display:inline-block;">Talk to a human agent &rarr;</button>' },

    // ── Trip planning ──────────────────────────────────────────────────
    { re: /\bitinerar(?:y|ies)\b|\bhow\s+long\b|\bhow\s+many\s+days\b|\bplan(?:ning|ned)?\b|\btrip\s+(?:to|in|for)\b|\bschedule\b|\bday\s+\d\b|\bweek\s+\d\b/i,
      html: '<p><strong>Ready-made itineraries:</strong></p>' +
            '<p>&bull; <strong>3-day express</strong> — Accra, Cape Coast Castle, Tafi Atome.</p>' +
            '<p>&bull; <strong>7-day essential</strong> — adds Kakum, Elmina and the Volta waterfalls.</p>' +
            '<p>&bull; <strong>14-day grand explorer</strong> — coast and Kumasi in week one, Northern safaris and Volta in week two.</p>' +
            '<p style="color:var(--text-muted);font-size:0.9rem;">Use the Trip Planner on the homepage, or ask me to shape one around your dates.</p>' },

    // ── Booking ────────────────────────────────────────────────────────
    { re: /\bbook(?:ing)?\b|\breserve|reservation\b|\bconfirm\b|\bdeposit\b|\bavailability\b/i,
      html: '<p><strong>Booking with ' + BRAND + ':</strong></p>' +
            '<p>&bull; Pick your destination or itinerary, then complete the booking form — you get an email confirmation with your QR pass.</p>' +
            '<p>&bull; Airport concierge meets you at Kotoka (ACC) with a name placard.</p>' +
            '<p>&bull; Tour guides, transfers and hotel arrangements are all arranged for you.</p>' +
            '<p style="color:var(--text-muted);font-size:0.9rem;">For dates, group sizes or anything unusual, an agent can confirm it directly.</p>' }
  ];

  // ── Small helpers ─────────────────────────────────────────────────────

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /** Escaping for the <HANDOFF> payload only. Quotes are left alone: this is
   *  element content, not an attribute, so `"` needs no escape — and touching
   *  it would render `&quot;` where the spec's tag must read as literal,
   *  parseable JSON. textContent of the tag is therefore exactly the string
   *  that was sent. */
  function jsonEsc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  /** The transfer link. With a configured number it opens a chat with the
   *  agent directly; without one it opens WhatsApp's share picker with the
   *  handoff pre-written, so nothing is ever lost either way. */
  function whatsappURL(text) {
    var t = encodeURIComponent(String(text || ''));
    var to = String(AGENT_WHATSAPP || '').replace(/\D/g, '');
    return to ? 'https://wa.me/' + to + '?text=' + t
              : 'https://wa.me/?text=' + t;
  }

  /** What the agent reads when the visitor lands in WhatsApp — name, their
   *  number and the question, all before they have typed a word. */
  function whatsappText(payload, detail, carried) {
    var lines = [BRAND + ' — chat handoff'];
    lines.push('Name: ' + payload.userName);
    lines.push('WhatsApp: ' + payload.contact);
    lines.push('Topic: ' + payload.topic);
    if (detail && detail !== payload.topic) lines.push('Their words: ' + detail);
    if (carried && carried !== payload.topic) lines.push('Asked earlier: ' + carried);
    return lines.join('\n');
  }

  function wantsHuman(text) {
    return HUMAN_WORD.test(text) && ACTION_WORD.test(text);
  }

  /** A handoff trigger: an explicit ask for a person, or commissioning a
   *  custom complex tour (which by definition needs a human to build). */
  function isHandoffTrigger(text) {
    return wantsHuman(text) || (CUSTOM_TOUR_WORD.test(text) && ACTION_WORD.test(text));
  }

  function demandsNow(raw) {
    return URGENT.test(raw) && !REFUSE_FIRST.test(raw);
  }

  function messagesEl() {
    return document.getElementById('ai-chat-messages');
  }

  /** Append a full bot bubble. Used when a button drives the flow, so no
   *  responder is running to wrap the HTML for us. */
  function appendBot(inner) {
    var msgs = messagesEl();
    if (!msgs) return null;
    var div = document.createElement('div');
    div.className = 'ai-message bot';
    div.innerHTML = '<div class="ai-msg-avatar">' + BOT_AVATAR + '</div>' +
                    '<div class="ai-msg-content">' + inner + '</div>';
    msgs.appendChild(div);
    msgs.scrollTop = msgs.scrollHeight;
    return div;
  }

  function focusInput() {
    var input = document.getElementById('ai-chat-input');
    if (input) input.focus();
  }

  function knowledge(l) {
    for (var i = 0; i < KNOWLEDGE.length; i++) {
      if (KNOWLEDGE[i].re.test(l)) return KNOWLEDGE[i].html;
    }
    return null;
  }

  // ── Gathering the three details ───────────────────────────────────────

  function nextMissing() {
    if (!lead.userName) return 'name';      // 1. Full Name
    if (!lead.contact) return 'contact';    // 2. Phone Number / Email
    // The quick path exists for a question the bot could not answer: their
    // question already IS the reason, so asking them to retype it as a
    // "reason" would be the third prompt in what should feel like two.
    if (lead.quick) return null;
    if (!lead.topic) return 'topic';        // 3. Reason for contacting
    return null;
  }

  function hasContact(s) {
    return EMAIL_FIND.test(s) || PHONE_FIND.test(s);
  }

  /** Trim a name down to the part that is actually a name. Without this,
   *  "Hi I'm Ama and I want to speak to a human about a refund" would be
   *  stored as a forty-character sentence and echoed back as "Thank you,
   *  Ama and I want to speak to a human about a". Cuts at the first word
   *  that is grammar rather than a name — and `of`/`in`/`is` only match as
   *  whole words, so "Ama Ofosu" survives intact. */
  function cleanName(s) {
    var v = String(s).replace(/[\s,;:.]+$/, '').trim();
    var cut = v.match(/^(.*?)\s+(?:and|then|i\b|my\b|to\b|about\b|for\b|with\b|please\b|who\b|need\b|want\b|would\b|like\b|the\b|a\b|an\b|is\b|are\b|of\b|in\b|on\b|from\b|regarding\b|because\b|that\b|speak\b|talk\b|connect\b|transfer\b).*$/i);
    if (cut && cut[1]) v = cut[1];
    return v.slice(0, 60);
  }

  function extractContact(s) {
    var e = s.match(EMAIL_FIND);
    if (e) return e[0].replace(/[.,;]+$/, '');
    var p = s.match(PHONE_FIND);
    if (p) {
      var digits = p[0].replace(/\D/g, '');
      if (digits.length >= 7 && digits.length <= 15) return p[0].trim();
    }
    return '';
  }

  /** Fold whatever the visitor volunteered into `lead`. Works whether they
   *  answered the prompt that was asked or dumped all three details into one
   *  message — the spec says collect what is "not already provided", so a
   *  single "I'm Kwame, 0244..., custom safari" ends the flow immediately.
   *
   *  `precise` is set when the message is itself another handoff request.
   *  Exact extractions (an address, a number, "my name is X", a classified
   *  reason) still count — they volunteered them — but the "you were asked
   *  for a name, so the whole message is the name" fallback is switched off,
   *  because that is how "talk to a human" ends up stored as the name "talk". */
  function absorb(raw, precise) {
    // 2. Contact — recognised anywhere in the message.
    if (!lead.contact) {
      var c = extractContact(raw);
      if (c) lead.contact = c;
    }

    // Whatever is left once the contact is taken out is prose about them.
    var rest = raw;
    if (lead.contact && raw.indexOf(lead.contact) !== -1) {
      rest = raw.replace(lead.contact, ' ');
    }
    rest = rest.replace(/\s{2,}/g, ' ').replace(/^[\s,;:\-–]+|[\s,;:\-–]+$/g, '');

    // 1. Name — an explicit declaration wins; otherwise the reply to the name
    //    prompt is simply the name, unless it is a question about it.
    //    Never inferred when we just asked for contact: "call me on 0244..."
    //    would otherwise be read as a name of "on".
    if (!lead.userName && asked !== 'contact' && rest && rest.indexOf('?') === -1) {
      var n = rest.match(NAME_FIND);
      var candidate = n ? cleanName(n[1]) : '';
      // Two letters minimum, and not a preposition the pattern can swallow.
      var usable = candidate.length > 1 &&
                   !/^(on|at|via|my|the|to|for|is|and|you|here)$/i.test(candidate);
      if (n && usable) {
        lead.userName = candidate;
      } else if (!precise && asked === 'name' && rest.length > 1) {
        lead.userName = cleanName(rest);
      }
    }

    // 3. Reason — classified into the spec's own examples when it matches one.
    //    Only the LABEL goes into `lead.topic`, because that string is echoed
    //    straight back to the visitor in the transfer sentence. Gluing their
    //    message onto it would produce "I understand you'd like to Refund
    //    request — Hi I'm Ama and I want to speak to a human about a refund!".
    //    Their raw words go to `lead.detail` instead and travel to the agent's
    //    inbox, where the context is useful and the clunkiness is invisible.
    if (!lead.topic && rest && rest.indexOf('?') === -1) {
      if (/\brefund\b|\bmoney\s+back\b|\bcancel(?:ed|lation)?\b/i.test(rest)) {
        lead.topic = 'Refund request';
        lead.detail = rest.slice(0, 200);
      } else if (CUSTOM_TOUR_WORD.test(rest) || /\bgroup\b|\bsafari\b|\bcustomi[sz]/i.test(rest)) {
        lead.topic = 'Custom booking';
        lead.detail = rest.slice(0, 200);
      } else if (/\bspecial\b|\bVIP\b|\baccessible\b/i.test(rest)) {
        lead.topic = 'Special tour';
        lead.detail = rest.slice(0, 200);
      } else if (!precise && asked === 'topic') {
        // Asked directly for a summary — their own words ARE the summary.
        lead.topic = rest.slice(0, 160);
        lead.detail = '';
      }
    }
  }

  function askHTML(field) {
    if (field === 'name') {
      // "First" would be a lie if the contact or reason already arrived.
      if (lead.contact || lead.topic) {
        return '<p>Almost there — I just need your name to finish the handoff.</p>' +
               '<p style="color:var(--text-muted);">What\'s your <strong>full name</strong>?</p>';
      }
      return '<p>Akwaaba! Let me pass you to one of our live travel representatives.</p>' +
             '<p style="color:var(--text-muted);">First — what\'s your <strong>full name</strong>?</p>';
    }
    if (field === 'contact') {
      if (lead.quick) {
        return '<p>Thank you, <strong>' + esc(lead.userName) + '</strong>. ' +
               'What\'s your <strong>WhatsApp number</strong>?</p>' +
               '<p style="color:var(--text-muted);font-size:0.88rem;">Example: <em>0244 123 456</em></p>';
      }
      return '<p>Thank you, <strong>' + esc(lead.userName) + '</strong>. ' +
             'What <strong>phone number or email</strong> should the agent reach you on?</p>' +
             '<p style="color:var(--text-muted);font-size:0.88rem;">Example: <em>0244 123 456</em> or <em>ama@example.com</em></p>';
    }
    return '<p>Last one — briefly, <strong>why</strong> do you want to speak to an agent?</p>' +
           '<p style="color:var(--text-muted);font-size:0.88rem;">For example: <em>Custom Booking</em>, ' +
           '<em>Refund Request</em> or <em>Special Tour</em>.</p>';
  }

  function badContactHTML() {
    if (lead.quick) {
      return '<p style="color:var(--danger);">I need a WhatsApp number so the agent can reach you.</p>' +
             '<p style="color:var(--text-muted);font-size:0.88rem;">Example: <em>0244 123 456</em></p>';
    }
    return '<p style="color:var(--danger);">I need a phone number or an email address so the agent can reach you.</p>' +
           '<p style="color:var(--text-muted);font-size:0.88rem;">Example: <em>0244 123 456</em> or <em>ama@example.com</em></p>';
  }

  // ── Delivery ──────────────────────────────────────────────────────────

  /** Fire the handoff. The result element is looked up when the response
   *  lands, not when this is called — the responder appends our returned HTML
   *  synchronously *after* this function returns, so the node does not exist
   *  yet. By the time a network promise settles the stack has unwound and it
   *  is there. */
  function submit(payload) {
    function done(html) {
      var el = document.getElementById('agent-status');
      if (el) el.innerHTML = html;
    }

    fetch('/api/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.success && d.emailSent) {
          done('Passed — reference <strong>' + esc(d.ticket) + '</strong>. An agent will follow up on ' +
               '<strong>' + esc(payload.contact) + '</strong>.');
        } else if (d && d.success && d.contact) {
          // SMTP refused it. Do not pretend it sent, and do not leave the
          // visitor stranded: hand them the same mailbox the agent reads.
          done('Our mail service wouldn\'t take that just now — email ' +
               '<strong>' + esc(d.contact) + '</strong> directly and an agent will pick it up.');
        } else {
          done(esc((d && d.error) || 'That didn\'t send — please try again.'));
        }
      })
      .catch(function () {
        done('No connection to the server — please try again in a moment.');
      });
  }

  /**
   * Build the transfer: fill anything ungathered with UNKNOWN, emit the
   * <HANDOFF> trigger tag, show it, and POST it. The tag is both the display
   * and the payload — parse it out of the rendered HTML and you get exactly
   * the body that went to /api/contact.
   */
  function transfer() {
    // Everything is read out of `lead` BEFORE the reset below — clearing
    // first would leave the composed message reading an emptied object.
    var carried = lead.question || '';
    var detail = lead.detail || '';
    var payload = {
      transfer: true,
      userName: lead.userName || 'UNKNOWN',
      contact: lead.contact || 'UNKNOWN',
      topic: lead.topic || carried || 'General enquiry'
    };

    var json = JSON.stringify(payload, null, 2);
    var summary = payload.topic === 'General enquiry'
      ? 'arrange this with our team'
      : payload.topic;

    // Their original question and their raw words ride along — context for
    // the agent. Neither reaches the chat bubble, only the inbox.
    var message = payload.topic;
    if (detail && detail !== payload.topic) message += '\n' + detail;
    if (carried && carried !== payload.topic) message += '\n\nAsked earlier: ' + carried;

    reset();

    submit({ name: payload.userName, contact: payload.contact, message: message });

    var waURL = whatsappURL(whatsappText(payload, detail, carried));

    return '<p>I understand you\'d like to <strong>' + esc(summary) + '</strong>! I\'ve noted down your request. ' +
           'I am now transferring this chat to one of our live travel representatives — ' +
           'open WhatsApp below and you\'re with them.</p>' +
           '<a href="' + esc(waURL) + '" target="_blank" rel="noopener noreferrer" ' +
           'style="display:inline-block;margin-top:8px;background:#25D366;color:#fff;' +
           'border:none;border-radius:6px;padding:9px 16px;font-size:0.88rem;font-weight:600;' +
           'cursor:pointer;text-decoration:none;">Open WhatsApp &rarr;</a> ' +
           '<span style="color:var(--text-muted);font-size:0.8rem;">your details are already written in</span>' +
           '<p id="agent-status" style="color:var(--text-muted);font-size:0.88rem;">Sending your details…</p>' +
           '<HANDOFF style="display:block;white-space:pre-wrap;margin-top:8px;padding:8px 10px;' +
           'background:rgba(128,128,128,.10);border:1px dashed rgba(128,128,128,.55);border-radius:6px;' +
           'font:0.74rem/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;' +
           'color:var(--text-muted);word-break:break-word;overflow-x:auto;">' +
           jsonEsc(json) +
           '</HANDOFF>';
  }

  function reset() {
    state = 'idle';
    asked = '';
    lead = { userName: '', contact: '', topic: '', detail: '', question: '' };
    lastQuestion = '';
  }

  // ── The one entry point ───────────────────────────────────────────────

  /**
   * Called at the very top of BOTH responders (exported as `agentHandoff`).
   * @returns {string|null} HTML content for the bot bubble, or null to let
   *   the normal keyword logic answer.
   */
  function respond(q) {
    var raw = String(q == null ? '' : q).trim();
    if (!raw) return null;
    var l = raw.toLowerCase();

    // ── Mid-gathering: this message is one of the three details. ────────
    if (state === 'collecting') {
      // Demand first: "stop asking and connect me" must transfer rather than
      // fall through to the refusal that leads it.
      if (demandsNow(raw)) return transfer();

      // Escape hatch — back to normal answering instead of reprompting.
      if (ABORT_RE.test(raw)) {
        reset();
        return '<p>No problem — ask me anything else.</p>';
      }

      // Repeating the request while we are asking for details is impatience,
      // not an answer: without this "talk to a human" would be swallowed as
      // their name (cleanName would even store it as "talk"). Transfer with
      // UNKNOWN — but take anything exact they happened to include, since
      // "I'm Kwame, custom group tour" is a real answer, not a repeat.
      if (isHandoffTrigger(l)) {
        absorb(raw, true);
        return transfer();
      }

      absorb(raw);

      if (asked === 'contact' && !lead.contact) return badContactHTML();

      var missing = nextMissing();
      if (!missing) return transfer();
      asked = missing;
      return askHTML(missing);
    }

    // ── A handoff is being requested. ───────────────────────────────────
    if (isHandoffTrigger(l)) {
      // state must flip here, or the visitor's next message would fall
      // through to ordinary keyword answering and the three details would
      // never be collected.
      state = 'collecting';
      asked = '';
      lead = { userName: '', contact: '', topic: '', detail: '', question: '', quick: false };
      absorb(raw);                               // catch details already given
      lead.question = lastQuestion && lastQuestion !== raw ? lastQuestion : '';
      lastQuestion = '';

      var first = nextMissing();
      if (!first) return transfer();             // they supplied all three at once
      asked = first;
      return askHTML(first);
    }

    // ── Persona / knowledge. Recorded too, so a handoff on the next turn
    //    still carries the question they cared about. ────────────────────
    var k = knowledge(l);
    if (k) {
      lastQuestion = raw;
      return k;
    }

    // ── Ordinary message: remember it in case they hand off next turn. ──
    lastQuestion = raw;
    return null;
  }

  /** Button in the fallback branch — starts the same flow without a trigger
   *  word, which is how a visitor whose question went unanswered gets out. */
  function startAgentHandoff() {
    if (state === 'collecting') { focusInput(); return; }
    asked = '';
    lead = { userName: '', contact: '', topic: '', detail: '', question: lastQuestion || '', quick: false };
    lastQuestion = '';
    state = 'collecting';
    var first = nextMissing();
    asked = first;
    appendBot(askHTML(first));
    focusInput();
  }

  /**
   * Appended to every responder's fallback reply — so reaching this function
   * IS the signal that the bot could not answer.
   *
   * Per the spec there is no button to click first: the same bubble starts
   * asking for their name, and their unanswered question is filed as the
   * reason so they never have to retype it. Two prompts, then WhatsApp.
   * (Deliberately returns a string rather than appending a bubble — this is
   * evaluated while the responder is still building its reply, so appending
   * here would land this prompt BEFORE the "I don't have that one" line.)
   */
  function agentHandoffCTA() {
    if (state !== 'collecting') {
      state = 'collecting';
      asked = 'name';
      lead = {
        userName: '', contact: '', topic: '',
        detail: lastQuestion || '', question: lastQuestion || '', quick: true
      };
      lastQuestion = '';
    }
    return '<p style="margin-top:8px;">I don\'t have that one — but a live person does.</p>' +
           askHTML('name') +
           '<button type="button" onclick="skipToAgent()" ' +
           'style="background:#25D366;color:#fff;border:none;border-radius:6px;' +
           'padding:7px 14px;font-size:0.85rem;font-weight:600;cursor:pointer;margin-top:6px;' +
           'display:inline-block;">Skip — open WhatsApp now &rarr;</button>';
  }

  /** One-click way past the questions: transfer immediately with UNKNOWN for
   *  whatever has not been given. The button-shaped equivalent of typing an
   *  urgent demand, for a visitor who will not fill in a form. */
  function skipToAgent() {
    if (state !== 'collecting') { talkToAgent(); return; }
    if (!lead.userName) lead.userName = 'UNKNOWN';
    if (!lead.contact) lead.contact = 'UNKNOWN';
    if (!lead.topic) lead.topic = lead.question || lead.detail || 'General enquiry';
    appendBot(transfer());
    focusInput();
  }

  /**
   * Footer "Talk to an Agent" entry point.
   *
   * On a page that has a chat window this opens it and drops straight into
   * the first question. planner and regions carry no chat markup at all, so
   * rather than a dead link the intent is parked in sessionStorage and picked
   * up when index.html loads — the visitor never has to ask twice.
   */
  function talkToAgent() {
    var win = document.getElementById('ai-chat-window');
    if (!win) {
      try { sessionStorage.setItem('memorra-open-agent', '1'); } catch (e) {}
      window.location.href = 'index.html';
      return;
    }
    win.classList.add('active');   // add, never toggle: a second click must not close it
    startAgentHandoff();
  }

  /** Runs on a page that DOES have a chat — honours a request made elsewhere. */
  function restorePendingHandoff() {
    var flag = false;
    try {
      flag = sessionStorage.getItem('memorra-open-agent') === '1';
      if (flag) sessionStorage.removeItem('memorra-open-agent');
    } catch (e) {}
    if (!flag) return;
    var win = document.getElementById('ai-chat-window');
    if (win) win.classList.add('active');
    startAgentHandoff();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', restorePendingHandoff);
  } else {
    restorePendingHandoff();
  }

  // The original names are kept so neither responder, nor any page, needs to
  // change: app.bundle.js and app.js already call `window.agentHandoff(q)`.
  window.Akwaaba = {
    name: PERSONA_NAME,
    respond: respond,
    knowledge: knowledge,
    agentHandoffCTA: agentHandoffCTA,
    startAgentHandoff: startAgentHandoff,
    skipToAgent: skipToAgent,
    talkToAgent: talkToAgent
  };
  window.talkToAgent = talkToAgent;
  window.agentHandoff = respond;
  window.startAgentHandoff = startAgentHandoff;
  window.skipToAgent = skipToAgent;
  window.agentHandoffCTA = agentHandoffCTA;
})();
