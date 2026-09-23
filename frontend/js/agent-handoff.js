/**
 * Agent Handoff — pass the chat to a human, on channels that are already free.
 *
 * ONE implementation, loaded by index.html and booking.html. The responder
 * itself is forked between those two pages (app.bundle.js `chatResponse` vs
 * app.js `generateAIResponse`) and this deliberately does not merge them — it
 * sits in front of both:
 *
 *     responder(q)
 *       -> agentHandoff(q)            // HTML if this message IS the handoff,
 *                                      // else null and keyword logic runs
 *       -> ... keyword branches ...
 *       -> fallback + agentHandoffCTA() // "talk to a human agent" button
 *
 * State machine — a single slot, because the bot needs a second message from
 * the visitor (the reply-to address):
 *
 *     idle --asks for human--> wantEmail --valid email--> idle (sent)
 *                                  |
 *                                  +--invalid--> wantEmail (reprompt)
 *
 * Delivery is POST /api/contact -> Brevo SMTP (free tier, 300/day). Nothing
 * paid, no third-party chat vendor, no webhook to babysit.
 */
(function () {
  'use strict';

  var BOT_AVATAR =
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
    '<rect x="3" y="11" width="18" height="10" rx="2"/><circle cx="12" cy="5" r="2"/></svg>';

  // 'idle'      = normal keyword answering
  // 'wantEmail' = the very next message is the address the agent replies to
  var state = 'idle';

  // The unanswered question to forward. Captured from the previous message so
  // a visitor who asks "is Mole safe in August?" and *then* demands a human
  // still gets their actual question carried across.
  var pendingQuestion = '';
  var lastQuestion = '';

  // Human detection needs BOTH a person-word and an action-word. Requiring
  // the pair (rather than either alone) is what keeps "your booking agent"
  // or "is there someone?" from yanking a visitor out of a normal Q&A.
  // Word boundaries matter: without them "person" matches inside
  // "personalised itinerary" and "agent" inside "agency", both of which are
  // ordinary travel questions that must fall through to the keyword logic.
  var HUMAN_WORD = /\b(humans?|agents?|person|representatives?|somebody|someone)\b|\blive support\b/i;
  var ACTION_WORD = /(talk|speak|chat|connect|transfer|reach|contact|want|need|give|put|call)/i;

  // Escape hatch. Without this a visitor who declines the prompt (or was
  // pulled in by a false positive) is reprompted for an address forever and
  // never gets back to normal answering. Checked ONLY after the email test
  // has failed — a valid address like `no.x@example.com` starts with a
  // prefix that would otherwise match and be thrown away.
  var ABORT_RE = /^(?:ok\s*,?\s*|actually\s*,?\s*)?(?:no\b|nope\b|nah\b|naw\b|cancel\b|stop\b|never\s*mind\b|nevermind\b|forget\s+(?:it|that)\b|not\s+now\b|go\s+back\b|exit\b|skip\b|leave\s+it\b|change\s+my\s+mind\b)/i;

  // Mirrors the server's check exactly, so a value accepted here is accepted
  // by /api/contact and the visitor never gets bounced after committing.
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function wantsHuman(text) {
    return HUMAN_WORD.test(text) && ACTION_WORD.test(text);
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

  function promptHTML() {
    return '<p>Sure — I\'ll pass you to a human agent.</p>' +
           '<p style="color:var(--text-muted);">What email address should they reply to?</p>';
  }

  function badEmailHTML() {
    return '<p style="color:var(--danger);">That doesn\'t look like an email address — could you check it?</p>' +
           '<p style="color:var(--text-muted);font-size:0.88rem;">Example: <em>ama@example.com</em></p>';
  }

  function confirmHTML() {
    return '<p>Handing you over to a human agent…</p>' +
           '<p id="agent-status" style="color:var(--text-muted);font-size:0.88rem;">' +
           'Sending your question…</p>';
  }

  /** Fire the handoff. The result element is looked up when the response
   *  lands, not when this is called — the responder appends our returned HTML
   *  synchronously *after* this function returns, so the node does not exist
   *  yet. By the time a network promise settles the stack has unwound and it
   *  is there. */
  function submit(question, email) {
    var body = JSON.stringify({
      name: '',
      email: email,
      message: question || 'Visitor asked to be passed to a human agent from the chatbot.'
    });

    function done(html) {
      var el = document.getElementById('agent-status');
      if (el) el.innerHTML = html;
    }

    fetch('/api/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body
    })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.success && d.emailSent) {
          done('Passed — reference <strong>' + esc(d.ticket) + '</strong>. ' +
               'An agent will reply to <strong>' + esc(email) + '</strong>.');
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
   * Called at the very top of BOTH responders.
   * @returns {string|null} HTML content for the bot bubble, or null to let
   *   the normal keyword logic answer.
   */
  function agentHandoff(q) {
    var raw = String(q == null ? '' : q).trim();
    if (!raw) return null;
    var l = raw.toLowerCase();

    // --- We are mid-handoff: this message is the reply-to address. ---
    if (state === 'wantEmail') {
      // Email test FIRST, abort second: a valid address such as
      // `no.x@example.com` begins with a prefix ABORT_RE would otherwise
      // swallow and throw away.
      if (EMAIL_RE.test(raw)) {
        var question = pendingQuestion;
        state = 'idle';
        pendingQuestion = '';
        lastQuestion = '';
        submit(question, raw);
        return confirmHTML();
      }
      if (ABORT_RE.test(raw)) {
        // Escape hatch — return to normal answering instead of reprompting.
        state = 'idle';
        pendingQuestion = '';
        lastQuestion = '';
        return '<p>No problem — ask me anything else.</p>';
      }
      return badEmailHTML();   // stay in wantEmail
    }

    // --- They asked for a person. ---
    if (wantsHuman(l)) {
      pendingQuestion = lastQuestion;   // carry the real question across
      lastQuestion = '';
      state = 'wantEmail';
      return promptHTML();
    }

    // --- Ordinary message: remember it in case they hand off next turn. ---
    lastQuestion = raw;
    return null;
  }

  /** Button in the fallback branch — starts the same flow without a trigger
   *  word, which is how a visitor whose question went unanswered gets out. */
  function startAgentHandoff() {
    if (state === 'wantEmail') { focusInput(); return; }
    pendingQuestion = lastQuestion;
    lastQuestion = '';
    state = 'wantEmail';
    appendBot(promptHTML());
    focusInput();
  }

  /** Appended to every responder's fallback reply. */
  function agentHandoffCTA() {
    return '<p style="margin-top:8px;">I don\'t have that one yet — but a human does. ' +
           '<button type="button" onclick="startAgentHandoff()" ' +
           'style="background:var(--brand-primary);color:#fff;border:none;border-radius:6px;' +
           'padding:7px 14px;font-size:0.85rem;font-weight:600;cursor:pointer;margin-top:6px;' +
           'display:inline-block;">Talk to a human agent &rarr;</button></p>';
  }

  /**
   * Footer "Talk to an Agent" entry point.
   *
   * On a page that has a chat window this opens it and drops straight into
   * the email prompt. planner and regions carry no chat markup at all, so
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

  window.talkToAgent = talkToAgent;
  window.agentHandoff = agentHandoff;
  window.startAgentHandoff = startAgentHandoff;
  window.agentHandoffCTA = agentHandoffCTA;
})();
