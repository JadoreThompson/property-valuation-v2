import re
import asyncio
from playwright.async_api import async_playwright
import json

from propai import fetcher, proximities
from cleaning import run_clean

import numpy as np


async def scrape_economic_relations(property_info):
    sold_date = property_info["sold_date"][-1].split()
    year = sold_date[-1]
    month = sold_date[1]

    keys = [
        ("bank_rate", bank_rate, "rate"),
        ("inflation_rate", inflation_rate, "cpi_rate"),
    ]

    for pair in keys:
        property_info[pair[0]].append(pair[1][(pair[1]["year"] == int(year)) & (pair[1]["month"] == month)][pair[2]].values[0])

    "2 year 95% LTV"

    m_keys = [
        "2 year 95% LTV",
        "2 year 90% LTV",
        "2 year 75% LTV",
        "2 year 60% LTV",
        "2 year 85% LTV"
    ]
    for key in m_keys:
        property_info["_".join(key.split())].append(
            mortgage_rate[(mortgage_rate["year"] == int(year)) &
                           (mortgage_rate["month"] == month)][key].values[0])

    r_keys = [""
        "regional_employment",
        "regional_gdp"
    ]

    print("-----------")
    if int(year) < 2023:
        value = regional_employment[regional_employment['borough'] == regional_employment["borough"]]['2022'].values
        result = [value[0] if len(value) > 0 else np.nan]
        property_info[r_keys[0]].append(result)
    else:
        property_info[r_keys[0]].append(np.nan)

    if int(year) < 2024:
        value = regional_gdp[(regional_gdp["Year"] == int(year)) & (regional_gdp["Area Name"] == property_info["borough"])]["Value"].values
        result = [value[0] if len(value) > 0 else np.nan]
        property_info[r_keys[1]].append(result)
    else:
        property_info[r_keys[1]].append(np.nan)

    property_info["year"].append(int(year))
    property_info["month"].append(month)
    property_info["day"].append(int(sold_date[0]))

    return property_info


async def scrape_ammenities(address, property_info):
    lat, lng = await fetcher.get_lat_long(address)

    amenity_distances = {}
    for item in proximities.proximity_ammenities:
        amenity_distances.update(await proximities.get_proximity(
            lat1=lat,
            lng1=lng,
            nearest=item[0],
            type_to_target=item[1],
            topic_name=item[2]
        ))

    amenity_distances.update(proximities.get_central_london_proximity(lat, lng))
    amenity_distances.update(await proximities.get_school_proximity(lat, lng))

    for key in [kn for kn in amenity_distances]:
        property_info[key].append(amenity_distances.get(key, np.nan))
    return property_info


async def scrape_more_features_from_face(listing, property_info):
    more_features = await fetcher.get_epc_rating(listing)

    property_info["epc_rating"].append(more_features[0])
    property_info["sqm"].append(more_features[1])
    property_info["borough"].append(more_features[2])
    property_info["postcode"].append(more_features[3])
    property_info["town"].append("London")
    property_info["council_tax_band"].append(await fetcher.get_council_tax_band(listing))
    property_info["crime_rate"].append(await fetcher.get_crime_rate(listing))

    return property_info


async def scrape_face(page, listing, property_info):
    property_info["address"].append(listing)

    feature_locators = [
        ("p:has(span:has-text('number of bedrooms'))", "bedrooms"),
        ("p:has(span:has-text('number of bathrooms'))", "bathrooms"),
        ("p:has(span:has-text('type of property'))", "property_type"),
        (".jzbJiun6qp6OGztBJ0zpJ", "estate_type"),
        ("._2Dz8cX76Q51EJE_1aidJrI", "sold_date"),
        ("._1uI3IvdF5sIuBtRIvKrreQ", "extra_features")
    ]

    for item in feature_locators:
        try:
            feature_locator = page.locator(item[0])

            if item[1] in ["estate_type", "sold_date"]:
                feature = await feature_locator.nth(0).text_content()
            else:
                feature = await feature_locator.text_content()

            if item[1] in ["property_type", "estate_type"]:
                feature = feature.split()[-1]
            elif item[1] in ["sold_date", "extra_features"]:
                pass
            else:
                feature = int(feature[-1])

            if not isinstance(feature, int) and not feature.strip():
                feature = np.nan
            property_info[item[1]].append(feature)
        except Exception as e:
            print(e)
            continue
    return property_info


