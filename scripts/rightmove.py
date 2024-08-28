import asyncio
from playwright.async_api import async_playwright


async def launch_scraper(page, location):
    url = f"https://www.rightmove.co.uk/house-prices/{location}.html?soldIn=2&radius=0.25&page=1"
    await page.goto(url)
    await page.locator("button:has-text('Accept all')").click()
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
