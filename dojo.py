import aiohttp
import os
from dotenv import load_dotenv


def run_dojo():
    while True:
        prompt = input("You: ")
        print("Bot: ")


load_dotenv(".env")

url = "https://places.googleapis.com/v1/places:searchText"
places_api_key = os.getenv('GOOGLE_PLACES_API_KEY')
header = {
    'X-Goog-Api-Key': places_api_key,
    'X-Goog-FieldMask': 'places.displayName,places.name,places.id,places.websiteUri,places.nationalPhoneNumber,places.rating,nextPageToken',
    'Content-Type': 'application/json'
}
payload = {
    'textQuery': "schools",
    'locationBias': {
        'circle': {
            'center': {'latitude': 51.5964, 'longitude': 0.0349},
            'radius': 50000.0
        }
    },
    'pageSize': 100
}


async with aiohttp.ClientSession() as session:
    async with session.post(url, headers=header, json=payload) as rsp:
        print(rsp)



if __name__ == "__main__":
    run_dojo()