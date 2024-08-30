import asyncio
import os
from dotenv import load_dotenv

import re
import aiohttp
from urllib.parse import urlencode
import numpy as np

from proximities import ROOT_DIR


load_dotenv(ROOT_DIR + ".env")

ONS_TOKEN = os.getenv("ONS_TOKEN")
ONS_HEADER = {
    "Accept": "application/json",
    'Authorization': f'Basic {ONS_TOKEN}'
}


def find_town(address):
    pattern = r',\s*([^,]+),\s*Greater London'
    match = re.search(pattern, address)
    if match:
        return match.group(1)
    return np.nan


def find_street(address):
    pattern = r'^(.*?),\s*([^,]+),\s*Greater London'
    match = re.search(pattern, address)
    if match:
        return match.group(1).strip()
    return np.nan


def find_postcode(address):
    postcode = address.split()[-2:]
    return "".join(postcode)


'''
    Returns a list of:
        - EPC rating
        - SQM
        - Town 
        - Borough 
        - Postcode
'''
async def get_epc_rating(address):
    try:
        postcode = find_postcode(address)
        if postcode is None:
            return np.nan
    except Exception as e:
        print(e)

    base_url = 'https://epc.opendatacommunities.org/api/v1/domestic/search'

    query_params = {"postcode": postcode}
    encoded_params = urlencode(query_params)

    full_url = f"{base_url}?{encoded_params}"

    async with aiohttp.ClientSession() as session:
        async with session.get(full_url, headers=ONS_HEADER) as rsp:
            epc_data = await rsp.json()

    details = []
    for item in epc_data["rows"]:
        if item["address"] == find_street(address):
            print(item)
            details.append(item.get("current-energy-rating", np.nan))
            details.append(float(item.get("total-floor-area", np.nan)))
            details.append(find_town(address))
            details.append(item.get("local-authority-label", np.nan))
            details.append(postcode)
    print(details)
    return details


if __name__ == "__main__":
    asyncio.run(get_epc_rating("12, Gwyn Close, London, Greater London SW6 2EQ"))
