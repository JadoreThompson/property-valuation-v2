import asyncio
import time

import aiohttp
import pandas as pd
from playwright.async_api import async_playwright
import re
from thefuzz import fuzz
from multiprocessing import Pool

from scripts import cleaning
from propai import fetcher, proximities


bank_rate, mortgage_rate, regional_employment, inflation_rate, \
    regional_gdp, data_2y = cleaning.run_clean()

regional_gdp.set_index("borough", inplace=True)


async def scrape_economic_relations(row):
    print("Starting scrape_economic_relations")
    month = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }[row["month"]]

    year = int(row["year"])
    district = row["district"].title()

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

    for key, dataframe, id in keys[: 2]:
        try:
            row[key] = dataframe[(dataframe["year"] == year) & (dataframe["month"] == month)][id].values[0]
        except IndexError:
            row[key] = pd.NA

    for key in keys[2: 7]:
        try:
            row["_".join(key.split())] = \
                mortgage_rate[(mortgage_rate["year"] == year) &
                               (mortgage_rate["month"] == month)][key].values[0]
        except IndexError:
            row["_".join(key.split())] = pd.NA

    if year < 2024:
        try:
            row[keys[-2]] = regional_employment.loc[
                (regional_employment["Area name"] == district) &
                (regional_employment["Year"] == str(year))
            ]["Value"].values[0]
        except Exception:
            row[keys[-2]] = pd.NA
    else:
        row[keys[-2]] = pd.NA

    if year == 2022:
        try:
            row[keys[-1]] = regional_gdp.at[str(district), '2022']
        except Exception:
            row[keys[-1]] = pd.NA
    else:
        row[keys[-1]] = pd.NA

    return row


async def scrape_amenities(row, postcode):
    print(f"Starting scrape_amenities for {postcode}")
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


async def scrape_more_features_from_face(row, address, postcode, session, browser):
    print(f"Starting scrape_more_features_from_face for {address}, {postcode}")
    epc_rating_task = fetcher.get_epc_rating(postcode, session)
    council_tax_band_task = fetcher.get_council_tax_band(address, postcode, browser)
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


async def scrape_face(page, row):
    print(f"Starting scrape_face")
    await asyncio.sleep(2)

    feature_locators = [
        ("p:has(span:has-text('number of bedrooms'))", "bedrooms"),
        ("p:has(span:has-text('number of bathrooms'))", "bathrooms"),
        ("p:has(span:has-text('type of property'))", "property_type"),
        (".jzbJiun6qp6OGztBJ0zpJ", "estate_type"),
        ("._1uI3IvdF5sIuBtRIvKrreQ", "extra_features")
    ]

    for locator, feature_name in feature_locators:
        try:
            feature_locator = page.locator(locator)

            if feature_name in ["estate_type"]:
                feature = await feature_locator.nth(0).text_content(timeout=3000)
            else:
                try:
                    feature = await feature_locator.text_content(timeout=3000)
                except TimeoutError:
                    feature = pd.NA

            if feature_name in ["property_type", "estate_type"]:
                feature = feature.split()[-1] if isinstance(feature, str) else pd.NA
            if feature_name in ["bathrooms", "bedrooms"]:
                try:
                    feature = int(feature.split()[-1])
                except (ValueError, AttributeError, IndexError):
                    feature = pd.NA

            if isinstance(feature, str) and not feature.strip():
                feature = pd.NA

            row[feature_name] = feature
        except Exception as e:
            print(f"Error processing {feature_name}: {str(e)}")
            row[feature_name] = pd.NA
    return row


def custom_address_comparison(address1, address2):
    parts1 = address1.split(',')
    parts2 = address2.split(',')

    number1 = parts1[0].strip()
    number2 = parts2[0].strip()

    if number1 != number2:
        return 50

    rest_of_address1 = ','.join(parts1[1:])
    rest_of_address2 = ','.join(parts2[1:])
    return fuzz.token_set_ratio(rest_of_address1, rest_of_address2)


def find_most_similar(target_address, page_listings):
    best_match = None
    best_score = -1

    for listing in page_listings:
        score = custom_address_comparison(target_address, listing)
        if score > best_score:
            best_score = score
            best_match = listing

    return best_match, best_score


async def handle_page_listings(all_page_listings):
    all_listings = []
    print("Handling page listings")
    for _, item in enumerate(all_page_listings, 1):
        page_text = await item.inner_text()
        starting_point = page_text.find("Page desc")
        lines = page_text[starting_point + len("Page desc"):].strip().split("\n")
        listings = [line for line in lines if re.match(r'^(?:(?:\d+|Flat\s+\d+|Apartment\s+\d+),\s+[\w\s]+,)', line)]
        all_listings.extend(listings)
    return all_listings


async def scrape_postcode(page, row, browser):
    await asyncio.sleep(3)
    address = row["address"]
    postcode = row["postcode"]
    print(f"Starting scrape_postcode for {postcode}")

    try:
        input_locator = page.locator('input.search-box-input')
        input_locator = input_locator.nth(1)
        await input_locator.fill("")
        await input_locator.fill(postcode)
        await input_locator.press("Enter")
    except Exception as e:
        print(f"Error filling postcode search box: {e}")
        return row

    try:
        await asyncio.sleep(2)
        all_page_listings = await page.locator(".results").all()
        page_listings = await handle_page_listings(all_page_listings)
        page_listings = [item for item in page_listings]

        most_similar = find_most_similar(row["full_address"], page_listings)

        link_locator = page.get_by_role("link", name=most_similar[0])
        link_locator = link_locator.nth(0)
        await link_locator.click(timeout=5000)
        print("Clicked Address...")

        async with aiohttp.ClientSession() as session:
            row = await scrape_more_features_from_face(row, address, postcode, session, browser)

        scrape_face_task = scrape_face(page, row)
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
        print(f"Error in scrape_postcode: {e}")
    finally:
        return row


async def run2(row):
    url = "https://www.rightmove.co.uk/house-prices/e1-0ed.html?country=england&searchLocation=E1+0ED"
    try:
        async with async_playwright() as p:
            print("Launching browser")
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            print("Navigating to URL")
            await page.goto(url)
            await page.locator("button:has-text('Accept all')").click()

            start_time = time.time()
            row = await scrape_postcode(page, row, browser)
            new_df = pd.DataFrame([row])
            fetcher.upload_to_bucket(new_df)
            end_time = time.time()
            print(f"Duration: {end_time - start_time} seconds")
    except Exception as e:
        print(f"Error in run2: {e}")
    finally:
        print("Closing browser")
        await browser.close()
        return row


def run(row):
    asyncio.run(run2(row))


async def main():
    chunk_size = 5
    print("Starting main function")

    with Pool(chunk_size) as p:
        for i in range(0, len(data_2y), chunk_size):
            chunk = data_2y.iloc[i: i + chunk_size]
            print(f"Processing chunk {i // chunk_size + 1}")
            p.map(run, [row for _, row in chunk.iterrows()])
