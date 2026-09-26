# Image credits

Photographs on this site come from three places: the project's own photo
library, images supplied by us, and images reused under an open licence. Every
reused image is listed below with its author, licence and source link, as that
licence requires.

## Open-licence images

### Masquerades Dancing in Takoradi

- **File used on:** Music & Festival Tours tile (`index.html`)
- **Local copy:** `assets/images/masquerade_takoradi_dancing.jpg`
- **Author:** Noahalorwu
- **Licence:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0)
- **Source:** [commons.wikimedia.org/wiki/File:Masquerades_Dancing_in_Takoradi.jpg](https://commons.wikimedia.org/wiki/File:Masquerades_Dancing_in_Takoradi.jpg)
- **Subject:** Masquerades dancing at the Takoradi Masquerade Festival,
  Western Region, Ghana.

### A lady Masquerade - Takoradi *(alternate, not currently displayed)*

- **Local copy:** `assets/images/masquerade_takoradi_lady.jpg`
- **Author:** Noahalorwu
- **Licence:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0)
- **Source:** [commons.wikimedia.org/wiki/File:A_lady_Masquerade_-_Takoradi.jpg](https://commons.wikimedia.org/wiki/File:A_lady_Masquerade_-_Takoradi.jpg)

### Old Man and the Son Masqurade Dressing in Takoradi *(alternate, not currently displayed)*

- **Local copy:** `assets/images/masquerade_takoradi_dressing.jpg`
- **Author:** Noahalorwu
- **Licence:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0)
- **Source:** [commons.wikimedia.org/wiki/File:Old_Man_and_the_Son_Masqurade_Dressing_in_Takoradi.jpg](https://commons.wikimedia.org/wiki/File:Old_Man_and_the_Son_Masqurade_Dressing_in_Takoradi.jpg)

### MAKOLA

- **File used on:** Food & Market Tours tile (`index.html`)
- **Local copy:** `assets/images/market_makola.jpg`
- **Author:** Amuzujoe
- **Licence:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0)
- **Source:** [commons.wikimedia.org/wiki/File:MAKOLA.jpg](https://commons.wikimedia.org/wiki/File:MAKOLA.jpg)
- **Subject:** Makola Market, Accra — the largest market in Ghana, trading
  food, cloth and everyday goods.

### A trader at Makola Market *(alternate, not currently displayed)*

- **Local copy:** `assets/images/market_makola_trader.jpg`
- **Author:** Vrinda Khushu
- **Licence:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0)
- **Source:** [commons.wikimedia.org/wiki/File:A_trader_at_Makola_Market.jpg](https://commons.wikimedia.org/wiki/File:A_trader_at_Makola_Market.jpg)

### Makola Kayeyei *(alternate, not currently displayed)*

- **Local copy:** `assets/images/market_makola_kayeyei.jpg`
- **Author:** mariamayunusah
- **Licence:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0)
- **Source:** [commons.wikimedia.org/wiki/File:Makola_Kayeyei.jpg](https://commons.wikimedia.org/wiki/File:Makola_Kayeyei.jpg)
- **Note:** Kayeyei is the cloth and garment section of Makola, so this is the
  clearest "clothes" image of the set.

## Notes for maintainers

- **Every image is served as a generated derivative, not the original.**
  `tools/build_image_variants.py` writes `<name>-400.jpg` and `<name>-800.jpg`
  next to each original, and `frontend/js/images.js` picks between them with
  `srcset`/`sizes`. The originals stay in the repository as the
  licence-attributed source and are only served when a derivative would not be
  smaller (see below). If you add a photograph, re-run that script; do not
  hand-edit the generated `frontend/js/image-variants.js`.
- The three masquerade files above are **resized copies** (1920px wide) of the
  originals, which are 6000×3376. The Makola files are likewise resized copies
  (1920px wide) of a 6000×4000 original. The crops you see on the tile come from
  CSS (`object-fit: cover` in `.hero-tile-media`), not from editing the file, so
  the stored image is an unmodified work apart from scaling.
- The `-400`/`-800` derivatives are **downscaled and re-encoded** versions of
  those same files, for delivery at the size the browser actually paints. They
  are the same photographs, uncropped and unretouched, and the credit above
  applies to them unchanged.
- CC BY-SA 4.0 asks that adaptations carry the same licence. Displaying these
  resized-but-otherwise-unaltered images on a page does not create a derivative
  of the site's own code, so nothing in this repository needs relicensing. If you
  ever crop, retouch or composite one of these images, keep the credit and note
  the edit here.
- **Do not add images scraped from news sites.** Photographs published by GBC,
  Daily Dispatch, GhanaWeb and similar outlets are copyrighted and all rights
  reserved, even when they show a public festival. Use Wikimedia Commons or your
  own photography instead, or get written permission from the photographer.
