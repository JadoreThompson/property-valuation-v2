import asyncio
import time

import aiohttp
import pandas as pd
from playwright.async_api import async_playwright
import re
# from thefuzz import fuzz
from rapidfuzz import fuzz
from multiprocessing import Pool
import numpy as np

import cleaning
from propai import fetcher, proximities


async def scrape_economic_relations(row):
    month = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }[row["month"]]

    year = int(row["year"])
    district = row["district"]

    keys = [
        ("bank_rate", bank_rate, "rate"),
        ("inflation_rate", inflation_rate, "cpi_rate"),
        "2 year 95% LTV",
        "2 year 90% LTV",
        "2 year 75% LTV",
        "2 year 60% LTV",
        "2 year 85% LTV",
        "regional_employment",
        "regional_gdp"
    ]

    for key, df, id in keys[: 2]:
        try:
            row[key] = df[(df["year"] == year) & (df["month"] == month)][id].values[0]
        except IndexError:
            row[key] = pd.NA

    for key in keys[2: 7]:
        try:
            row["_".join(key.split())] = \
                mortgage_rate[(mortgage_rate["year"] == year) &
                               (mortgage_rate["month"] == month)][key].values[0]
        except IndexError:
            row["_".join(key.split())] = pd.NA

    if int(row["year"]) < 2024:
        regional_gdp.set_index('borough', inplace=True)
        try:
            row[keys[-2]] = regional_gdp.at[district, '2022']
        except KeyError:
            row[keys[-2]] = pd.NA
    else:
        row[keys[-2]] = pd.NA

    if year < 2023:
        regional_gdp.set_index("borough", inplace=True)
        try:
            row[keys[-1]] = regional_gdp.at[district, '2022']
        except KeyError:
            row[keys[-1]] = pd.NA
    else:
        row[keys[-1]] = pd.NA
    return row


async def scrape_amenities(row, postcode):
    lat, lng = await fetcher.get_lat_long(postcode)
    row["lat"], row["lng"] = lat, lng

    amenity_distances = {}
    tasks = [proximities.get_proximity(lat, lng, item[0], item[1], item[2]) for item in proximities.proximity_ammenities]
    results = await asyncio.gather(*tasks)
    for result in results:
        amenity_distances.update(result)

    amenity_distances.update(proximities.get_central_london_proximity(lat, lng))
    amenity_distances.update(await proximities.get_school_proximity(lat, lng))

    for key in [kn for kn in amenity_distances]:
        row[key] = amenity_distances.get(key, pd.NA)
    return row


async def scrape_more_features_from_face(row, address, postcode, session):
    epc_rating_task = fetcher.get_epc_rating(postcode, session)
    council_tax_band_task = fetcher.get_council_tax_band(address, postcode)
    crime_rate_task = fetcher.get_crime_rate(postcode, session)

    epc_rating_result, council_tax_band_result, crime_rate_result = await asyncio.gather(
        epc_rating_task,
        council_tax_band_task,
        crime_rate_task
    )

    row["epc_rating"], row["sqm"] = epc_rating_result
    row["council_tax_band"] = council_tax_band_result
    row["crime_rate"] = crime_rate_result
    return row


async def scrape_face(page, row, address):
    await asyncio.sleep(2)

    feature_locators = [
        ("p:has(span:has-text('number of bedrooms'))", "bedrooms"),
        ("p:has(span:has-text('number of bathrooms'))", "bathrooms"),
        ("p:has(span:has-text('type of property'))", "property_type"),
        (".jzbJiun6qp6OGztBJ0zpJ", "estate_type"),
        ("._2Dz8cX76Q51EJE_1aidJrI", "sold_date"),
        ("._1uI3IvdF5sIuBtRIvKrreQ", "extra_features")
    ]

    for locator, feature_name in feature_locators:
        try:
            feature_locator = page.locator(locator)

            if feature_name in ["estate_type", "sold_date"]:
                feature = await feature_locator.nth(0).text_content(timeout=3000)
            else:
                try:
                    feature = await feature_locator.text_content(timeout=3000)
                except TimeoutError:
                    feature = np.nan

            if feature_name in ["property_type", "estate_type"]:
                feature = feature.split()[-1] if isinstance(feature, str) else pd.NA
            if feature_name in ["bathrooms", "bedrooms"]:
                try:
                    feature = int(feature.split()[-1])
                except (ValueError, AttributeError, IndexError):
                    feature = np.nan

            if isinstance(feature, str) and not feature.strip():
                feature = pd.NA

            row[feature_name] = feature
        except Exception as e:
            print(f"Error processing {feature_name}: {str(e)}")
            row[feature_name] = pd.NA
    return row


