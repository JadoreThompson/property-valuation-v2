import asyncio
import time

import aiohttp
import pandas as pd
from playwright.async_api import async_playwright
import re
from thefuzz import fuzz
from tqdm import tqdm
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
    ]

    for key, df, id in keys:
        try:
            row[key] = df[(df["year"] == year) & (df["month"] == month)][id].values[0]
        except IndexError:
            row[key] = pd.NA

    m_keys = [
        "2 year 95% LTV",
        "2 year 90% LTV",
        "2 year 75% LTV",
        "2 year 60% LTV",
        "2 year 85% LTV"
    ]
    for key in m_keys:
        try:
            row["_".join(key.split())] = \
                mortgage_rate[(mortgage_rate["year"] == year) &
                               (mortgage_rate["month"] == month)][key].values[0]
        except IndexError:
            row["_".join(key.split())] = pd.NA

    r_keys = [""
        "regional_employment",
        "regional_gdp"
    ]

    if int(row["year"]) < 2024:
        try:
            value = \
            regional_employment[(regional_employment["Year"] == year) & (regional_employment["Area name"] == district)]["Value"].values

            result = [value[0] if len(value) > 0 else pd.NA]
            row[r_keys[0]] = result
        except IndexError:
            row[r_keys[0]] = pd.NA
    else:
        row[r_keys[0]] = pd.NA

    if year < 2023:
        try:
            value = regional_gdp[regional_gdp['borough'] == district]['2022'].values
            result = [value[0] if len(value) > 0 else pd.NA]
            row[r_keys[1]] = result
        except IndexError:
            row[r_keys[1]] = pd.NA
    else:
        row[r_keys[1]] = pd.NA

    return row


async def scrape_amenities(row, postcode):
    lat, lng = await fetcher.get_lat_long(postcode)
    row["lat"], row["lng"] = lat, lng

    amenity_distances = {}

    # for item in proximities.proximity_ammenities:
    #     amenity_distances.update(await proximities.get_proximity(
    #         lat1=lat,
    #         lng1=lng,
    #         nearest=item[0],
    #         type_to_target=item[1],
    #         topic_name=item[2]
    #     ))

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
    row["epc_rating"], row["sqm"] = await fetcher.get_epc_rating(postcode, session)
    row["council_tax_band"] = await fetcher.get_council_tax_band(address, postcode)
    row["crime_rate"] = await fetcher.get_crime_rate(postcode, session)
    return row


async def scrape_face(page, row):
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
                feature = await feature_locator.nth(0).text_content(timeout=5000)
            else:
                try:
                    feature = await feature_locator.text_content(timeout=3000)
                except TimeoutError:
                    feature = np.nan

            if feature_name in ["property_type", "estate_type"]:
                feature = feature.split()[-1] if isinstance(feature, str) else pd.NA
            elif feature_name in ["sold_date", "extra_features"]:
                pass
            else:
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


# def get_listing(lines):
#     locations = []
#
#     for line in lines:
#         if re.match(r'^(?:(?:\d+|Flat\s+\d+|Apartment\s+\d+),\s+[\w\s]+,)', line):
#             locations.append(line)
#     return locations


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
        await asyncio.sleep(5)
        all_page_listings = await page.locator(".results").all()
        page_listings = await handle_page_listings(all_page_listings)
        page_listings = [item.upper() for item in page_listings]

        # Finding most similar
        most_similar = find_most_similar(address, page_listings)
        await page.locator(f"a:has-text('{most_similar[0]}')").click(timeout=5000)

        async with aiohttp.ClientSession() as session:
            row = await scrape_more_features_from_face(row, address, postcode, session)

        scrape_face_task = scrape_face(page, row)
        scrape_amenities_task = scrape_amenities(row, postcode)
        scrape_economic_relations_task = scrape_economic_relations(row)

        results = await asyncio.gather(
            scrape_face_task,
            scrape_amenities_task,
            scrape_economic_relations_task
        )

        for result in results:
            row.update(result)

        # row = await scrape_face(page, row)
        # row = await scrape_ammenities(row, postcode)
        # row = await scrape_economic_relations(row)

    except Exception as e:
        print("func: scrape postcode, ", e)
    finally:
        await page.go_back()
        return row


async def run(row):
    url = "https://www.rightmove.co.uk/house-prices/e1-0ed.html?country=england&searchLocation=E1+0ED"
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()

            # Entering the site
            await page.goto(url)
            await page.locator("button:has-text('Accept all')").click()


            # coroutines = []
            # for _, row in tqdm(data_2y.iterrows(), total=len(data_2y)):
            #     coroutines.append(scrape_postcode(page, row))
            #
            # updated_rows = await asyncio.gather(*coroutines)
            # df_updated = pd.DataFrame(updated_rows)
            # await fetcher.upload_to_bucket(df_updated)

            start_time = time.time()
            row = await scrape_postcode(page, row)
            end_time = time.time()
            print(f"Duration: {end_time - start_time} seconds*")

            print("Scraper Ending...")
            await browser.close()
            return row
    except Exception as e:
        print(f"function: run, {e}")
        return row


# df = data_2y[0: 2]
async def main():
    updated_rows = []
    chunk_size = 3

    for i in range(0, len(data_2y), chunk_size):
        updated_rows = []

        chunk = data_2y.iloc[i: i + chunk_size]
        coroutines = [run(row) for _, row in chunk.iterrows()]
        chunk_results = await asyncio.gather(*coroutines)

        updated_rows.extend(chunk_results)
        df_updated = pd.DataFrame(updated_rows)
        await fetcher.upload_to_bucket(df_updated)

    # coroutines = []
    # for _, row in tqdm(df.iterrows(), total=len(df)):
    #     coroutines.append(run(row))
    # updated_rows = await asyncio.gather(*coroutines)


if __name__ == "__main__":
    # _, _, _, _, _, data_2y = cleaning.run_clean()
    bank_rate, mortgage_rate, regional_employment, inflation_rate, \
        regional_gdp, data_2y = cleaning.run_clean()

    asyncio.run(main())
