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

def guess_sector(place):
    name = (place.get("name") or "").lower()
    types = place.get("types", [])

    if "avukat" in name or "law" in types:
        return "law"
    if "kargo" in name or "logistics" in name:
        return "logistics"
    if "market" in name or "store" in types:
        return "retail"
    if "restoran" in name or "restaurant" in types:
        return "restaurant"
    if "ecz" in name:
        return "pharmacy"
    return "other"


def google_nearby(lat, lng, radius, keyword, api_key):
    url = (
        "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        f"?location={lat},{lng}&radius={radius}&key={api_key}"
    )
    if keyword:
        url += f"&keyword={keyword}"

    print("Nearby URL:", url)  # DEBUG

    return requests.get(url).json()


def google_details(place_id, api_key):
    url = (
        "https://maps.googleapis.com/maps/api/place/details/json"
        f"?place_id={place_id}"
        f"&fields=name,formatted_phone_number,website,geometry,types"
        f"&key={api_key}"
    )

    print("Details URL:", url)  # DEBUG

    return requests.get(url).json()


@app.post("/scan")
def scan(payload: dict):

    lat = payload.get("lat")
    lng = payload.get("lng")
    radius = payload.get("radius", 5000)
    keyword = payload.get("keyword", "").strip()
    api_key = payload.get("apiKey")

    if not lat or not lng:
        return {"firms": []}

    # 1) İlk ham veri çekimi
    nearby = google_nearby(lat, lng, radius, keyword, api_key)
    results = nearby.get("results", [])

    print("Nearby count:", len(results))  # DEBUG

    firms = []

    # 2) Daha fazla firma gelsin diye 60 tanesine kadar bakıyoruz
    for place in results[:60]:
        pid = place.get("place_id")
        if not pid:
            continue

        detail = google_details(pid, api_key)
        result = detail.get("result", {})

        phone = result.get("formatted_phone_number")

        # 🔥 Website ZORUNLU DEĞİL → CRM'de seçenekli zaten
        if not phone:
            continue  # sadece telefon zorunlu

        name = result.get("name", "")
        geom = result.get("geometry", {}).get("location", {})

        firm = {
            "id": pid,
            "name": name,
            "phone": phone,
            "website": result.get("website", ""),  # opsiyonel
            "lat": geom.get("lat"),
            "lng": geom.get("lng"),
            "sector": guess_sector(result),
        }

        firms.append(firm)

        if len(firms) >= 20:
            break

    print("Final firm count:", len(firms))

    return {"firms": firms}
