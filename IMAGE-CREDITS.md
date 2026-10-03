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

### Slave trade photograph

- **File used on:** Diaspora Tours tile (`index.html`)
- **Local copy:** `assets/images/slavetrade.jpeg` (678x452, 26 KB) with the
  generated `slavetrade-400.jpg`
- **Authors:** unknown
- **Licence:** unknown
- **Source:** supplied directly for this project by the site owner
- **Subject:** unknown. The file arrived with no accompanying description and the
  frame has not been visually verified, so the alt text (`Slave trade history`)
  names the tile's subject rather than claiming to describe the photograph.
- **Status — verify before launch:** the provenance and licence above are
  placeholders, not findings. This is the one image on the site whose right to
  display has not been established. The previous tile image was a Wikimedia
  bronze, `The Slave Scene` by Nji Gbetkom Salifou (CC BY-SA 4.0), which was
  removed because the captives it depicts are Tikar from what is now northern
  Cameroon rather than Ghanaian. Confirm what this photograph shows, who made it
  and under what licence, then replace this section.

### 18th-Century Slave Shackles from Tamale *(alternate, not currently displayed)*

- **Local copy:** `assets/images/slave_shackles_tamale.jpg`
- **Author:** Adam Jones (Flickr)
- **Licence:** [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0)
- **Source:** [commons.wikimedia.org/wiki/File:18th-Century_Slave_Shackles_from_Tamale,_Northern_Ghana_-_International_Slavery_Museum_-_Liverpool,_England_(28144996426).jpg](https://commons.wikimedia.org/wiki/File:18th-Century_Slave_Shackles_from_Tamale,_Northern_Ghana_-_International_Slavery_Museum_-_Liverpool,_England_(28144996426).jpg)
- **Original:** <https://www.flickr.com/photos/adam_jones/28144996426/>
- **Subject:** Eighteenth-century iron slave shackles made in Tamale, Northern
  Region, Ghana, photographed on display at the International Slavery Museum
  in Liverpool. The shackles are Ghana-made, which is why it was the first
  fallback for the tile rather than a generic European artefact.
- **Edit made:** downscaled from 3648x2736 to 1920x1440 and re-encoded. Nothing
  else.
- **To restore:** point the tile `img` in `index.html` back at
  `assets/images/slave_shackles_tamale-400.jpg` / `-800.jpg`, put Adam Jones
  back in the footer credit, and drop the "not currently displayed" note above.
  The derivatives are already generated and in the repository.

### Kejetia Market — destination front image

- **File used on:** Kejetia Market card and modal hero (`index.html`)
- **Local copy:** `assets/images/attractions/kejetia-market.jpg`
- **Author:** [Afus199620](https://commons.wikimedia.org/wiki/User:Afus199620)
- **Licence:** [CC0](https://creativecommons.org/publicdomain/zero/1.0/) (public domain
  dedication — no attribution legally required; credited here because this file is
  the project's record of where every image came from)
- **Source:** [commons.wikimedia.org/wiki/File:Modern_market_hall_of_Kejetia_market.jpg](https://commons.wikimedia.org/wiki/File:Modern_market_hall_of_Kejetia_market.jpg)
- **Subject:** the modern market hall at Kejetia Market, Kumasi. The file's own title
  is the whole of what is claimed about it here.
- **Why this file replaced the previous one:** the previous image was 683×1024 —
  **portrait**, in a slot that is 268×180 **landscape** (aspect 1.49) rendered with
  `object-fit: cover`. Only the middle ~45% of its height was ever visible; the top
  and bottom were cropped away on every visitor's screen. At 683px wide it was also
  below the 335px the slot needs at 1.25× device pixel ratio, so it was upscaled
  as well as cropped. Both defects were measurable without looking at the picture.
- **How it was chosen:** four properly-licensed Commons candidates were downloaded
  at the 1920px master width and shown to the site owner cropped to the exact slot
  with the site's own `object-fit`, so the comparison showed what would ship. The
  owner chose this one. The other three became the additional photographs in the
  destination's gallery, credited in the table below. All four are CC BY-SA 2.0 or
  CC0; none was scraped from anywhere but Commons.
- **Edits made:** downscaled from 4032×3024 to 1920×1440 (Lanczos, downscale only,
  no crop, no colour change), then the `-400` and `-800` derivatives were generated
  from that master.
- **Not verified:** that the hall looks like this when a visitor stands there, and
  whether it is the most attractive photograph of the market. The pipeline cannot
  judge either; the owner chose from a comparison of four.

### A traditional market woman

- **File used on:** Food & Market Tours tile (`index.html`)
- **Local copy:** `assets/images/market_makola_foodstuffs.jpg`
- **Author:** [JustSwanzy](https://commons.wikimedia.org/wiki/User:JustSwanzy)
- **Licence:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0)
- **Source:** [commons.wikimedia.org/wiki/File:A_traditional_market_woman.jpg](https://commons.wikimedia.org/wiki/File:A_traditional_market_woman.jpg)
- **Subject:** A market woman at Makola Market, Accra, with her goods laid out
  for sale. The uploader's description: *"A market woman displaying her food
  stuffs on sale which includes fish, plantain, palm oil, cocoyam leaf and
  mushrooms."* The tile is meant to show what you actually see for sale when you
  walk into a Ghanaian market, so the merchandise is the subject.
- **Why this file replaced the previous one:** the tile previously used `MAKOLA`
  (below), a correct photograph of Makola Market that reads as an empty scene
  rather than a market full of goods. Measured at the tile size it scored 22nd of
  24 candidates: edge detail 677 in the top half against 2422 in the bottom
  (balance 0.28), so the upper half of the tile was a flat bright band. Twenty-two
  properly-licensed Ghanaian market photographs were shortlisted and measured at
  16:10 before this one was chosen. An earlier revision of this tile used a
  portrait of a woman in kente regalia, which was rejected: it showed no goods.
- **Edits made:**
  1. downscaled from 4032×3024 to 1920×1440 (Lanczos, downscale only);
  2. white balanced — the frame is shot under warm indoor market light and the
     cast is in the highlights, not just the subject, so it is a real fault
     rather than scene content. Measured gain on the 1920px result was
     R ×0.925, G ×0.959, B ×1.140, which brought the cast from 0.204 to 0.006.
     No saturation reduction was needed afterwards.
  The frame was **not** cropped. The tile crops in CSS via `object-fit: cover`.

### MAKOLA *(alternate, not currently displayed)*

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

<!-- gallery-credits:start -->

### Destination and festival gallery photographs

These are the extra photographs shown in each destination's or festival's
*View Details* window. Every one is reproduced unmodified from the Commons
1920px downscale of the original, which is the repository's standard
master width; the `-400` and `-800` files served to browsers are
downscales of that same master, and the credit applies to them unchanged.

| Place | Local file | Author | Licence | Source |
| --- | --- | --- | --- | --- |
| Aboakyer Festival (Deer Hunting Festival) | `aboakyer-festival-2.jpg` | [Fquasie](https://commons.wikimedia.org/wiki/File:Aboakyer_hunters.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Aboakyer_hunters.jpg) |
| Aboakyer Festival (Deer Hunting Festival) | `aboakyer-festival-3.jpg` | [Fquasie](https://commons.wikimedia.org/wiki/File:Aboakyer_festival_in_Winneba.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Aboakyer_festival_in_Winneba.jpg) |
| Aboakyer Festival (Deer Hunting Festival) | `aboakyer-festival.jpg` | [Fquasie](https://commons.wikimedia.org/wiki/File:Aboakyer_festival_10.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Aboakyer_festival_10.jpg) |
| Accra International Conference Centre | `accra-international-conference-centre-2.jpg` | [Fkoku](https://commons.wikimedia.org/wiki/File:Accra_International_Conference_Center_fore_court.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Accra_International_Conference_Center_fore_court.jpg) |
| Accra International Conference Centre | `accra-international-conference-centre.jpg` | [Michael Sean Gallagher](https://commons.wikimedia.org/wiki/File:Conference_Hall_in_Accra_International_Conference_Centre,_Accra,_Ghana.jpg) | CC BY-SA 2.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Conference_Hall_in_Accra_International_Conference_Centre,_Accra,_Ghana.jpg) |
| Ada Foah Beach | `ada-foah-beach-beach-boats.jpg` | [Philip Nalangan](https://commons.wikimedia.org/wiki/File:Ada_Foah_Beach_2.jpg) | CC BY 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Ada_Foah_Beach_2.jpg) |
| Ada Foah Beach | `ada-foah-beach-boats-fishing.jpg` | [Peter Fitzgerald](https://commons.wikimedia.org/wiki/File:Ada_fishing_boats_on_the_Volta.JPG) | CC BY 3.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Ada_fishing_boats_on_the_Volta.JPG) |
| Adomi Bridge | `adomi-bridge-boats-bridge.jpg` | [mariamayunusah](https://commons.wikimedia.org/wiki/File:Adomi_II.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Adomi_II.jpg) |
| Adomi Bridge | `adomi-bridge-bridge-2.jpg` | [Matti Blume](https://commons.wikimedia.org/wiki/File:Adomi_Bridge,_Asuogyaman_(20230204-P1090970).jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Adomi_Bridge,_Asuogyaman_(20230204-P1090970).jpg) |
| Adomi Bridge | `adomi-bridge-bridge-3.jpg` | [Matti Blume](https://commons.wikimedia.org/wiki/File:Adomi_Bridge,_Atimpoku_(P1100005).jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Adomi_Bridge,_Atimpoku_(P1100005).jpg) |
| Adomi Bridge | `adomi-bridge-bridge.jpg` | [Df181](https://commons.wikimedia.org/wiki/File:Frimpongs_Adomi_Bridge.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Frimpongs_Adomi_Bridge.jpg) |
| Akosombo Dam | `akosombo-dam-river.jpg` | [ZSM](https://commons.wikimedia.org/wiki/File:Akosombo_Dam_is_spilling_water,_Ghana.JPG) | CC BY-SA 3.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Akosombo_Dam_is_spilling_water,_Ghana.JPG) |
| Akosombo Dam | `akosombo-dam-view.jpg` | [Matti Blume](https://commons.wikimedia.org/wiki/File:Akosombo_Dam,_Akosombo_(P1100018-Pano).jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Akosombo_Dam,_Akosombo_(P1100018-Pano).jpg) |
| Akosombo Dam | `akosombo-dam.jpg` | [jbdodane](https://commons.wikimedia.org/wiki/File:Akosombo_Dam,_Akosombo.jpg) | CC BY 2.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Akosombo_Dam,_Akosombo.jpg) |
| Amedzofe Mountains | `amedzofe-mountains-aerial-view.jpg` | [Williams Penuku](https://commons.wikimedia.org/wiki/File:Amedzofe_Volta_Region_Ghana.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Amedzofe_Volta_Region_Ghana.jpg) |
| Amedzofe Mountains | `amedzofe-mountains-aerial-village.jpg` | [Williams Penuku](https://commons.wikimedia.org/wiki/File:Amedzofe_village_Ghana.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Amedzofe_village_Ghana.jpg) |
| Amedzofe Mountains | `amedzofe-mountains-trees.jpg` | [Kobby.ak](https://commons.wikimedia.org/wiki/File:Amedzofe_scenery_-.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Amedzofe_scenery_-.jpg) |
| Bakatue Festival | `bakatue-festival-2.jpg` | [Robertjamal12](https://commons.wikimedia.org/wiki/File:Bakatue_Festival_28.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Bakatue_Festival_28.jpg) |
| Bakatue Festival | `bakatue-festival-boat-boats.jpg` | [official photographer of the US Embassy in Ghana/USAID in Ghana](https://commons.wikimedia.org/wiki/File:Bakatue_2016_001_B001.jpg) | Public domain | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Bakatue_2016_001_B001.jpg) |
| Bakatue Festival | `bakatue-festival-boats-fishing.jpg` | [official photographer of the US Embassy in Ghana / USAID in Ghana](https://commons.wikimedia.org/wiki/File:Elmina_Bakatue_2016_002_B002.jpg) | Public domain | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Elmina_Bakatue_2016_002_B002.jpg) |
| Bakatue Festival | `bakatue-festival.jpg` | [Imagez2010](https://commons.wikimedia.org/wiki/File:Bakatue_Festival_celebrated_By_the_people_of_Elmina_in_Ghana.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Bakatue_Festival_celebrated_By_the_people_of_Elmina_in_Ghana.jpg) |
| Bia National Park | `bia-national-park-entrance-forest.jpg` | [Akiwumi](https://commons.wikimedia.org/wiki/File:Entrance_to_Bia_Forest_reserve.jpg) | CC BY-SA 3.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Entrance_to_Bia_Forest_reserve.jpg) |
| Bia National Park | `bia-national-park.jpg` | [AmarAfshin](https://commons.wikimedia.org/wiki/File:Bia_National_Park.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Bia_National_Park.jpg) |
| Black Star Square & Independence Arch | `black-star-square-01.jpg` | [Celestinesucess](https://commons.wikimedia.org/wiki/File:Black_Star_Square_01.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Black_Star_Square_01.jpg) |
| Black Star Square & Independence Arch | `black-star-square-ghana-54th-pic005-b002.jpg` | [Ben Sutherland (on Flickr)](https://commons.wikimedia.org/wiki/File:Ghana_54th_Pic005_B002.jpg) | CC BY 2.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Ghana_54th_Pic005_B002.jpg) |
| Black Star Square & Independence Arch | `black-star-square-ii-1.jpg` | [[[[[[Kwaku Berko](https://commons.wikimedia.org/wiki/File:Black_star_square_(ii-(1).jpg)]([Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Black_star_square_(ii-(1).jpg))]([Wikimedia Commons]([Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Black_star_square_(ii-(1).jpg)))]([Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Black_star_square_(ii-(1).jpg))))]([Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Black_star_square_(ii-(1).jpg)))))]([Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Black_star_square_(ii-(1).jpg)))))) | CC BY-SA 4.0 | [Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Black_star_square_(ii-(1).jpg)))))) |
| Black Star Square & Independence Arch | `black-star-square-ii-3.jpg` | [[[[[[Kwaku Berko](https://commons.wikimedia.org/wiki/File:Black_star_square_(ii-(3).jpg)]([Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Black_star_square_(ii-(3).jpg))]([Wikimedia Commons]([Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Black_star_square_(ii-(3).jpg)))]([Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Black_star_square_(ii-(3).jpg))))]([Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Black_star_square_(ii-(3).jpg)))))]([Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Black_star_square_(ii-(3).jpg)))))) | CC BY-SA 4.0 | [Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons]([Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Black_star_square_(ii-(3).jpg)))))) |
| Black Volta River | `black-volta-river-river-2.jpg` | [Knowledge and philosophy](https://commons.wikimedia.org/wiki/File:Black_volta_passing_at_Bamboi.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Black_volta_passing_at_Bamboi.jpg) |
| Black Volta River | `black-volta-river-river.jpg` | [Andreas Aryeh](https://commons.wikimedia.org/wiki/File:The_beautiful_black_Volta_(Ghana).jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:The_beautiful_black_Volta_(Ghana).jpg) |
| Boabeng-Fiema Monkey Sanctuary | `boabeng-fiema-monkey-sanctuary-2.jpg` | [Malibu xoxo](https://commons.wikimedia.org/wiki/File:Boabeng_Fiema_monkey_sanctuary_2.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Boabeng_Fiema_monkey_sanctuary_2.jpg) |
| Boabeng-Fiema Monkey Sanctuary | `boabeng-fiema-monkey-sanctuary-3.jpg` | [Malibu xoxo](https://commons.wikimedia.org/wiki/File:Boabeng_Fiema_monkey_sanctuary_3.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Boabeng_Fiema_monkey_sanctuary_3.jpg) |
| Boabeng-Fiema Monkey Sanctuary | `boabeng-fiema-monkey-sanctuary-4.jpg` | [Malibu xoxo](https://commons.wikimedia.org/wiki/File:Boabeng_Fiema_monkey_sanctuary_4.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Boabeng_Fiema_monkey_sanctuary_4.jpg) |
| Boabeng-Fiema Monkey Sanctuary | `boabeng-fiema-monkey-sanctuary-koczkodan-liberyjski.jpg` | [Nero2022](https://commons.wikimedia.org/wiki/File:Koczkodan_liberyjski.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Koczkodan_liberyjski.jpg) |
| Boabeng-Fiema Monkey Sanctuary | `boabeng-fiema-monkey-sanctuary-małpi-cmentarz-w-fiema-boabeng-monkey-sanctuary.jpg` | [Nero2022](https://commons.wikimedia.org/wiki/File:Ma%C5%82pi_cmentarz_w_Fiema-Boabeng_Monkey_Sanctuary.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Ma%C5%82pi_cmentarz_w_Fiema-Boabeng_Monkey_Sanctuary.jpg) |
| Bolgatanga Basket Weaving Village | `bolgatanga-basketry-village-a-young-ghanaian-basketry-craftman.jpg` | [Tahiru Rajab](https://commons.wikimedia.org/wiki/File:A_Young_Ghanaian_Basketry_Craftman.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:A_Young_Ghanaian_Basketry_Craftman.jpg) |
| Bolgatanga Basket Weaving Village | `bolgatanga-basketry-village-basket-weavers-banner.jpg` | [Vrinda Khushu](https://commons.wikimedia.org/wiki/File:Basket_Weavers_(banner).jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Basket_Weavers_(banner).jpg) |
| Bolgatanga Basket Weaving Village | `bolgatanga-basketry-village-basket-weavers.jpg` | [Vrinda Khushu](https://commons.wikimedia.org/wiki/File:Basket_Weavers.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Basket_Weavers.jpg) |
| Bolgatanga Basket Weaving Village | `bolgatanga-basketry-village-bɔliga-piɛ-wuɣira.jpg` | [Alhassan Peter](https://commons.wikimedia.org/wiki/File:B%C9%94liga_pi%C9%9B%27_wu%C9%A3ira.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:B%C9%94liga_pi%C9%9B%27_wu%C9%A3ira.jpg) |
| Bonwire Kente Weaving Village | `bonwire-kente-village-kente-72.jpg` | [Amuzujoe](https://commons.wikimedia.org/wiki/File:Kente_72.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kente_72.jpg) |
| Bonwire Kente Weaving Village | `bonwire-kente-village-kente-75.jpg` | [Amuzujoe](https://commons.wikimedia.org/wiki/File:Kente_75.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kente_75.jpg) |
| Bonwire Kente Weaving Village | `bonwire-kente-village-kente-80.jpg` | [Amuzujoe](https://commons.wikimedia.org/wiki/File:Kente_80.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kente_80.jpg) |
| Bonwire Kente Weaving Village | `bonwire-kente-village-kente-81.jpg` | [Amuzujoe](https://commons.wikimedia.org/wiki/File:Kente_81.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kente_81.jpg) |
| Bonwire Kente Weaving Village | `bonwire-kente-village-kente-84.jpg` | [Amuzujoe](https://commons.wikimedia.org/wiki/File:Kente_84.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kente_84.jpg) |
| Bonwire Kente Weaving Village | `bonwire-kente-village-kente-85.jpg` | [Amuzujoe](https://commons.wikimedia.org/wiki/File:Kente_85.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kente_85.jpg) |
| Boti Waterfalls & Umbrella Rock | `boti-waterfalls-boti-canopy-umbrella-rock.jpg` | [Penwills](https://commons.wikimedia.org/wiki/File:Boti_canopy_umbrella_rock.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Boti_canopy_umbrella_rock.jpg) |
| Boti Waterfalls & Umbrella Rock | `boti-waterfalls-boti-umbrella-rock-serving-as-shade-for-natives.jpg` | [Penwills](https://commons.wikimedia.org/wiki/File:Boti_umbrella_rock_serving_as_shade_for_natives.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Boti_umbrella_rock_serving_as_shade_for_natives.jpg) |
| Boti Waterfalls & Umbrella Rock | `boti-waterfalls-boti-umbrella-rock.jpg` | [Penwills](https://commons.wikimedia.org/wiki/File:Boti_Umbrella_rock.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Boti_Umbrella_rock.jpg) |
| Boti Waterfalls & Umbrella Rock | `boti-waterfalls-residents-of-boti-waterfalls-resting-under-the-umbrella-rock.jpg` | [Penwills](https://commons.wikimedia.org/wiki/File:Residents_of_Boti_waterfalls_resting_under_the_umbrella_rock.2.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Residents_of_Boti_waterfalls_resting_under_the_umbrella_rock.2.jpg) |
| Busua Beach | `busua-beach-beach-2.jpg` | [Mac-Jordan Degadjor](https://commons.wikimedia.org/wiki/File:Busua_Beach_Resort_setting_in_Western_region,_Ghana.jpg) | CC BY 2.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Busua_Beach_Resort_setting_in_Western_region,_Ghana.jpg) |
| Busua Beach | `busua-beach-beach-3.jpg` | [Mac Jordan](https://commons.wikimedia.org/wiki/File:Busua_-_Seashore,_Western_region,_Ghana.jpg) | CC BY 2.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Busua_-_Seashore,_Western_region,_Ghana.jpg) |
| Busua Beach | `busua-beach-beach.jpg` | [Tom Lubbe](https://commons.wikimedia.org/wiki/File:Busua_Beach_on_rainy_day_01.jpg) | CC BY-SA 3.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Busua_Beach_on_rainy_day_01.jpg) |
| Cape Coast Castle | `cape-coast-castle-09-05-2025.jpg` | [Jenef Offei Emmanuel](https://commons.wikimedia.org/wiki/File:Cape_Coast_Castle_09_05_2025.jpg) | CC BY 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Cape_Coast_Castle_09_05_2025.jpg) |
| Cape Coast Castle | `cape-coast-castle-34.jpg` | [Antorsu10](https://commons.wikimedia.org/wiki/File:Cape_Coast_Castle_34.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Cape_Coast_Castle_34.jpg) |
| Cape Coast Castle | `cape-coast-castle-35.jpg` | [Antorsu10](https://commons.wikimedia.org/wiki/File:Cape_Coast_Castle_35.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Cape_Coast_Castle_35.jpg) |
| Cape Coast Castle | `cape-coast-castle-cape-coast-ghana-castle-2.jpg` | [Philip Nalangan](https://commons.wikimedia.org/wiki/File:Cape_Coast_Ghana_Castle_2.jpg) | CC BY 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Cape_Coast_Ghana_Castle_2.jpg) |
| Cape Coast Castle | `cape-coast-castle-cape-coast-ghana-castle-3.jpg` | [Philip Nalangan](https://commons.wikimedia.org/wiki/File:Cape_Coast_Ghana_Castle_3.jpg) | CC BY 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Cape_Coast_Ghana_Castle_3.jpg) |
| Cape Coast Castle | `cape-coast-castle-coast-2.jpg` | [Antorsu10](https://commons.wikimedia.org/wiki/File:Cape_Coast_Castle_28.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Cape_Coast_Castle_28.jpg) |
| Cape Coast Castle | `cape-coast-castle-the-inner-court-of-cape-coast-castle.jpg` | [Kwameghana(Bright Kwame Ayisi)](https://commons.wikimedia.org/wiki/File:The_inner_court_of_Cape_Coast_Castle.jpg) | CC0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:The_inner_court_of_Cape_Coast_Castle.jpg) |
| Centre for National Culture | `centre-for-national-culture-3.jpg` | [Nate N.](https://commons.wikimedia.org/wiki/File:Centre_for_National_Culture,_Fijai_-_panoramio.jpg) | CC BY-SA 3.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Centre_for_National_Culture,_Fijai_-_panoramio.jpg) |
| Centre for National Culture | `centre-for-national-culture.jpg` | [Jude Hammond](https://commons.wikimedia.org/wiki/File:Centre_for_National_Culture_at_Kumasi,_Ghana.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Centre_for_National_Culture_at_Kumasi,_Ghana.jpg) |
| Damba Festival | `damba-festival-2.jpg` | [Alliance abio](https://commons.wikimedia.org/wiki/File:Image_from_damba_festival_celebration_2.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Image_from_damba_festival_celebration_2.jpg) |
| Damba Festival | `damba-festival-3.jpg` | [Abdulfatawu12](https://commons.wikimedia.org/wiki/File:Image_From_2021_Damba_festival_celebration_2.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Image_From_2021_Damba_festival_celebration_2.jpg) |
| Damba Festival | `damba-festival-drumming.jpg` | [Celestinesucess](https://commons.wikimedia.org/wiki/File:Damba_Festival_05.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Damba_Festival_05.jpg) |
| Damba Festival | `damba-festival.jpg` | [Celestinesucess](https://commons.wikimedia.org/wiki/File:2016_Damba_Festival_02.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:2016_Damba_Festival_02.jpg) |
| Dipo (Puberty Rites) Festival | `dipo-festival-2.jpg` | [FatawuY1](https://commons.wikimedia.org/wiki/File:Dipo_Rites_Ornaments_02.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Dipo_Rites_Ornaments_02.jpg) |
| Dipo (Puberty Rites) Festival | `dipo-festival-3.jpg` | [SaeedLescott1](https://commons.wikimedia.org/wiki/File:Dipo_Rites_26.jpg) | CC BY 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Dipo_Rites_26.jpg) |
| Dipo (Puberty Rites) Festival | `dipo-festival-procession.jpg` | [FatawuY1](https://commons.wikimedia.org/wiki/File:Dipo_Rights_Procession_1.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Dipo_Rights_Procession_1.jpg) |
| Dipo (Puberty Rites) Festival | `dipo-festival.jpg` | [Sunkanmi12](https://commons.wikimedia.org/wiki/File:Dipo_Festival.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Dipo_Festival.jpg) |
| Elmina Castle (St. George's Castle) | `elmina-castle-11.jpg` | [Esthee2010](https://commons.wikimedia.org/wiki/File:Elmina_Castle_11.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Elmina_Castle_11.jpg) |
| Elmina Castle (St. George's Castle) | `elmina-castle-12.jpg` | [Esthee2010](https://commons.wikimedia.org/wiki/File:Elmina_Castle_12.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Elmina_Castle_12.jpg) |
| Elmina Castle (St. George's Castle) | `elmina-castle-13.jpg` | [Esthee2010](https://commons.wikimedia.org/wiki/File:Elmina_Castle_13.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Elmina_Castle_13.jpg) |
| Elmina Castle (St. George's Castle) | `elmina-castle-14.jpg` | [Esthee2010](https://commons.wikimedia.org/wiki/File:Elmina_Castle_14.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Elmina_Castle_14.jpg) |
| Elmina Castle (St. George's Castle) | `elmina-castle-2.jpg` | [Barrowbob](https://commons.wikimedia.org/wiki/File:Elmina_Beach_from_the_castle.jpg) | CC0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Elmina_Beach_from_the_castle.jpg) |
| Elmina Castle (St. George's Castle) | `elmina-castle-elmina.jpg` | [Brans Wyte GH](https://commons.wikimedia.org/wiki/File:Elmina_Castle_-_Elmina.jpg) | CC0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Elmina_Castle_-_Elmina.jpg) |
| Elmina Castle (St. George's Castle) | `elmina-castle-ghana.jpg` | [Damien Halleux Radermecker](https://commons.wikimedia.org/wiki/File:Elmina_Castle_-_Ghana.jpg) | CC BY-SA 2.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Elmina_Castle_-_Ghana.jpg) |
| Elmina Castle (St. George's Castle) | `elmina-castle-inside.jpg` | [Noahalorwu](https://commons.wikimedia.org/wiki/File:Elmina_03.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Elmina_03.jpg) |
| Elmina Castle (St. George's Castle) | `elmina-castle.jpg` | [Francisco Anzola](https://commons.wikimedia.org/wiki/File:Elmina_Castle_Ramparts_(3587901478).jpg) | CC BY 2.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Elmina_Castle_Ramparts_(3587901478).jpg) |
| Fort Apollonia | `fort-apollonia-beach.jpg` | [Coenraad Liebrecht Temminck Groll](https://commons.wikimedia.org/wiki/File:Fort_St._Apollonia,_bouwvakkers_tijdens_restauratie_-_20651736_-_RCE.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Fort_St._Apollonia,_bouwvakkers_tijdens_restauratie_-_20651736_-_RCE.jpg) |
| Fort Batenstein | `fort-batenstein-2.jpg` | [Loek Tangel](https://commons.wikimedia.org/wiki/File:Overzicht_met_ru%C3%AFne_bovenop_heuvel_-_Butre_-_20375423_-_RCE.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Overzicht_met_ru%C3%AFne_bovenop_heuvel_-_Butre_-_20375423_-_RCE.jpg) |
| Fort Batenstein | `fort-batenstein.jpg` | [Kwameghana](https://commons.wikimedia.org/wiki/File:Fort_Batenstein.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Fort_Batenstein.jpg) |
| Fort Good Hope | `fort-good-hope-2.jpg` | [mattcatpurple from Hay River, Canada](https://commons.wikimedia.org/wiki/File:Fort_Good_Hope_(99536196).jpg) | CC BY-SA 2.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Fort_Good_Hope_(99536196).jpg) |
| Fort Good Hope | `fort-good-hope.jpg` | [Treysam](https://commons.wikimedia.org/wiki/File:Fort_Good_Hope_in_Ghana.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Fort_Good_Hope_in_Ghana.jpg) |
| Fort Groß Friedrichsburg | `fort-gross-friedrichsburg-2.jpg` | [Obruni](https://commons.wikimedia.org/wiki/File:Gro%C3%9F_Friedrichsburg.JPG) | CC BY 3.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Gro%C3%9F_Friedrichsburg.JPG) |
| Fort Groß Friedrichsburg | `fort-gross-friedrichsburg.jpg` | [Timothy Asare](https://commons.wikimedia.org/wiki/File:Fort_Gro%C3%9F_Friedrichsburg.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Fort_Gro%C3%9F_Friedrichsburg.jpg) |
| Fort Metal Cross | `fort-metal-cross-2.jpg` | [Nicholas McGee](https://commons.wikimedia.org/wiki/File:Fort_Metal_Cross.jpg) | CC BY-SA 3.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Fort_Metal_Cross.jpg) |
| Fort Nassau (Mouri) | `fort-nassau-mouri-2.jpg` | [Coenraad Liebrecht Temminck Groll](https://commons.wikimedia.org/wiki/File:Fort_Nassau,_overzicht_-_20651802_-_RCE.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Fort_Nassau,_overzicht_-_20651802_-_RCE.jpg) |
| Fort Nassau (Mouri) | `fort-nassau-mouri-3.jpg` | [Noahalorwu](https://commons.wikimedia.org/wiki/File:Fort_Nassau_02.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Fort_Nassau_02.jpg) |
| Fort Nassau (Mouri) | `fort-nassau-mouri-4.jpg` | [Coenraad Liebrecht Temminck Groll](https://commons.wikimedia.org/wiki/File:Fort_Nassau,_poort_-_20651798_-_RCE.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Fort_Nassau,_poort_-_20651798_-_RCE.jpg) |
| Fort Nassau (Mouri) | `fort-nassau-mouri.jpg` | [Coenraad Liebrecht Temminck Groll](https://commons.wikimedia.org/wiki/File:Fort_Nassau,_westelijk_bastion_-_20651796_-_RCE.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Fort_Nassau,_westelijk_bastion_-_20651796_-_RCE.jpg) |
| Fort Patience | `fort-patience-walls.jpg` | [Loek Tangel](https://commons.wikimedia.org/wiki/File:Overzicht_achterzijde_vanaf_buitenmuur_-_Apam_-_20375239_-_RCE.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Overzicht_achterzijde_vanaf_buitenmuur_-_Apam_-_20375239_-_RCE.jpg) |
| Fort Patience | `fort-patience.jpg` | [HijabGirl1](https://commons.wikimedia.org/wiki/File:Fort_Patience_(Apam).jpg) | CC0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Fort_Patience_(Apam).jpg) |
| Gbewaa Palace (Daboya) | `gbewaa-palace-at-the-gbewaa-palace.jpg` | [Abdul-Hanan Chambihi](https://commons.wikimedia.org/wiki/File:At_the_Gbewaa_palace.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:At_the_Gbewaa_palace.jpg) |
| Gbewaa Palace (Daboya) | `gbewaa-palace-in-yendi.jpg` | [Shahadusadik](https://commons.wikimedia.org/wiki/File:Gbewaa_palace_in_Yendi.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Gbewaa_palace_in_Yendi.jpg) |
| Gbewaa Palace (Daboya) | `gbewaa-palace-visits-to-gbewaa-palace.jpg` | [Zak Raha](https://commons.wikimedia.org/wiki/File:Visits_to_Gbewaa_palace.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Visits_to_Gbewaa_palace.jpg) |
| Kakum National Park Canopy Walk | `kakum-national-park-a-section-of-kakum.jpg` | [Kojo kissi](https://commons.wikimedia.org/wiki/File:A_section_of_kakum.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:A_section_of_kakum.jpg) |
| Kakum National Park Canopy Walk | `kakum-national-park-canopy-walk.jpg` | [Dieu-Donné Gameli](https://commons.wikimedia.org/wiki/File:Kakum_National_Park_Canopy_Walk.jpg) | CC BY-SA 3.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kakum_National_Park_Canopy_Walk.jpg) |
| Kakum National Park Canopy Walk | `kakum-national-park-canopy-walkway.jpg` | [Kojo kissi](https://commons.wikimedia.org/wiki/File:Canopy_walkway.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Canopy_walkway.jpg) |
| Kakum National Park Canopy Walk | `kakum-national-park-from-the-canopy-walk.jpg` | [Gianluca Floris](https://commons.wikimedia.org/wiki/File:Kakum_National_Park_-_from_the_canopy_walk.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kakum_National_Park_-_from_the_canopy_walk.jpg) |
| Kakum National Park Canopy Walk | `kakum-national-park-kakum-canopy-walk-kakum-national-park-ghana.jpg` | [Benggriff](https://commons.wikimedia.org/wiki/File:Kakum_Canopy_Walk,_Kakum_National_Park,_Ghana.JPG) | CC BY-SA 3.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kakum_Canopy_Walk,_Kakum_National_Park,_Ghana.JPG) |
| Kakum National Park Canopy Walk | `kakum-national-park-kakum-park-canopy-walk.jpg` | [Dangbe23](https://commons.wikimedia.org/wiki/File:Kakum_Park_Canopy_Walk.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kakum_Park_Canopy_Walk.jpg) |
| Kejetia Market | `kejetia-market-kente-kumasi.jpg` | [Adam Jones](https://commons.wikimedia.org/wiki/File:Kente_Kumasi_2010-06-30.jpg) | CC BY-SA 2.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kente_Kumasi_2010-06-30.jpg) |
| Kejetia Market | `kejetia-market-markt.jpg` | [Afus199620](https://commons.wikimedia.org/wiki/File:Kejetia-Markt.jpg) | CC0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kejetia-Markt.jpg) |
| Kejetia Market | `kejetia-market-street-scene.jpg` | [Adam Jones from Kelowna, BC, Canada](https://commons.wikimedia.org/wiki/File:Street_Scene_in_Kejetia_Market_-_Kumasi_-_Ghana_(4755556785).jpg) | CC BY-SA 2.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Street_Scene_in_Kejetia_Market_-_Kumasi_-_Ghana_(4755556785).jpg) |
| Kintampo Waterfalls | `kintampo-waterfalls-2.jpg` | [Malibu xoxo](https://commons.wikimedia.org/wiki/File:Kintampo_Waterfalls_2.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kintampo_Waterfalls_2.jpg) |
| Kintampo Waterfalls | `kintampo-waterfalls-3.jpg` | [Malibu xoxo](https://commons.wikimedia.org/wiki/File:Kintampo_Waterfalls_3.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kintampo_Waterfalls_3.jpg) |
| Kintampo Waterfalls | `kintampo-waterfalls-4.jpg` | [Malibu xoxo](https://commons.wikimedia.org/wiki/File:Kintampo_Waterfalls_4.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kintampo_Waterfalls_4.jpg) |
| Kintampo Waterfalls | `kintampo-waterfalls-5.jpg` | [Malibu xoxo](https://commons.wikimedia.org/wiki/File:Kintampo_Waterfalls_5.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kintampo_Waterfalls_5.jpg) |
| Kintampo Waterfalls | `kintampo-waterfalls-a-landscape-view-of-the-famous-kintampo-waterfall-in-ghana1.jpg` | [Treysam](https://commons.wikimedia.org/wiki/File:A_landscape_view_of_the_famous_Kintampo_waterfall_in_Ghana1.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:A_landscape_view_of_the_famous_Kintampo_waterfall_in_Ghana1.jpg) |
| Kintampo Waterfalls | `kintampo-waterfalls-kintampo-waterfall-level-1.jpg` | [Kwameghana(Bright Kwame Ayisi)](https://commons.wikimedia.org/wiki/File:Kintampo_Waterfall_level_1.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kintampo_Waterfall_level_1.jpg) |
| Kwame Nkrumah Memorial Park & Mausoleum | `kwame-nkrumah-mausoleum-kwame-nkrumah-memorial-park-mausoleum-02.jpg` | [Amuzujoe](https://commons.wikimedia.org/wiki/File:Kwame_Nkrumah_Memorial_Park_%26_Mausoleum_02.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kwame_Nkrumah_Memorial_Park_%26_Mausoleum_02.jpg) |
| Kwame Nkrumah Memorial Park & Mausoleum | `kwame-nkrumah-mausoleum-kwame-nkrumah-memorial-park-mausoleum-1.jpg` | [Amuzujoe](https://commons.wikimedia.org/wiki/File:Kwame_Nkrumah_Memorial_Park_%26_Mausoleum_1.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kwame_Nkrumah_Memorial_Park_%26_Mausoleum_1.jpg) |
| Kwame Nkrumah Memorial Park & Mausoleum | `kwame-nkrumah-mausoleum-kwame-nkrumah-memorial-park-mausoleum-2.jpg` | [Fquasie](https://commons.wikimedia.org/wiki/File:Kwame_Nkrumah_Memorial_Park_%26_Mausoleum_2.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kwame_Nkrumah_Memorial_Park_%26_Mausoleum_2.jpg) |
| Kwame Nkrumah Memorial Park & Mausoleum | `kwame-nkrumah-mausoleum-kwame-nkrumah-memorial-park-mausoleum-3.jpg` | [Fquasie](https://commons.wikimedia.org/wiki/File:Kwame_Nkrumah_Memorial_Park_%26_Mausoleum_3.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kwame_Nkrumah_Memorial_Park_%26_Mausoleum_3.jpg) |
| Kwame Nkrumah Memorial Park & Mausoleum | `kwame-nkrumah-mausoleum-kwame-nkrumah-memorial-park-mausoleum-6.jpg` | [Fquasie](https://commons.wikimedia.org/wiki/File:Kwame_Nkrumah_Memorial_Park_%26_Mausoleum_6.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kwame_Nkrumah_Memorial_Park_%26_Mausoleum_6.jpg) |
| Kwame Nkrumah Memorial Park & Mausoleum | `kwame-nkrumah-mausoleum-kwame-nkrumah-memorial-park-mausoleum.jpg` | [Fquasie](https://commons.wikimedia.org/wiki/File:Kwame_Nkrumah_Memorial_Park_%26_Mausoleum.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kwame_Nkrumah_Memorial_Park_%26_Mausoleum.jpg) |
| Lake Bosomtwe Crater Lake | `lake-bosomtwe-02.jpg` | [Noahalorwu](https://commons.wikimedia.org/wiki/File:Lake_Bosomtwe_02.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Lake_Bosomtwe_02.jpg) |
| Lake Bosomtwe Crater Lake | `lake-bosomtwe-08.jpg` | [Noahalorwu](https://commons.wikimedia.org/wiki/File:Lake_Bosomtwe_08.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Lake_Bosomtwe_08.jpg) |
| Lake Bosomtwe Crater Lake | `lake-bosomtwe-breathtaking-afternoon-at-lake-bosomtwe.jpg` | [Kradolferp](https://commons.wikimedia.org/wiki/File:Breathtaking_afternoon_at_Lake_Bosomtwe.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Breathtaking_afternoon_at_Lake_Bosomtwe.jpg) |
| Lake Bosomtwe Crater Lake | `lake-bosomtwe-breathtaking-lake-bosomtwe.jpg` | [Kradolferp](https://commons.wikimedia.org/wiki/File:Breathtaking_Lake_Bosomtwe.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Breathtaking_Lake_Bosomtwe.jpg) |
| Lake Bosomtwe Crater Lake | `lake-bosomtwe-clouds-overlooking-lake-bosomtwe-1.jpg` | [Kwameghana(Bright Kwame Ayisi)](https://commons.wikimedia.org/wiki/File:Clouds_overlooking_Lake_Bosomtwe_1.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Clouds_overlooking_Lake_Bosomtwe_1.jpg) |
| Lake Bosomtwe Crater Lake | `lake-bosomtwe-just-beautiful-lake-bosomtwe.jpg` | [Kradolferp](https://commons.wikimedia.org/wiki/File:Just_beautiful_Lake_Bosomtwe.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Just_beautiful_Lake_Bosomtwe.jpg) |
| Larabanga Ancient Mosque | `larabanga-mosque-0.jpg` | [Amuzujoe](https://commons.wikimedia.org/wiki/File:Larabanga_Mosque_0.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Larabanga_Mosque_0.jpg) |
| Larabanga Ancient Mosque | `larabanga-mosque-1.jpg` | [Amuzujoe](https://commons.wikimedia.org/wiki/File:Larabanga_Mosque_1.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Larabanga_Mosque_1.jpg) |
| Larabanga Ancient Mosque | `larabanga-mosque-2.jpg` | [Amuzujoe](https://commons.wikimedia.org/wiki/File:Larabanga_Mosque_2.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Larabanga_Mosque_2.jpg) |
| Larabanga Ancient Mosque | `larabanga-mosque-larabanga-central-mosque-side-view.jpg` | [Amuzujoe](https://commons.wikimedia.org/wiki/File:Larabanga_Central_Mosque_Side_view.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Larabanga_Central_Mosque_Side_view.jpg) |
| Larabanga Ancient Mosque | `larabanga-mosque-larabanga-central-mosque.jpg` | [Amuzujoe](https://commons.wikimedia.org/wiki/File:Larabanga_Central_Mosque.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Larabanga_Central_Mosque.jpg) |
| Larabanga Ancient Mosque | `larabanga-mosque-mistry-stone-in-larabanja.jpg` | [Amuzujoe](https://commons.wikimedia.org/wiki/File:Mistry_Stone_in_Larabanja.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Mistry_Stone_in_Larabanja.jpg) |
| Manhyia Palace Museum | `manhyia-palace-an-image-baes-of-the-artifacts-at-the-manhyia-palace-museum.jpg` | [Nichoooo](https://commons.wikimedia.org/wiki/File:An_image_baes_of_the_artifacts_at_the_Manhyia_Palace_Museum.jpg) | CC BY 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:An_image_baes_of_the_artifacts_at_the_Manhyia_Palace_Museum.jpg) |
| Manhyia Palace Museum | `manhyia-palace-artifact-at-the-manhyia-palace-museum.jpg` | [Nichoooo](https://commons.wikimedia.org/wiki/File:Artifact_at_the_Manhyia_Palace_Museum.jpg) | CC BY 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Artifact_at_the_Manhyia_Palace_Museum.jpg) |
| Manhyia Palace Museum | `manhyia-palace-artifacts-at-the-manhyia-palace-museum.jpg` | [Nichoooo](https://commons.wikimedia.org/wiki/File:Artifacts_at_the_Manhyia_Palace_Museum.jpg) | CC BY 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Artifacts_at_the_Manhyia_Palace_Museum.jpg) |
| Manhyia Palace Museum | `manhyia-palace-museum-kumasi-ghana-2017.jpg` | [Dan Sloan](https://commons.wikimedia.org/wiki/File:Manhyia_Palace_Museum_(Kumasi,_Ghana_2017).jpg) | CC BY-SA 2.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Manhyia_Palace_Museum_(Kumasi,_Ghana_2017).jpg) |
| Manhyia Palace Museum | `manhyia-palace-the-entrance-to-manhyia-palace-museum.jpg` | [Achina Comfort Afrah](https://commons.wikimedia.org/wiki/File:The_entrance_to_Manhyia_Palace_Museum.jpg) | CC BY 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:The_entrance_to_Manhyia_Palace_Museum.jpg) |
| Mole National Park Elephant Safari | `mole-national-park-safari-in-mole-191042526.jpg` | [Stig Nygaard](https://commons.wikimedia.org/wiki/File:Safari_in_Mole_(191042526).jpg) | CC BY 2.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Safari_in_Mole_(191042526).jpg) |
| Mole National Park Elephant Safari | `mole-national-park-savanna-landscape-northern-region-ghana.jpg` | [Stig Nygaard](https://commons.wikimedia.org/wiki/File:Savanna_landscape,_Northern_region,_Ghana.jpg) | CC BY 2.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Savanna_landscape,_Northern_region,_Ghana.jpg) |
| Mole National Park Elephant Safari | `mole-national-park-éléphant-120916033.jpg` | [Alexandre Ultré](https://commons.wikimedia.org/wiki/File:%C3%89l%C3%A9phant_(120916033).jpeg) | CC BY-SA 3.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:%C3%89l%C3%A9phant_(120916033).jpeg) |
| Mount Afadja (Afadjato) | `mount-afadjato-223m-up.jpg` | [Blaq dynamite](https://commons.wikimedia.org/wiki/File:223m_up.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:223m_up.jpg) |
| Mount Afadja (Afadjato) | `mount-afadjato-664m-up.jpg` | [Blaq dynamite](https://commons.wikimedia.org/wiki/File:664m_up.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:664m_up.jpg) |
| Mount Afadja (Afadjato) | `mount-afadjato-a-view-from-the-summit.jpg` | [Blaq dynamite](https://commons.wikimedia.org/wiki/File:A_View_from_the_Summit.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:A_View_from_the_Summit.jpg) |
| Mount Afadja (Afadjato) | `mount-afadjato-wild-fruits-on-the-afadjato-mountain2.jpg` | [Treysam](https://commons.wikimedia.org/wiki/File:Wild_fruits_on_the_Afadjato_mountain2.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Wild_fruits_on_the_Afadjato_mountain2.jpg) |
| Mount Gemi | `mount-gemi-amedzofe-blickvomgemi-1892-300dpi.jpg` | [Ernst Bürgi (?)](https://commons.wikimedia.org/wiki/File:Amedzofe_BlickVomGemi_1892_300dpi.jpg) | Public domain | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Amedzofe_BlickVomGemi_1892_300dpi.jpg) |
| Mount Gemi | `mount-gemi-amedzofe-gemi-1892-300dpi.jpg` | [Unknown author Unknown author](https://commons.wikimedia.org/wiki/File:Amedzofe_Gemi_1892_300dpi.jpg) | Public domain | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Amedzofe_Gemi_1892_300dpi.jpg) |
| Mount Gemi | `mount-gemi-mt-gemi-01.jpg` | [Gaewu](https://commons.wikimedia.org/wiki/File:Mt._Gemi_01.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Mt._Gemi_01.jpg) |
| Mount Gemi | `mount-gemi-mt-gemi-03.jpg` | [Gaewu](https://commons.wikimedia.org/wiki/File:Mt._Gemi_03.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Mt._Gemi_03.jpg) |
| Mount Gemi | `mount-gemi-rock-on-mount-gemi.jpg` | [Kwameghana(Bright Kwame Ayisi)](https://commons.wikimedia.org/wiki/File:Rock_on_Mount_Gemi.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Rock_on_Mount_Gemi.jpg) |
| Mount Gemi | `mount-gemi-sighting-of-mount-gemi-from-akofa-guest-house-amedzofe.jpg` | [Daniel Oladapo](https://commons.wikimedia.org/wiki/File:Sighting_of_Mount_Gemi_from_Akofa_Guest_house,_Amedzofe.jpg) | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Sighting_of_Mount_Gemi_from_Akofa_Guest_house,_Amedzofe.jpg) |
| Navrongo Catholic Basilica | `navrongo-basilica-cathedral-basilica1.jpg` | [Mwintirew](https://commons.wikimedia.org/wiki/File:Cathedral_Basilica1.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Cathedral_Basilica1.jpg) |
| Navrongo Catholic Basilica | `navrongo-basilica-cathedral-basilica2.jpg` | [Mwintirew](https://commons.wikimedia.org/wiki/File:Cathedral_Basilica2.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Cathedral_Basilica2.jpg) |
| Navrongo Catholic Basilica | `navrongo-basilica-cathedral-basilica3.jpg` | [Mwintirew](https://commons.wikimedia.org/wiki/File:Cathedral_Basilica3.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Cathedral_Basilica3.jpg) |
| Navrongo Catholic Basilica | `navrongo-basilica-cathedral-basilica4.jpg` | [Mwintirew](https://commons.wikimedia.org/wiki/File:Cathedral_Basilica4.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Cathedral_Basilica4.jpg) |
| Navrongo Catholic Basilica | `navrongo-basilica-interior-of-the-cathedral-basilica-of-our-lady-of-seven-sorr.jpg` | [Sucram Yef](https://commons.wikimedia.org/wiki/File:Interior_of_the_Cathedral_Basilica_of_Our_Lady_of_Seven_Sorrows_(Navrongo,_Ghana_2019).jpg) | [CC BY 2.0](https://creativecommons.org/licenses/by/2.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Interior_of_the_Cathedral_Basilica_of_Our_Lady_of_Seven_Sorrows_(Navrongo,_Ghana_2019).jpg) |
| Navrongo Catholic Basilica | `navrongo-basilica-old-navrongo-catholic-cathedral.jpg` | [Kwameghana](https://commons.wikimedia.org/wiki/File:Old_Navrongo_Catholic_Cathedral.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Old_Navrongo_Catholic_Cathedral.jpg) |
| Nzulezo Stilt Village | `nzulezo-stilt-village-nzulezo-home.jpg` | [KwesiRaul](https://commons.wikimedia.org/wiki/File:Nzulezo_home.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Nzulezo_home.jpg) |
| Nzulezo Stilt Village | `nzulezo-stilt-village-nzulezo-stilt-village.jpg` | [Luke Bosman](https://commons.wikimedia.org/wiki/File:Nzulezo_stilt_village.jpg) | CC BY-SA 1.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Nzulezo_stilt_village.jpg) |
| Nzulezo Stilt Village | `nzulezo-stilt-village-nzulezo-village-1.jpg` | [KwesiRaul](https://commons.wikimedia.org/wiki/File:Nzulezo_village_1.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Nzulezo_village_1.jpg) |
| Nzulezo Stilt Village | `nzulezo-stilt-village-nzulezo-village-3.jpg` | [KwesiRaul](https://commons.wikimedia.org/wiki/File:Nzulezo_village_3.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Nzulezo_village_3.jpg) |
| Nzulezo Stilt Village | `nzulezo-stilt-village-nzulezo-village-4.jpg` | [KwesiRaul](https://commons.wikimedia.org/wiki/File:Nzulezo_village_4.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Nzulezo_village_4.jpg) |
| Nzulezo Stilt Village | `nzulezo-stilt-village-nzulezo-village-5.jpg` | [KwesiRaul](https://commons.wikimedia.org/wiki/File:Nzulezo_village_5.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Nzulezo_village_5.jpg) |
| Osu Castle (Fort Christiansborg) | `osu-castle-fort-christiansborg-castle-10.jpg` | [Esthee2010](https://commons.wikimedia.org/wiki/File:Fort_Christiansborg_Castle_10.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Fort_Christiansborg_Castle_10.jpg) |
| Osu Castle (Fort Christiansborg) | `osu-castle-fort-christiansborg-castle-11.jpg` | [Esthee2010](https://commons.wikimedia.org/wiki/File:Fort_Christiansborg_Castle_11.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Fort_Christiansborg_Castle_11.jpg) |
| Osu Castle (Fort Christiansborg) | `osu-castle-fort-christiansborg-castle-2.jpg` | [Esthee2010](https://commons.wikimedia.org/wiki/File:Fort_Christiansborg_Castle_2.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Fort_Christiansborg_Castle_2.jpg) |
| Osu Castle (Fort Christiansborg) | `osu-castle-fort-christiansborg-castle-3.jpg` | [Esthee2010](https://commons.wikimedia.org/wiki/File:Fort_Christiansborg_Castle_3.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Fort_Christiansborg_Castle_3.jpg) |
| Osu Castle (Fort Christiansborg) | `osu-castle-fort-christiansborg-castle-4.jpg` | [Esthee2010](https://commons.wikimedia.org/wiki/File:Fort_Christiansborg_Castle_4.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Fort_Christiansborg_Castle_4.jpg) |
| Osu Castle (Fort Christiansborg) | `osu-castle-osu-castle.jpg` | [Kwameghana](https://commons.wikimedia.org/wiki/File:Osu_Castle.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Osu_Castle.jpg) |
| Paga Sacred Crocodile Pond | `paga-crocodile-pond-a-crocodile-partially-submerged-in-paga-pond.jpg` | [Ibrahim Achiri](https://commons.wikimedia.org/wiki/File:A_crocodile_partially_submerged_in_Paga_pond.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:A_crocodile_partially_submerged_in_Paga_pond.jpg) |
| Paga Sacred Crocodile Pond | `paga-crocodile-pond-crocodile-at-paga-crocodile-pond.jpg` | [Knowledge and philosophy](https://commons.wikimedia.org/wiki/File:Crocodile_at_Paga_crocodile_pond.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Crocodile_at_Paga_crocodile_pond.jpg) |
| Paga Sacred Crocodile Pond | `paga-crocodile-pond-crocodile-in-water-at-paga-crocodile-pond.jpg` | [Knowledge and philosophy](https://commons.wikimedia.org/wiki/File:Crocodile_in_water_at_Paga_crocodile_pond.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Crocodile_in_water_at_Paga_crocodile_pond.jpg) |
| Paga Sacred Crocodile Pond | `paga-crocodile-pond-crocodile-inside-paga-crocodile-pond.jpg` | [Knowledge and philosophy](https://commons.wikimedia.org/wiki/File:Crocodile_inside_Paga_crocodile_pond.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Crocodile_inside_Paga_crocodile_pond.jpg) |
| Paga Sacred Crocodile Pond | `paga-crocodile-pond-crocodile-resting-at-the-shore-of-paga-crocodile-pond.jpg` | [Knowledge and philosophy](https://commons.wikimedia.org/wiki/File:Crocodile_resting_at_the_shore_of_Paga_crocodile_pond.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Crocodile_resting_at_the_shore_of_Paga_crocodile_pond.jpg) |
| Paga Sacred Crocodile Pond | `paga-crocodile-pond-crocodile-walking-out-of-water-at-paga-crocodile-pond.jpg` | [Knowledge and philosophy](https://commons.wikimedia.org/wiki/File:Crocodile_walking_out_of_water_at_Paga_crocodile_pond.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Crocodile_walking_out_of_water_at_Paga_crocodile_pond.jpg) |
| Sekondi-Takoradi Beach | `sekondi-takoradi-beach-a-wooden-house.jpg` | [Kwameghana](https://commons.wikimedia.org/wiki/File:A_wooden_house.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:A_wooden_house.jpg) |
| Sekondi-Takoradi Beach | `sekondi-takoradi-beach-near-takoradi-1942-12-24.jpg` | [British Royal Air Force - uploaded by John Atherton on Flickr](https://commons.wikimedia.org/wiki/File:Near_Takoradi_1942-12-24.jpg) | [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Near_Takoradi_1942-12-24.jpg) |
| Sekondi-Takoradi Beach | `sekondi-takoradi-beach-residential-houses-in-secondi-takoradi-2.jpg` | [Kwameghana](https://commons.wikimedia.org/wiki/File:Residential_houses_in_Secondi_Takoradi_%CC%A0_2.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Residential_houses_in_Secondi_Takoradi_%CC%A0_2.jpg) |
| Sekondi-Takoradi Beach | `sekondi-takoradi-beach-street-shops-takoradi-2011-b002.jpg` | [Ben Sutherland (on Flickr)](https://commons.wikimedia.org/wiki/File:Street_Shops_Takoradi_2011_B002.jpg) | [CC BY 2.0](https://creativecommons.org/licenses/by/2.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Street_Shops_Takoradi_2011_B002.jpg) |
| Sekondi-Takoradi Beach | `sekondi-takoradi-beach-takoradi-technical-institute-campus-center.jpg` | [Andrew Kvalheim](https://commons.wikimedia.org/wiki/File:Takoradi_Technical_Institute_campus_center.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Takoradi_Technical_Institute_campus_center.jpg) |
| Sekondi-Takoradi Beach | `sekondi-takoradi-beach-tvshop-takoradi-2011-b002.jpg` | [Ben Sutherland (on Flickr)](https://commons.wikimedia.org/wiki/File:TVshop_Takoradi_2011_B002.jpg) | [CC BY 2.0](https://creativecommons.org/licenses/by/2.0) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:TVshop_Takoradi_2011_B002.jpg) |
| Tafi Atome Monkey Sanctuary | `tafi-atome-monkey-sanctuary-3.jpg` | [Malibu xoxo](https://commons.wikimedia.org/wiki/File:Tafi_Atome_monkey_sanctuary_3.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Tafi_Atome_monkey_sanctuary_3.jpg) |
| Tafi Atome Monkey Sanctuary | `tafi-atome-monkey-sanctuary-7.jpg` | [Malibu xoxo](https://commons.wikimedia.org/wiki/File:Tafi_Atome_monkey_sanctuary_7.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Tafi_Atome_monkey_sanctuary_7.jpg) |
| Tafi Atome Monkey Sanctuary | `tafi-atome-monkey-sanctuary-9.jpg` | [Malibu xoxo](https://commons.wikimedia.org/wiki/File:Tafi_Atome_monkey_sanctuary_9.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Tafi_Atome_monkey_sanctuary_9.jpg) |
| Tafi Atome Monkey Sanctuary | `tafi-atome-monkey-sanctuary-a-monkey-on-top-of-a-tree-at-the-tafi-atome-monkey-sanctuary.jpg` | [Treysam](https://commons.wikimedia.org/wiki/File:A_monkey_on_top_of_a_tree_at_the_Tafi_Atome_Monkey_Sanctuary_in_the_Volta_Region_of_Ghana.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:A_monkey_on_top_of_a_tree_at_the_Tafi_Atome_Monkey_Sanctuary_in_the_Volta_Region_of_Ghana.jpg) |
| Tafi Atome Monkey Sanctuary | `tafi-atome-monkey-sanctuary-a-monkey-specie-in-the-tafi-atome-monkey-sanctuary-in-the-vo.jpg` | [Treysam](https://commons.wikimedia.org/wiki/File:A_monkey_specie_in_the_Tafi_Atome_Monkey_Sanctuary_in_the_Volta_Region_of_Ghana.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:A_monkey_specie_in_the_Tafi_Atome_Monkey_Sanctuary_in_the_Volta_Region_of_Ghana.jpg) |
| Tafi Atome Monkey Sanctuary | `tafi-atome-monkey-sanctuary-a-monkey-specie-in-the-tafi-atome-monkey-sanctuary-located-i.jpg` | [Treysam](https://commons.wikimedia.org/wiki/File:A_monkey_specie_in_the_Tafi_Atome_Monkey_Sanctuary_located_in_the_Volta_Region_of_Ghana.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:A_monkey_specie_in_the_Tafi_Atome_Monkey_Sanctuary_located_in_the_Volta_Region_of_Ghana.jpg) |
| Wli Waterfalls | `wli-waterfall-volta-region-way-to-wli-waterfalls-10.jpg` | [Malibu xoxo](https://commons.wikimedia.org/wiki/File:Volta_Region_way_to_Wli_waterfalls_10.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Volta_Region_way_to_Wli_waterfalls_10.jpg) |
| Wli Waterfalls | `wli-waterfall-volta-region-way-to-wli-waterfalls-2.jpg` | [Malibu xoxo](https://commons.wikimedia.org/wiki/File:Volta_Region_way_to_Wli_waterfalls_2.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Volta_Region_way_to_Wli_waterfalls_2.jpg) |
| Wli Waterfalls | `wli-waterfall-volta-region-way-to-wli-waterfalls-3.jpg` | [Malibu xoxo](https://commons.wikimedia.org/wiki/File:Volta_Region_way_to_Wli_waterfalls_3.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Volta_Region_way_to_Wli_waterfalls_3.jpg) |
| Wli Waterfalls | `wli-waterfall-volta-region-way-to-wli-waterfalls-4.jpg` | [Malibu xoxo](https://commons.wikimedia.org/wiki/File:Volta_Region_way_to_Wli_waterfalls_4.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Volta_Region_way_to_Wli_waterfalls_4.jpg) |
| Wli Waterfalls | `wli-waterfall-volta-region-wli-waterfalls-2.jpg` | [Malibu xoxo](https://commons.wikimedia.org/wiki/File:Volta_Region_Wli_waterfalls_2.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Volta_Region_Wli_waterfalls_2.jpg) |
| Wli Waterfalls | `wli-waterfall-volta-region-wli-waterfalls-5.jpg` | [Malibu xoxo](https://commons.wikimedia.org/wiki/File:Volta_Region_Wli_waterfalls_5.jpg) | CC BY-SA 4.0 | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Volta_Region_Wli_waterfalls_5.jpg) |

187 photographs across 45 places, from 88 photographers. Licences in use: CC BY-SA 4.0 (140), CC BY 2.0 (10), CC BY 4.0 (9), CC BY-SA 3.0 (9), CC BY-SA 2.0 (7), CC0 (5), Public domain (4), CC BY 3.0 (2), CC BY-SA 1.0 (1).
<!-- gallery-credits:end -->

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
  (1920px wide) of a 6000×4000 original. The market foodstuffs photo on the Food
  & Market tile is a 1920px copy of a 4032×3024 original. The crops you see on
  the tile come from CSS (`object-fit: cover` in `.hero-tile-media`), not from
  editing the file, so the stored image is an unmodified work apart from scaling.
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
