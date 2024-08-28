import re
import asyncio
from playwright.async_api import async_playwright


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


async def scrape_individual_page_listing(listing, page):
    try:
        await page.locator(f"a:has-text('{listing}')").click(timeout=3000)
    except Exception as e:
        print(f"Couldn't find link for {listing}: {e}")
        return


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
    main()
