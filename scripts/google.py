import asyncio
import os
from dotenv import load_dotenv
import math
import aiohttp
import json


ROOT_DIR = "../"
load_dotenv(ROOT_DIR + ".env")

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
        ("train station", "train_station"),
        ("shopping mall", "shopping_mall"),
        ("leisure facility", "health"),
        ("gym", "gym")
    ]



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

    km = rad * c
    miles = float(km * 0.621371)

    return km


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

    async with aiohttp.ClientSession() as session:
        async with session.post(URL, headers=HEADER, json=payload) as rsp:
            data = await rsp.json()

    schools_dict = {}

    for school in data["places"]:
        if "primary_school" in school["types"]:
            distance = haversine(lat1, lng1, school["location"]["latitude"],
                                 school["location"]["longitude"])
            schools_dict[len(dict)] = {"name": school["displayName"]["text"], "distance": distance, "type": "primary"}

        if "secondary_school" in school["types"]:
            distance = haversine(lat1, lng1, school["location"]["latitude"],
                                 school["location"]["longitude"])
            schools_dict[len(dict)] = {"name": school["displayName"]["text"], "distance": distance, "type": "secondary"}

    prim_dis = [item["distance"] for item in schools_dict.values() if item["type"] == "primary"]
    sec_dis = [item["distance"] for item in schools_dict.values() if item["type"] == "secondary"]

    for item in schools_dict.values():
        if item["distance"] == min(prim_dis):
            # TODO: Handle
            pass
        if item["distance"] == min(sec_dis):
            # TODO: Handle
            pass


async def get_proximity(lat1, lng1, nearest, type):
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
    # print(data)
    all_topics = {}
    for item in data["places"]:
        if type in item["types"]:
            all_topics[len(all_topics)] = {
                "name": item["displayName"]["text"],
                "distance": haversine(lat1, lng1, item["location"]["latitude"], item["location"]["longitude"])
            }

    if len(all_topics) > 0:
        all_distances = [item["distance"] for item in all_topics.values()]
        min_distance = min(all_distances)

        for item in all_topics.values():
            if item["distance"] == min_distance:
                print(item)
                # TODO: Handle
                pass


if __name__ == "__main__":
    asyncio.run(get_proximity(
        51.5963606, -0.0349,
        nearest=proximity_ammenities[2][0],
        type=proximity_ammenities[2][1]
    ))
