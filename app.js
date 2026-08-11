document.addEventListener('DOMContentLoaded', () => {

  // ── Mobile Navigation Toggle ─────────────────────────────────────────────
  const mobileToggle = document.querySelector('.mobile-toggle');
  const navLinks     = document.querySelector('.nav-links');
  const navItems     = document.querySelectorAll('.nav-link');

  if (mobileToggle && navLinks) {
    mobileToggle.setAttribute('aria-expanded', 'false');

    mobileToggle.addEventListener('click', () => {
      const isOpen = navLinks.classList.toggle('active');
      mobileToggle.classList.toggle('active', isOpen);
      mobileToggle.setAttribute('aria-expanded', String(isOpen));
      mobileToggle.setAttribute('aria-label', isOpen ? 'Close navigation menu' : 'Open navigation menu');
      // Prevent body scroll while the mobile drawer is open
      document.body.classList.toggle('nav-open', isOpen);
    });

    // Close the drawer when any nav link is tapped
    navItems.forEach(link => {
      link.addEventListener('click', () => {
        navLinks.classList.remove('active');
        mobileToggle.classList.remove('active');
        mobileToggle.setAttribute('aria-expanded', 'false');
        document.body.classList.remove('nav-open');
      });
    });

    // Close drawer when user taps the dark overlay behind the menu
    document.addEventListener('click', (e) => {
      if (
        navLinks.classList.contains('active') &&
        !navLinks.contains(e.target) &&
        !mobileToggle.contains(e.target)
      ) {
        navLinks.classList.remove('active');
        mobileToggle.classList.remove('active');
        mobileToggle.setAttribute('aria-expanded', 'false');
        document.body.classList.remove('nav-open');
      }
    });
  }

  // ── Card tap-to-expand (mobile only) ─────────────────────────────────────
  document.querySelectorAll('.card, .glass-card').forEach(card => {
    card.addEventListener('click', () => {
      if (window.innerWidth <= 768) {
        card.classList.toggle('active');
        document.body.classList.toggle('card-open');
      }
    });
  });

});
// Comprehensive Ghana Destinations Dataset (20+ Top Tourist Sites)
const DESTINATIONS = [
  {
    id: "tafi-atome-monkey-sanctuary",
    name: "Tafi Atome Monkey Sanctuary",
    category: "national-parks",
    categoryName: "Wildlife Sanctuary",
    region: "Volta Region",
    location: "Tafi Atome, Hohoe District",
    image: "assets/images/tafi_atome_monkeys_1.png",
    rating: 4.9,
    reviews: 840,
    fee: "GHS 60 / $5",
    hours: "8:00 AM – 5:00 PM Daily",
    bestTime: "Early Morning (7 AM – 10 AM)",
    accessibility: "Easy guided walking forest path",
    lat: 6.9056,
    lng: 0.3850,
    shortDesc: "Sacred sanctuary where friendly Mona monkeys roam freely and interact gently with visitors in a protected tropical forest.",
    fullDesc: "Tafi Atome Monkey Sanctuary is a community-based eco-tourism project in the Volta Region of Ghana. For over 200 years, the sacred Mona monkeys (Cercopithecus mona) have been protected by local traditional beliefs, considered divine messengers of the gods. Visitors can feed bananas to friendly monkeys right from their hands while taking guided forest walks with local community guides.",
    highlights: ["Hand-feeding Mona Monkeys", "Sacred Forest Walk", "Traditional Ewe Village Experience", "Community Eco-Lodge"],
    nearbyHotels: ["Tafi Atome Eco-Lodge", "Wli Water Heights Lodge", "Hohoe Executive Hotel"],
    guideContact: "+233 24 666 4321 (Tafi Atome Eco-Desk)"
  },
  {
    id: "boabeng-fiema-monkey-sanctuary",
    name: "Boabeng-Fiema Monkey Sanctuary",
    category: "national-parks",
    categoryName: "Wildlife Sanctuary",
    region: "Bono East Region",
    location: "Nkoranza North District",
    image: "assets/images/tafi_atome_monkeys_2.jpg",
    rating: 4.8,
    reviews: 720,
    fee: "GHS 70 / $6",
    hours: "8:00 AM – 5:00 PM Daily",
    bestTime: "Year-Round (Best in dry season)",
    accessibility: "Shaded canopy walking trails",
    lat: 7.7167,
    lng: -1.7000,
    shortDesc: "Ghana's famous sanctuary home to over 700 Mona monkeys and rare Geoffroy's Pied Colobus monkeys living together peacefully.",
    fullDesc: "Boabeng-Fiema is unique in Africa as the only sanctuary where two distinct species of monkeys—the Campbell's Mona monkey and the black-and-white Geoffroy's Pied Colobus monkey—live in close harmony near human villages. Local taboo strictly forbids harming the monkeys, and deceased monkeys are even buried with traditional funeral ceremonies in a special monkey cemetery.",
    highlights: ["Black & White Colobus Monkeys", "Sacred Monkey Cemetery", "Forest Canopy Nature Walk", "Nkoranza Cultural Heritage"],
    nearbyHotels: ["Boabeng-Fiema Guest House", "Nkoranza Heritage Hotel", "Techiman Palace Hotel"],
    guideContact: "+233 20 555 9988 (Boabeng Tourism Committee)"
  },
  {
    id: "cape-coast-castle",
    name: "Cape Coast Castle",
    category: "historical",
    categoryName: "Historical Site",
    region: "Central Region",
    location: "Cape Coast, Atlantic Coast",
    image: "assets/images/cape_coast_castle.png",
    rating: 4.9,
    reviews: 1420,
    fee: "GHS 120 / $10",
    hours: "9:00 AM – 4:30 PM Daily",
    bestTime: "Nov – Mar (Dry Season)",
    accessibility: "Wheelchair accessible lower courtyard",
    lat: 5.1053,
    lng: -1.2417,
    shortDesc: "UNESCO World Heritage fortress standing over the Atlantic Ocean, preserving deep historical memory and colonial architecture.",
    fullDesc: "Cape Coast Castle is one of about forty slave castles built on the Gold Coast of West Africa by European traders. Originally built by the Swedes in 1653 and later taken over by the British, it served as a major hub for the transatlantic slave trade. Visitors experience guided tours through the historic dungeons, the infamous 'Door of No Return', and the upper museum detailing West African maritime history.",
    highlights: ["Door of No Return", "Historical Museum", "Cannon Ramparts", "Atlantic Ocean View"],
    nearbyHotels: ["Coconut Grove Beach Resort", "Ridge Royal Hotel", "Oasis Beach Resort"],
    guideContact: "+233 24 555 0192 (GTA Certified Guide)"
  },
  {
    id: "kakum-national-park",
    name: "Kakum National Park Canopy Walk",
    category: "national-parks",
    categoryName: "National Park",
    region: "Central Region",
    location: "Cape Coast / Abrafo",
    image: "assets/images/kakum_canopy.png",
    rating: 4.8,
    reviews: 2180,
    fee: "GHS 150 / $12",
    hours: "6:00 AM – 4:00 PM Daily",
    bestTime: "Early Morning (6 AM – 9 AM)",
    accessibility: "Moderate physical hiking involved",
    lat: 5.3500,
    lng: -1.3833,
    shortDesc: "Suspended 40 meters above the jungle floor, Kakum offers Africa's most famous rainforest canopy walkway experience.",
    fullDesc: "Kakum National Park covers 375 square kilometers of virgin tropical rainforest in southern Ghana. It is one of only three locations in Africa with a canopy walkway. Suspended across 7 tree-top bridges extending over 330 meters, visitors enjoy panoramic views of ancient hardwoods, rare birds, butterflies, and forest flora.",
    highlights: ["7-Bridge Canopy Walkway", "Guided Birdwatching", "Camping Grounds", "Rainforest Nature Trails"],
    nearbyHotels: ["Kakum Rainforest Lodge", "Hans Cottage Botel", "Elmina Beach Resort"],
    guideContact: "+233 20 888 1234 (Ranger Desk)"
  },
  {
    id: "wli-waterfall",
    name: "Wli Waterfalls",
    category: "waterfalls",
    categoryName: "Waterfall",
    region: "Volta Region",
    location: "Hohoe, Volta Region",
    image: "assets/images/wli_waterfall.png",
    rating: 4.9,
    reviews: 950,
    fee: "GHS 80 / $7",
    hours: "7:00 AM – 5:00 PM Daily",
    bestTime: "April – October (Peak Flow)",
    accessibility: "Flat 45-min jungle walk to Lower Falls",
    lat: 7.1219,
    lng: 0.5906,
    shortDesc: "The highest waterfall in West Africa, cascading dramatically from a cliff face down into a fresh natural pool.",
    fullDesc: "Wli Waterfall (locally known as Agumatsa Falls, meaning 'Allow Me to Flow') drops over 80 meters down a sheer vertical rock face in the Agumatsa Wildlife Sanctuary. Surrounded by lush forest home to thousands of fruit bats, butterflies, and monkeys, visitors can swim in the cool, refreshing natural plunge pool.",
    highlights: ["Lower & Upper Falls Hike", "Fruit Bat Colony Sanctuary", "Natural Swimming Pool", "Agumatsa Forest Trail"],
    nearbyHotels: ["Wli Water Heights Lodge", "Waterfall Sanctuary Lodge", "Gbadzeme Eco-Lodge"],
    guideContact: "+233 54 321 9876 (Wli Tourism Board)"
  },
  {
    id: "mole-national-park",
    name: "Mole National Park Elephant Safari",
    category: "national-parks",
    categoryName: "National Park",
    region: "Savannah Region",
    location: "Damongo, Northern Ghana",
    image: "assets/images/mole_elephants.png",
    rating: 4.9,
    reviews: 1640,
    fee: "GHS 200 / $16",
    hours: "6:00 AM – 5:30 PM (Safari Hours)",
    bestTime: "Dec – April (Dry Season for Wildlife)",
    accessibility: "4x4 Vehicle & Foot Safaris Available",
    lat: 9.2560,
    lng: -1.8490,
    shortDesc: "Ghana's largest wildlife refuge offering walking foot safaris alongside wild African elephants, antelopes, and baboons.",
    fullDesc: "Spanning nearly 5,000 square kilometers of savannah wood and riparian forest, Mole is Ghana's premier wildlife destination. It is famous for its close-up walking safaris where visitors can approach peaceful herds of wild African elephants on foot with experienced armed rangers.",
    highlights: ["Walking Foot Safaris", "Drive Safaris (4x4)", "Mole Motel Pool Outlook", "Larabanga Mosque Nearby"],
    nearbyHotels: ["Zaina Lodge (Luxury Safari)", "Mole Motel", "Damongo Guest House"],
    guideContact: "+233 24 900 1122 (Park Headquarters)"
  },
  {
    id: "black-star-square",
    name: "Black Star Square & Independence Arch",
    category: "cultural",
    categoryName: "Cultural Landmark",
    region: "Greater Accra",
    location: "Accra Central Coast",
    image: "assets/images/black_star_square.png",
    rating: 4.7,
    reviews: 3100,
    fee: "Free Entry",
    hours: "Open 24/7 (Best during day)",
    bestTime: "Year-Round (Best at sunset)",
    accessibility: "Fully Paved & Accessible",
    lat: 5.5486,
    lng: -0.1931,
    shortDesc: "The monumental heart of modern Ghana's independence movement featuring the Black Star Gate and Eternal Flame.",
    fullDesc: "Commissioned by Kwame Nkrumah to honor Ghana's 1957 independence as the first sub-Saharan African nation to gain freedom from colonial rule. The site features the massive Black Star Gate, Independence Arch, the Flame of African Liberation, and seating for 30,000 spectators overlooking the Gulf of Guinea.",
    highlights: ["Independence Arch", "Black Star Gate", "Kwame Nkrumah Park Nearby", "Oceanfront Esplanade"],
    nearbyHotels: ["Mövenpick Ambassador Hotel", "Kempinski Hotel Gold Coast City", "Alisa Hotel"],
    guideContact: "+233 30 222 4455 (Accra City Tours)"
  },
  {
    id: "paga-crocodile-pond",
    name: "Paga Sacred Crocodile Pond",
    category: "cultural",
    categoryName: "Sacred Sanctuary",
    region: "Upper East Region",
    location: "Paga, Burkina Faso Border",
    image: "assets/images/Paga.jpg",
    rating: 4.6,
    reviews: 580,
    fee: "GHS 50 / $4",
    hours: "8:00 AM – 5:00 PM Daily",
    bestTime: "Dry Season (Nov – May)",
    accessibility: "Flat terrain near pond",
    lat: 10.9936,
    lng: -1.1128,
    shortDesc: "Famous sacred pond where wild West African crocodiles live peacefully alongside villagers and visitors can pose with them.",
    fullDesc: "Paga Crocodile Pond in northern Ghana is famous worldwide for its friendly, sacred crocodiles. According to local legend, the soul of every resident in Paga is tied to a crocodile in the pond. Guided by traditional caretakers, visitors can safely touch, pose with, and sit near tame crocodiles that emerge from the water.",
    highlights: ["Posing with Sacred Crocodiles", "Paga Slave Camp Nearby", "Burkina Border Market", "Nania Slave Route"],
    nearbyHotels: ["Paga Eco-Lodge", "Navrongo Catering Rest House", "Bolgatanga Plaza Hotel"],
    guideContact: "+233 24 777 3311 (Paga Tourism Center)"
  },
  {
    id: "nzulezo-stilt-village",
    name: "Nzulezo Stilt Village",
    category: "historical",
    categoryName: "UNESCO Heritage Site",
    region: "Western Region",
    location: "Beyin, Lake Tadane",
    image: "assets/images/ghana-stilt-village.jpg",
    rating: 4.8,
    reviews: 890,
    fee: "GHS 100 / $8",
    hours: "8:00 AM – 4:00 PM Daily",
    bestTime: "Rainy Season (Best water levels)",
    accessibility: "Canoe trip required across lake",
    lat: 5.0167,
    lng: -2.6000,
    shortDesc: "Ancient 500-year-old village built entirely on wooden stilts standing over Lake Tadane in western Ghana.",
    fullDesc: "Nzulezo (meaning 'Surface of Water' in the Nzema language) is a remarkable village built entirely on stilts over Lake Tadane. Founded over 500 years ago by migrants from Oualata, all structures, school, church, and walkways are suspended above the water. Visitors take a scenic 45-minute traditional canoe ride through raffia palm channels to reach the village.",
    highlights: ["Lake Tadane Canoe Ride", "Stilt Architecture & School", "Raffia Palm Jungle Canal", "Beyin Fort Apollonia"],
    nearbyHotels: ["Maaha Beach Resort", "Lou Moon Eco-Lodge", "Beyin Beach Hotel"],
    guideContact: "+233 24 333 8822 (Nzulezo Tourist Board)"
  },
  {
    id: "mount-afadjato",
    name: "Mount Afadja (Afadjato)",
    category: "national-parks",
    categoryName: "Adventure Mountain",
    region: "Volta Region",
    location: "Liati Wote, Gbledi",
    image: "assets/images/Afaja.jpg",
    rating: 4.8,
    reviews: 1100,
    fee: "GHS 70 / $6",
    hours: "6:00 AM – 4:00 PM Daily",
    bestTime: "Early Morning (Clear summit views)",
    accessibility: "Strenuous mountain hike",
    lat: 7.1167,
    lng: 0.5833,
    shortDesc: "The highest mountain peak in Ghana (885m), offering breathtaking summit views over Togo and the Volta forest.",
    fullDesc: "Mount Afadja (commonly called Afadjato) stands at 885 meters (2,904 ft) above sea level, making it the highest elevation in Ghana. Located near the Togo border, a challenging 2-hour summit hike rewards adventurers with panoramic views of lush mountain valleys, Tagbo Falls, and surrounding tropical rain forest.",
    highlights: ["Summit Peak View of Togo", "Tagbo Waterfall Hike", "Liati Wote Butterfly Sanctuary", "Mountain Trekking Trail"],
    nearbyHotels: ["Tagbo Falls Lodge", "Hohoe Executive Hotel", "Wli Sanctuary Lodge"],
    guideContact: "+233 20 444 5566 (Liati Wote Eco-Desk)"
  },
  {
    id: "boti-waterfalls",
    name: "Boti Waterfalls & Umbrella Rock",
    category: "waterfalls",
    categoryName: "Waterfall",
    region: "Eastern Region",
    location: "Yilo Krobo, Koforidua",
    image: "assets/images/boti-falls.jpg",
    rating: 4.7,
    reviews: 1250,
    fee: "GHS 80 / $7",
    hours: "8:00 AM – 5:00 PM Daily",
    bestTime: "June – October (Twin Falls Flow)",
    accessibility: "250 stone steps to falls base",
    lat: 6.1667,
    lng: -0.2167,
    shortDesc: "Famous twin waterfalls ('Male and Female') nestled in the Huhunya forest alongside the gravity-defying Umbrella Rock.",
    fullDesc: "Boti Falls is a seasonal twin waterfall located in the Eastern Region. The twin falls are referred to locally as the 'Male' and 'Female' falls; during high flow in the rainy season, they merge together in a sacred 'mating ceremony'. A 30-minute hike from the falls leads to the famous Umbrella Rock and a three-headed palm tree.",
    highlights: ["Twin Falls Mating Ceremony", "Umbrella Rock Balancing Formation", "3-Headed Palm Tree", "Forest Hike"],
    nearbyHotels: ["Mac-Dic Royal Plaza Koforidua", "Capital View Hotel", "Boti Eco-Lodge"],
    guideContact: "+233 24 111 6655 (Boti Falls Tourist Desk)"
  },
  {
    id: "elmina-castle",
    name: "Elmina Castle (St. George's Castle)",
    category: "historical",
    categoryName: "UNESCO Heritage Site",
    region: "Central Region",
    location: "Elmina, Central Coast",
    image: "assets/images/Elimina.webp",
    rating: 4.9,
    reviews: 1890,
    fee: "GHS 120 / $10",
    hours: "9:00 AM – 4:30 PM Daily",
    bestTime: "Year-Round",
    accessibility: "Paved courtyards & historic stairs",
    lat: 5.0844,
    lng: -1.3492,
    shortDesc: "The oldest European building in existence in sub-Saharan Africa, erected by the Portuguese in 1482.",
    fullDesc: "St. George's Castle in Elmina was constructed by Portuguese traders in 1482 as the first European trading post built on the Gulf of Guinea. Initially established for gold trading, it later became a central site of the transatlantic slave trade under Dutch and British control. Today, it stands as a UNESCO World Heritage site and powerful monument of remembrance.",
    highlights: ["Portuguese & Dutch Dungeons", "Female Slave Cells", "Governor's Suite", "Elmina Fishing Harbor Overlook"],
    nearbyHotels: ["Elmina Beach Resort", "Coconut Grove Beach Resort", "Golden Hill Parker Hotel"],
    guideContact: "+233 24 888 7766 (Elmina Castle Desk)"
  },
  {
    id: "larabanga-mosque",
    name: "Larabanga Ancient Mosque",
    category: "historical",
    categoryName: "Architectural Heritage",
    region: "Savannah Region",
    location: "Larabanga, near Mole Park",
    image: "assets/images/Larabanga.webp",
    rating: 4.7,
    reviews: 640,
    fee: "GHS 40 / $3",
    hours: "8:00 AM – 5:30 PM Daily",
    bestTime: "Dry Season (Combines with Mole Safari)",
    accessibility: "Flat village walking access",
    lat: 9.2197,
    lng: -1.8603,
    shortDesc: "Ghana's oldest mosque built in 1421 in Sudanic-Sahelian architectural style, known as the 'Mecca of West Africa'.",
    fullDesc: "Larabanga Mosque is an ancient mud-brick mosque founded in 1421 by Islamic trader Ayuba. Built using whitewashed mud, timber logs, and pyradmidal towers, it is the oldest existing mosque in Ghana and one of the most famous examples of Sudanic architecture in West Africa. It houses an ancient Koran believed to have descended from heaven.",
    highlights: ["Sudanese Mud-Brick Architecture", "Ancient Holy Koran Replica", "Larabanga Mystic Stone", "Mole Safari Stopover"],
    nearbyHotels: ["Zaina Lodge", "Mole Motel", "Damongo Guest House"],
    guideContact: "+233 24 555 4321 (Larabanga Tourism Guild)"
  },
  {
    id: "aburi-botanical-gardens",
    name: "Aburi Botanical Gardens",
    category: "national-parks",
    categoryName: "Botanical Reserve",
    region: "Eastern Region",
    location: "Aburi, Akuapem Hills",
    image: "assets/images/Aburi.webp",
    rating: 4.7,
    reviews: 1950,
    fee: "GHS 50 / $4",
    hours: "8:30 AM – 5:00 PM Daily",
    bestTime: "Year-Round (Cool mountain breeze)",
    accessibility: "Wide paved garden avenues",
    lat: 5.8483,
    lng: -0.1747,
    shortDesc: "Historic 1890s hilltop garden retreat nestled in the cool Akuapem mountains featuring giant palm avenues and exotic trees.",
    fullDesc: "Established in 1890 by the British colonial administration, Aburi Botanical Gardens spans 160 acres of lush mountain forest. Known for its majestic royal palm avenue, carved tree of life, exotic medicinal plants, and cool temperate climate, Aburi is a favorite weekend getaway just 45 minutes drive from Accra.",
    highlights: ["Royal Palm Tree Avenue", "Carved Tree of Life", "Old Helicopter Monument", "Cocoa Tree Demonstration Plot"],
    nearbyHotels: ["Peduase Valley Resort", "Aburi Heights Hotel", "Hillburi Resort"],
    guideContact: "+233 20 222 9988 (Aburi Gardens Desk)"
  },
  {
    id: "bonwire-kente-village",
    name: "Bonwire Kente Weaving Village",
    category: "cultural",
    categoryName: "Craft Heritage",
    region: "Ashanti Region",
    location: "Bonwire, near Kumasi",
    image: "assets/images/Kente.jpg",
    rating: 4.8,
    reviews: 810,
    fee: "Free Entry (Shopping extra)",
    hours: "8:00 AM – 5:00 PM (Mon – Sat)",
    bestTime: "Year-Round",
    accessibility: "Village workshop walking paths",
    lat: 6.7833,
    lng: -1.4833,
    shortDesc: "The historic heartland of royal Ashanti Kente cloth weaving, where master weavers craft silk fabrics on wooden looms.",
    fullDesc: "Bonwire is world-famous as the birth village of Kente cloth weaving in the Ashanti Kingdom. Legend has it that two brothers learned the art by observing a spider weaving its web. Today, visitors can watch master craftsmen operate hand looms, try weaving their own patterns, and purchase authentic royal Kente directly from artisan families.",
    highlights: ["Live Hand-Loom Weaving", "Custom Kente Ordering", "Kente Origin Legends", "Bonwire Kente Museum"],
    nearbyHotels: ["Manhyia Palace Hotel", "Golden Tulip Kumasi", "Royal Basin Resort"],
    guideContact: "+233 24 444 1199 (Bonwire Weavers Guild)"
  }
];

