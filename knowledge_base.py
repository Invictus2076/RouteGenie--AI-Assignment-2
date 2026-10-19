"""
knowledge_base.py
═══════════════════════════════════════════════════════════════
Travel Planner — World Knowledge Base
Stores facts about cities, hotels, attractions, routes, costs.
These facts populate the PDDL problem files at planning time.

Units and caveats
  • All money is USD. Hotel prices are typical per-night rates and
    attraction prices are typical adult entry or tour prices for a
    foreign visitor. They are planning estimates, not live quotes.
  • Attraction categories match the interest chips in the UI:
    culture | nature | food | beach | nightlife | shopping |
    hiking | photography
  • Every destination offers all four hotel styles:
    budget | midrange | luxury | boutique
  • Flights: explicit fares in FLIGHT_ROUTES / FLIGHT_HOURS win.
    Any other origin→destination pair is estimated from the
    great-circle distance between the two cities' coordinates.
"""

import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ── PDDL identifiers ──────────────────────────────────────────────────

# Letters that Unicode decomposition does not reduce to ASCII.
_TRANSLITERATE = str.maketrans({
    "œ": "oe", "Œ": "OE", "æ": "ae", "Æ": "AE", "ß": "ss",
    "ø": "o", "Ø": "O", "ı": "i", "ł": "l", "Ł": "L", "đ": "d", "Đ": "D",
})

def pddl_ident(text: str) -> str:
    """Turn any name into a safe PDDL identifier.

    Accents are folded to ASCII and every run of characters other than
    a–z / 0–9 becomes a single underscore, so names like
    "Montmartre & Sacré-Cœur" or "Bondi to Coogee (Coastal Walk)"
    produce valid PDDL symbols.
    """
    text = text.translate(_TRANSLITERATE)
    ascii_text = (unicodedata.normalize("NFKD", text)
                  .encode("ascii", "ignore").decode("ascii"))
    ident = re.sub(r"[^a-z0-9]+", "_", ascii_text.lower().replace("'", "")).strip("_")
    if not ident:
        ident = "x"
    if ident[0].isdigit():
        ident = "n_" + ident
    return ident


# ── Data Classes ──────────────────────────────────────────────────────

@dataclass
class Hotel:
    name: str
    style: str          # budget | midrange | luxury | boutique
    cost_per_night: int # USD per night per room
    stars: int
    amenities: List[str] = field(default_factory=list)

    def pddl_id(self) -> str:
        return pddl_ident(self.name)


@dataclass
class Attraction:
    name: str
    category: str       # culture | nature | food | beach | nightlife | shopping | hiking | photography
    entry_cost: int     # USD per person
    duration_hours: float
    tip: str = ""

    def pddl_id(self) -> str:
        return pddl_ident(self.name)


@dataclass
class City:
    name: str
    country: str
    flag: str
    climate: str
    cost_per_day: int       # avg daily spend per person (excl. hotel)
    best_season: str
    transport_mode: str
    timezone: str
    hotels: Dict[str, Hotel] = field(default_factory=dict)
    attractions: List[Attraction] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    lat: float = 0.0        # used to estimate flights not in FLIGHT_ROUTES
    lon: float = 0.0
    region: str = ""

    def pddl_id(self) -> str:
        return pddl_ident(self.name)


HOTEL_STYLES = ("budget", "midrange", "luxury", "boutique")
ATTRACTION_CATEGORIES = ("culture", "nature", "food", "beach", "nightlife",
                         "shopping", "hiking", "photography")


# ── Flight Routes & Costs ─────────────────────────────────────────────
# Hand-checked fares (one-way economy, USD). Pairs not listed here are
# estimated from distance by estimate_flight_cost().

FLIGHT_ROUTES: Dict[tuple, int] = {
    ("new_york",  "paris"):         650,
    ("new_york",  "bali"):         1200,
    ("new_york",  "tokyo"):         800,
    ("new_york",  "rome"):          650,
    ("new_york",  "santorini"):     900,
    ("new_york",  "kyoto"):         850,
    ("new_york",  "machu_picchu"):  700,
    ("new_york",  "london"):        550,
    ("new_york",  "reykjavik"):     400,
    ("new_york",  "lisbon"):        550,
    ("london",    "paris"):          85,
    ("london",    "bali"):         1000,
    ("london",    "tokyo"):         900,
    ("london",    "rome"):          120,
    ("london",    "santorini"):     310,
    ("london",    "kyoto"):         950,
    ("london",    "machu_picchu"):  900,
    ("london",    "barcelona"):     110,
    ("london",    "amsterdam"):      90,
    ("london",    "prague"):        110,
    ("london",    "lisbon"):        130,
    ("london",    "marrakech"):     150,
    ("london",    "reykjavik"):     180,
    ("tokyo",     "bali"):          380,
    ("tokyo",     "paris"):         900,
    ("tokyo",     "rome"):          980,
    ("tokyo",     "santorini"):    1300,
    ("tokyo",     "machu_picchu"): 1500,
    ("tokyo",     "seoul"):         200,
    ("sydney",    "bali"):          350,
    ("sydney",    "tokyo"):         600,
    ("sydney",    "paris"):        1100,
    ("sydney",    "rome"):         1150,
    ("sydney",    "machu_picchu"): 1600,
    ("sydney",    "queenstown"):    250,
    ("dubai",     "paris"):         350,
    ("dubai",     "bali"):          700,
    ("dubai",     "tokyo"):         700,
    ("dubai",     "rome"):          380,
    ("dubai",     "santorini"):     450,
    ("dubai",     "kyoto"):         750,
    ("dubai",     "machu_picchu"): 1200,
    ("dubai",     "maldives"):      300,
    ("paris",     "santorini"):     280,
    ("paris",     "rome"):          140,
    ("delhi",     "dubai"):         200,
    ("delhi",     "london"):        550,
    ("delhi",     "singapore"):     280,
    ("delhi",     "bangkok"):       220,
    ("delhi",     "kathmandu"):     150,
    ("delhi",     "goa"):            70,
    ("delhi",     "leh"):            80,
    ("mumbai",    "dubai"):         180,
    ("mumbai",    "london"):        600,
    ("mumbai",    "singapore"):     280,
    ("mumbai",    "maldives"):      250,
    ("mumbai",    "goa"):            50,
    ("bangalore", "singapore"):     220,
    ("bangalore", "maldives"):      200,
    ("chennai",   "singapore"):     200,
    ("chennai",   "bangkok"):       220,
    ("hyderabad", "dubai"):         200,
    ("kolkata",   "bangkok"):       180,
    ("singapore", "bali"):          150,
    ("singapore", "phuket"):        120,
    ("singapore", "bangkok"):       120,
}

FLIGHT_HOURS: Dict[tuple, float] = {
    ("new_york",  "paris"):        7.0,
    ("new_york",  "bali"):        22.0,
    ("new_york",  "tokyo"):       14.0,
    ("new_york",  "rome"):         9.0,
    ("new_york",  "santorini"):   10.0,
    ("new_york",  "machu_picchu"): 8.5,
    ("london",    "paris"):        1.5,
    ("london",    "bali"):        15.0,
    ("london",    "tokyo"):       11.5,
    ("london",    "rome"):         2.5,
    ("london",    "santorini"):    4.0,
    ("london",    "machu_picchu"):13.0,
    ("tokyo",     "bali"):         7.0,
    ("tokyo",     "paris"):       12.0,
    ("sydney",    "bali"):         5.5,
    ("sydney",    "tokyo"):        9.5,
    ("dubai",     "paris"):        7.0,
    ("paris",     "santorini"):    3.5,
    ("paris",     "rome"):         2.0,
}

AIRLINES: Dict[tuple, str] = {
    ("new_york", "paris"):       "Air France",
    ("new_york", "tokyo"):       "Japan Airlines",
    ("new_york", "bali"):        "Singapore Airlines",
    ("new_york", "rome"):        "ITA Airways",
    ("new_york", "reykjavik"):   "Icelandair",
    ("new_york", "lisbon"):      "TAP Air Portugal",
    ("london",   "paris"):       "Eurostar / British Airways",
    ("london",   "bali"):        "Emirates",
    ("london",   "tokyo"):       "British Airways",
    ("london",   "rome"):        "easyJet / British Airways",
    ("london",   "santorini"):   "easyJet",
    ("london",   "amsterdam"):   "KLM / British Airways",
    ("london",   "reykjavik"):   "Icelandair",
    ("tokyo",    "bali"):        "Garuda Indonesia",
    ("tokyo",    "seoul"):       "Korean Air / ANA",
    ("sydney",   "bali"):        "Jetstar",
    ("sydney",   "queenstown"):  "Air New Zealand / Qantas",
    ("dubai",    "paris"):       "Emirates",
    ("dubai",    "bali"):        "Emirates",
    ("dubai",    "maldives"):    "Emirates / flydubai",
    ("paris",    "santorini"):   "Aegean Airlines",
    ("paris",    "rome"):        "Air France",
    ("delhi",    "kathmandu"):   "Air India / Nepal Airlines",
    ("delhi",    "leh"):         "Air India / IndiGo",
    ("mumbai",   "maldives"):    "IndiGo / Air India",
    ("singapore","bali"):        "Singapore Airlines / Scoot",
}

# Fallback carrier when a pair has no entry in AIRLINES: the main
# airline(s) flying out of the origin city.
HOME_CARRIERS: Dict[str, str] = {
    "new_york":    "Delta / United",
    "los_angeles": "Delta / United / American",
    "london":      "British Airways",
    "paris":       "Air France",
    "tokyo":       "Japan Airlines / ANA",
    "sydney":      "Qantas",
    "dubai":       "Emirates",
    "singapore":   "Singapore Airlines",
    "delhi":       "Air India / IndiGo",
    "mumbai":      "Air India / IndiGo",
    "bangalore":   "Air India / IndiGo",
    "chennai":     "Air India / IndiGo",
    "hyderabad":   "Air India / IndiGo",
    "kolkata":     "Air India / IndiGo",
}


def _pair(table: dict, origin: str, dest: str):
    if (origin, dest) in table:
        return table[(origin, dest)]
    return table.get((dest, origin))


def _coords(city_id: str) -> Optional[Tuple[float, float]]:
    if city_id in CITIES and (CITIES[city_id].lat or CITIES[city_id].lon):
        return CITIES[city_id].lat, CITIES[city_id].lon
    if city_id in ORIGIN_CITIES and "lat" in ORIGIN_CITIES[city_id]:
        o = ORIGIN_CITIES[city_id]
        return o["lat"], o["lon"]
    return None


