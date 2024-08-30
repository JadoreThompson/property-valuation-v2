import re
import asyncio
from playwright.async_api import async_playwright
import json

from cleaning import run_clean


async def scrape_face(page, listing, property_info):
    property_info["address"] = listing

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
                feature = feature
            else:
                feature = int(feature[-1])

            property_info[item[1]].append(feature)
            print(listing)
            print("Feature: ", item[1])
            print("Value: ", feature)
        except Exception as e:
            print(e)
            continue


async def scrape_individual_page_listing(listing, page):
    try:
        await page.locator(f"a:has-text('{listing}')").click(timeout=3000)
    except Exception as e:
        print(e)
        return

    try:
        # TODO: scrape data
        property_info = {
            "sold_date": [],
            "property_type": [],
            "estate_type": [],
            "bedrooms": [],
            "bathrooms": [],
            "sqm": [],
            "address": [],
            "postcode": [],
            "town": [],
            "city": [],
            "borough": [],
            "garden": [],
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
            "interest_rate": [],
            "inflation_rate": [],
            "bank_rate": [],
            "mortgage_rate": [],
            "regional_employment": [],
            "regional_unemployment": [],
            "extra_features": []
        }

        await scrape_face(page, listing, property_info)
    except Exception as e:
        print(f"Couldn't find link for {listing}: {e}")
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
    try:
        all_page_listings = await page.locator(".results").all()
        if all_page_listings:
            page_listings = await handle_page_listings(all_page_listings)
            for listing in page_listings:
                await scrape_individual_page_listing(listing, page)
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