async def scrape_individual_page_listing(listing, page):
    try:
        await page.locator(f"a:has-text('{listing}')").click(timeout=3000)
    except Exception as e:
        print(e)
        return

    try:
        property_info = {
            "sold_date": [],
            "year": [],
            "month": [],
            "day": [],
            "property_type": [],
            "estate_type": [],
            "bedrooms": [],
            "bathrooms": [],
            "sqm": [],
            "address": [],
            "postcode": [],
            "town": [],
            "borough": [],
            "council_tax_band": [],
            "crime_rate": [],
            "epc_rating": [],
            "park_distance": [],
            "park_name": [],
            "primary_school_distance": [],
            "primary_school_name": [],
            "secondary_school_distance": [],
            "secondary_school_name": [],
            "train_station_distance": [],
            "train_station_name": [],
            "shopping_mall_distance": [],
            "shopping_mall_name": [],
            "gym_distance": [],
            "gym_name": [],
            "leisure_distance": [],
            "leisure_name": [],
            "proximity_to_london": [],
            # "interest_rate": [],
            "inflation_rate": [],
            "bank_rate": [],
            # "mortgage_rate": [],
            "2_year_95%_LTV": [],
            "2_year_90%_LTV": [],
            "2_year_75%_LTV": [],
            "2_year_60%_LTV": [],
            "2_year_85%_LTV": [],
            "regional_employment": [],
            "regional_gdp": [],
            "extra_features": []
        }

        property_info = await scrape_face(page, listing, property_info)
        property_info = await scrape_more_features_from_face(listing, property_info)
        property_info = await scrape_ammenities(listing, property_info)
        property_info = await scrape_economic_relations(property_info)
        print(json.dumps(property_info, indent=4))
    except Exception as e:
        print("scrape individual page listing: ", e)
    finally:
        await asyncio.sleep(2)
        await page.go_back()


# ---------------------------
# Scraping the landing page
# --------------------------

def get_listing(lines):
    locations = []

    for line in lines:
        if re.match(r'^(?:(?:\d+|Flat\s+\d+|Apartment\s+\d+),\s+[\w\s]+,)', line):
            locations.append(line)
    return locations


async def handle_page_listings(all_page_listings):
    for _, item in enumerate(all_page_listings, 1):
        page_text = await item.inner_text()
        starting_point = page_text.find("Page desc")
        lines = page_text[starting_point + len("Page desc"):].strip().split("\n")
        listings = get_listing(lines)
    return listings


async def get_page_listings(page):
    while True:
        try:
            all_page_listings = await page.locator(".results").all()
            if all_page_listings:
                page_listings = await handle_page_listings(all_page_listings)
                for listing in page_listings:
                    await scrape_individual_page_listing(listing, page)
                try:
                    await page.wait_for_selector('div.pagination.pagination-next', state='visible', timeout=5000)
                    await page.click('div.pagination.pagination-next:has-text("Next")')
                except Exception as e:
                    print(f"get page listings: {e}")
                    break
        except Exception as e:
            print(e)


# ------------------------------
#                    Run
# ------------------------------
async def launch_scraper(page, location):
    url = f"https://www.rightmove.co.uk/house-prices/{location}.html?soldIn=2&page=1"
    await page.goto(url)
    await page.locator("button:has-text('Accept all')").click()
    await get_page_listings(page)
    await asyncio.sleep(10000)


async def run(location):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await launch_scraper(page, location)

        await browser.close()


def main():
    location = "london"
    asyncio.run(run(location))


if __name__ == "__main__":
    (bank_rate, mortgage_rate, regional_employment, inflation_rate,
     regional_gdp) = run_clean()
    main()
