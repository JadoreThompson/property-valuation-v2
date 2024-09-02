import asyncio
import os

import pandas as pd
from dotenv import load_dotenv
import math
import aiohttp
from app import ROOT_DIR


load_dotenv(os.path.join(ROOT_DIR, ".env"))

# --------Google textSearch-------------
URL = "https://places.googleapis.com/v1/places:searchText"
API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
HEADER = {
    'X-Goog-Api-Key': API_KEY,
    "X-Goog-FieldMask": "places.types,places.location,places.rating,places.formattedAddress,places.displayName",
    'Content-Type': 'application/json'
}

# ----------Ammenities-------------
proximity_ammenities = [
    ("train station", "train_station", "train_station"),
    ("shopping mall", "shopping_mall", "shopping_mall"),
    ("leisure facility", "health", "leisure"),
    ("gym", "gym", "gym"),
    ("park", "park", "park")
]


# -----------Script------------
def haversine(lat1, lon1, lat2, lon2):
    # distance between latitudes
    # and longitudes
    dLat = (lat2 - lat1) * math.pi / 180.0
    dLon = (lon2 - lon1) * math.pi / 180.0

    # convert to radians
    lat1 = (lat1) * math.pi / 180.0
    lat2 = (lat2) * math.pi / 180.0

    # apply formulae
    a = (pow(math.sin(dLat / 2), 2) +
         pow(math.sin(dLon / 2), 2) *
         math.cos(lat1) * math.cos(lat2));
    rad = 6371
    c = 2 * math.asin(math.sqrt(a))

    km = float(rad * c)
    miles = float(km * 0.621371)

    return miles


async def get_school_proximity(lat1, lng1):
    payload = {
        'textQuery': "schools",
        'locationBias': {
            'circle': {
                'center': {'latitude': lat1, 'longitude': lng1},
                'radius': 50000.0
            }
        },
        'pageSize': 100
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(URL, headers=HEADER, json=payload) as rsp:
                data = await rsp.json()
    except Exception:
        return {
            "primary_school_distance": pd.NA,
            "primary_school_name": pd.NA,
            "secondary_school_distance": pd.NA,
            "secondary_school_name": pd.NA
        }

    schools_dict = []

    for school in data.get("places", []):
        school_types = school.get("types", [])
        location = school.get("location", {})

        if "primary_school" in school_types or "secondary_school" in school_types:
            try:
                distance = haversine(lat1, lng1, location.get("latitude"), location.get("longitude"))
            except Exception:
                distance = pd.NA

            schools_dict.append({
                "name": school.get("displayName", {}).get("text", pd.NA),
                "distance": distance,
                "type": "primary" if "primary_school" in school_types else "secondary"
            })

    prim_dis = [item["distance"] for item in schools_dict if
                item["type"] == "primary" and not pd.isna(item["distance"])]
    sec_dis = [item["distance"] for item in schools_dict if
               item["type"] == "secondary" and not pd.isna(item["distance"])]

    return_dict = {
        "primary_school_distance": pd.NA,
        "primary_school_name": pd.NA,
        "secondary_school_distance": pd.NA,
        "secondary_school_name": pd.NA,
    }

    if prim_dis:
        min_prim = min(prim_dis)
        prim_school = next(
            (item for item in schools_dict if item["type"] == "primary" and item["distance"] == min_prim), None)
        if prim_school:
            return_dict["primary_school_distance"] = float(min_prim)
            return_dict["primary_school_name"] = prim_school["name"]

    if sec_dis:
        min_sec = min(sec_dis)
        sec_school = next(
            (item for item in schools_dict if item["type"] == "secondary" and item["distance"] == min_sec), None)
        if sec_school:
            return_dict["secondary_school_distance"] = float(min_sec)
            return_dict["secondary_school_name"] = sec_school["name"]

    return return_dict


async def get_proximity(lat1, lng1, nearest, type_to_target, topic_name):
    try:
        payload = {
            'textQuery': f"nearest {nearest}",
            'locationBias': {
                'circle': {
                    'center': {'latitude': lat1, 'longitude': lng1},
                    'radius': 50000.0
                }
            },
            'pageSize': 100
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(URL, headers=HEADER, json=payload) as rsp:
                data = await rsp.json()

        all_items = []
        for item in data["places"]:
            if type_to_target in item["types"]:
                all_items.append({
                    "name": item["displayName"]["text"],
                    "distance": haversine(lat1, lng1, item["location"]["latitude"], item["location"]["longitude"])
                })

        if all_items:
            all_distances = [item["distance"] for item in all_items]
            min_distance = min(all_distances)

            for item in all_items:
                if item["distance"] == min_distance:
                    return {
                        topic_name + "_distance": item["distance"],
                        topic_name + "_name": item["name"]
                    }
    except Exception as e:
        print("Get Proximity, ", e)


def get_central_london_proximity(lat1, lng1):
    central_london_lat = 51.507438
    central_london_lng = -0.1375026
    distance = haversine(lat1, lng1, central_london_lat, central_london_lng)
    return {"proximity_to_london": distance}


if __name__ == "__main__":
    pass
