import httpx
from typing import List, Dict, Any, Optional, Set
from ..config import settings
from . import weather as weather_tool

BASE = "https://api.opentripmap.com/0.1/en"
API_KEY = settings.opentripmap_api_key
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
WIKI_GEOSEARCH = "https://en.wikipedia.org/w/api.php"

def _require_key():
    if not API_KEY:
        raise RuntimeError(
            "OPENTRIPMAP_API_KEY is required for POI lookups. "
            "Get a free key at https://opentripmap.io"
        )

def _otm_geoname(city: str) -> Optional[Dict[str, Any]]:
    url = f"{BASE}/places/geoname"
    r = httpx.get(url, params={"name": city, "apikey": API_KEY}, timeout=20)
    r.raise_for_status()
    d = r.json()
    if "lat" in d and "lon" in d:
        return {"lat": d["lat"], "lon": d["lon"], "name": d.get("name", city)}
    return None

def geoname(city: str) -> Dict[str, Any]:
    try:
        g = _otm_geoname(city)
        if g:
            return g
    except Exception:
        pass
    g2 = weather_tool.geocode_city(city)  # {'name','lat','lon','country'}
    return {"lat": g2["lat"], "lon": g2["lon"], "name": g2.get("name", city)}

def _radius_query_otm(lat: float, lon: float, radius_m: int, kinds: Optional[str], rate: int, limit: int):
    params = {
        "lat": lat,
        "lon": lon,
        "radius": radius_m,
        "limit": limit,
        "apikey": API_KEY,
        "format": "geojson",
        "rate": rate,
    }
    if kinds:
        params["kinds"] = kinds
    url = f"{BASE}/places/radius"
    r = httpx.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("features", [])

def _overpass_query(lat: float, lon: float, radius_m: int, topic: str = "general") -> List[Dict[str, Any]]:
    """
    Live OSM Overpass.
    topic='restaurants' → restaurant-like amenities
    topic='nature'      → parks/gardens/natural/water
    topic='general'     → tourist attractions/historic/sightseeing
    """
    if topic == "restaurants":
        q = f"""
        [out:json][timeout:25];
        (
          node(around:{radius_m},{lat},{lon})["amenity"~"restaurant|cafe|fast_food|food_court|biergarten"];
          way(around:{radius_m},{lat},{lon})["amenity"~"restaurant|cafe|fast_food|food_court|biergarten"];
        );
        out center 200;
        """
    elif topic == "nature":
        q = f"""
        [out:json][timeout:25];
        (
          node(around:{radius_m},{lat},{lon})["leisure"~"park|garden"];
          way(around:{radius_m},{lat},{lon})["leisure"~"park|garden"];
          node(around:{radius_m},{lat},{lon})["natural"];
          way(around:{radius_m},{lat},{lon})["natural"];
          node(around:{radius_m},{lat},{lon})["water"~"lake|river|reservoir|lagoon|pond"];
          way(around:{radius_m},{lat},{lon})["water"~"lake|river|reservoir|lagoon|pond"];
          node(around:{radius_m},{lat},{lon})["waterway"~"waterfall|river"];
          way(around:{radius_m},{lat},{lon})["waterway"~"waterfall|river"];
          node(around:{radius_m},{lat},{lon})["tourism"="viewpoint"];
          way(around:{radius_m},{lat},{lon})["tourism"="viewpoint"];
        );
        out center 200;
        """
    else:
        q = f"""
        [out:json][timeout:25];
        (
          node(around:{radius_m},{lat},{lon})["tourism"~"attraction|museum|zoo|theme_park|viewpoint|information"];
          way(around:{radius_m},{lat},{lon})["tourism"~"attraction|museum|zoo|theme_park|viewpoint|information"];
          node(around:{radius_m},{lat},{lon})["historic"];
          way(around:{radius_m},{lat},{lon})["historic"];
          node(around:{radius_m},{lat},{lon})["leisure"~"park|garden"];
          way(around:{radius_m},{lat},{lon})["leisure"~"park|garden"];
          node(around:{radius_m},{lat},{lon})["natural"];
          way(around:{radius_m},{lat},{lon})["natural"];
        );
        out center 200;
        """
    r = httpx.post(OVERPASS_URL, data={"data": q}, timeout=40)
    r.raise_for_status()
    elements = r.json().get("elements", [])
    out: List[Dict[str, Any]] = []
    for el in elements:
        tags = el.get("tags", {}) or {}
        name = (tags.get("name") or "").strip()
        if not name:
            continue
        if topic == "restaurants":
            kind = "amenity:" + (tags.get("amenity") or "")
        elif topic == "nature":
            parts = []
            for k in ["leisure", "natural", "water", "waterway", "tourism"]:
                if tags.get(k):
                    parts.append(f"{k}:{tags.get(k)}")
            kind = ",".join(parts)
        else:
            parts = []
            for k in ["tourism", "historic", "leisure", "natural"]:
                if tags.get(k):
                    parts.append(f"{k}:{tags.get(k)}")
            kind = ",".join(parts)
        out.append({"name": name, "kinds": kind or None, "rate": None, "source": "overpass"})
    return out