def distance_km(origin: str, dest: str) -> Optional[float]:
    """Great-circle distance between two city IDs, or None if unknown."""
    a, b = _coords(origin), _coords(dest)
    if a is None or b is None:
        return None
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 2 * 6371 * math.asin(math.sqrt(h))


def estimate_flight_cost(km: float) -> int:
    """Rough one-way economy fare in USD for a given distance."""
    return int(round(max(50, 35 + 0.075 * km), -1))


def estimate_flight_hours(km: float) -> float:
    """Rough door-to-gate flight time; very long trips assume one stop."""
    hours = km / 780 + 0.5
    if km > 9000:
        hours += 3.0
    return round(hours * 2) / 2


def get_flight_cost(origin: str, dest: str) -> Optional[int]:
    """Return one-way flight cost (USD) between two city PDDL IDs, or None if unknown."""
    fare = _pair(FLIGHT_ROUTES, origin, dest)
    if fare is not None:
        return fare
    km = distance_km(origin, dest)
    return estimate_flight_cost(km) if km is not None else None


def get_flight_hours(origin: str, dest: str) -> float:
    hours = _pair(FLIGHT_HOURS, origin, dest)
    if hours is not None:
        return hours
    km = distance_km(origin, dest)
    return estimate_flight_hours(km) if km is not None else 9.0


def get_airline(origin: str, dest: str) -> str:
    return (_pair(AIRLINES, origin, dest)
            or HOME_CARRIERS.get(origin)
            or HOME_CARRIERS.get(dest)
            or "International Airlines")


# ── City Knowledge Base ───────────────────────────────────────────────