# Returns a tuple of the address and the fuzz ratio between it and the target address
def find_most_similar(full_address, page_listings):
    return max([(item, fuzz.partial_ratio(full_address[0], item)) for item in page_listings])


async def handle_page_listings(all_page_listings):
    for _, item in enumerate(all_page_listings, 1):
        page_text = await item.inner_text()
        starting_point = page_text.find("Page desc")
        lines = page_text[starting_point + len("Page desc"):].strip().split("\n")
        listings = [line for line in lines if re.match(r'^(?:(?:\d+|Flat\s+\d+|Apartment\s+\d+),\s+[\w\s]+,)', line)]
    return listings


async def scrape_postcode(page, row):
    await asyncio.sleep(3)
    address = row["address"]
    postcode = row["postcode"]

    try:
        input_locator = page.locator('input.search-box-input')
        input_locator = input_locator.nth(1)
        await input_locator.fill("")
        await input_locator.fill(postcode)
        await input_locator.press("Enter")
    except Exception as e:
        print(e)
        return row

    try:
        # Getting listings
        await asyncio.sleep(2)
        all_page_listings = await page.locator(".results").all()
        page_listings = await handle_page_listings(all_page_listings)
        page_listings = [item.upper() for item in page_listings]

        # Finding most similar
        most_similar = find_most_similar(address, page_listings)
        await page.locator(f"a:has-text('{most_similar[0]}')").click(timeout=5000)

        async with aiohttp.ClientSession() as session:
            row = await scrape_more_features_from_face(row, address, postcode, session)

        scrape_face_task = scrape_face(page, row, address)
        scrape_amenities_task = scrape_amenities(row, postcode)
        scrape_economic_relations_task = scrape_economic_relations(row)

        results = await asyncio.gather(
            scrape_face_task,
            scrape_amenities_task,
            scrape_economic_relations_task,
            return_exceptions=True
        )

        for result in results:
            row.update(result)

    except Exception as e:
        print("func: scrape postcode, ", e)
    finally:
        await page.go_back()
        return row


async def run2(row):
    url = "https://www.rightmove.co.uk/house-prices/e1-0ed.html?country=england&searchLocation=E1+0ED"
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Entering the site
            await page.goto(url)
            await page.locator("button:has-text('Accept all')").click()


            start_time = time.time()
            row = await scrape_postcode(page, row)
            new_df = pd.DataFrame([row])
            await fetcher.upload_to_bucket(new_df)
            end_time = time.time()
            print(f"Duration: {end_time - start_time} seconds*")

            print("Scraper Ending...")
            await browser.close()
            return row
    except Exception as e:
        print(f"function: run, {e}")
        return row


def run(row):
    asyncio.run(run2(row))


async def main():
    chunk_size = 10

    for i in range(0, len(data_2y), chunk_size):
        chunk = data_2y.iloc[i: i + chunk_size]
        rows = [row for _, row in chunk.iterrows()]
        with Pool(chunk_size) as p:
            p.map(run, rows)


if __name__ == "__main__":
    bank_rate, mortgage_rate, regional_employment, inflation_rate, \
        regional_gdp, data_2y = cleaning.run_clean()

    asyncio.run(main())