def _wikipedia_geosearch(lat: float, lon: float, radius_m: int, limit: int) -> List[Dict[str, Any]]:
    params = {
        "action": "query",
        "list": "geosearch",
        "gscoord": f"{lat}|{lon}",
        "gsradius": radius_m,
        "gslimit": limit,
        "format": "json",
    }
    r = httpx.get(WIKI_GEOSEARCH, params=params, timeout=20)
    r.raise_for_status()
    pages = r.json().get("query", {}).get("geosearch", [])
    return [
        {"name": p.get("title"), "kinds": "wikipedia", "rate": None, "source": "wikipedia"}
        for p in pages if p.get("title")
    ]

def list_pois(
    city: str,
    limit: int = 18,
    kinds: str = (
        "interesting_places,architecture,museums,heritage,urban_environment,"
        "religion,natural,fortifications,monuments,memorial,towers,other_temples,temples,churches,mosques,"
        "bridges,attractions,amusements,parks,zoos,theatres_and_entertainments,sport"
    ),
    initial_radius_m: int = 12000,
    topic: str = "general",  
) -> Dict[str, Any]:
    _require_key()
    g = geoname(city)
    lat, lon = g["lat"], g["lon"]

    if topic == "restaurants":
        kinds = "catering,restaurants,cafes,fast_food"
        initial_radius_m = max(3000, min(initial_radius_m, 8000))
    elif topic == "nature":
        kinds = "natural,parks,gardens,water,view_points"
        initial_radius_m = max(4000, min(initial_radius_m, 10000))

    otm_strategies = [
        (initial_radius_m, kinds, 2),
        (20000 if topic == "restaurants" else 25000, kinds, 2),
        (35000 if topic == "restaurants" else 50000, kinds, 2),
        (20000, kinds, 1),
        (35000, kinds, 1),
        (25000, None, 1),
        (50000, None, 1),
    ]
    items: List[Dict[str, Any]] = []
    for radius_m, k_filter, rate in otm_strategies:
        try:
            feats = _radius_query_otm(lat, lon, radius_m, k_filter, rate, limit)
            if feats:
                items = feats
                break
        except Exception:
            continue

    results: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    if items:
        for it in items:
            p = it.get("properties", {})
            name = p.get("name") or p.get("wikidata") or p.get("xid")
            if not name:
                continue
            key = str(name).strip().lower()
            if key in seen:
                continue
            seen.add(key)
            results.append({
                "name": str(name),
                "kinds": p.get("kinds"),
                "rate": p.get("rate"),
                "otm": f"https://opentripmap.com/en/card/{p.get('xid')}" if p.get("xid") else None,
                "source": "opentripmap",
            })

    if len(results) < max(6, limit // 2):
        try:
            overpass_items = _overpass_query(lat, lon, max(initial_radius_m, 20000), topic=topic)
            for it in overpass_items:
                key = str(it["name"]).strip().lower()
                if key in seen:
                    continue
                seen.add(key)
                results.append(it)
        except Exception:
            pass

    if len(results) < max(6, limit // 2):
        try:
            wiki_items = _wikipedia_geosearch(lat, lon, max(initial_radius_m, 20000), limit=limit)
            for it in wiki_items:
                key = str(it["name"]).strip().lower()
                if key in seen:
                    continue
                seen.add(key)
                results.append(it)
        except Exception:
            pass

    results.sort(key=lambda x: (x.get("rate") or 0), reverse=True)
    if len(results) > limit:
        results = results[:limit]

    return {"city": g.get("name", city), "items": results, "source": ["opentripmap","overpass","wikipedia"]}

def list_foods(city: str, limit: int = 16, initial_radius_m: int = 12000) -> Dict[str, Any]:
    """
    Live OSM-based 'foods to try' using restaurant cuisine tags near the city.
    Returns unique cuisine/dish names (normalized).
    """
    g = geoname(city)
    lat, lon = g["lat"], g["lon"]

    q = f"""
    [out:json][timeout:25];
    (
      node(around:{max(initial_radius_m,8000)},{lat},{lon})["amenity"~"restaurant|cafe|fast_food|food_court|biergarten"]["cuisine"];
      way(around:{max(initial_radius_m,8000)},{lat},{lon})["amenity"~"restaurant|cafe|fast_food|food_court|biergarten"]["cuisine"];
    );
    out tags 200;
    """
    r = httpx.post(OVERPASS_URL, data={"data": q}, timeout=40)
    r.raise_for_status()
    elements = r.json().get("elements", [])
    seen: Set[str] = set()
    foods: List[str] = []
    for el in elements:
        tags = el.get("tags", {}) or {}
        raw = (tags.get("cuisine") or "").strip()
        if not raw:
            continue
        parts = [p.strip() for p in raw.replace(",", ";").split(";") if p.strip()]
        for p in parts:
            name = p.replace("_", " ").title()
            key = name.lower()
            if key not in seen:
                seen.add(key)
                foods.append(name)
            if len(foods) >= limit:
                break
        if len(foods) >= limit:
            break
    return {
        "city": g.get("name", city),
        "items": [{"name": f, "kinds": "cuisine", "rate": None, "source": "overpass"} for f in foods],
    }
