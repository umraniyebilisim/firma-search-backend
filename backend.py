from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fallback, HTML tarafı apiKey'i body ile gönderiyor
GOOGLE_API_KEY = "YOUR_API_KEY"


def guess_sector(place):
    name = place.get("name", "").lower()
    types = place.get("types", [])

    if "restaurant" in types or "food" in types:
        return "restaurant"
    if "health" in types or "hospital" in types:
        return "health"
    if "real_estate" in types or "estate" in name:
        return "real_estate"
    if "car" in name or "oto" in name:
        return "automotive"
    if "logistics" in name or "kargo" in name:
        return "logistics"
    if "law" in name or "avukat" in name:
        return "law"
    if "pharmacy" in types or "ecz" in name:
        return "pharmacy"
    if "hotel" in types or "otel" in name:
        return "hospitality"
    if "school" in types or "kolej" in name:
        return "education"
    if "gym" in types or "spor" in name:
        return "sports"
    if "bank" in types or "finans" in name:
        return "finance"
    if "store" in types or "market" in name:
        return "retail"

    return "other"


def google_nearby(lat, lng, radius, keyword, api_key):
    url = (
        "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        f"?location={lat},{lng}&radius={radius}"
    )
    if keyword:
        url += f"&keyword={keyword}"
    url += f"&key={api_key}"
    return requests.get(url).json()


def google_details(place_id, api_key):
    url = (
        "https://maps.googleapis.com/maps/api/place/details/json"
        f"?place_id={place_id}"
        f"&fields=name,formatted_phone_number,website,geometry"
        f"&key={api_key}"
    )
    return requests.get(url).json()


@app.post("/scan")
def scan(payload: dict):
    lat = payload.get("lat")
    lng = payload.get("lng")
    radius = payload.get("radius", 5000)
    keyword = payload.get("keyword", "")
    api_key = payload.get("apiKey") or GOOGLE_API_KEY

    if not (lat and lng):
        return {"firms": []}

    resp = google_nearby(lat, lng, radius, keyword, api_key)
    results = resp.get("results", [])

    final = []
    for place in results[:40]:
        pid = place.get("place_id")
        if not pid:
            continue

        detail = google_details(pid, api_key)
        result = detail.get("result", {})

        phone = result.get("formatted_phone_number")
        website = result.get("website")

        # Sadece telefon ve web sitesi olanlar
        if not phone or not website:
            continue

        geom = result.get("geometry", {}).get("location", {})
        lat2 = geom.get("lat")
        lng2 = geom.get("lng")

        firm = {
            "id": pid,
            "name": result.get("name", "Bilinmeyen Firma"),
            "phone": phone,
            "website": website,
            "lat": lat2,
            "lng": lng2,
            "sector": guess_sector(place),
        }
        final.append(firm)

        if len(final) >= 20:
            break

    return {"firms": final}
