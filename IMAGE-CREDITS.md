# Image credits

Photographs on this site come from three places: the project's own photo
library, images supplied by us, and images reused under an open licence. Every
reused image is listed below with its author, licence and source link, as that
licence requires.

## Open-licence images

### Destination card photos replaced in the low-resolution sweep

Fourteen destination cards were being painted from source files between 105 and
333 pixels wide, against slots that need 291–356 CSS px (712 on a 2x phone).
Twelve have been replaced with properly-licensed photographs of the actual
subject. All twelve were chosen by measurement, not by eye: each was shortlisted
from Wikimedia Commons, scored after resampling to the card size, and the frame
with detail present in *both* halves won, because a photo that is sharp only in a
big sky reads as a flat bright band at 180px tall.

| Local file | Subject | Author | Licence |
| --- | --- | --- | --- |
| `akaa-falls.jpg` | Akaa Falls, Eastern Region | [Lauren Gardenbelle Fritts](https://commons.wikimedia.org/wiki/File:Roots_at_Akaa_Falls_Ghana.jpg) | [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0) |
| `bia-national-park.jpg` | Bia National Park, Western Region | [AmarAfshin](https://commons.wikimedia.org/wiki/File:Bia_National_Park.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) |
| `bolgatanga-basketry-village.jpg` | Bolga basket weaving, Bolgatanga | [Dnshitobu](https://commons.wikimedia.org/wiki/File:Weaving_buskets_at_the_Bolga_market.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) |
| `daboya-fugu-weaving-village.jpg` | Fugu smock cloth being woven, Northern Region | [daSupremo](https://commons.wikimedia.org/wiki/File:Smock_(fugu)_making_02.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) |
| `fort-batenstein.jpg` | Fort Batenstein, Butre | [Kwameghana](https://commons.wikimedia.org/wiki/File:Fort_Batenstein.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) |
| `fort-dorothea.jpg` | Ruins of Fort Dorotheenschanze, Akwidaa | [Stig Nygaard](https://commons.wikimedia.org/wiki/File:Akwida_Ruins_Dorotheenschanze_B02_B003.jpg) | [CC BY 2.0](https://creativecommons.org/licenses/by/2.0) |
| `fort-mccarthy.jpg` | Fort McCarthy, Pra River area | [Kodex](https://commons.wikimedia.org/wiki/File:Fort_McCarthy.jpg) | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0) |
| `gambaga-chief-palace.jpg` | Talking drum at the Gambaga chief's palace | [Wumbeidoo](https://commons.wikimedia.org/wiki/File:Talking_drum_at_Gambaga_chief_palace.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) |
| `labadi-beach.jpg` | Labadi Beach, Accra | [Ghassan Mroue](https://commons.wikimedia.org/wiki/File:Labadi_Beach_-_Accra_-_panoramio.jpg) | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0) |
| `prempeh-ii-jubilee-museum.jpg` | Entrance gates to Manhyia Palace, Kumasi | [Tryongliph](https://commons.wikimedia.org/wiki/File:The_Manhyia_Gates.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) |
| `tetteh-quarshie-cocoa-farm.jpg` | Tetteh Quarshie cocoa farm, Mampong | [Obruni](https://commons.wikimedia.org/wiki/File:Tetteh_Quarshie_Cocao_Farm_-_One_of_the_original_trees,_planted_1879.JPG) | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0) |
| `w.e.b-du-bois-memorial.jpg` | W. E. B. Du Bois with the Nkrumahs, Accra, 1963 | Special Collections, University of Massachusetts Amherst | Public domain |

Every local file above is in `assets/images/attractions/`. Each was taken from
the Commons 1920px downscale of the original (the repository's standard master
width), re-encoded at quality 82. Nothing was upscaled, and no frame was cropped
— the cards crop in CSS via `object-fit: cover`, as with the rest of the set.

Three of the twelve were white balanced, because their colour cast is in the
light rather than in the subject: `bia-national-park` (0.228 → 0.003),
`fort-batenstein` (0.127 → 0.000) and `labadi-beach` (0.244 → 0.002), each with
the per-channel gain measured from the frame itself. The other nine were left
alone. Several have a high overall cast that is *not* a fault — green canopy at
`tetteh-quarshie-cocoa-farm` (0.300) and at `prempeh-ii-jubilee-museum` (0.184),
and brightly dyed baskets at `bolgatanga-basketry-village` (0.319) — and their
highlights measure neutral, which is the signature of scene content rather than
a cast. Grey-world correction would have turned those greens cyan.

Three of the twelve show the destination's setting or its craft rather than the
named building, because no photograph of the exact subject is licensed on
Commons. These were chosen deliberately over a wrong-but-sharper photo:

- **`prempeh-ii-jubilee-museum.jpg`** shows the entrance gates to **Manhyia
  Palace**. The Prempeh II Jubilee Museum stands inside the Manhyia Palace
  complex in Kumasi, so the gates are its actual approach, but the museum
  building itself is not photographed under a free licence.
- **`daboya-fugu-weaving-village.jpg`** shows **fugu smock cloth being woven in
  Tamale**, not in Daboya. It is the same craft, by the same kind of weaver, in
  the same region. `Category:Fugu` on Commons contains no photographs at all.
- **`tetteh-quarshie-cocoa-farm.jpg`** is one of the original trees planted in
  1879 at the Tetteh Quarshie farm, so it is the exact site — note the filename
  spells the crop "Cocao", which is the uploader's typo and is not corrected
  here so the link resolves.

Two subjects in the sweep had no accurate photograph available on Commons, so
their low-resolution files were left in place rather than substituted with a
photo of somewhere else:

- **`kukuo-pottery-centre.jpg`** (330×186) — Commons has Ghanaian pottery, but
  nothing identifiable as Kukuo. Substituting generic pottery would mislabel it.
- **`sefwi-wiawso-palace.jpg`** (275×183) — no photograph of the Sefwi Wiawso
  paramount chief's palace exists on Commons. The searches returned a road near
  Wiawso and the palace of a different chief.

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

### The Slave Scene

- **File used on:** Diaspora Tours tile (`index.html`)
- **Local copy:** `assets/images/slave_scene_captives.jpg`
- **Authors:** Nji Gbetkom Salifou (sculptor), Chief Mongbet Vessah Ibrahim,
  Bruno Kemayou and David W. Reed PhD
- **Licence:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0)
- **Source:** [commons.wikimedia.org/wiki/File:The_Slave_Scene_by_Nji_Gbetkom_Salifou_(Tikar_Bamum).jpg](https://commons.wikimedia.org/wiki/File:The_Slave_Scene_by_Nji_Gbetkom_Salifou_(Tikar_Bamum).jpg)
- **Subject:** Six bronze statues, cast c. 1946-1950, showing four Tikar captives
  driven in chains down to a coastal port by a colonial guard and a royal guard
  in the pay of the slave merchants. The captives are nude and shoeless, wearing
  wooden beads at neck, waist and ankle that mark their shared village. The
  woman wears chains earned by resisting; the two chained men were to be
  manacled below deck; the elderly man is travelling unbound. Sculpted by
  Nji Gbetkom Salifou, a Bamoun artist of Cameroon's Grasslands.
- **Note on the subject:** the captives are Tikar, from what is now northern
  Cameroon, not Ghana. The tile caption and alt text say so. Do not describe
  them as Ghanaians.
- **Edits made** (CC BY-SA 4.0 asks that changes be indicated):
  1. cropped to 16:10 — the statue group already spans the full width, so this
     trimmed 6px of height and nothing of substance;
  2. white balance — the raw frame is lit by tungsten and was heavily orange
     (mean channel gain applied: R x0.735, G x0.991, B x1.586);
  3. saturation reduced to 0.70, because correcting the cast left it too warm
     next to the naturally-lit tiles;
  4. shadows lifted (x0.90 + 16) so the black backdrop reads as space rather
     than a dead hole;
  5. downscaled from 2500x1568 to 1920x1204.
  The figures themselves were not retouched, moved or removed. If you ever
  change these numbers, the measured effect is in `tools/`-adjacent notes in the
  commit message — re-derive them rather than guessing.

### 18th-Century Slave Shackles from Tamale *(alternate, not currently displayed)*

- **Local copy:** `assets/images/slave_shackles_tamale.jpg`
- **Author:** Adam Jones (Flickr)
- **Licence:** [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0)
- **Source:** [commons.wikimedia.org/wiki/File:18th-Century_Slave_Shackles_from_Tamale,_Northern_Ghana_-_International_Slavery_Museum_-_Liverpool,_England_(28144996426).jpg](https://commons.wikimedia.org/wiki/File:18th-Century_Slave_Shackles_from_Tamale,_Northern_Ghana_-_International_Slavery_Museum_-_Liverpool,_England_(28144996426).jpg)
- **Original:** <https://www.flickr.com/photos/adam_jones/28144996426/>
- **Subject:** Eighteenth-century iron slave shackles made in Tamale, Northern
  Region, Ghana, photographed on display at the International Slavery Museum
  in Liverpool. The shackles are Ghana-made, which is why they are the fallback
  for the tile rather than a generic European artefact.
- **Edit made:** downscaled from 3648x2736 to 1920x1440 and re-encoded. Nothing
  else.
- **To restore:** point the tile `img` in `index.html` back at
  `assets/images/slave_shackles_tamale-400.jpg` / `-800.jpg`, put Adam Jones
  back in the footer credit, and drop the "not currently displayed" note above.
  The derivatives are already generated and in the repository.

### MAKOLA

- **File used on:** Food & Market Tours tile (`index.html`)
- **Local copy:** `assets/images/market_makola.jpg`
- **Author:** Amuzujoe
- **Licence:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0)
- **Source:** [commons.wikimedia.org/wiki/File:MAKOLA.jpg](https://commons.wikimedia.org/wiki/File:MAKOLA.jpg)
- **Subject:** Makola Market, Accra — the largest market in Ghana, trading
  food, cloth and everyday goods.

### Lake Bosomtwe 100

- **File used on:** Lake Bosomtwe Crater Lake destination card
  (`backend/data/destinations.json`, id `lake-bosomtwe`)
- **Local copy:** `assets/images/attractions/lake-bosomtwe.jpg`
- **Author:** Amuzujoe
- **Licence:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0)
- **Source:** [commons.wikimedia.org/wiki/File:Lake_Bosomtwe_100.jpg](https://commons.wikimedia.org/wiki/File:Lake_Bosomtwe_100.jpg)
- **Subject:** Lake Bosomtwe, the natural crater lake in the Ashanti Region, near
  Kumasi. Photographed 12 February 2023.
- **Why this file replaced the previous one:** the file at this path used to be
  105×1024 pixels, so the 291×180 destination card was being painted from a
  105px-wide sliver — a 2.8× upscale at 1x and 6.8× at 2x. That is why the card
  read as blurry. Nothing was wrong with the card CSS; the pixels were not there.
- **Edits made:**
  1. downscaled from 4847×3226 to 1920×1278 (Lanczos, downscale only);
  2. white balanced — the original is shot through a heavy cyan cast (channel
     means R 133 / G 181 / B 186). Applied after the downscale so the resampler
     averages the chroma noise before it is multiplied. Measured gain on the
     1920px result was R ×1.131, G ×0.9526, B ×0.938, which brought the cast
     from 0.319 to 0.004. No saturation reduction was needed afterwards.
  The frame was **not** cropped. The card crops in CSS via `object-fit: cover`,
  as with every other image in the set.

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
