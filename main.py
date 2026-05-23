import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =========================================
# CONFIG
# =========================================

API_KEY = os.getenv("API_KEY")
URL = os.getenv("URL_API")

STORES = [
    "Starbucks",
    "McDonald's",
]

AREAS = [
    "Koramangala Bangalore",
    "Indiranagar Bangalore",
    "HSR Layout Bangalore",
]

# =========================================
# GOOGLE PLACES API CONFIG
# =========================================

# URL is now loaded from .env

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.types",
    "places.primaryType",
    "places.googleMapsUri",
    "places.websiteUri",
    "places.businessStatus",
])

# Minimal filtering only
ALLOWED_TYPES = {
    "restaurant",
    "cafe",
    "coffee_shop",
    "food",
    "meal_takeaway",
    "fast_food_restaurant",
}

# =========================================
# STORAGE
# =========================================

all_places = {}
final_results = []

# =========================================
# API FUNCTION
# =========================================

def search_places(query):

    payload = {
        "textQuery": query
    }

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }

    response = requests.post(
        URL,
        json=payload,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# =========================================
# MAIN LOOP
# =========================================

for store in STORES:

    for area in AREAS:

        query = f"{store} in {area}"

        print(f"\nSearching: {query}")

        try:

            data = search_places(query)

            places = data.get("places", [])

            print(f"Found {len(places)} results")

            for place in places:

                # ---------------------------------
                # DEDUPLICATION
                # ---------------------------------

                place_id = place.get("id")

                if not place_id:
                    continue

                if place_id in all_places:
                    continue

                # ---------------------------------
                # BASIC TYPE FILTERING
                # ---------------------------------

                place_types = place.get("types", [])

                if place_types:

                    valid = any(
                        t in ALLOWED_TYPES
                        for t in place_types
                    )

                    if not valid:
                        continue

                # ---------------------------------
                # EXTRACT DATA
                # ---------------------------------

                result = {
                    "searched_brand": store,
                    "searched_area": area,
                    "query": query,

                    "place_id": place.get("id"),

                    "name": (
                        place.get("displayName", {})
                        .get("text")
                    ),

                    "address": place.get(
                        "formattedAddress"
                    ),

                    "latitude": (
                        place.get("location", {})
                        .get("latitude")
                    ),

                    "longitude": (
                        place.get("location", {})
                        .get("longitude")
                    ),

                    "types": place.get("types"),

                    "primary_type": place.get(
                        "primaryType"
                    ),

                    "google_maps_uri": place.get(
                        "googleMapsUri"
                    ),

                    "website_uri": place.get(
                        "websiteUri"
                    ),

                    "business_status": place.get(
                        "businessStatus"
                    ),

                    # VERY IMPORTANT
                    # Store raw object for future analysis
                    "raw_response": place,
                }

                all_places[place_id] = result
                final_results.append(result)

            # Rate limiting safety
            time.sleep(1)

        except Exception as e:

            print(f"ERROR: {query}")
            print(str(e))


# =========================================
# SAVE RESULTS
# =========================================

output_file = "places_results.json"

with open(output_file, "w", encoding="utf-8") as f:

    json.dump(
        final_results,
        f,
        ensure_ascii=False,
        indent=2
    )

print("\n=====================================")
print(f"TOTAL UNIQUE PLACES: {len(final_results)}")
print(f"DATA SAVED TO: {output_file}")
print("=====================================")