import requests
import os
from dotenv import load_dotenv
from geopy.distance import geodesic
import csv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
CSE_ID = os.getenv("GOOGLE_CSE_ID")
REFERENCE_LAT = float(os.getenv("REFERENCE_LAT"))
REFERENCE_LON = float(os.getenv("REFERENCE_LON"))
RADIUS_KM = float(os.getenv("RADIUS_KM", 30))
FACEBOOK_GROUP = os.getenv("FACEBOOK_GROUP")

REFERENCE_COORDS = (REFERENCE_LAT, REFERENCE_LON)

def load_suburbs(csv_path):
    suburbs = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["suburb"]
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            suburbs.append((name, (lat, lon)))
    return suburbs

def get_nearby_suburbs(reference_coords, all_suburbs, radius_km):
    return [
        name for name, coords in all_suburbs
        if geodesic(reference_coords, coords).km <= radius_km
    ]

def build_facebook_group_query(base_term="pug", suburbs=None):
    location_filter = " OR ".join(suburbs) if suburbs else ""
    return f'site:{FACEBOOK_GROUP}/posts {base_term}'

def google_search(query, api_key, cse_id, num_results=10):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": api_key,
        "cx": cse_id,
        "num": num_results,
    }
    print(f"Making request to Google with query: {query}")
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return []
    data = response.json()

    results = []
    for item in data.get("items", []):
        title = item.get("title")
        link = item.get("link")
        snippet = item.get("snippet")
        results.append((title, link, snippet))

    return results

if __name__ == "__main__":
    suburbs_data = load_suburbs("suburbs.csv")
    nearby_suburbs = get_nearby_suburbs(REFERENCE_COORDS, suburbs_data, RADIUS_KM)
    print(f"Nearby suburbs ({len(nearby_suburbs)} found): {', '.join(nearby_suburbs)}")

    google_query = build_facebook_group_query("pug", nearby_suburbs)
    print(f"\nRunning search with query:\n{google_query}\n{'='*60}")

    google_results = google_search(google_query, API_KEY, CSE_ID, 10)

    if google_results:
        for i, (title, link, snippet) in enumerate(google_results, 1):
            print(f"{i}. {title}\n{link}\n{snippet}\n{'-'*60}")
    else:
        print("No results found or an error occurred.")
