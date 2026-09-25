/**
 * Theme — ONE implementation, loaded by all four pages.
 *
 * index/planner/regions used to run app.bundle.js's `initTheme()` while
 * booking.html ran app.js's `initThemeToggle()`: two hand-kept copies of the
 * same idea that had already drifted once (booking wrote 'visitGhanaTheme'
 * defaulting to 'dark', so it ignored the Light choice the other pages had
 * saved, and a toggle made there never reached them). Both were fixed, but
 * with two copies still in place they could drift again.
 *
 * Now every page loads this file and every duplicate binder is removed, so
 * the pages cannot disagree. Same contract as app.bundle.js had:
 *
 *     localStorage['memorra-theme'] = 'dark' | 'light'   (default 'light')
 *     <html data-theme="dark">                            (attribute is the truth)
 *
 * Sync paths, in the order they bite:
 *   load       - inline <head> script paints early (no flash), this re-applies
 *   storage    - another tab flipped it
 *   pageshow   - back/forward restores come from the bfcache: <head> never
 *                re-runs, so a page cached as light came back light while the
 *                saved value said dark. This is the "I toggled dark on booking,
 *                the next page loaded light" bug.
 *   visibility - a frozen background tab can miss the storage event entirely
 */
(function () {
  var KEY = 'memorra-theme';

  function saved() {
    try { return localStorage.getItem(KEY) || 'light'; } catch (e) { return 'light'; }
  }

  function applyStoredTheme() {
    document.documentElement.setAttribute('data-theme', saved() === 'dark' ? 'dark' : 'light');
  }

  function setTheme(next) {
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem(KEY, next); } catch (e) {}
  }

  function announce(next) {
    // Toast element/styles differ per page; never let a missing one break the toggle.
    try { if (typeof showToast === 'function') showToast('Switched to ' + (next === 'light' ? 'Light' : 'Dark') + ' theme'); }
    catch (e) {}
  }

  function initTheme() {
    // Paint before anything else; the <head> script already did this but a
    // caller may hand us a different stored value mid-session.
    applyStoredTheme();

    // Another tab / window changed it.
    window.addEventListener('storage', function (e) {
      if (e.key === KEY) applyStoredTheme();
    });

    // Page returned from the back/forward cache.
    window.addEventListener('pageshow', function (e) {
      if (e.persisted) applyStoredTheme();
    });

    // Tab became visible again (storage events can be dropped while frozen).
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'visible') applyStoredTheme();
    });

    document.querySelectorAll('.theme-toggle-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var next = (document.documentElement.getAttribute('data-theme') || 'light') === 'dark' ? 'light' : 'dark';
        setTheme(next);
        announce(next);
      });
    });
  }

  // Expose it so page scripts can re-apply on demand.
  window.initTheme = initTheme;

  function boot() { initTheme(); }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