// Complete Ghanaian Cultural Festivals Dataset
const FESTIVALS = [
  {
    id: "aboakyer-festival",
    name: "Aboakyer Festival (Deer Hunting Festival)",
    culture: "Effutu People of Winneba Traditional Area",
    month: "May (1st Saturday in May)",
    duration: "1 Week Celebration",
    location: "Winneba",
    region: "Central Region",
    image: "assets/images/aboakyer_festival.jpg",
    shortDesc: "Famous deer hunting ritual where rival Asafo warrior companies capture a live bushbuck deer unarmed to present to the Paramount Chief.",
    fullDesc: "The Aboakyer festival is celebrated on the 1st Saturday in May by the Effutu people of Winneba in the Central Region. It commemorates their migration from the ancient Western Sudan Empire to their present settlement. The highlight features a fierce competitive deer hunt between two traditional Asafo warrior groups—the Dentsefo and Tuafo. The first group to capture a live, uninjured deer using only bare hands wins high prestige, presenting it to the Simpa Otuano royal stool.",
    keyRituals: ["Asafo Warrior Deer Hunt", "Royal Stool Consecration", "Durbar of Paramount Chiefs", "Highlife Musical Concerts"]
  },
  {
    id: "homowo-festival",
    name: "Homowo Festival",
    culture: "Ga People of Accra",
    month: "August / September",
    duration: "1 Month Festival Season",
    location: "Accra, Tema, Ningo",
    region: "Greater Accra Region",
    image: "assets/images/cultural_dancers.png",
    shortDesc: "Meaning 'hooting at hunger', celebrating victory over historical famine with traditional Kpokpoi food sharing and drumming.",
    fullDesc: "Homowo is the most celebrated festival of the Ga people in Greater Accra. The word 'Homowo' literally translates to 'hooting at hunger'. It commemorates a devastating famine that plagued the Ga ancestors during their migration to Accra before a miraculous bountiful harvest. Chiefs and family heads sprinkle traditional 'Kpokpoi' (steamed cornmeal and palm oil soup) across family ancestral homes and streets while drumming and dancing.",
    keyRituals: ["Kpokpoi Ritual Sprinkling", "Twin Celebrations (Akweley Suma)", "Twin Drumming & Dancing", "Family Reconciliation Feasts"]
  },
  {
    id: "adekyem-festival",
    name: "Adekyem Festival",
    culture: "Akan People of Bechem",
    month: "December",
    duration: "3 Days",
    location: "Bechem",
    region: "Ahafo Region",
    image: "assets/images/cultural_dancers.png",
    shortDesc: "Derived from Akan 'Adekyem' meaning 'gift distribution', celebrating harvest bounty and community sharing.",
    fullDesc: "Bechem is derived from the Akan phrase 'Adekyem', which literally translates to a place where gifts or harvested items are shared. Celebrated annually in December, the chief and elders distribute symbolic gifts, agricultural harvest produce, and awards to outstanding community members while honoring ancestral spirits.",
    keyRituals: ["Harvest Gift Sharing", "Ancestral Libation Pouring", "Akan Fontomfrom Drumming", "Development Fundraiser"]
  },
  {
    id: "apoo-festival",
    name: "Apoo Festival",
    culture: "Bono People of Techiman & Sunyani",
    month: "October",
    duration: "1 Week",
    location: "Techiman & Sunyani",
    region: "Bono Region",
    image: "assets/images/cultural_dancers.png",
    shortDesc: "A cleansing festival allowing citizens to speak honest truths to leaders and cleanse social grievances.",
    fullDesc: "Apoo is an ancient purification festival celebrated by the Bono people of Techiman and Sunyani. The name comes from 'Apo' meaning to reject or cleanse evil. During the festival week, citizens are permitted to publicly express grievances, critique chiefs and leaders constructively without penalty, bringing social harmony and spiritual cleansing.",
    keyRituals: ["Public Honest Critiques (Apoo Songs)", "Town Spiritual Cleansing", "Royal Durbar", "Traditional Pacification Shrines"]
  },
  {
    id: "asafotufiam-festival",
    name: "Asafotufiam Festival",
    culture: "Ga-Adangbe People of Ada",
    month: "July – August (1st Week)",
    duration: "1 Week",
    location: "Ada Traditional Area",
    region: "Greater Accra Region",
    image: "assets/images/cultural_dancers.png",
    shortDesc: "Warrior festival commemorating ancestral victories with musketry firing displays and colourful Volta river regattas.",
    fullDesc: "Asafotufiam is celebrated by the chiefs and people of Ada in remembrance of ancient war achievements of their brave ancestors who fought for the settlement of Ada land. Asafo warrior groups dress in traditional battle armor, fire ceremonial muskets, and parade through the streets followed by boat racing along the Volta River estuary.",
    keyRituals: ["Ceremonial Musket Firing", "Volta Estuary Boat Regatta", "Asafo Company Reenactments", "Miss Ada Cultural Pageant"]
  },
  {
    id: "bakatue-festival",
    name: "Bakatue Festival",
    culture: "Elmina & Fante People",
    month: "1st Tuesday in July",
    duration: "1 Week",
    location: "Elmina",
    region: "Central Region",
    image: "assets/images/cape_coast_castle.png",
    shortDesc: "Meaning 'opening of the lagoon', marking the start of the fishing season with royal canoe races and sea rituals.",
    fullDesc: "Bakatue means 'the opening of the lagoon' (Benya Lagoon). Celebrated by the chiefs and people of Elmina, the festival invokes ancestral blessings for a bountiful fishing harvest. The Paramount Chief casts a net into the lagoon 3 times, after which colorful decorated canoes race across the water in front of Castle Elmina.",
    keyRituals: ["Casting of the Royal Net", "Benya Lagoon Canoe Race", "Royal Palanquin Procession", "Seafood Festival & Highlife"]
  },
  {
    id: "damba-festival",
    name: "Damba Festival",
    culture: "Dagbamba, Gonja, Mamprusi & Waala People",
    month: "July – August",
    duration: "1 Week",
    location: "Tamale, Yendi, Wa",
    region: "Northern & Savannah Regions",
    image: "assets/images/cultural_dancers.png",
    shortDesc: "Vibrant Northern festival featuring royal horse riding displays, traditional Batakari smocks, and talking drum performances.",
    fullDesc: "Damba is one of the most prominent cultural festivals in Northern Ghana, celebrated by the Dagbamba, Gonja, Mamprusi, and Waala ethnic groups. Originally marking the birth of Prophet Muhammad, it has evolved into a glorious display of chieftaincy, horse-riding choreography, traditional Northern smocks (Batakari), and intricate talking drum (Dondo) dancing.",
    keyRituals: ["Somokun (Rice Picking Ritual)", "Royal Horse Dancing Display", "High Chiefs Procession", "Batakari Fashion & Dance Showcase"]
  },
  {
    id: "dipo-festival",
    name: "Dipo (Puberty Rites) Festival",
    culture: "Krobo People of Somanya & Manya Krobo",
    month: "February / April",
    duration: "4 Days",
    location: "Somanya & Odumase Krobo",
    region: "Eastern Region",
    image: "assets/images/cultural_dancers.png",
    shortDesc: "Ancient initiation rites ushering young women into womanhood, adorned in famous Krobo glass beads and royal attire.",
    fullDesc: "Dipo is a traditional puberty rite celebrated by the Krobo people of the Eastern Region. It marks the transition of young maidens from adolescence into womanhood. Initiates are adorned with precious Krobo glass beads, silk cloths, and woven hats, performing the traditional Klama dance on sacred initiation stones.",
    keyRituals: ["Sacred Stone Cleansing (Tefo)", "Klama Dance Performance", "Adornment with Royal Krobo Beads", "Initiation Certification"]
  },
  {
    id: "fao-festival",
    name: "FAO Harvest Festival",
    culture: "Kassena-Nankana People",
    month: "January",
    duration: "3 Days",
    location: "Navrongo",
    region: "Upper East Region",
    image: "assets/images/cultural_dancers.png",
    shortDesc: "Thanksgiving harvest festival featuring traditional horn blowing, shield dancing, and millet harvest celebrations.",
    fullDesc: "FAO is celebrated by the Kassena-Nankana people of Navrongo to thank the Almighty God and ancestral spirits for a successful agricultural harvest season. Farmers display their largest crops, and traditional horn-blowers and shield warriors perform celebratory dances.",
    keyRituals: ["Harvest Thanksgiving Libation", "Traditional Horn & Flute Music", "Warrior Shield Dance", "Agricultural Produce Exhibition"]
  },
  {
    id: "fetu-afahye-festival",
    name: "Fetu Afahye Festival",
    culture: "Oguaa People of Cape Coast",
    month: "September (1st Saturday)",
    duration: "1 Week",
    location: "Cape Coast",
    region: "Central Region",
    image: "assets/images/cape_coast_castle.png",
    shortDesc: "Celebrated to purify Oguaa land of historic epidemics and invoke blessings from the 77 traditional deities.",
    fullDesc: "Fetu Afahye is celebrated by the Oguaa people of Cape Coast. It commemorates a historic plague that was eradicated through ancestral prayers to 77 local deities. Highlights include a grand procession of paramount chiefs carried in opulent palanquins under giant royal umbrellas, accompanied by Asafo drum beats.",
    keyRituals: ["Pouring Libation to 77 Deities", "Asafo Warriors Parade", "Grand Durbar of Chiefs", "Cape Coast Street Carnival"]
  },
  {
    id: "gologo-festival",
    name: "Gologo Festival",
    culture: "Talensi People of Tengzug",
    month: "March",
    duration: "3 Days",
    location: "Tengzug, Talensi",
    region: "Upper East Region",
    image: "assets/images/cultural_dancers.png",
    shortDesc: "Pre-planting festival seeking rain and bountiful soil fertility from the sacred Tengzug rock shrines.",
    fullDesc: "Gologo is celebrated by the Talensi people living amongst the majestic granitic rocks of Tengzug. Held in March before the rainy season, worshippers gather at the ancient Golib cave shrine to pray for rain, bumper grain harvests, and good health for all families.",
    keyRituals: ["Golib Shrine Invocations", "Pre-Planting Rain Rituals", "Sacred Rock Cave Chanting", "Community Communal Feast"]
  },
  {
    id: "hogbetsotso-festival",
    name: "Hogbetsotso Festival",
    culture: "Anlo Ewe People",
    month: "November (1st Saturday)",
    duration: "1 Week",
    location: "Anloga",
    region: "Volta Region",
    image: "assets/images/cultural_dancers.png",
    shortDesc: "Commemorating the historic escape of the Ewe people from ancient tyrannical rule, featuring famous backward walking dances.",
    fullDesc: "Hogbetsotso (pronounced 'Hogbe-tso-tso') is celebrated by the Anlo Ewe people of the Volta Region. It commemorates their historic migration escape from Notsie in present-day Togo to avoid the tyranny of King Agorkoli. During the festival, dancers perform the Agbadza and Atsiagbekor dances, reenacting their backward walking strategy used to deceive pursuers.",
    keyRituals: ["Reenactment of Backward Escape Walk", "Agbadza & Atsiagbekor Dances", "Peace & Reconciliation Purification", "Durbar of Ewe Chiefs"]
  },
  {
    id: "kloyo-sikplemi-festival",
    name: "Kloyo Sikplemi Festival",
    culture: "Yilo Krobo People",
    month: "November",
    duration: "1 Week",
    location: "Somanya",
    region: "Eastern Region",
    image: "assets/images/cultural_dancers.png",
    shortDesc: "Commemorating the Krobo ancestors' relocation from the Kloyo Mountain to their present lowlands.",
    fullDesc: "Kloyo Sikplemi is celebrated by the Yilo Krobo traditional area. It commemorates the historic eviction of their ancestors from the Kloyo mountain reserve by British colonial forces in 1892. The festival features a pilgrimage hike up the sacred Kloyo Mountain.",
    keyRituals: ["Sacred Mountain Pilgrimage Hike", "Ancestral Tribute Libations", "Fontomfrom Drumming", "Yilo Krobo Cultural Pageant"]
  }
];

