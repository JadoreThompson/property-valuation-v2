import asyncio
import random
from datetime import datetime
from thefuzz import fuzz
from urllib.parse import urlencode
import re
import json
from bs4 import BeautifulSoup

import os
from dotenv import load_dotenv

import pandas
import pandas as pd

import googlemaps
from google.cloud import storage
from google.cloud.storage import transfer_manager

#Directory Modules
from db_connection import get_db_conn

load_dotenv("../.env")

# Google
GOOGLE_CREDS = "../prop-llm-80aaec11f50b.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CREDS

ONS_TOKEN = os.getenv("ONS_TOKEN")
ONS_HEADER = {
    "Accept": "application/json",
    'Authorization': f'Basic {ONS_TOKEN}'
}

storage_client = storage.Client.from_service_account_json(GOOGLE_CREDS)
bucket = storage_client.bucket(bucket_name=os.getenv("BUCKET_NAME"))

user_agents = [
    # Android User Agents
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36,gzip(gfe)",
    "Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S901U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S908U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-G991U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-G998U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A536U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A515F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-A515U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 6a) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 6 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; moto g pure) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; moto g stylus 5G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; moto g stylus 5G (2022)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; moto g 5G (2022)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; moto g power (2022)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; moto g power (2021)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Redmi Note 9 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; Redmi Note 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; VOG-L29) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; MAR-LX1A) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; M2101K6G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; M2102J20SG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; 2201116SG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; DE2118) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",

    # iPhone User Agents
    "Mozilla/5.0 (iPhone14,6; U; CPU iPhone OS 15_4 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Mobile/19E241 Safari/602.1",
    "Mozilla/5.0 (iPhone14,3; U; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Mobile/19A346 Safari/602.1",
    "Mozilla/5.0 (iPhone13,2; U; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Mobile/15E148 Safari/602.1",
    "Mozilla/5.0 (iPhone12,1; U; CPU iPhone OS 13_0 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Mobile/15E148 Safari/602.1",
    "Mozilla/5.0 (iPhone11,4; U; CPU iPhone OS 12_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Mobile/16B91 Safari/605.1",
    "Mozilla/5.0 (iPhone11,2; U; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Mobile/16A366 Safari/605.1",
    "Mozilla/5.0 (iPhone10,6; U; CPU iPhone OS 11_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.3 Mobile/15E302 Safari/605.1",
    "Mozilla/5.0 (iPhone10,5; U; CPU iPhone OS 11_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.2 Mobile/15C107 Safari/605.1",
    "Mozilla/5.0 (iPhone9,4; U; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.3 Mobile/14E277 Safari/603.1",
    "Mozilla/5.0 (iPhone9,3; U; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.3 Mobile/14E277 Safari/603.1"
]


def detect_platform_and_mobile(user_agent):
    """
    Detects the platform and mobile status from the User-Agent string.
    """

    platform = "Unknown"
    is_mobile = "?0"  # Default to non-mobile unless detected otherwise

    # Determine platform
    if "Android" in user_agent:
        platform = "Android"
        is_mobile = "?1"
    elif "iPhone" in user_agent or "iPad" in user_agent:
        platform = "iOS"
        is_mobile = "?1"
    elif "Macintosh" in user_agent:
        platform = "macOS"
    elif "Windows NT" in user_agent:
        platform = "Windows"
    elif "Linux" in user_agent:
        platform = "Linux"
    elif "CrOS" in user_agent:
        platform = "Chrome OS"

    # Check if the device is mobile or not based on the user-agent
    if "Mobile" in user_agent:
        is_mobile = "?1"

    return {
        "sec-ch-ua-platform": platform,
        "sec-ch-ua-mobile": is_mobile
    }


def set_header():
    user_agent = user_agents[random.randint(0, len(user_agents) - 1)]

    """
    Sets the HTTP headers including User-Agent, sec-ch-ua-mobile, and sec-ch-ua-platform.
    """
    platform_info = detect_platform_and_mobile(user_agent)

    headers = {
        "User-Agent": user_agent,
        "sec-ch-ua-mobile": platform_info["sec-ch-ua-mobile"],
        "sec-ch-ua-platform": platform_info["sec-ch-ua-platform"],
    }
    return headers


def find_town(address):
    pattern = r',\s*([^,]+),\s*Greater London'
    match = re.search(pattern, address)
    if match:
        return match.group(1)
    return pd.NA


def find_street(address):
    pattern = r'^(.*?),\s*([^,]+),\s*Greater London'
    match = re.search(pattern, address)
    if match:
        return match.group(1).strip()
    return pd.NA


def find_postcode(address):
    postcode = address.split()[-2:]
    return "".join(postcode)


