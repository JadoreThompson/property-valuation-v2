import os
from dotenv import load_dotenv
import urllib.request
from urllib.parse import urlencode
import asyncio
import aiohttp


def run_dojo():
    while True:
        prompt = input("You: ")
        print("Bot: ")


load_dotenv(".env")


def ons():
    ONS_TOKEN = os.getenv("ONS_TOKEN")

    headers = {
        # 'Accept': 'text/csv',
        "Accept": "application/json",
        'Authorization': f'Basic {ONS_TOKEN}'
    }

    # Define base URL and query parameters separately
    base_url = 'https://epc.opendatacommunities.org/api/v1/domestic/search'
    query_params = {'postcode': 'N21 2JP'}

    # Encode query parameters
    encoded_params = urlencode(query_params)

    # Append parameters to the base URL
    full_url = f"{base_url}?{encoded_params}"

    import json
    # Now make request
    with urllib.request.urlopen(urllib.request.Request(full_url, headers=headers)) as response:
        response_body = response.read()
        data = response_body.decode()
        # print(json.dumps(data, indent=4))
        parsed = json.loads(data)
        # print(parsed)
        print(parsed["rows"][0][""])


import json
async def one():
    async with aiohttp.ClientSession() as session:
        async with session.post("https://data.police.uk/api/crimes-street/all-crime?lat=51.595172&lng=-0.378002&date=2024-01") as rsp:
            data = await rsp.json()
            print(json.dumps(data, indent=4))
            # print(len(data))


if __name__ == "__main__":
    asyncio.run(one())