// Practical Information Content Data
const PRACTICAL_INFO = {
  "getting-around": {
    title: "Getting Around Ghana",
    badge: "Transportation Guide",
    content: `
      <h4>✈️ Domestic Flights</h4>
      <p>PassionAir and Africa World Airlines (AWA) fly daily between Accra (ACC), Kumasi (KMS), Tamale (TML), and Takoradi (TKD).</p>
      
      <h4>🚗 Ride Hailing & Taxis</h4>
      <p>Uber, Yango, and Bolt operate extensively throughout Greater Accra and Kumasi with cashless options. Local orange-fender taxis are also widely available.</p>
      
      <h4>🚌 Tro-Tros & Intercity Coaches</h4>
      <p>Tro-tros (shared minibuses) are the quintessential Ghanaian commuting experience. For long distances, VIP Jeoun and STC offer comfortable air-conditioned coaches.</p>
    `
  },
  "flight-visa": {
    title: "Flight & Visa Requirements",
    badge: "Travel Documentation",
    content: `
      <h4> Visa on Arrival & E-Visa</h4>
      <p>Ghana offers online e-Visa applications and Visa on Arrival for ECOWAS citizens, African Union passport holders, and during the annual December in GH season.</p>
      
      <h4> Major Airlines Serving Accra (ACC)</h4>
      <p>Kotoka International Airport in Accra is served directly by Delta Air Lines, British Airways, Emirates, KLM, Qatar Airways, Ethiopian Airlines, and Turkish Airlines.</p>
      
      <h4> Yellow Fever Certificate</h4>
      <p>A valid international yellow fever vaccination card is mandatory for entry for all incoming travelers over 9 months of age.</p>
    `
  },
  "practical-info": {
    title: "Practical Information & Tips",
    badge: "Essential Tourist Tips",
    content: `
      <h4> Currency & Mobile Money (MoMo)</h4>
      <p>The currency is the Ghana Cedi (GHS). Mobile Money (MTN MoMo) and cards are used everywhere in cities, but carry cash Cedis when visiting rural waterfalls and parks.</p>
      
      <h4> Language & Greetings</h4>
      <p>English is the official language. Learning basic Twi greetings like <em>"Akwaaba"</em> (Welcome), <em>"Eti sen?"</em> (How are you?), and <em>"Medaase"</em> (Thank you) will warm every heart!</p>
      
      <h4> Power & Adapters</h4>
      <p>Ghana uses Type G 3-pin British plugs (230V, 50Hz). It's recommended to pack a universal travel adapter and power bank for safari trips.</p>
    `
  }
};