async def get_epc_rating(postcode, session):
    '''
        :param postcode:
        :param session:
        :return: Tuple(epc_rating, total sqm)
    '''

    try:
        if postcode is None:
            return pd.NA
    except Exception as e:
        print("Get EPC Rating, ", e)

    base_url = os.getenv("ONS_API_LINK")
    query_params = {"postcode": postcode}
    encoded_params = urlencode(query_params)

    full_url = f"{base_url}?{encoded_params}"

    async with session.get(full_url, headers=ONS_HEADER) as rsp:
        epc_data = await rsp.json()

    epc_items = []
    for i in range(0, len(epc_data["rows"])):
        epc_items.append((
            epc_data["rows"][i].get("current-energy-rating", pd.NA),
            float(epc_data["rows"][i].get("total-floor-area", pd.NA))
        ))

    maximum = max([item[-1] for item in epc_items])
    for i in range(0, len(epc_items)):
        if epc_items[i][-1] == maximum:
            return epc_items[i]


async def get_crime_rate(postcode, session):
    '''
        :param postcode:
        :param session:
        :return: float(total_crime_rate)
    '''

    postcode = "".join(postcode.split())

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
            return float(total_rate)
        except KeyError:
            return pd.NA

    base_url = os.getenv("CRIME_RATE_API_LINK")
    link_to_scrape = base_url + f"{postcode}/crime"

    async with session.get(link_to_scrape) as rsp:
        html_document = await rsp.text()

    total_rate = extract_total_rate(html_document)
    return total_rate


async def get_council_tax_band(target_address, postcode, browser):
    '''
        :param target_address:
        :param postcode:
        :param browser:
        :return: str(council_tax_band)
    '''

    url = "https://www.tax.service.gov.uk/check-council-tax-band/search"

    context = await browser.new_context()
    page = await context.new_page()
    await page.goto(url)

    try:
        await page.locator("button:has-text('Reject additional cookies')").click(timeout=3000)
    except:
        print("Cookie button not found or already handled")
        await context.close()
        return pd.NA

    await page.fill("#postcode", postcode, timeout=3000)
    await page.keyboard.press("Enter")

    vals = []
    while True:
        try:
            await page.wait_for_selector(".govuk-table__body", timeout=3000)
            table_locator = page.locator(".govuk-table__body")
            content = await table_locator.inner_text(timeout=3000)

            content = content.split("\n")

            for item in content:
                cu = item.upper()
                count = fuzz.ratio(target_address, cu)
                vals.append({"address": item, "count": count})

            locator = page.locator("a.voa-pagination__link:has(span:has-text('Next'))")
            await locator.click(timeout=3000)

        except Exception as e:
            print("Get Council Rax Band, ", e)
            break

    await context.close()

    maximum = max([v["count"] for v in vals])

    for v in vals:
        if v["count"] == maximum:
            target = v["address"]
            target = target.split("\t")
            band = target[-2]
            return band


async def get_lat_long(postcode):
    '''
    :param postcode:
    :return: tuple(lat, long)
    '''
    gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))
    data = gmaps.geocode(f"{postcode}, EN")
    return data[0]["geometry"]["location"]["lat"], data[0]["geometry"]["location"]["lng"]


def upload_to_bucket(df):
    print("Attempting to upload to bucket...")
    try:
        blob = bucket.blob("rightmove{0}.csv".format(datetime.now().strftime("%Y-%m-%d 5H_%M_%S_%f")))
        blob.upload_from_string(df.to_csv(index=False), "text/csv")
        print("Successfully sent to bucket...")
    except Exception as e:
        print("Upload to Bucket, ", e)
        pass


def download_from_bucket(destination_directory="../data/scraped", max_results=1000, workers=10):
    blob_names = [blob.name for blob in bucket.list_blobs()]
    results = transfer_manager.download_many_to_path(
        bucket, blob_names, destination_directory=destination_directory, max_workers=workers
    )

    for name, result in zip(blob_names, results):
        # The results list is either `None` or an exception for each blob in
        # the input list, in order.

        if isinstance(result, Exception):
            print("Failed to download {} due to exception: {}".format(name, result))
        else:
            print("Downloaded {} to {}.".format(name, destination_directory + name))


def insert_to_db(df: pandas.DataFrame):
    """
    :param df:
    :return: Inserts scraped item to property_data table
    """

    with get_db_conn() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("""\
                SELECT 1\
                FROM property_data\
                WHERE full_address = %s AND sold_date = %s;
               """, (df["full_address"][0], df["sold_date"][0],))
                if cur.fetchone():
                    print("Insert to DB: This item already exists")
                    return

                # Inserting to table when doesn't already exist
                cur.execute(f"""\
                    INSERT INTO property_data({df.columns})
                    VALUES ({len([col for col in df.columns])})
                    ON CONFLICT DO NOTHING;
               """)
                conn.commit()
                print("Insert to DB: Successfully inserted item to DB")
            except Exception as e:
                conn.rollback()
                print(f"Insert to DB: {type(e).__name__} - {str(e)}")


if __name__ == "__main__":
    pass
