from dotenv import load_dotenv


def run_dojo():
    while True:
        prompt = input("You: ")
        print("Bot: ")


if __name__ == "__main__":
    run_dojo()


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

        while True:
            try:
                await page.wait_for_selector(".govuk-table__body", timeout=10000)
                table_locator = page.locator(".govuk-table__body")
                content = await table_locator.inner_text()

                content = content.split("\n")

                vals = []
                for c in content:
                    cu = c.upper()
                    # count = sum(1 for a, b in zip(cu, address) if a == b)
                    count = fuzz.ratio(address, cu)
                    vals.append({"address": c, "count": count})

                print(vals)

                maximum = max([v["count"] for v in vals])
                if maximum < 65:
                    locator = page.locator("a.voa-pagination__link:has(span:has-text('Next'))")
                    # locator = locator.nth(4)

                    await locator.click()
            # for v in vals:
            #     if v["count"] == maximum:
            #         target = v["address"]
            #         target = target.split("\t")
            #         band = target[-2]
            #
            # await asyncio.sleep(1000)
            # if len(band) > 1:
            #     band = np.nan
            #     print(band)
            #     return band
            # print(band)
            # return band
            except Exception as e:
                print(e)
                return np.nan