// Global State
let currentCategory = 'all';
let searchQuery = '';
let savedBookmarks = JSON.parse(localStorage.getItem('visitGhanaBookmarks') || '[]');

// DOM Loaded Initialization
document.addEventListener('DOMContentLoaded', () => {
  renderDestinations();
  renderFestivals();
  setupEventListeners();
});

// Advanced Multi-Field Search & Render Destinations
function renderDestinations() {
  const grid = document.getElementById('destinations-grid');
  if (!grid) return;

  const q = searchQuery.toLowerCase().trim();

  const filtered = DESTINATIONS.filter(item => {
    const matchesCat = currentCategory === 'all' || item.category === currentCategory;
    const matchesSearch = !q || 
                          item.name.toLowerCase().includes(q) || 
                          item.location.toLowerCase().includes(q) ||
                          item.region.toLowerCase().includes(q) ||
                          item.categoryName.toLowerCase().includes(q) ||
                          item.shortDesc.toLowerCase().includes(q) ||
                          item.fullDesc.toLowerCase().includes(q) ||
                          item.highlights.some(h => h.toLowerCase().includes(q));

    return matchesCat && matchesSearch;
  });

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px; background: var(--bg-card-glass); border-radius: var(--radius-lg); border: 1px solid var(--border-glass);">
        <h3 style="font-size: 1.5rem; margin-bottom: 8px; color: #FFF;">No matching destinations found for "${searchQuery}"</h3>
        <p style="color: var(--text-secondary); margin-bottom: 16px;">Try searching for "Monkey", "Waterfall", "Castle", "Safari", "Volta", "Accra", or "Hiking".</p>
        <button class="hero-pill-btn" onclick="clearSearch()">Clear Search Filter</button>
      </div>
    `;
    return;
  }

  grid.innerHTML = filtered.map(item => {
    const isSaved = savedBookmarks.includes(item.id);
    return `
      <div class="destination-card" data-id="${item.id}">
        <div class="card-media">
          <img src="${item.image}" alt="${item.name}" loading="lazy">
          <span class="card-badge">${item.categoryName}</span>
          <button class="card-bookmark-btn ${isSaved ? 'saved' : ''}" onclick="toggleBookmark('${item.id}', event)" title="Bookmark Destination">
            <svg viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
          </button>
        </div>
        <div class="card-body">
          <div class="card-location">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>
            ${item.location}
          </div>
          <h3 class="card-title">${item.name}</h3>
          <p class="card-description">${item.shortDesc}</p>
          <div class="card-meta">
            <div class="meta-item">
              <span class="meta-label">Entrance Fee</span>
              <span class="meta-val">${item.fee}</span>
            </div>
            <button class="btn-card-details" onclick="openDestinationModal('${item.id}')">Explore Details →</button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function clearSearch() {
  searchQuery = '';
  const searchInput = document.getElementById('search-input');
  if (searchInput) searchInput.value = '';
  renderDestinations();
}

// Render Cultural Festivals
function renderFestivals() {
  const festivalContainer = document.getElementById('festivals-grid-container');
  if (!festivalContainer) return;

  festivalContainer.innerHTML = FESTIVALS.map(item => {
    return `
      <div class="festival-card-expanded">
        <div class="festival-card-img">
          <img src="${item.image}" alt="${item.name}" loading="lazy">
          <span class="festival-month-badge">📅 ${item.month}</span>
        </div>
        <div class="festival-card-content">
          <div class="festival-culture-tag"> ${item.culture}</div>
          <h3 class="festival-card-title">${item.name}</h3>
          
          <div class="festival-meta-row">
            <span> <strong>Location:</strong> ${item.location}, ${item.region}</span>
            <span> <strong>Duration:</strong> ${item.duration}</span>
          </div>

          <p class="festival-card-desc">${item.shortDesc}</p>

          <button class="btn-card-details" onclick="openFestivalModal('${item.id}')" style="width: 100%; text-align: center; margin-top: 12px;">
            Explore Festival Rituals & Details →
          </button>
        </div>
      </div>
    `;
  }).join('');
}

// Open Festival Detail Modal
function openFestivalModal(id) {
  const festival = FESTIVALS.find(f => f.id === id);
  if (!festival) return;

  const overlay = document.getElementById('destination-modal-overlay');
  const card = document.getElementById('destination-modal-card');
  if (!overlay || !card) return;

  card.innerHTML = `
    <button class="modal-close-btn" onclick="closeModal('destination-modal-overlay')">✕</button>
    <img src="${festival.image}" class="modal-hero-img" alt="${festival.name}">
    <div class="modal-content-body">
      <div class="modal-header-meta">
        <span class="card-badge" style="background: var(--crimson-gradient); color: #FFF; border: none;">👑 ${festival.culture}</span>
        <span style="font-weight: 700; color: var(--emerald-accent);">📍 ${festival.location}, ${festival.region}</span>
      </div>
      <h2 class="modal-title">${festival.name}</h2>
      
      <div class="modal-fact-grid">
        <div class="fact-item">
          <h5>Month / Time of Year</h5>
          <p>📅 ${festival.month}</p>
        </div>
        <div class="fact-item">
          <h5>Duration</h5>
          <p>${festival.duration}</p>
        </div>
        <div class="fact-item">
          <h5>Location</h5>
          <p>📍 ${festival.location}</p>
        </div>
        <div class="fact-item">
          <h5>Region</h5>
          <p>${festival.region}</p>
        </div>
      </div>

      <h3 style="font-size: 1.25rem; margin: 24px 0 12px 0;">Cultural History & Celebration</h3>
      <p style="color: var(--text-secondary); line-height: 1.7; font-size: 1rem; margin-bottom: 24px;">${festival.fullDesc}</p>

      <h4 style="font-size: 1.1rem; margin-bottom: 12px;">Key Rituals & Event Highlights</h4>
      <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 28px;">
        ${festival.keyRituals.map(r => `<span style="background: rgba(255, 184, 0, 0.12); color: var(--gold-primary); border: 1px solid var(--border-gold); font-weight: 700; font-size: 0.85rem; padding: 8px 16px; border-radius: 20px;">🥁 ${r}</span>`).join('')}
      </div>

      <div style="display: flex; gap: 12px;">
        <button class="hero-pill-btn" style="flex: 1; justify-content: center;" onclick="showToast('Festival added to your cultural itinerary!')">
          Add Festival to My Trip
        </button>
        <button class="btn-card-details" style="padding: 14px 24px;" onclick="closeModal('destination-modal-overlay')">Close</button>
      </div>
    </div>
  `;

  overlay.classList.add('active');
}



// Open Destination Detail Modal
function openDestinationModal(id) {
  const item = DESTINATIONS.find(d => d.id === id);
  if (!item) return;

  const overlay = document.getElementById('destination-modal-overlay');
  const card = document.getElementById('destination-modal-card');
  if (!overlay || !card) return;

  card.innerHTML = `
    <button class="modal-close-btn" onclick="closeModal('destination-modal-overlay')">✕</button>
    <img src="${item.image}" class="modal-hero-img" alt="${item.name}">
    <div class="modal-content-body">
      <div class="modal-header-meta">
        <span class="card-badge">${item.categoryName}</span>
        <span style="font-weight: 700; color: var(--emerald-accent);">📍 ${item.region}</span>
      </div>
      <h2 class="modal-title">${item.name}</h2>
      
      <div class="modal-fact-grid">
        <div class="fact-item">
          <h5>Opening Hours</h5>
          <p> ${item.hours}</p>
        </div>
        <div class="fact-item">
          <h5>Entrance Fee</h5>
          <p> ${item.fee}</p>
        </div>
        <div class="fact-item">
          <h5>Best Time to Visit</h5>
          <p>${item.bestTime}</p>
        </div>
        <div class="fact-item">
          <h5>Accessibility</h5>
          <p>♿ ${item.accessibility}</p>
        </div>
      </div>

      <h3 style="font-size: 1.25rem; margin: 24px 0 12px 0;">About ${item.name}</h3>
      <p style="color: var(--text-secondary); line-height: 1.7; font-size: 1rem; margin-bottom: 24px;">${item.fullDesc}</p>

      <h4 style="font-size: 1.1rem; margin-bottom: 12px;">Key Experience Highlights</h4>
      <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 28px;">
        ${item.highlights.map(h => `<span style="background: rgba(255, 184, 0, 0.12); color: var(--gold-primary); border: 1px solid var(--border-gold); font-weight: 700; font-size: 0.85rem; padding: 6px 14px; border-radius: 20px;">✨ ${h}</span>`).join('')}
      </div>

      <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-glass); padding: 20px; border-radius: 16px; margin-bottom: 24px;">
        <h4 style="font-size: 1rem; margin-bottom: 8px; color: #FFF;">🏨 Nearby Accommodations</h4>
        <p style="font-size: 0.9rem; color: var(--text-secondary);">${item.nearbyHotels.join(' • ')}</p>
        <h4 style="font-size: 1rem; margin: 16px 0 8px 0; color: #FFF;">📞 Certified Local Tour Guide</h4>
        <p style="font-size: 0.9rem; color: var(--gold-primary); font-weight: 800;">${item.guideContact}</p>
      </div>

      <div style="display: flex; gap: 12px;">
        <button class="hero-pill-btn" style="flex: 1; justify-content: center;" onclick="showToast('Destination added to your travel plan!')">
          ➕ Add to My Trip Itinerary
        </button>
        <button class="btn-card-details" style="padding: 14px 24px;" onclick="closeModal('destination-modal-overlay')">Close</button>
      </div>
    </div>
  `;

  overlay.classList.add('active');
}

// Open Info Modal
function openInfoModal(type) {
  const info = PRACTICAL_INFO[type];
  if (!info) return;

  const overlay = document.getElementById('info-modal-overlay');
  const card = document.getElementById('info-modal-card');
  if (!overlay || !card) return;

  card.innerHTML = `
    <button class="modal-close-btn" onclick="closeModal('info-modal-overlay')">✕</button>
    <div class="modal-content-body" style="padding: 40px;">
      <span class="card-badge" style="margin-bottom: 16px; display: inline-block;">${info.badge}</span>
      <h2 style="font-size: 2rem; margin-bottom: 24px;">${info.title}</h2>
      <div style="line-height: 1.8; color: var(--text-secondary); font-size: 1rem;">
        ${info.content}
      </div>
      <button class="hero-pill-btn" style="margin-top: 32px; width: 100%; justify-content: center;" onclick="closeModal('info-modal-overlay')">Got It</button>
    </div>
  `;

  overlay.classList.add('active');
}

function closeModal(modalId) {
  const overlay = document.getElementById(modalId);
  if (overlay) overlay.classList.remove('active');
}

// Toggle Bookmarks
function toggleBookmark(id, event) {
  event.stopPropagation();
  const index = savedBookmarks.indexOf(id);
  if (index > -1) {
    savedBookmarks.splice(index, 1);
    showToast("Removed from bookmarks");
  } else {
    savedBookmarks.push(id);
    showToast("Added to bookmarks!");
  }
  localStorage.setItem('visitGhanaBookmarks', JSON.stringify(savedBookmarks));
  renderDestinations();
}

// Interactive Itinerary Generator
function generateItinerary() {
  const days = document.getElementById('planner-days').value;
  const style = document.getElementById('planner-style').value;
  const resultsContainer = document.getElementById('itinerary-results');
  
  if (!resultsContainer) return;

  let planHTML = `<h3 style="color: var(--gold-primary); font-size: 1.3rem; margin-bottom: 16px;">Your Custom ${days}-Day Ghana ${style.toUpperCase()} Itinerary</h3>`;

  if (days === "3") {
    planHTML += `
      <div class="day-item">
        <h4>Day 1: Accra Heritage & Tafi Atome Monkey Sanctuary</h4>
        <p>Visit Black Star Square in Accra, followed by an excursion to Tafi Atome Monkey Sanctuary to feed Mona monkeys.</p>
      </div>
      <div class="day-item">
        <h4>Day 2: Winneba Aboakyer & Cape Coast Castle</h4>
        <p>Witness Winneba Effutu traditions and explore UNESCO slave dungeons at Cape Coast Castle over the ocean.</p>
      </div>
      <div class="day-item">
        <h4>Day 3: Crafts & Local Markets</h4>
        <p>Shopping at Accra Arts Centre for wood carvings, beads, and Kente cloth. Farewell Ghanaian Jollof & Live Highlife Music evening.</p>
      </div>
    `;
  } else if (days === "7") {
    planHTML += `
      <div class="day-item">
        <h4>Days 1–2: Accra & Central Coast Fortresses</h4>
        <p>Accra monuments, Winneba Aboakyer traditions, Cape Coast Castle, Kakum Canopy Walk, and Elmina St. George's Castle.</p>
      </div>
      <div class="day-item">
        <h4>Days 3–4: Boabeng-Fiema Monkey Sanctuary & Ashanti Culture</h4>
        <p>Explore Boabeng-Fiema Monkey Sanctuary, Manhyia Palace Museum, and Kente weaving in Bonwire Village.</p>
      </div>
      <div class="day-item">
        <h4>Days 5–7: Volta Region Tafi Atome Monkeys & Wli Waterfalls</h4>
        <p>Feed Mona monkeys at Tafi Atome, hike to Wli Waterfalls, and scale Mount Afadjato.</p>
      </div>
    `;
  } else {
    planHTML += `
      <div class="day-item">
        <h4>Week 1: Coastal Fortresses, Monkey Sanctuaries & Kumasi Royal Heritage</h4>
        <p>Complete historical immersion from Accra through Winneba, Cape Coast, Boabeng-Fiema, and Kumasi.</p>
      </div>
      <div class="day-item">
        <h4>Week 2: Northern Safaris (Mole, Larabanga, Paga) & Volta Waterfalls</h4>
        <p>Tamale Damba horse dances, Mole elephant safaris, Paga sacred crocodiles, Tafi Atome monkeys, and Wli Waterfalls.</p>
      </div>
    `;
  }

  resultsContainer.innerHTML = planHTML;
  resultsContainer.classList.add('active');
  showToast("Custom itinerary generated!");
}

// Toast Notifications
function showToast(msg) {
  let toast = document.getElementById('global-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'global-toast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.innerHTML = `✨ <span>${msg}</span>`;
  toast.classList.add('active');
  setTimeout(() => {
    toast.classList.remove('active');
  }, 3000);
}

// Event Listeners
function setupEventListeners() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      tabBtns.forEach(b => b.classList.remove('active'));
      e.currentTarget.classList.add('active');
      currentCategory = e.currentTarget.dataset.category;
      renderDestinations();
    });
  });

  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value;
      renderDestinations();
    });
  }

  window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
      e.target.classList.remove('active');
    }
  });
}
