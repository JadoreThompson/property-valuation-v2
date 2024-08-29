import asyncio
import os
from dotenv import load_dotenv
import aiohttp
import json
from scripts.msc import haversine
import googlemaps

def run_dojo():
    while True:
        prompt = input("You: ")
        print("Bot: ")


async def google():
    load_dotenv(".env")

    url = "https://places.googleapis.com/v1/places:searchText"
    places_api_key = os.getenv('GOOGLE_PLACES_API_KEY')
    header = {
        'X-Goog-Api-Key': places_api_key,
        # 'X-Goog-FieldMask': 'places.formattedAddress,places.displayName,places.name,places.id,places.websiteUri,places.nationalPhoneNumber,places.rating,nextPageToken',
        "X-Goog-FieldMask": "places.types,places.location,places.rating,places.formattedAddress,places.displayName",
        'Content-Type': 'application/json'
    }
    payload = {
        'textQuery': "gym",
        'locationBias': {
            'circle': {
                'center': {'latitude': 51.5963606, 'longitude': -0.0349},
                'radius': 50000.0
            }
        },
        'pageSize': 100
    }

    # try:
    #     gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))
    #     data = gmaps.geocode("Pinner")
    #     print(data)
    # except Exception as e:
    #     print(e)

    async with aiohttp.ClientSession() as session:
        async with session.post("https://data.police.uk/api/crimes-street/all-crime?lat=51.595172&lng=-0.378002&date=2024-01") as rsp:
            data = await rsp.json()
            # print(json.dumps(data, indent=4))
            print(len(data))

    # async with aiohttp.ClientSession() as session:
    #     async with session.post(url, headers=header, json=payload) as rsp:
    #         data = await rsp.json()
    #         print(json.dumps(data, indent=4))
            # dict = {}
            #
            # for school in data["places"]:
            #     if "primary_school" in school["types"]:
            #         distance = haversine(51.5963606, -0.0349, school["location"]["latitude"],
            #                              school["location"]["longitude"])
            #         dict[len(dict)] = {"name": school["displayName"]["text"], "distance": distance, "type": "primary"}
            #
            #     if "secondary_school" in school["types"]:
            #         distance = haversine(51.5963606, -0.0349, school["location"]["latitude"],
            #                              school["location"]["longitude"])
            #         dict[len(dict)] = {"name": school["displayName"]["text"], "distance": distance, "type": "secondary"}
            #
            # prim_dis = [item["distance"] for item in dict.values() if item["type"] == "primary"]
            # sec_dis = [item["distance"] for item in dict.values() if item["type"] == "secondary"]
            #
            # print("Min prim: ", min(prim_dis))
            # print("Min sec: ", min(sec_dis))
            # for item in dict.values():
            #     if item["distance"] == min(prim_dis):
            #         print(item["name"])
            #     if item["distance"] == min(sec_dis):
            #         print(item["name"])


if __name__ == "__main__":
    import pandas as pd
    asyncio.run(google())
