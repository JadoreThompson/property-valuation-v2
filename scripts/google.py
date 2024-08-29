import asyncio
import os
from dotenv import load_dotenv
import math
import aiohttp
import json


ROOT_DIR = "../"
load_dotenv(ROOT_DIR + ".env")

URL = "https://places.googleapis.com/v1/places:searchText"
API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
HEADER = {
    'X-Goog-Api-Key': API_KEY,
    "X-Goog-FieldMask": "places.types,places.location,places.rating,places.formattedAddress,places.displayName",
    'Content-Type': 'application/json'
}


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


async def get_train_proximity(lat1, lng1):
    payload = {
        'textQuery': "nearest train station",
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

    print(json.dumps(data, indent=4))
    all_stations = {}
    for station in data["places"]:
        if "train_station" in station["types"]:
            all_stations[len(all_stations)] = {
                "name": station["displayName"]["text"],
                "distance": haversine(lat1, lng1, station["location"]["latitude"], station["location"]["longitude"])
            }

    all_distances = [item["distance"] for item in all_stations.values()]
    min_distance = min(all_distances)

    for station in all_stations.values():
        if station["distance"] == min_distance:
            print(station["name"])


if __name__ == "__main__":
    asyncio.run(get_train_proximity(51.5963606, -0.0349))