CITIES: Dict[str, City] = {

    # ═══ Europe ═══════════════════════════════════════════════════════

    "paris": City(
        name="Paris", country="France", flag="🇫🇷",
        climate="Temperate Oceanic", cost_per_day=200,
        best_season="Apr–Jun, Sep–Oct", transport_mode="Metro",
        timezone="CET (UTC+1)", lat=48.857, lon=2.352, region="Europe",
        hotels={
            "budget":   Hotel("Generator Paris",      "budget",   60,  3, ["WiFi","Bar"]),
            "midrange": Hotel("Hotel du Marais",      "midrange", 160, 4, ["WiFi","Breakfast","Concierge"]),
            "luxury":   Hotel("Le Bristol Paris",     "luxury",   750, 5, ["Spa","Pool","Michelin Restaurant","Butler"]),
            "boutique": Hotel("Maison Souquet",       "boutique", 380, 5, ["Library Bar","Courtyard","Art Collection"]),
        },
        attractions=[
            Attraction("Eiffel Tower",        "culture",  30, 2.5, "Book skip-the-line tickets. Visit at sunset."),
            Attraction("Louvre Museum",        "culture",  22, 4.0, "Start at Denon wing — Mona Lisa, Venus de Milo."),
            Attraction("Notre-Dame Cathedral", "culture",   0, 1.5, "Reopened Dec 2024. Free entry — reserve a time slot online to skip the queue."),
            Attraction("Musée d'Orsay",        "culture",  16, 3.0, "Best Impressionist collection in the world."),
            Attraction("Palace of Versailles", "culture",  21, 4.5, "Take the RER C train. Arrive before 9 AM."),
            Attraction("Montmartre & Sacré-Cœur","culture",0, 2.0, "Walk the cobblestone streets. Artists quarter."),
            Attraction("Seine River Cruise",   "photography",17,1.5, "Bateaux Parisiens evening cruise highly recommended."),
            Attraction("Champs-Élysées",       "shopping",  0, 2.0, "Walk from Arc de Triomphe to Place de la Concorde."),
            Attraction("Sainte-Chapelle",      "culture",  13, 1.0, "Stunning Gothic stained glass. Hidden gem."),
            Attraction("Le Marais Food Walk",  "food",     15, 2.0, "Falafel on Rue des Rosiers, then Marché des Enfants Rouges."),
        ],
        tags=["culture","food","shopping","photography","romance"]
    ),

    "rome": City(
        name="Rome", country="Italy", flag="🇮🇹",
        climate="Mediterranean", cost_per_day=170,
        best_season="Apr–Jun, Sep–Oct", transport_mode="Bus & Walking",
        timezone="CET (UTC+1)", lat=41.903, lon=12.496, region="Europe",
        hotels={
            "budget":   Hotel("Alessandro Palace Hostel","budget",  50, 2, ["Rooftop Bar","Tours"]),
            "midrange": Hotel("Hotel Capo d'Africa",    "midrange",155, 4, ["Rooftop Pool","Colosseum View"]),
            "luxury":   Hotel("Hotel de Russie",        "luxury",  680, 5, ["Secret Garden","Spa","Le Jardin de Russie"]),
            "boutique": Hotel("Portrait Roma",          "boutique",420, 5, ["Piazza di Spagna Views","Salvatore Ferragamo"]),
        },
        attractions=[
            Attraction("Colosseum & Roman Forum",   "culture",  18, 3.5, "Book combined ticket. Avoid midday heat."),
            Attraction("Vatican Museums & Sistine Chapel","culture",20,4.0,"Book 6+ weeks ahead. Join early-morning tour."),
            Attraction("Trevi Fountain",            "photography",0,0.5, "Visit at midnight to avoid the crowds."),
            Attraction("Pantheon",                  "culture",   5, 1.0, "Engineering marvel — 2000 years old."),
            Attraction("Borghese Gallery",          "culture",  15, 2.0, "Timed tickets mandatory. Bernini sculptures unmissable."),
            Attraction("Trastevere Neighborhood",   "nightlife", 0, 2.5, "Medieval alleyways. Best neighbourhood for dinner."),
            Attraction("Campo de' Fiori Market",    "food",      0, 1.0, "Morning market. Fresh produce, flowers, street food."),
            Attraction("Palatine Hill",             "culture",  18, 1.5, "Best views over the Forum. Included in Colosseum ticket."),
        ],
        tags=["culture","food","history","photography","romance"]
    ),

    "santorini": City(
        name="Santorini", country="Greece", flag="🇬🇷",
        climate="Mediterranean", cost_per_day=220,
        best_season="May–Oct", transport_mode="ATV & Bus & Cable Car",
        timezone="EET (UTC+2)", lat=36.393, lon=25.461, region="Europe",
        hotels={
            "budget":   Hotel("Fira Backpackers",        "budget",  55, 2, ["Pool","Caldera Views"]),
            "midrange": Hotel("Katikies Cliff Side",    "midrange",280, 4, ["Infinity Pool","Breakfast","Sea View"]),
            "luxury":   Hotel("Mystique Hotel Santorini","luxury",  900, 5, ["Plunge Pools","Thalasso Spa","Iconic Suites"]),
            "boutique": Hotel("Andronis Boutique Hotel","boutique", 500, 5, ["Cave Suites","Private Terrace","Sunset Views"]),
        },
        attractions=[
            Attraction("Oia Sunset Viewpoint",      "photography",0, 2.0, "Arrive 2 hours early for a good spot. Worth every minute."),
            Attraction("Akrotiri Ruins",             "culture",   14, 2.0, "Bronze Age Pompeii. Well-preserved — visually stunning."),
            Attraction("Red Beach",                  "beach",      0, 2.0, "15-min walk from Akrotiri. Dramatic red volcanic cliffs."),
            Attraction("Caldera Boat Tour",          "nature",    80, 4.0, "Sail to volcano, hot springs, and Thirassia island."),
            Attraction("Santorini Wine Tour",        "food",      50, 3.0, "Visit Santo Wines & Venetsanos. Assyrtiko wine tasting."),
            Attraction("Pyrgos Village",             "culture",    0, 1.5, "Highest point on island. Authentic non-touristy experience."),
            Attraction("Perissa Black Sand Beach",  "beach",      0, 3.0, "Volcanic black sand. Many beach bars and tavernas."),
            Attraction("Fira to Oia Caldera Hike",  "hiking",     0, 4.0, "10 km cliff-top trail. Start early and carry water."),
        ],
        tags=["beach","photography","food","romance","sunsets"]
    ),

    "london": City(
        name="London", country="UK", flag="🇬🇧",
        climate="Temperate Oceanic", cost_per_day=200,
        best_season="May–Sep", transport_mode="Tube & Bus (contactless)",
        timezone="GMT (UTC+0)", lat=51.507, lon=-0.128, region="Europe",
        hotels={
            "budget":   Hotel("Generator London",        "budget",   55, 2, ["Bar","Late Check-in","Social Events"]),
            "midrange": Hotel("The Hoxton Holborn",      "midrange", 230, 4, ["Free Breakfast Bag","Rooftop","Lobby Café"]),
            "luxury":   Hotel("The Savoy",               "luxury",   850, 5, ["Thames Views","American Bar","Afternoon Tea"]),
            "boutique": Hotel("The Zetter Townhouse Clerkenwell","boutique",350,4,["Cocktail Lounge","Antique Interiors"]),
        },
        attractions=[
            Attraction("British Museum",             "culture",    0, 3.0, "Free. Rosetta Stone and Parthenon sculptures — go at opening."),
            Attraction("Tower of London",            "culture",   40, 3.0, "See the Crown Jewels first, before the queues build."),
            Attraction("Westminster Abbey",          "culture",   35, 1.5, "Book online. Evensong service is free and atmospheric."),
            Attraction("Borough Market",             "food",       0, 1.5, "Go hungry on a weekday morning. Try the raclette."),
            Attraction("Camden Market",              "shopping",   0, 2.5, "Street food, vintage stalls and canal-side views."),
            Attraction("West End Show",              "nightlife", 60, 3.0, "TKTS booth in Leicester Square sells same-day discounts."),
            Attraction("Hyde Park & Kensington Gardens","nature",  0, 2.0, "Rent a pedal boat on the Serpentine in summer."),
            Attraction("Sky Garden",                 "photography",0, 1.0, "Free, but tickets are released online about 3 weeks ahead."),
        ],
        tags=["culture","food","shopping","nightlife","history"]
    ),

    "barcelona": City(
        name="Barcelona", country="Spain", flag="🇪🇸",
        climate="Mediterranean", cost_per_day=150,
        best_season="May–Jun, Sep–Oct", transport_mode="Metro & Walking",
        timezone="CET (UTC+1)", lat=41.385, lon=2.173, region="Europe",
        hotels={
            "budget":   Hotel("Generator Barcelona",     "budget",   45, 2, ["Rooftop Terrace","Bar"]),
            "midrange": Hotel("Praktik Rambla",          "midrange", 140, 3, ["Modernista Building","Terrace"]),
            "luxury":   Hotel("Hotel Arts Barcelona",    "luxury",   500, 5, ["Beachfront","Two-Michelin-Star Dining","Spa"]),
            "boutique": Hotel("Casa Bonay",              "boutique", 220, 4, ["Rooftop Bar","Design Rooms","Café"]),
        },
        attractions=[
            Attraction("Sagrada Família",            "culture",   30, 2.0, "Book a timed ticket online. Tower access costs extra."),
            Attraction("Park Güell",                 "culture",   13, 2.0, "Timed entry to the monumental zone. Go early for soft light."),
            Attraction("Casa Batlló",                "culture",   35, 1.5, "Gaudí's dragon-roofed house. Evening visits are quieter."),
            Attraction("Gothic Quarter",             "culture",    0, 2.0, "Get lost in the lanes around the cathedral."),
            Attraction("La Boqueria Market",         "food",       0, 1.0, "Skip the front stalls; eat at the counter bars inside."),
            Attraction("Barceloneta Beach",          "beach",      0, 3.0, "Watch your belongings. Seafood paella nearby."),
            Attraction("Montjuïc & Magic Fountain",  "photography",0, 2.0, "Check the fountain schedule — shows pause in droughts."),
            Attraction("Tapas Crawl in El Born",     "nightlife", 30, 3.0, "Locals eat late — start after 9 PM."),
        ],
        tags=["culture","beach","food","nightlife","architecture"]
    ),

    "amsterdam": City(
        name="Amsterdam", country="Netherlands", flag="🇳🇱",
        climate="Temperate Oceanic", cost_per_day=170,
        best_season="Apr–May (Tulips), Jun–Aug", transport_mode="Tram & Bicycle",
        timezone="CET (UTC+1)", lat=52.368, lon=4.904, region="Europe",
        hotels={
            "budget":   Hotel("ClinkNOORD",              "budget",   45, 2, ["Free Ferry Access","Bar","Kitchen"]),
            "midrange": Hotel("Hotel V Nesplein",        "midrange", 170, 4, ["Central Location","Restaurant"]),
            "luxury":   Hotel("Waldorf Astoria Amsterdam","luxury",  800, 5, ["Canal Palaces","Michelin Dining","Spa"]),
            "boutique": Hotel("Pulitzer Amsterdam",      "boutique", 400, 5, ["25 Canal Houses","Garden","Bike Rental"]),
        },
        attractions=[
            Attraction("Rijksmuseum",                "culture",   25, 3.0, "Rembrandt's Night Watch. Book a morning slot."),
            Attraction("Van Gogh Museum",            "culture",   22, 2.0, "Timed tickets online only — they sell out."),
            Attraction("Anne Frank House",           "culture",   16, 1.5, "Tickets release online 6 weeks ahead. No walk-ups."),
            Attraction("Canal Cruise",               "photography",20,1.0, "Choose a small open boat over the big glass ones."),
            Attraction("Jordaan & Nine Streets",     "shopping",   0, 2.0, "Independent boutiques and brown cafés."),
            Attraction("Keukenhof Gardens",          "nature",    20, 4.0, "Open mid-March to mid-May only. Combine with bike ride."),
            Attraction("Vondelpark",                 "nature",     0, 1.5, "Rent a bike and join the locals."),
            Attraction("Foodhallen",                 "food",      20, 1.5, "Indoor food hall in an old tram depot."),
        ],
        tags=["culture","nature","shopping","nightlife","cycling"]
    ),

    "prague": City(
        name="Prague", country="Czech Republic", flag="🇨🇿",
        climate="Continental", cost_per_day=100,
        best_season="May–Sep, Dec (Christmas Markets)", transport_mode="Tram & Walking",
        timezone="CET (UTC+1)", lat=50.076, lon=14.438, region="Europe",
        hotels={
            "budget":   Hotel("Czech Inn",               "budget",   30, 2, ["Bar","Lounge","24h Reception"]),
            "midrange": Hotel("Hotel Josef",             "midrange", 140, 4, ["Design Rooms","Garden","Old Town"]),
            "luxury":   Hotel("Four Seasons Hotel Prague","luxury",  600, 5, ["Charles Bridge Views","Spa","Riverfront"]),
            "boutique": Hotel("Aria Hotel Prague",       "boutique", 300, 5, ["Music-Themed Rooms","Rooftop Terrace","Library"]),
        },
        attractions=[
            Attraction("Prague Castle",              "culture",   18, 3.0, "Largest ancient castle complex. See St Vitus Cathedral."),
            Attraction("Charles Bridge",             "photography",0, 1.0, "Go at sunrise to have it almost to yourself."),
            Attraction("Old Town Square & Astronomical Clock","culture",0,1.0,"The clock performs on the hour, 9 AM–11 PM."),
            Attraction("Jewish Quarter",             "culture",   22, 2.0, "One ticket covers the synagogues and old cemetery."),
            Attraction("Petřín Hill",                "nature",     0, 2.0, "Funicular up, walk down through the orchards."),
            Attraction("Lennon Wall",                "photography",0, 0.5, "Ever-changing graffiti tribute in Malá Strana."),
            Attraction("Czech Beer Hall Dinner",     "food",      15, 2.0, "Try tank Pilsner and svíčková at a traditional hall."),
            Attraction("Vyšehrad Fortress",          "culture",    0, 1.5, "Quiet hilltop fort with river views — few tourists."),
        ],
        tags=["culture","photography","food","history","budget-friendly"]
    ),

    "interlaken": City(
        name="Interlaken", country="Switzerland", flag="🇨🇭",
        climate="Alpine", cost_per_day=220,
        best_season="Jun–Sep (Hiking), Dec–Mar (Skiing)", transport_mode="Swiss Travel Pass Trains",
        timezone="CET (UTC+1)", lat=46.686, lon=7.863, region="Europe",
        hotels={
            "budget":   Hotel("Balmers Hostel",          "budget",   50, 2, ["Bar","Adventure Desk","Kitchen"]),
            "midrange": Hotel("Hotel Interlaken",        "midrange", 220, 4, ["Historic Building","Garden","Restaurant"]),
            "luxury":   Hotel("Victoria-Jungfrau Grand Hotel & Spa","luxury",700,5,["Jungfrau Views","Spa","Fine Dining"]),
            "boutique": Hotel("The Hey Hotel",           "boutique", 250, 4, ["Design Rooms","Bar","Central"]),
        },
        attractions=[
            Attraction("Jungfraujoch Top of Europe", "photography",230,8.0, "Check the summit webcam first. Swiss Travel Pass gives a discount."),
            Attraction("Harder Kulm",                "photography", 40,1.5, "Funicular to a viewpoint over both lakes."),
            Attraction("Lauterbrunnen Valley",       "nature",       0,3.0, "72 waterfalls. Walk to Staubbach Falls from the station."),
            Attraction("Lake Brienz Boat Cruise",    "nature",      40,2.0, "Free with the Swiss Travel Pass. Turquoise water."),
            Attraction("Bachalpsee Hike from First", "hiking",      70,4.0, "Gondola to First, then an easy hike to the alpine lake."),
            Attraction("Paragliding over Interlaken","nature",     180,1.5, "Tandem flights land in the town park. Book a morning slot."),
            Attraction("Schilthorn Piz Gloria",      "photography",110,4.0, "Revolving restaurant from a James Bond film."),
        ],
        tags=["nature","hiking","photography","adventure","mountains"]
    ),

    "reykjavik": City(
        name="Reykjavik", country="Iceland", flag="🇮🇸",
        climate="Subarctic", cost_per_day=200,
        best_season="Jun–Aug (Midnight Sun), Sep–Mar (Northern Lights)", transport_mode="Rental Car & Tours",
        timezone="GMT (UTC+0)", lat=64.147, lon=-21.942, region="Europe",
        hotels={
            "budget":   Hotel("Kex Hostel",              "budget",   60, 2, ["Gastropub","Ocean Views","Live Music"]),
            "midrange": Hotel("Fosshotel Reykjavik",     "midrange", 200, 4, ["Restaurant","Bar","Central"]),
            "luxury":   Hotel("The Reykjavik EDITION",   "luxury",   600, 5, ["Harbour Views","Spa","Rooftop Bar"]),
            "boutique": Hotel("Hotel Borg",              "boutique", 350, 4, ["Art Deco","Spa","Old Town Square"]),
        },
        attractions=[
            Attraction("Golden Circle",              "nature",    80, 8.0, "Thingvellir, Geysir and Gullfoss in one day trip."),
            Attraction("Blue Lagoon",                "nature",    90, 3.0, "Book a time slot in advance. Go straight from the airport."),
            Attraction("Northern Lights Tour",       "photography",70,4.0, "Sep–Mar only. Check the aurora forecast; most tours rebook free."),
            Attraction("Hallgrímskirkja Tower",      "culture",   10, 1.0, "Lift to the top for city views."),
            Attraction("South Coast & Reynisfjara",  "beach",    100,10.0, "Black-sand beach. Stay well back — sneaker waves are deadly."),
            Attraction("Harpa Concert Hall",         "culture",    0, 1.0, "Free to walk in. Glass facade glows at night."),
            Attraction("Whale Watching",             "nature",    90, 3.0, "Departs from the Old Harbour. Dress warmly year-round."),
        ],
        tags=["nature","photography","adventure","hiking"]
    ),

    "lisbon": City(
        name="Lisbon", country="Portugal", flag="🇵🇹",
        climate="Mediterranean", cost_per_day=120,
        best_season="Mar–Jun, Sep–Oct", transport_mode="Tram & Metro",
        timezone="WET (UTC+0)", lat=38.722, lon=-9.139, region="Europe",
        hotels={
            "budget":   Hotel("Lisbon Destination Hostel","budget",  35, 2, ["Inside Rossio Station","Free Breakfast"]),
            "midrange": Hotel("Hotel Avenida Palace",    "midrange", 180, 5, ["Belle Époque Building","Central"]),
            "luxury":   Hotel("Four Seasons Hotel Ritz Lisbon","luxury",650,5,["Rooftop Track","Spa","Art Collection"]),
            "boutique": Hotel("Memmo Alfama",            "boutique", 250, 4, ["Infinity Pool","River Views","Wine Bar"]),
        },
        attractions=[
            Attraction("Belém Tower & Jerónimos Monastery","culture",18,3.0,"Finish with custard tarts at Pastéis de Belém."),
            Attraction("Alfama & São Jorge Castle",  "culture",   15, 3.0, "Wander downhill from the castle. Fado bars at night."),
            Attraction("Tram 28",                    "culture",    3, 1.0, "Ride early from Martim Moniz. Mind pickpockets."),
            Attraction("LX Factory",                 "shopping",   0, 2.0, "Old factory turned design market. Sunday market best."),
            Attraction("Time Out Market",            "food",      20, 1.5, "Many Lisbon chefs under one roof."),
            Attraction("Sintra Day Trip",            "culture",   30, 8.0, "Pena Palace needs a timed ticket. Train from Rossio."),
            Attraction("Bairro Alto Nightlife",      "nightlife",  0, 3.0, "Street drinking culture; busiest after 11 PM."),
            Attraction("Miradouro da Senhora do Monte","photography",0,1.0,"Best sunset viewpoint in the city."),
        ],
        tags=["culture","food","nightlife","photography","budget-friendly"]
    ),

    # ═══ Asia ═════════════════════════════════════════════════════════

    "tokyo": City(
        name="Tokyo", country="Japan", flag="🇯🇵",
        climate="Temperate", cost_per_day=180,
        best_season="Mar–May (Cherry Blossom), Sep–Nov",
        transport_mode="Subway & JR Pass", timezone="JST (UTC+9)",
        lat=35.676, lon=139.650, region="Asia",
        hotels={
            "budget":   Hotel("Khaosan Tokyo Hostel",   "budget",   45, 2, ["Capsule Option","Common Area"]),
            "midrange": Hotel("Shinjuku Granbell Hotel","midrange", 140, 4, ["WiFi","Bar","City View"]),
            "luxury":   Hotel("The Peninsula Tokyo",   "luxury",   700, 5, ["Spa","Helicopter Pad","5 Restaurants"]),
            "boutique": Hotel("Trunk Hotel Shibuya",   "boutique", 300, 4, ["Social Lounge","Design Rooms","Rooftop"]),
        },
        attractions=[
            Attraction("Shibuya Crossing",         "photography",0, 1.0, "Visit at night for full impact. Shibuya Sky has the best view."),
            Attraction("Senso-ji Temple",           "culture",   0, 1.5, "Asakusa district. Nakamise Shopping Street nearby."),
            Attraction("teamLab Borderless",        "culture",  25, 2.5, "Now at Azabudai Hills. Book weeks ahead. Immersive digital art."),
            Attraction("Tsukiji Outer Market",      "food",      0, 2.0, "Best sushi breakfast at 6 AM. Omakase counters."),
            Attraction("Shinjuku Gyoen Garden",     "nature",    4, 2.0, "Best cherry blossom spot. Peaceful urban escape."),
            Attraction("Akihabara Electric Town",   "shopping",  0, 2.5, "Anime, gaming, electronics wonderland."),
            Attraction("Tokyo Skytree",             "culture",  20, 1.5, "Buy tickets online. Views reach Mt. Fuji on clear days."),
            Attraction("Harajuku Takeshita Street", "shopping",  0, 1.5, "Fashion subcultures. Crepe shops everywhere."),
            Attraction("Meiji Jingu Shrine",        "culture",   0, 1.0, "Forested sanctuary in central Tokyo. Very serene."),
            Attraction("Golden Gai",                "nightlife", 0, 2.5, "Tiny bars in six alleys. Some charge a seat fee."),
        ],
        tags=["culture","food","shopping","nightlife","photography","anime"]
    ),

    "kyoto": City(
        name="Kyoto", country="Japan", flag="🇯🇵",
        climate="Temperate", cost_per_day=160,
        best_season="Mar–May (Sakura), Oct–Nov (Koyo)",
        transport_mode="Bus & Bicycle", timezone="JST (UTC+9)",
        lat=35.012, lon=135.768, region="Asia",
        hotels={
            "budget":   Hotel("Piece Hostel Kyoto",    "budget",   40, 2, ["Bike Rental","Common Kitchen"]),
            "midrange": Hotel("Hotel Granvia Kyoto",  "midrange", 130, 4, ["Station Access","Restaurants"]),
            "luxury":   Hotel("Aman Kyoto",           "luxury",  1200, 5, ["Secret Garden","Onsen","Forest Retreat"]),
            "boutique": Hotel("Tawaraya Ryokan",      "boutique", 650, 5, ["Traditional Kaiseki","Tatami Rooms","300 Years Old"]),
        },
        attractions=[
            Attraction("Fushimi Inari Taisha",     "hiking",    0, 3.0, "Thousands of torii gates. Go at 6 AM — trails empty and magical."),
            Attraction("Arashiyama Bamboo Grove",  "nature",    0, 1.5, "Arrive before 7 AM. Stunning, meditative walk."),
            Attraction("Kinkaku-ji (Gold Pavilion)","culture",  4, 1.0, "Zen temple coated in gold leaf. Reflective pond iconic."),
            Attraction("Gion Geisha District",     "culture",   0, 2.0, "Evening stroll on Hanamikoji. Don't photograph maiko up close."),
            Attraction("Nishiki Market",            "food",      0, 2.0, "Kyoto's Kitchen — 400-year-old covered market."),
            Attraction("Philosopher's Path",        "nature",    0, 1.5, "2km canal walk lined with cherry trees."),
            Attraction("Nijo Castle",              "culture",   9, 2.0, "Shogun palace with 'nightingale floors' that squeak."),
            Attraction("Ryoan-ji Zen Garden",      "culture",   4, 1.0, "Most famous karesansui rock garden in Japan."),
        ],
        tags=["culture","photography","nature","food","tradition"]
    ),

    "bali": City(
        name="Bali", country="Indonesia", flag="🇮🇩",
        climate="Tropical", cost_per_day=80,
        best_season="Apr–Oct", transport_mode="Scooter & Private Driver",
        timezone="WITA (UTC+8)", lat=-8.409, lon=115.189, region="Asia",
        hotels={
            "budget":   Hotel("Kuta Beach Hostel",   "budget",   25, 2, ["Pool","Common Kitchen"]),
            "midrange": Hotel("The Layar Villa",     "midrange", 120, 4, ["Private Pool","Breakfast","Garden"]),
            "luxury":   Hotel("COMO Uma Ubud",       "luxury",   550, 5, ["Spa","Yoga Pavilion","Jungle View"]),
            "boutique": Hotel("Alaya Resort Ubud",   "boutique", 200, 4, ["Rice Field View","Cooking Class","Pool"]),
        },
        attractions=[
            Attraction("Tanah Lot Temple",       "culture",    5, 2.0, "Iconic sea temple. Best at sunset."),
            Attraction("Ubud Rice Terraces",     "nature",     2, 2.0, "Tegalalang — arrive at dawn before crowds."),
            Attraction("Sacred Monkey Forest",   "nature",     6, 1.5, "Keep sunglasses and snacks hidden. Don't feed the macaques."),
            Attraction("Mount Batur Sunrise Trek","hiking",   40, 5.0, "Start at 2 AM. Guide required. Sunrise unforgettable."),
            Attraction("Uluwatu Temple",         "culture",    3, 1.5, "Clifftop temple with Kecak fire dance at dusk (extra ticket)."),
            Attraction("Seminyak Beach",         "beach",      0, 3.0, "Beach clubs like Potato Head for sunset."),
            Attraction("Tirta Empul Temple",     "culture",    3, 1.5, "Holy spring water purification ritual. Bring a sarong."),
            Attraction("Nusa Penida Day Trip",   "beach",     45, 8.0, "Kelingking Beach — most dramatic view in Bali."),
            Attraction("Balinese Cooking Class", "food",      30, 4.0, "Morning market visit, then cook in a family compound."),
        ],
        tags=["beach","culture","nature","hiking","wellness"]
    ),

    "singapore": City(
        name="Singapore", country="Singapore", flag="🇸🇬",
        climate="Tropical", cost_per_day=150,
        best_season="Feb–Apr (any time is fine)", transport_mode="MRT",
        timezone="SGT (UTC+8)", lat=1.290, lon=103.852, region="Asia",
        hotels={
            "budget":   Hotel("The Pod Boutique Capsule Hotel","budget",60,3,["Capsule Pods","Rooftop","Breakfast"]),
            "midrange": Hotel("Carlton Hotel Singapore", "midrange", 200, 4, ["Pool","Gym","Civic District"]),
            "luxury":   Hotel("Marina Bay Sands",        "luxury",   650, 5, ["Rooftop Infinity Pool","SkyPark","Casino"]),
            "boutique": Hotel("The Warehouse Hotel",     "boutique", 300, 4, ["Riverside","Converted Godown","Infinity Pool"]),
        },
        attractions=[
            Attraction("Gardens by the Bay",         "nature",    28, 3.0, "Supertree light show at 7:45 and 8:45 PM is free."),
            Attraction("Marina Bay Sands SkyPark",   "photography",25,1.0, "Go just before sunset for day-to-night views."),
            Attraction("Maxwell & Lau Pa Sat Hawker Centres","food",8,1.5,"Michelin-listed hawkers for under $5 a dish."),
            Attraction("Little India & Chinatown",   "culture",    0, 2.5, "Sri Veeramakaliamman Temple, then Buddha Tooth Relic Temple."),
            Attraction("Singapore Botanic Gardens",  "nature",     0, 2.0, "UNESCO site. National Orchid Garden costs about $15."),
            Attraction("Clarke Quay",                "nightlife",  0, 3.0, "Riverside bars. Happy hours keep drink prices sane."),
            Attraction("Orchard Road",               "shopping",   0, 3.0, "Malls end to end. Tourist GST refund at the airport."),
            Attraction("Night Safari",               "nature",    55, 3.0, "World's first nocturnal zoo. Take the tram, then walk trails."),
        ],
        tags=["food","shopping","culture","nature","family"]
    ),

    "bangkok": City(
        name="Bangkok", country="Thailand", flag="🇹🇭",
        climate="Tropical", cost_per_day=70,
        best_season="Nov–Feb", transport_mode="BTS Skytrain & River Boat",
        timezone="ICT (UTC+7)", lat=13.756, lon=100.502, region="Asia",
        hotels={
            "budget":   Hotel("Lub d Bangkok Silom",     "budget",   25, 2, ["Social Bar","Pods","Lockers"]),
            "midrange": Hotel("Chatrium Hotel Riverside Bangkok","midrange",110,5,["River Views","Pool","Shuttle Boat"]),
            "luxury":   Hotel("Mandarin Oriental Bangkok","luxury",  600, 5, ["Riverside","Legendary Spa","Bamboo Bar"]),
            "boutique": Hotel("The Siam",                "boutique", 450, 5, ["Art Deco Villas","Muay Thai Ring","River Pier"]),
        },
        attractions=[
            Attraction("Grand Palace & Wat Phra Kaew","culture",  15, 3.0, "Cover shoulders and knees. Ignore 'palace is closed' scams."),
            Attraction("Wat Pho",                    "culture",    9, 1.5, "Giant reclining Buddha. Massage school on site."),
            Attraction("Wat Arun",                   "culture",    3, 1.0, "Cross by ferry. Best seen at sunset from the opposite bank."),
            Attraction("Chatuchak Weekend Market",   "shopping",   0, 4.0, "Saturday and Sunday only. 15,000 stalls — go early."),
            Attraction("Yaowarat Chinatown Street Food","food",   10, 2.5, "Comes alive after dark. Try the seafood and mango sticky rice."),
            Attraction("Chao Phraya River Boat",     "photography",1, 1.5, "Orange-flag express boats cost less than a dollar."),
            Attraction("Khao San Road",              "nightlife",  0, 3.0, "Backpacker street. Rooftop bars in Silom are calmer."),
            Attraction("Damnoen Saduak Floating Market","culture",20,5.0, "Go early. Touristy, but photogenic."),
        ],
        tags=["food","culture","shopping","nightlife","budget-friendly"]
    ),

    "phuket": City(
        name="Phuket", country="Thailand", flag="🇹🇭",
        climate="Tropical", cost_per_day=80,
        best_season="Nov–Apr", transport_mode="Taxi & Scooter",
        timezone="ICT (UTC+7)", lat=7.880, lon=98.392, region="Asia",
        hotels={
            "budget":   Hotel("Lub d Phuket Patong",     "budget",   30, 3, ["Muay Thai Ring","Pool","Bar"]),
            "midrange": Hotel("Holiday Inn Resort Phuket","midrange",120, 4, ["Pools","Kids Club","Near Beach"]),
            "luxury":   Hotel("Trisara",                 "luxury",   800, 5, ["Private Pool Villas","Ocean Views","Fine Dining"]),
            "boutique": Hotel("Keemala",                 "boutique", 500, 5, ["Tree-House Pool Villas","Rainforest","Spa"]),
        },
        attractions=[
            Attraction("Phi Phi Islands Day Trip",   "beach",     60, 9.0, "Maya Bay closes some months to recover — check before booking."),
            Attraction("Big Buddha",                 "culture",    0, 1.5, "45m marble statue with island views. Dress modestly."),
            Attraction("Phuket Old Town",            "culture",    0, 2.0, "Sino-Portuguese shophouses. Sunday walking street market."),
            Attraction("Kata & Karon Beaches",       "beach",      0, 3.0, "Calmer than Patong. Red flags mean rip currents."),
            Attraction("Phang Nga Bay Sea Canoe",    "nature",    60, 8.0, "Paddle into limestone caves and James Bond Island."),
            Attraction("Bangla Road",                "nightlife",  0, 3.0, "Patong's neon party street. Agree prices before ordering."),
            Attraction("Promthep Cape",              "photography",0, 1.0, "Island's famous sunset point. Arrive 45 minutes early."),
        ],
        tags=["beach","nightlife","nature","photography"]
    ),

    "maldives": City(
        name="Maldives", country="Maldives", flag="🇲🇻",
        climate="Tropical", cost_per_day=120,
        best_season="Nov–Apr", transport_mode="Speedboat & Seaplane",
        timezone="MVT (UTC+5)", lat=4.175, lon=73.509, region="Asia",
        hotels={
            "budget":   Hotel("Kaani Village & Spa Maafushi","budget",90,3,["Local Island","Excursion Desk","Bikini Beach Nearby"]),
            "midrange": Hotel("Adaaran Select Hudhuranfushi","midrange",300,4,["Surf Break","All-Inclusive Option","House Reef"]),
            "luxury":   Hotel("Soneva Fushi",            "luxury",  2000, 5, ["Barefoot Luxury","Observatory","Private Villas"]),
            "boutique": Hotel("Gili Lankanfushi",        "boutique",1200, 5, ["Overwater Villas","Personal Butler","No Shoes"]),
        },
        attractions=[
            Attraction("House Reef Snorkelling",     "nature",     0, 2.0, "Most resorts lend gear free. Reef-safe sunscreen only."),
            Attraction("Sandbank Picnic",            "beach",     60, 3.0, "Private strip of sand mid-ocean. Bring shade."),
            Attraction("Dolphin Sunset Cruise",      "nature",    70, 2.0, "Spinner dolphins are seen on most evenings."),
            Attraction("Whale Shark Excursion",      "nature",   150, 6.0, "South Ari Atoll has whale sharks year-round."),
            Attraction("Malé City Tour",             "culture",    0, 2.0, "Old Friday Mosque, fish market. Dress modestly."),
            Attraction("Bioluminescent Beach Night", "photography",0, 1.0, "Glowing plankton show best on dark, moonless nights; not guaranteed."),
        ],
        tags=["beach","nature","romance","wellness"]
    ),

    "dubai": City(
        name="Dubai", country="UAE", flag="🇦🇪",
        climate="Desert", cost_per_day=180,
        best_season="Nov–Mar", transport_mode="Metro & Taxi",
        timezone="GST (UTC+4)", lat=25.205, lon=55.271, region="Middle East",
        hotels={
            "budget":   Hotel("Rove Downtown",           "budget",   90, 3, ["Pool","Burj Khalifa Views","24h Gym"]),
            "midrange": Hotel("Vida Downtown",           "midrange", 200, 4, ["Pool","Walk to Dubai Mall","Café"]),
            "luxury":   Hotel("Burj Al Arab Jumeirah",   "luxury",  1500, 5, ["Duplex Suites","Butler","Private Beach"]),
            "boutique": Hotel("XVA Art Hotel",           "boutique", 150, 3, ["Gallery Courtyard","Al Fahidi Heritage","Vegetarian Café"]),
        },
        attractions=[
            Attraction("Burj Khalifa At the Top",    "photography",45,1.5, "Book a sunset slot well ahead — they sell out."),
            Attraction("Dubai Mall & Fountain Show", "shopping",   0, 3.0, "Fountain shows every 30 minutes from 6 PM. Free."),
            Attraction("Desert Safari",              "nature",    60, 6.0, "Dune drive, camel ride and BBQ dinner under the stars."),
            Attraction("Al Fahidi & Creek Abra Ride","culture",    1, 2.5, "Cross the creek by wooden abra for 1 dirham."),
            Attraction("Gold & Spice Souks",         "shopping",   0, 1.5, "Bargaining is expected. Gold price is set by weight."),
            Attraction("Museum of the Future",       "culture",   40, 2.0, "Book a timed slot online."),
            Attraction("Dubai Marina & JBR Walk",    "nightlife",  0, 3.0, "Waterfront restaurants and beach walk."),
        ],
        tags=["shopping","culture","nature","luxury","family"]
    ),

    "seoul": City(
        name="Seoul", country="South Korea", flag="🇰🇷",
        climate="Continental", cost_per_day=130,
        best_season="Apr–Jun, Sep–Nov", transport_mode="Subway (T-money Card)",
        timezone="KST (UTC+9)", lat=37.567, lon=126.978, region="Asia",
        hotels={
            "budget":   Hotel("Ibis Ambassador Seoul Myeongdong","budget",90,3,["Central","Restaurant","Rooftop"]),
            "midrange": Hotel("L7 Myeongdong by Lotte",  "midrange", 140, 4, ["Rooftop Bar","Design Rooms"]),
            "luxury":   Hotel("Signiel Seoul",           "luxury",   600, 5, ["Floors 76–101 of Lotte Tower","Spa","Michelin Dining"]),
            "boutique": Hotel("Rakkojae Seoul",          "boutique", 250, 4, ["Traditional Hanok","Bukchon Village","Mud Sauna"]),
        },
        attractions=[
            Attraction("Gyeongbokgung Palace",       "culture",    2, 2.5, "Free entry if you wear a hanbok. Changing of the guard at 10 AM."),
            Attraction("Bukchon Hanok Village",      "culture",    0, 1.5, "People live here — keep quiet; visiting hours are restricted."),
            Attraction("N Seoul Tower",              "photography",15,1.5, "Cable car up Namsan; best at dusk."),
            Attraction("Myeongdong Street Food",     "food",      15, 2.0, "Evening stalls: tteokbokki, egg bread, grilled cheese lobster."),
            Attraction("Gwangjang Market",           "food",      10, 1.5, "Bindaetteok and mayak kimbap at the counters."),
            Attraction("Hongdae",                    "nightlife",  0, 3.0, "Buskers, clubs and indie bars near the university."),
            Attraction("DMZ Tour",                   "culture",   60, 7.0, "Passport required. Book with a licensed operator."),
            Attraction("Insadong",                   "shopping",   0, 1.5, "Tea houses, crafts and Ssamziegil spiral mall."),
        ],
        tags=["culture","food","shopping","nightlife","k-culture"]
    ),

    "kathmandu": City(
        name="Kathmandu", country="Nepal", flag="🇳🇵",
        climate="Subtropical Highland", cost_per_day=35,
        best_season="Oct–Nov, Mar–Apr", transport_mode="Taxi & Walking",
        timezone="NPT (UTC+5:45)", lat=27.717, lon=85.324, region="Asia",
        hotels={
            "budget":   Hotel("Zostel Kathmandu",        "budget",   10, 2, ["Rooftop","Common Room","Thamel"]),
            "midrange": Hotel("Kathmandu Guest House",   "midrange",  50, 3, ["Garden","Historic","Thamel"]),
            "luxury":   Hotel("Dwarika's Hotel",         "luxury",   300, 5, ["Heritage Architecture","Spa","Courtyards"]),
            "boutique": Hotel("Baber Mahal Vilas",       "boutique", 150, 4, ["Rana Palace Wing","Antiques","Garden"]),
        },
        attractions=[
            Attraction("Swayambhunath (Monkey Temple)","culture",  2, 1.5, "365 steps up. Walk clockwise around the stupa."),
            Attraction("Boudhanath Stupa",           "culture",    4, 1.5, "Join the evening kora with pilgrims. Rooftop cafés around it."),
            Attraction("Pashupatinath Temple",       "culture",   10, 1.5, "Hindus only inside. Cremation ghats — no close-up photos."),
            Attraction("Kathmandu Durbar Square",    "culture",   10, 2.0, "See the Kumari's house — the living goddess."),
            Attraction("Bhaktapur Day Trip",         "culture",   15, 4.0, "Best-preserved medieval town. Try juju dhau yoghurt."),
            Attraction("Everest Mountain Flight",    "photography",220,1.0, "Early-morning flight. Weather cancellations are common."),
            Attraction("Nagarkot Sunrise Hike",      "hiking",     0, 4.0, "Himalayan panorama on clear mornings, Oct–Mar."),
            Attraction("Thamel Shopping",            "shopping",   0, 2.0, "Trekking gear, pashmina and singing bowls. Bargain."),
        ],
        tags=["culture","hiking","nature","spirituality","budget-friendly"]
    ),

    "istanbul": City(
        name="Istanbul", country="Türkiye", flag="🇹🇷",
        climate="Temperate", cost_per_day=110,
        best_season="Apr–May, Sep–Nov", transport_mode="Tram & Ferry (Istanbulkart)",
        timezone="TRT (UTC+3)", lat=41.008, lon=28.978, region="Europe",
        hotels={
            "budget":   Hotel("Cheers Hostel",           "budget",   30, 2, ["Sultanahmet","Rooftop Terrace"]),
            "midrange": Hotel("Hotel Amira Istanbul",    "midrange", 120, 4, ["Terrace Breakfast","Old City"]),
            "luxury":   Hotel("Çırağan Palace Kempinski","luxury",   700, 5, ["Ottoman Palace","Bosphorus Pool","Spa"]),
            "boutique": Hotel("Pera Palace Hotel",       "boutique", 300, 5, ["1892 Building","Agatha Christie Room","Patisserie"]),
        },
        attractions=[
            Attraction("Hagia Sophia",               "culture",   28, 1.5, "Foreign visitors use the upper gallery. Dress modestly."),
            Attraction("Blue Mosque",                "culture",    0, 1.0, "Free. Closed to visitors during prayer times."),
            Attraction("Topkapı Palace",             "culture",   40, 3.0, "The Harem needs a separate ticket. Closed Tuesdays."),
            Attraction("Grand Bazaar",               "shopping",   0, 2.5, "4,000 shops. Closed Sundays. Bargain politely."),
            Attraction("Basilica Cistern",           "culture",   30, 1.0, "Medusa heads under the city. Evening entry is quieter."),
            Attraction("Bosphorus Ferry Cruise",     "photography",5, 2.0, "Public Şehir Hatları ferries cost a fraction of tour boats."),
            Attraction("Spice Bazaar",               "food",       0, 1.0, "Lokum, saffron and dried fruit. Taste before you buy."),
            Attraction("Galata Tower",               "photography",30,1.0, "Go at opening to avoid long queues."),
        ],
        tags=["culture","food","shopping","history","photography"]
    ),

    # ═══ India ════════════════════════════════════════════════════════

    "goa": City(
        name="Goa", country="India", flag="🇮🇳",
        climate="Tropical", cost_per_day=50,
        best_season="Nov–Mar", transport_mode="Scooter & Taxi",
        timezone="IST (UTC+5:30)", lat=15.491, lon=73.828, region="India",
        hotels={
            "budget":   Hotel("Zostel Goa",              "budget",   15, 2, ["Hostel Vibes","Bike Rental","Café"]),
            "midrange": Hotel("Novotel Goa Resort & Spa","midrange", 110, 4, ["Pool","Spa","Near Candolim Beach"]),
            "luxury":   Hotel("Taj Exotica Resort & Spa","luxury",   350, 5, ["Beachfront","Golf","Spa"]),
            "boutique": Hotel("Siolim House",            "boutique", 150, 4, ["Portuguese Mansion","Pool","Heritage"]),
        },
        attractions=[
            Attraction("Baga & Calangute Beaches",   "beach",      0, 3.0, "North Goa's busiest beaches. Water sports on offer."),
            Attraction("Basilica of Bom Jesus",      "culture",    0, 1.0, "UNESCO-listed Old Goa church with St Francis Xavier's relics."),
            Attraction("Fontainhas Latin Quarter",   "photography",0, 2.0, "Colourful Portuguese-era houses in Panaji."),
            Attraction("Anjuna Flea Market",         "shopping",   0, 2.5, "Wednesdays in season. Bargain hard."),
            Attraction("Dudhsagar Falls",            "nature",    45, 6.0, "Jeep safari from Mollem. Best just after the monsoon."),
            Attraction("Palolem Beach",              "beach",      0, 3.0, "South Goa — calm crescent bay, kayaks, silent discos."),
            Attraction("Spice Plantation Tour",      "food",      10, 3.0, "Ponda plantations include a Goan buffet lunch."),
            Attraction("Tito's Lane",                "nightlife",  0, 3.0, "Baga's club strip. Busy from 10 PM in season."),
            Attraction("Fort Aguada",                "culture",    0, 1.0, "17th-century Portuguese fort and lighthouse."),
        ],
        tags=["beach","nightlife","food","culture","budget-friendly"]
    ),

    "jaipur": City(
        name="Jaipur", country="India", flag="🇮🇳",
        climate="Semi-Arid", cost_per_day=45,
        best_season="Oct–Mar", transport_mode="Auto-rickshaw & Cab",
        timezone="IST (UTC+5:30)", lat=26.912, lon=75.787, region="India",
        hotels={
            "budget":   Hotel("Zostel Jaipur",           "budget",   12, 2, ["Rooftop Café","Common Room"]),
            "midrange": Hotel("Alsisar Haveli",          "midrange",  90, 4, ["Heritage Haveli","Pool","Courtyard"]),
            "luxury":   Hotel("Rambagh Palace",          "luxury",   600, 5, ["Former Maharaja Palace","Peacock Gardens","Spa"]),
            "boutique": Hotel("Samode Haveli",           "boutique", 220, 4, ["Painted Dining Hall","Pool","Old City"]),
        },
        attractions=[
            Attraction("Amber Fort",                 "culture",    6, 3.0, "Arrive at opening. Evening light-and-sound show available."),
            Attraction("Hawa Mahal",                 "photography",2, 1.0, "Best photographed from the cafés across the road."),
            Attraction("City Palace",                "culture",    8, 2.0, "Still a royal residence. See the Peacock Gate."),
            Attraction("Jantar Mantar",              "culture",    3, 1.0, "UNESCO observatory with the world's largest stone sundial."),
            Attraction("Nahargarh Fort",             "photography",2, 2.0, "Sunset over the Pink City."),
            Attraction("Johari & Bapu Bazaar",       "shopping",   0, 2.0, "Gems, block-print textiles and mojari shoes. Bargain."),
            Attraction("Chokhi Dhani Village Dinner","food",      12, 3.0, "Rajasthani thali with folk dance and puppet shows."),
            Attraction("Albert Hall Museum",         "culture",    4, 1.5, "Indo-Saracenic building, lit up beautifully at night."),
        ],
        tags=["culture","history","shopping","photography","food"]
    ),

    "udaipur": City(
        name="Udaipur", country="India", flag="🇮🇳",
        climate="Semi-Arid", cost_per_day=45,
        best_season="Sep–Mar", transport_mode="Auto-rickshaw & Boat",
        timezone="IST (UTC+5:30)", lat=24.585, lon=73.712, region="India",
        hotels={
            "budget":   Hotel("Zostel Udaipur",          "budget",   12, 2, ["Lake View Rooftop","Common Room"]),
            "midrange": Hotel("Jagat Niwas Palace",      "midrange",  70, 3, ["Lakeside Haveli","Rooftop Restaurant"]),
            "luxury":   Hotel("Taj Lake Palace",         "luxury",   700, 5, ["Floating Palace","Boat Transfer","Spa"]),
            "boutique": Hotel("Amet Haveli",             "boutique", 110, 4, ["Lake Pichola Views","Ambrai Restaurant"]),
        },
        attractions=[
            Attraction("City Palace Udaipur",        "culture",    4, 3.0, "Largest palace complex in Rajasthan. Audio guide worth it."),
            Attraction("Lake Pichola Boat Ride",     "photography",6, 1.0, "Take the sunset boat with a stop at Jag Mandir."),
            Attraction("Bagore Ki Haveli Dance Show","culture",    3, 1.5, "Dharohar folk dance show at 7 PM. Arrive early for seats."),
            Attraction("Saheliyon Ki Bari",          "nature",     1, 1.0, "Garden of the maidens with lotus pools and fountains."),
            Attraction("Sajjangarh Monsoon Palace",  "photography",4, 1.5, "Hilltop palace for the city's best sunset."),
            Attraction("Ambrai Ghat Dinner",         "food",      15, 2.0, "Lake-level dining with the City Palace lit up opposite."),
            Attraction("Hathi Pol Bazaar",           "shopping",   0, 1.5, "Miniature paintings and silver jewellery."),
        ],
        tags=["culture","romance","photography","history"]
    ),

    "agra": City(
        name="Agra", country="India", flag="🇮🇳",
        climate="Semi-Arid", cost_per_day=40,
        best_season="Oct–Mar", transport_mode="Auto-rickshaw & Cab",
        timezone="IST (UTC+5:30)", lat=27.177, lon=78.008, region="India",
        hotels={
            "budget":   Hotel("Zostel Agra",             "budget",   10, 2, ["Rooftop Taj View","Café"]),
            "midrange": Hotel("Courtyard by Marriott Agra","midrange",90, 5, ["Pool","Restaurants","Spa"]),
            "luxury":   Hotel("The Oberoi Amarvilas",    "luxury",   900, 5, ["Taj View From Every Room","Pool","Spa"]),
            "boutique": Hotel("ITC Mughal",              "boutique", 200, 5, ["Mughal Gardens","Kaya Kalp Spa","Peshawri Restaurant"]),
        },
        attractions=[
            Attraction("Taj Mahal",                  "culture",   15, 3.0, "Closed Fridays. Enter at sunrise from the East Gate."),
            Attraction("Agra Fort",                  "culture",    8, 2.0, "Red sandstone Mughal fortress with Taj views."),
            Attraction("Mehtab Bagh",                "photography",3, 1.0, "Sunset view of the Taj from across the Yamuna."),
            Attraction("Fatehpur Sikri",             "culture",    8, 3.0, "Abandoned Mughal capital, 40 km away. Hire an official guide."),
            Attraction("Itimad-ud-Daulah (Baby Taj)","culture",    4, 1.0, "Delicate marble inlay, far fewer crowds."),
            Attraction("Kinari Bazaar",              "shopping",   0, 1.5, "Try Agra's famous petha sweets."),
        ],
        tags=["culture","history","photography"]
    ),

    "varanasi": City(
        name="Varanasi", country="India", flag="🇮🇳",
        climate="Humid Subtropical", cost_per_day=35,
        best_season="Oct–Mar", transport_mode="Boat & Cycle-rickshaw",
        timezone="IST (UTC+5:30)", lat=25.318, lon=83.010, region="India",
        hotels={
            "budget":   Hotel("Zostel Varanasi",         "budget",   10, 2, ["Rooftop","Common Room"]),
            "midrange": Hotel("Hotel Ganges View",       "midrange",  90, 3, ["Assi Ghat","River Views","Music Evenings"]),
            "luxury":   Hotel("Taj Nadesar Palace",      "luxury",   450, 5, ["Royal Palace","Horse Carriage","Gardens"]),
            "boutique": Hotel("BrijRama Palace",         "boutique", 250, 5, ["18th-Century Ghat Palace","River Views"]),
        },
        attractions=[
            Attraction("Ganga Aarti at Dashashwamedh Ghat","culture",0,1.5, "Arrive 45 min early, or watch from a boat."),
            Attraction("Sunrise Boat Ride on the Ganges","photography",6,1.5,"Golden light on the ghats. Agree the fare first."),
            Attraction("Kashi Vishwanath Temple",    "culture",    0, 1.5, "Phones and bags not allowed — use the lockers."),
            Attraction("Sarnath",                    "culture",    2, 3.0, "Where the Buddha gave his first sermon. 10 km away."),
            Attraction("Manikarnika Ghat",           "culture",    0, 0.5, "Main cremation ghat. Be respectful; no photos of rites."),
            Attraction("Kachori Gali Street Food",   "food",       3, 1.5, "Kachori sabzi breakfast, then lassi at Blue Lassi."),
            Attraction("Banarasi Silk Weavers",      "shopping",   0, 2.0, "Visit a weaving workshop. Check for the silk mark."),
        ],
        tags=["culture","spirituality","photography","food"]
    ),

    "kochi": City(
        name="Kochi", country="India", flag="🇮🇳",
        climate="Tropical Monsoon", cost_per_day=45,
        best_season="Oct–Mar", transport_mode="Auto-rickshaw & Ferry",
        timezone="IST (UTC+5:30)", lat=9.931, lon=76.267, region="India",
        hotels={
            "budget":   Hotel("Zostel Fort Kochi",       "budget",   12, 2, ["Heritage Building","Café"]),
            "midrange": Hotel("Forte Kochi",             "midrange",  90, 4, ["Colonial Mansion","Pool","Fort Kochi"]),
            "luxury":   Hotel("Grand Hyatt Kochi Bolgatty","luxury", 220, 5, ["Waterfront","Infinity Pool","Spa"]),
            "boutique": Hotel("Brunton Boatyard",        "boutique", 200, 5, ["Harbour Views","Colonial Shipyard","Pool"]),
        },
        attractions=[
            Attraction("Chinese Fishing Nets",       "photography",0, 1.0, "Watch them at work at sunset on Fort Kochi beach."),
            Attraction("Mattancherry Palace",        "culture",    1, 1.0, "Kerala murals of the Ramayana. Closed Fridays."),
            Attraction("Jew Town & Paradesi Synagogue","culture",  1, 1.5, "Synagogue closed Fridays, Saturdays and Jewish holidays."),
            Attraction("Kathakali Performance",      "culture",    5, 2.0, "Arrive an hour early to watch the make-up being applied."),
            Attraction("Alleppey Backwater Houseboat","nature",  120, 8.0, "Day cruise from Alleppey, 1.5 h away. Overnight option."),
            Attraction("St. Francis Church",         "culture",    0, 0.5, "Vasco da Gama's original burial place."),
            Attraction("Fort Kochi Seafood Stalls",  "food",      10, 1.5, "Pick your catch and have it fried on the spot."),
        ],
        tags=["culture","nature","food","backwaters"]
    ),

    "leh": City(
        name="Leh", country="India", flag="🇮🇳",
        climate="Cold Desert", cost_per_day=50,
        best_season="Jun–Sep", transport_mode="Taxi & Motorbike",
        timezone="IST (UTC+5:30)", lat=34.153, lon=77.577, region="India",
        hotels={
            "budget":   Hotel("Zostel Leh",              "budget",   15, 2, ["Mountain Views","Bike Rental"]),
            "midrange": Hotel("The Grand Dragon Ladakh", "midrange", 140, 4, ["Oxygen Support","Heated Rooms","Restaurant"]),
            "luxury":   Hotel("Chamba Camp Thiksey",     "luxury",   700, 5, ["Luxury Tents","Monastery Views","All Meals"]),
            "boutique": Hotel("Stok Palace Heritage Hotel","boutique",250, 4, ["Royal Palace Rooms","Museum","Garden"]),
        },
        attractions=[
            Attraction("Pangong Tso Lake",           "nature",     5, 10.0, "Acclimatise 48 h in Leh first. Inner-line permit needed."),
            Attraction("Nubra Valley via Khardung La","nature",    5, 10.0, "One of the highest motorable passes. Camels at Hunder dunes."),
            Attraction("Thiksey Monastery",          "culture",    1, 1.5, "Arrive by 6 AM for morning prayers."),
            Attraction("Shanti Stupa",               "photography",0, 1.0, "Sunset over Leh and the Stok range."),
            Attraction("Leh Palace",                 "culture",    3, 1.0, "Nine-storey palace modelled on Lhasa's Potala."),
            Attraction("Magnetic Hill & Sangam",     "nature",     0, 2.0, "Indus and Zanskar rivers meet in two colours."),
            Attraction("Hemis Monastery",            "culture",    2, 2.0, "Ladakh's largest monastery. Festival in June or July."),
        ],
        tags=["nature","hiking","adventure","photography","culture"]
    ),

    # ═══ Americas ═════════════════════════════════════════════════════

    "new_york": City(
        name="New York", country="USA", flag="🇺🇸",
        climate="Continental", cost_per_day=250,
        best_season="Apr–Jun, Sep–Nov", transport_mode="Subway & Walking",
        timezone="EST (UTC−5)", lat=40.713, lon=-74.006, region="Americas",
        hotels={
            "budget":   Hotel("The Local NYC",       "budget",   80, 3, ["Bar","LIC Location","Skyline View"]),
            "midrange": Hotel("Hotel Indigo LIC",   "midrange", 200, 4, ["Rooftop Pool","Manhattan Views"]),
            "luxury":   Hotel("The Plaza Hotel",    "luxury",   900, 5, ["Central Park Views","Eloise Suite","Afternoon Tea"]),
            "boutique": Hotel("The NoMad Hotel",    "boutique", 450, 5, ["Rooftop Bar","Library Lounge","NoMad Restaurant"]),
        },
        attractions=[
            Attraction("Central Park",              "nature",    0, 3.0, "Rent a rowboat. Strawberry Fields. Belvedere Castle."),
            Attraction("Metropolitan Museum of Art","culture",   30, 4.0, "Temple of Dendur, Egyptian Wing, Rooftop Garden."),
            Attraction("Brooklyn Bridge Walk",      "photography",0,1.5, "Walk Manhattan→Brooklyn. Best views from DUMBO afterward."),
            Attraction("Statue of Liberty & Ellis Island","culture",25,4.0,"Book crown tickets months ahead."),
            Attraction("MoMA",                      "culture",   30, 3.0, "Picasso, Warhol, Van Gogh's Starry Night."),
            Attraction("High Line Park",            "nature",     0, 2.0, "Elevated rail-to-park. Beautiful gardens and food stalls."),
            Attraction("Times Square",              "nightlife",  0, 1.0, "Overwhelming but unmissable. Better at midnight."),
            Attraction("One World Trade & 9/11 Memorial","culture",33,2.5,"Emotional and important. Book in advance."),
            Attraction("Chelsea Market",            "food",       0, 1.5, "Tacos, lobster rolls and doughnuts under one roof."),
        ],
        tags=["culture","food","shopping","nightlife","photography"]
    ),

    "machu_picchu": City(
        name="Machu Picchu", country="Peru", flag="🇵🇪",
        climate="Highland Subtropical", cost_per_day=120,
        best_season="May–Sep (Dry Season)", transport_mode="Train & Bus",
        timezone="PET (UTC−5)", lat=-13.163, lon=-72.545, region="Americas",
        hotels={
            "budget":   Hotel("Hatun Inti Lodge",          "budget",   40, 2, ["Mountain Views","Breakfast"]),
            "midrange": Hotel("El Mapi Hotel Aguas Calientes","midrange",120,4,["Rooftop Terrace","Pool"]),
            "luxury":   Hotel("Belmond Sanctuary Lodge",  "luxury",   700, 5, ["Only Hotel At Ruins Gate","Garden","Pool"]),
            "boutique": Hotel("Inkaterra Machu Picchu",   "boutique", 350, 4, ["Cloud Forest","Orchid Garden","Birdwatching"]),
        },
        attractions=[
            Attraction("Machu Picchu Citadel",     "culture",    45, 4.0, "Timed entry by circuit. Buy official tickets weeks ahead."),
            Attraction("Sun Gate (Inti Punku)",     "hiking",      0, 3.0, "Round trip from the citadel. Classic view of Machu Picchu."),
            Attraction("Huayna Picchu Trek",        "hiking",     55, 4.0, "Very steep. Limited daily permits — book months ahead."),
            Attraction("Sacred Valley Tour",        "culture",    80, 8.0, "Pisac Market, Ollantaytambo fortress, Moray Terraces."),
            Attraction("Rainbow Mountain (Vinicunca)","nature",   30, 8.0, "Day trip from Cusco. Altitude 5,200m — acclimatise first."),
            Attraction("Aguas Calientes Town",     "food",         0, 2.0, "Hot springs, local markets, fresh trout restaurants."),
        ],
        tags=["hiking","nature","culture","photography","adventure"]
    ),

    # ═══ Africa ═══════════════════════════════════════════════════════

    "cape_town": City(
        name="Cape Town", country="South Africa", flag="🇿🇦",
        climate="Mediterranean", cost_per_day=90,
        best_season="Nov–Mar", transport_mode="Uber & MyCiTi Bus",
        timezone="SAST (UTC+2)", lat=-33.925, lon=18.424, region="Africa",
        hotels={
            "budget":   Hotel("Once in Cape Town",       "budget",   30, 2, ["Kloof Street","Café","Tours Desk"]),
            "midrange": Hotel("Protea Hotel Fire & Ice! Cape Town","midrange",120,4,["Rooftop Pool","Burger Bar"]),
            "luxury":   Hotel("Belmond Mount Nelson Hotel","luxury", 450, 5, ["Pink Colonial Landmark","Gardens","Afternoon Tea"]),
            "boutique": Hotel("Ellerman House",          "boutique", 650, 5, ["Art Collection","Wine Gallery","Ocean Views"]),
        },
        attractions=[
            Attraction("Table Mountain Cableway",    "photography",25,3.0, "Check the wind — the cableway closes in strong gusts."),
            Attraction("Cape Point & Boulders Beach Penguins","nature",40,8.0,"Drive Chapman's Peak on the way. Penguins at Boulders."),
            Attraction("Robben Island",              "culture",   35, 4.0, "Former prisoners guide the tour. Book ahead; ferries cancel in rough seas."),
            Attraction("V&A Waterfront",             "shopping",   0, 2.5, "Zeitz MOCAA museum is in the old grain silo."),
            Attraction("Kirstenbosch Gardens",       "nature",    15, 2.5, "Tree-canopy walkway. Summer sunset concerts."),
            Attraction("Lion's Head Hike",           "hiking",     0, 3.0, "Popular sunset or full-moon hike. Chains near the top."),
            Attraction("Stellenbosch Wine Tasting",  "food",      40, 6.0, "Book a tour or use the hop-on wine tram in Franschhoek."),
            Attraction("Bo-Kaap",                    "culture",    0, 1.0, "Brightly painted Cape Malay houses. Try a koesister."),
        ],
        tags=["nature","hiking","food","beach","adventure"]
    ),

    "marrakech": City(
        name="Marrakech", country="Morocco", flag="🇲🇦",
        climate="Semi-Arid", cost_per_day=70,
        best_season="Mar–May, Sep–Nov", transport_mode="Walking & Petit Taxi",
        timezone="WET (UTC+1)", lat=31.630, lon=-7.989, region="Africa",
        hotels={
            "budget":   Hotel("Equity Point Hostel Marrakech","budget",25,2,["Riad Courtyard","Pool","Medina"]),
            "midrange": Hotel("Riad Kniza",              "midrange", 180, 4, ["Traditional Riad","Rooftop","Hammam"]),
            "luxury":   Hotel("La Mamounia",             "luxury",   700, 5, ["Legendary Gardens","Spa","Pool"]),
            "boutique": Hotel("El Fenn",                 "boutique", 350, 4, ["Rooftop Bar","Art Collection","Pools"]),
        },
        attractions=[
            Attraction("Jemaa el-Fnaa",              "food",      10, 2.5, "Evening food stalls. Agree prices before eating or photos."),
            Attraction("Majorelle Garden & YSL Museum","nature",  17, 2.0, "Book online. Go at opening for the cobalt-blue villa."),
            Attraction("Bahia Palace",               "culture",    8, 1.5, "Painted cedar ceilings and zellige tiles."),
            Attraction("Medina Souks",               "shopping",   0, 3.0, "Leather, spices and lamps. Haggle with a smile."),
            Attraction("Ben Youssef Madrasa",        "culture",    6, 1.0, "Restored Koranic school with stunning carvings."),
            Attraction("Atlas Mountains & Ourika Valley","hiking", 40, 8.0, "Berber villages and waterfalls on a day trip."),
            Attraction("Agafay Desert Dinner",       "nature",    60, 5.0, "Stone desert 40 min away. Camel ride and sunset dinner."),
        ],
        tags=["culture","shopping","food","photography"]
    ),

    # ═══ Oceania ══════════════════════════════════════════════════════

    "sydney": City(
        name="Sydney", country="Australia", flag="🇦🇺",
        climate="Temperate", cost_per_day=170,
        best_season="Sep–Nov, Mar–May", transport_mode="Train & Ferry (Opal)",
        timezone="AEST (UTC+10)", lat=-33.869, lon=151.209, region="Oceania",
        hotels={
            "budget":   Hotel("Wake Up! Sydney",         "budget",   45, 2, ["Central Station","Bar","Tours Desk"]),
            "midrange": Hotel("Rydges World Square",     "midrange", 200, 4, ["CBD","Restaurant","Gym"]),
            "luxury":   Hotel("Park Hyatt Sydney",       "luxury",   900, 5, ["Opera House Views","Rooftop Pool","Spa"]),
            "boutique": Hotel("Ovolo Woolloomooloo",     "boutique", 350, 5, ["Historic Wharf","Free Minibar","Pool"]),
        },
        attractions=[
            Attraction("Sydney Opera House Tour",    "culture",   30, 1.5, "Or book any performance for the full experience."),
            Attraction("Harbour Bridge Climb",       "photography",250,3.5,"Twilight climbs are the most popular. Pricey but memorable."),
            Attraction("Bondi to Coogee Coastal Walk","hiking",    0, 3.0, "6 km clifftop walk. Swim at Bronte or Clovelly."),
            Attraction("Manly Ferry",                "beach",      8, 3.0, "Cheapest harbour cruise in the world. Beach at the end."),
            Attraction("Taronga Zoo",                "nature",    40, 4.0, "Take the ferry; cable car up the hill. Harbour views."),
            Attraction("Blue Mountains Day Trip",    "nature",    30, 9.0, "Three Sisters lookout. Train from Central."),
            Attraction("The Rocks Markets",          "shopping",   0, 2.0, "Weekend markets in Sydney's oldest streets."),
            Attraction("Darling Harbour",            "nightlife",  0, 3.0, "Waterfront bars and Saturday fireworks."),
        ],
        tags=["beach","nature","hiking","culture","food"]
    ),

    "queenstown": City(
        name="Queenstown", country="New Zealand", flag="🇳🇿",
        climate="Temperate Oceanic", cost_per_day=180,
        best_season="Dec–Feb, Jun–Aug (Skiing)", transport_mode="Bus & Rental Car",
        timezone="NZST (UTC+12)", lat=-45.031, lon=168.663, region="Oceania",
        hotels={
            "budget":   Hotel("Nomads Queenstown",       "budget",   40, 2, ["Central","Free Dinner Some Nights","Bar"]),
            "midrange": Hotel("Novotel Queenstown Lakeside","midrange",220,4,["Lake Wakatipu","Restaurant"]),
            "luxury":   Hotel("Eichardt's Private Hotel","luxury",   800, 5, ["Lakefront","Suites","Bar"]),
            "boutique": Hotel("The Rees Hotel",          "boutique", 350, 5, ["Lake Views","Wine Cellar","Apartments"]),
        },
        attractions=[
            Attraction("Milford Sound Cruise",       "nature",   150,12.0, "Long day by coach — scenic flights save hours."),
            Attraction("Skyline Gondola & Luge",     "photography",50,2.0, "Ride the luge at least twice. Sunset dinner option."),
            Attraction("Kawarau Bridge Bungy",       "nature",   200, 2.0, "The world's first commercial bungy site."),
            Attraction("Shotover Jet",               "nature",   140, 1.5, "Jet boat through narrow canyons. You will get wet."),
            Attraction("Ben Lomond Track",           "hiking",     0, 7.0, "Hard day hike with 360° alpine views."),
            Attraction("Arrowtown",                  "culture",    0, 2.5, "Gold-rush village. Golden autumn colours in April."),
            Attraction("Fergburger",                 "food",      15, 1.0, "Famous burger joint. Order by phone to skip the queue."),
        ],
        tags=["adventure","nature","hiking","photography"]
    ),

}

