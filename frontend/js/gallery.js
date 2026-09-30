/**
 * Photo gallery inside the destination and festival modals.
 *
 * Each destination and festival on this site carries a single photograph, which
 * is all that Wikimedia Commons reliably holds for most of these places. The
 * modal therefore showed one hero image and nothing else, so tapping "View
 * Details" moved a visitor from a card straight to a wall of text.
 *
 * This adds a row of additional photographs of the same place underneath the
 * hero. The photos are real, and they are of the same destination: the data
 * carries an `images` array per entry and every path in it is a photograph of
 * that entry, credited in IMAGE-CREDITS.md. Nothing here substitutes a nearby
 * place to pad the row out, and an entry with no extra photographs simply gets
 * no row rather than a misleading one.
 *
 * Two pieces:
 *   stripHtml()  markup for the thumbnail row
 *   open()       a full-size viewer with arrows, dots, keyboard and swipe
 *
 * Click handling is delegated from the document, so re-rendering a modal needs
 * no rebinding.
 */
(function (global) {
  'use strict';

  /** Photos of the entity whose modal is currently open. */
  var photos = [];

  /** Index into `photos` shown by the viewer, or -1 when it is closed. */
  var current = -1;

  /** The viewer root, created on first use and reused thereafter. */
  var viewer = null;
  var stageImg = null;
  var captionEl = null;
  var dotsEl = null;
  var prevBtn = null;
  var nextBtn = null;
  var lastFocus = null;

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  /**
   * Markup for the row of additional photographs.
   *
   * Returns '' when the entity has fewer than two extra photos, because a
   * single lone thumbnail is not a gallery and reads as a mistake. The hero is
   * already on screen, so two is the point at which the row says something.
   *
   * @param {Array<{image: string, alt: string}>} list Extra photos, in order.
   * @returns {string} HTML, or '' when there is nothing worth showing.
   */
  function stripHtml(list) {
    if (!list || list.length < 2) return '';

    var total = list.length + 1; // the hero counts as the first photo
    var buttons = list.map(function (p, i) {
      return '<button class="modal-gallery-item" type="button"' +
        ' data-gallery-index="' + (i + 1) + '"' +
        ' aria-label="View photo ' + (i + 2) + ' of ' + total + ' full size">' +
        global.imgTag(p.image, esc(p.alt), {
          slot: 'modalThumb',
          className: 'modal-gallery-img'
        }) +
        '</button>';
    }).join('');

    return '<div class="modal-gallery">' +
      '<p class="modal-gallery-heading">More photos of this place' +
      (list.length > 3 ? ' <span class="modal-gallery-count">(' + list.length + ')</span>' : '') +
      '</p>' +
      '<div class="modal-gallery-track">' + buttons + '</div>' +
      '</div>';
  }

  function buildViewer() {
    var d = document.createElement('div');
    d.className = 'gallery-viewer';
    d.setAttribute('role', 'dialog');
    d.setAttribute('aria-modal', 'true');
    d.setAttribute('aria-label', 'Photo viewer');
    d.innerHTML =
      '<button class="gallery-viewer-btn gallery-viewer-close" type="button" aria-label="Close photo viewer">' +
      '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>' +
      '</button>' +
      '<button class="gallery-viewer-btn gallery-viewer-prev" type="button" aria-label="Previous photo">' +
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polyline points="15 18 9 12 15 6"/></svg>' +
      '</button>' +
      '<button class="gallery-viewer-btn gallery-viewer-next" type="button" aria-label="Next photo">' +
      '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polyline points="9 18 15 12 9 6"/></svg>' +
      '</button>' +
      '<div class="gallery-viewer-stage"><img alt=""></div>' +
      '<p class="gallery-viewer-caption"></p>' +
      '<div class="gallery-viewer-dots"></div>';
    document.body.appendChild(d);

    stageImg = d.querySelector('.gallery-viewer-stage img');
    captionEl = d.querySelector('.gallery-viewer-caption');
    dotsEl = d.querySelector('.gallery-viewer-dots');
    prevBtn = d.querySelector('.gallery-viewer-prev');
    nextBtn = d.querySelector('.gallery-viewer-next');

    d.querySelector('.gallery-viewer-close').addEventListener('click', close);
    prevBtn.addEventListener('click', function () { show(current - 1); });
    nextBtn.addEventListener('click', function () { show(current + 1); });
    // Tapping the backdrop closes, but a tap on the photo itself must not.
    d.addEventListener('click', function (e) { if (e.target === d) close(); });

    bindSwipe(d.querySelector('.gallery-viewer-stage'));
    bindKeys(d);
    return d;
  }

  function show(i) {
    if (!photos.length) return;
    if (i < 0) i = photos.length - 1;
    if (i >= photos.length) i = 0;

    // Preload the neighbours so paging does not flash an empty stage.
    [i + 1, i - 1].forEach(function (n) {
      var p = photos[(n + photos.length) % photos.length];
      if (p) { var pre = new Image(); pre.src = p.image; }
    });

    current = i;
    var p = photos[i];
    // The viewer is the one place the full-resolution master is served. The
    // thumbnails and the hero are right-sized derivatives; here the visitor has
    // explicitly asked to see the photograph properly.
    stageImg.src = p.image;
    stageImg.alt = p.alt || '';
    captionEl.textContent = (i + 1) + ' of ' + photos.length +
      (p.credit ? '  \u00b7  ' + p.credit : '');

    var many = photos.length > 1;
    prevBtn.hidden = !many;
    nextBtn.hidden = !many;

    if (photos.length > 1) {
      if (dotsEl.children.length !== photos.length) {
        dotsEl.innerHTML = photos.map(function (p2, n) {
          return '<button class="gallery-viewer-dot" type="button" data-gallery-dot="' + n +
            '" aria-label="Photo ' + (n + 1) + '"></button>';
        }).join('');
      }
      dotsEl.hidden = false;
      Array.prototype.forEach.call(dotsEl.children, function (dot, n) {
        dot.classList.toggle('is-active', n === i);
        dot.setAttribute('aria-current', n === i ? 'true' : 'false');
      });
    } else {
      dotsEl.hidden = true;
    }
  }

  function open(i) {
    if (!photos.length) return;
    if (!viewer) viewer = buildViewer();
    lastFocus = document.activeElement;
    viewer.classList.add('is-open');
    document.documentElement.classList.add('gallery-open');
    show(i);
    // Focus the close button so Escape and Tab behave from inside the dialog.
    viewer.querySelector('.gallery-viewer-close').focus();
  }

  function close() {
    if (!viewer) return;
    viewer.classList.remove('is-open');
    document.documentElement.classList.remove('gallery-open');
    current = -1;
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  function bindKeys(d) {
    d.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { e.stopPropagation(); close(); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); show(current - 1); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); show(current + 1); }
    });
  }

  function bindSwipe(stage) {
    var x0 = null, y0 = null;
    stage.addEventListener('touchstart', function (e) {
      if (e.touches.length !== 1) return;
      x0 = e.touches[0].clientX;
      y0 = e.touches[0].clientY;
    }, { passive: true });
    stage.addEventListener('touchend', function (e) {
      if (x0 === null || !e.changedTouches.length) return;
      var dx = e.changedTouches[0].clientX - x0;
      var dy = e.changedTouches[0].clientY - y0;
      x0 = null; y0 = null;
      // Horizontal intent only, so a vertical scroll is never hijacked.
      if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy) * 1.5) {
        show(dx < 0 ? current + 1 : current - 1);
      }
    }, { passive: true });
  }

  // One delegated handler for the whole document: thumbnail buttons open the
  // viewer, and the dots inside it jump. Modals are re-rendered on every tap, so
  // per-element listeners would have to be re-attached each time.
  document.addEventListener('click', function (e) {
    var dot = e.target.closest && e.target.closest('[data-gallery-dot]');
    if (dot) {
      e.preventDefault();
      show(parseInt(dot.getAttribute('data-gallery-dot'), 10));
      return;
    }
    var btn = e.target.closest && e.target.closest('[data-gallery-index]');
    if (btn) {
      e.preventDefault();
      open(parseInt(btn.getAttribute('data-gallery-index'), 10));
      return;
    }
    // The hero is photo 1 of the set, so clicking it opens the viewer at the
    // start rather than doing nothing. Only inside a modal, and only when there
    // is more than one photo, so a lone image does not invite a click it cannot
    // honour.
    var hero = e.target.closest && e.target.closest('.modal-hero-img');
    if (hero && photos.length > 1) {
      e.preventDefault();
      open(0);
    }
  });

  /**
   * Record the photo set for the entity whose modal is being rendered.
   * The hero is index 0 so the viewer can page from it into the extra photos.
   */
  function setPhotos(hero, extra) {
    photos = [];
    if (hero && hero.image) {
      photos.push({ image: hero.image, alt: hero.alt || '', credit: hero.credit || '' });
    }
    (extra || []).forEach(function (p) {
      if (p && p.image) {
        photos.push({ image: p.image, alt: p.alt || '', credit: p.credit || '' });
      }
    });
  }

  global.ModalGallery = {
    stripHtml: stripHtml,
    setPhotos: setPhotos,
    open: open,
    close: close
  };
})(window);
