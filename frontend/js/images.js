/**
 * Right-sized image sources.
 *
 * Destination cards paint into a 291x180 box (356x180 on a 390px phone) and the
 * tour tiles into roughly 305x190, but the source photos are 640-1920px wide
 * and average 166 KB. Served as-is, the destinations grid asked for 23 MB to
 * fill a grid of thumbnails, and images trickled in so slowly that cards sat
 * visibly blank.
 *
 * tools/build_image_variants.py writes 400px and 800px derivatives of every
 * image and records which widths actually exist in window.IMAGE_VARIANTS.
 * This file turns that into a srcset so the browser fetches one file at the
 * size it is about to paint, and falls back to the original when no derivative
 * exists (vectors, and photos already smaller than the target).
 *
 * The `sizes` values below must track the CSS. They are the browser's only clue
 * about how wide the image will be, so if a card or tile changes size, update
 * the matching preset here too.
 */
(function (global) {
  'use strict';

  var WIDTHS = global.IMAGE_VARIANTS || {};

  /**
   * Coarse CSS width of each slot. The browser combines these with the device
   * pixel ratio to choose a candidate: a 2x phone on a 356px card needs ~712
   * device pixels and so picks the 800w file.
   */
  var SIZES = {
    card: '(max-width: 700px) 92vw, 300px',
    tile: '(max-width: 700px) 92vw, 320px',
    modal: '(max-width: 900px) 100vw, 800px'
  };

  /**
   * Keep in step with variant_path() in tools/build_image_variants.py.
   * Handles .jpg, .jpeg, .png and .webp sources alike.
   */
  function variantUrl(path, width) {
    return String(path).replace(/(\.[a-z0-9]+)$/i, '-' + width + '.jpg');
  }

  /**
   * Build an <img> tag for a site image.
   *
   * `alt` is inserted verbatim, so callers must pass already-escaped text.
   *
   * @param {string} path   Source path exactly as stored in the data.
   * @param {string} alt    Pre-escaped alternative text.
   * @param {object} [opts] slot: 'card' | 'tile' | 'modal'; className; loading;
   *                        decoding; width/height for layout stability.
   * @returns {string} An <img> tag, or '' when there is no image.
   */
  function imgTag(path, alt, opts) {
    if (!path) return '';
    opts = opts || {};

    var widths = WIDTHS[path] || [];
    // Fall back to the smallest derivative, not the original, so a browser
    // without srcset support still gets a thumbnail rather than a 200 KB photo.
    var src = widths.length ? variantUrl(path, widths[0]) : path;

    var out = '<img src="' + src + '" alt="' + (alt || '') + '"';
    if (opts.className) out += ' class="' + opts.className + '"';
    if (opts.width) out += ' width="' + opts.width + '"';
    if (opts.height) out += ' height="' + opts.height + '"';
    if (widths.length) {
      out += ' srcset="' + widths.map(function (w) {
        return variantUrl(path, w) + ' ' + w + 'w';
      }).join(', ') + '"';
      out += ' sizes="' + (SIZES[opts.slot] || SIZES.card) + '"';
    }
    out += ' loading="' + (opts.loading || 'lazy') + '"';
    out += ' decoding="' + (opts.decoding || 'async') + '"';
    return out + '>';
  }

  global.variantUrl = variantUrl;
  global.imgTag = imgTag;
  global.IMAGE_SIZES = SIZES;
})(window);
