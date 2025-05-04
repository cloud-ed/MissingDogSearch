import requests
import os
from dotenv import load_dotenv
from geopy.distance import geodesic
import csv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
CSE_ID = os.getenv("GOOGLE_CSE_ID")
ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
GROUP_ID = os.getenv("FACEBOOK_GROUP_ID")
REFERENCE_LAT = float(os.getenv("REFERENCE_LAT"))
REFERENCE_LON = float(os.getenv("REFERENCE_LON"))
RADIUS_KM = float(os.getenv("RADIUS_KM", 30))

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

def build_local_query(base_term="missing pug", suburbs=None):
    if not suburbs:
        return base_term
    location_filter = " OR ".join(suburbs)
    return f"{base_term} AND ({location_filter})"

def google_search(query, api_key, cse_id, num_results=10):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": api_key,
        "cx": cse_id,
        "num": num_results,
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    results = []
    for item in data.get("items", []):
        title = item.get("title")
        link = item.get("link")
        snippet = item.get("snippet")
        results.append((title, link, snippet))
    
    return results

def fetch_facebook_posts(group_id, access_token, num_posts=10):
    url = f"https://graph.facebook.com/{group_id}/feed"
    params = {
        "access_token": access_token,
        "fields": "message,created_time,from,id",
        "limit": num_posts
    }
    response = requests.get(url, params=params)
    data = response.json()

    posts = []
    if "data" in data:
        for post in data["data"]:
            posts.append({
                "message": post.get("message", "No message"),
                "created_time": post.get("created_time"),
                "from": post.get("from", {}).get("name", "Unknown"),
                "post_id": post.get("id")
            })
    else:
        print("Error fetching Facebook posts:", data)
    
    return posts

if __name__ == "__main__":
    suburbs_data = load_suburbs("australian_suburbs.csv")
    nearby_suburbs = get_nearby_suburbs(REFERENCE_COORDS, suburbs_data, RADIUS_KM)
    print(f"Nearby suburbs ({len(nearby_suburbs)} found): {', '.join(nearby_suburbs)}")
    
    google_query = build_local_query("missing pug", nearby_suburbs)
    print(f"\nRunning Google search query:\n{google_query}\n{'='*60}")

    google_results = google_search(google_query, API_KEY, CSE_ID, 10)

    if google_results:
        for i, (title, link, snippet) in enumerate(google_results, 1):
            print(f"{i}. {title}\n{link}\n{snippet}\n{'-'*60}")
    else:
        print("No Google results found or an error occurred.")

    print("\nFetching Facebook posts...\n{'='*60}")
    facebook_posts = fetch_facebook_posts(GROUP_ID, ACCESS_TOKEN, 10)

    if facebook_posts:
        for i, post in enumerate(facebook_posts, 1):
            print(f"{i}. From: {post['from']}")
            print(f"Message: {post['message']}")
            print(f"Created Time: {post['created_time']}")
            print(f"Post ID: {post['post_id']}")
            print("-" * 60)
    else:
        print("No Facebook posts found or an error occurred.")
