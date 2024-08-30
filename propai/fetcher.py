import asyncio
import os

from thefuzz import fuzz
from dotenv import load_dotenv

import re
import aiohttp
from urllib.parse import urlencode
import json
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

import numpy as np

from propai.proximities import ROOT_DIR


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
        print("get epc rating: ", e)

    base_url = os.getenv("ONS_API_LINK")
    query_params = {"postcode": postcode}
    encoded_params = urlencode(query_params)

    full_url = f"{base_url}?{encoded_params}"

    async with aiohttp.ClientSession() as session:
        async with session.get(full_url, headers=ONS_HEADER) as rsp:
            epc_data = await rsp.json()
    # print(epc_data)
    details = {}
    for item in epc_data["rows"]:
        if item["address"] == find_street(address):
            details["epc"] = item.get("current-energy-rating", np.nan)
            details["sqm"] = float(item.get("total-floor-area", np.nan))
            details["borough"] = item.get("local-authority-label", np.nan)
            details["postcode"] = postcode
    return details


'''
    Returns the crime rate per thousand as a float
'''
async def get_crime_rate(postcode="DA145JG"):
    def extract_total_rate(html_content):
        soup = BeautifulSoup(html_content, 'html.parser')

        script_tag = soup.find('script', id='__NEXT_DATA__')

        if script_tag is None:
            return "Error: Could not find __NEXT_DATA__ script tag"

        json_data = json.loads(script_tag.string)

        try:
            total_rate = \
            json_data['props']['initialReduxState']['report']['sectionResponses']['crime']['data']['crimeLsoa'][
                'totalRate']
            return total_rate
        except KeyError:
            return "Error: Could not find totalRate in the JSON data"

    base_url = os.getenv("CRIME_RATE_API_LINK")
    link_to_scrape = base_url + f"{postcode}/crime"
    async with aiohttp.ClientSession() as session:
        async with session.get(link_to_scrape) as rsp:
            html_document = await rsp.text()

    total_rate = extract_total_rate(html_document)
    return float(total_rate)


def find_closes():
    # for
    pass


async def get_council_tax_band(
        address="Third Floor Flat, 49, Ossington Street, London, Greater London W2 4LY", postcode="W24LY"):

    address = address.replace(",", "")
    address = address.split()
    address = " ".join(address[:-4]).upper()

    url = "https://www.tax.service.gov.uk/check-council-tax-band/search"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)

        try:
            await page.locator("button:has-text('Reject additional cookies')").click(timeout=5000)
        except:
            print("Cookie button not found or already handled")

        await page.fill("#postcode", postcode)
        await page.keyboard.press("Enter")

        vals = []
        while True:
            try:
                await page.wait_for_selector(".govuk-table__body", timeout=10000)
                table_locator = page.locator(".govuk-table__body")
                content = await table_locator.inner_text()

                content = content.split("\n")

                for c in content:
                    cu = c.upper()
                    count = fuzz.ratio(address, cu)
                    vals.append({"address": c, "count": count})

                locator = page.locator("a.voa-pagination__link:has(span:has-text('Next'))")
                await locator.click(timeout=5000)

            except Exception as e:
                print(e)
                break

    maximum = max([v["count"] for v in vals])

    for v in vals:
        if v["count"] == maximum:
            target = v["address"]
            target = target.split("\t")
            band = target[-2]
            return band


if __name__ == "__main__":
    asyncio.run(get_council_tax_band())
    pass