# Origin cities (departure only — no full tourism data needed)
ORIGIN_CITIES = {
    "new_york":    {"name": "New York",    "flag": "🗽", "country": "USA",       "lat": 40.713, "lon": -74.006},
    "los_angeles": {"name": "Los Angeles", "flag": "🌴", "country": "USA",       "lat": 34.052, "lon": -118.244},
    "london":      {"name": "London",      "flag": "🎡", "country": "UK",        "lat": 51.507, "lon": -0.128},
    "paris":       {"name": "Paris",       "flag": "🗼", "country": "France",    "lat": 48.857, "lon": 2.352},
    "tokyo":       {"name": "Tokyo",       "flag": "🗼", "country": "Japan",     "lat": 35.676, "lon": 139.650},
    "sydney":      {"name": "Sydney",      "flag": "🦘", "country": "Australia", "lat": -33.869, "lon": 151.209},
    "dubai":       {"name": "Dubai",       "flag": "🏙️", "country": "UAE",       "lat": 25.205, "lon": 55.271},
    "singapore":   {"name": "Singapore",   "flag": "🦁", "country": "Singapore", "lat": 1.290, "lon": 103.852},
    "delhi":       {"name": "New Delhi",   "flag": "🇮🇳", "country": "India",     "lat": 28.614, "lon": 77.209},
    "mumbai":      {"name": "Mumbai",      "flag": "🇮🇳", "country": "India",     "lat": 19.076, "lon": 72.878},
    "bangalore":   {"name": "Bengaluru",   "flag": "🇮🇳", "country": "India",     "lat": 12.972, "lon": 77.595},
    "chennai":     {"name": "Chennai",     "flag": "🇮🇳", "country": "India",     "lat": 13.083, "lon": 80.271},
    "hyderabad":   {"name": "Hyderabad",   "flag": "🇮🇳", "country": "India",     "lat": 17.385, "lon": 78.487},
    "kolkata":     {"name": "Kolkata",     "flag": "🇮🇳", "country": "India",     "lat": 22.573, "lon": 88.364},
}

DESTINATION_IDS = list(CITIES.keys())
ORIGIN_IDS = list(ORIGIN_CITIES.keys())

ALL_CITY_NAMES = {k: v["name"] if isinstance(v, dict) else v.name
                  for k, v in {**ORIGIN_CITIES,
                                **{k: v for k, v in CITIES.items()}}.items()}
