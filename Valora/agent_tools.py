from typing import List, Any, Optional, Type

import aiohttp
import asyncio
import os
from dotenv import load_dotenv
import json
from pprint import pprint
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright

from langchain.tools import BaseTool
from langchain_core.tools import tool
from pydantic import BaseModel, Field


load_dotenv("../.env")

# Environment Variables
SERP_ENDPOINT = "https://serpapi.com/search"
SERP_API_KEY = os.getenv("SERP_API_KEY")


class PropertySearchInput(BaseModel):
    location: str = Field(default=None, description="The location to search for properties")
    min_price: Optional[str] = Field(default=None, description="Minimum Price")
    max_price: Optional[str] = Field(default=None, description="Maximum Price")
    property_type: Optional[str] = Field(default=None, description="Type of property (e.g., house, flat, detached)")


class Property(BaseModel):
    address: str
    price: str
    description: str
    link: str


async def search_rightmove(search_params: PropertySearchInput) -> List[Property]:
    """
    :param search_params:
    :return: A list of properties from the first page that mach the features specified in the form
        of the Property Class
    """
    properties = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Constructing the URL
            url = f"https://www.rightmove.co.uk/property-for-sale/{search_params.location.title()}.html?"

            if search_params.min_price:
                url += f"minPrice={search_params.min_price}&"
            if search_params.max_price:
                url += f"maxPrice={search_params.max_price}&"
            if search_params.property_type:
                url += f"propertyTypes={search_params.property_type}&"

            url += "maxDaysSinceAdded=14"

            # Heading to the page
            await page.goto(url)

            # Handling cookie consent
            await page.locator("button:has-text('Accept All')").click(timeout=5000)

            # Handling each result card
            search_result_cards = await page.query_selector_all(".is-list")
            for card in search_result_cards:
                try:
                    address_locator = await card.query_selector("address")
                    address = await address_locator.get_attribute("title")

                    price_locator = await card.query_selector(".propertyCard-priceValue")
                    price = await price_locator.text_content()

                    description_locator = await card.query_selector("span[data-test='property-description'] span")
                    description = await description_locator.text_content()

                    link_locator = await card.query_selector("a[data-test='property-header']")
                    link = f"https://www.rightmove.co.uk{await link_locator.get_attribute("href")}"

                    properties.append(Property(
                        address=address,
                        price=price,
                        description=description,
                        link=link
                    ))
                except Exception as e:
                    #print(f"Search Rightmove: {type(e).__name__} - {str(e)}")
                    continue
    except Exception as e:
        #print(f"Search Rightmove: {type(e).__name__} - {str(e)}")
        pass
    finally:
        return properties


async def search_zoopla(search_params: PropertySearchInput):
    # TODO: Get proxy for headless mode, currently getting blocked
    """
    :param search_params:
    :return: A list of properties from the first page that mach the features specified in the form
        of the Property Class
    """
    properties = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Constructing URL
            url = f"https://www.zoopla.co.uk/for-sale/property/{search_params.location.lower()}/"
            url += f"?q={search_params.location.lower()}&results_sort=newest_listings&"

            if search_params.min_price:
                url += f"price_min={search_params.min_price}&"
            if search_params.max_price:
                url += f"price_max={search_params.max_price}&"
            if search_params.property_type:
                url += f"property_sub_type={search_params.property_type}&"

            # Heading to page and handling cookie
            await page.goto(url)
            await page.locator("#onetrust-accept-btn-handler").click(timeout=5000)

            # Handling all the cards
            result_cards = await page.query_selector_all(".dkr2t83")
            for card in result_cards:
                try:
                    address_locator = await card.query_selector("address")
                    address = await address_locator.text_content()

                    price_locator = await card.query_selector("p[data-testid='listing-price']")
                    price = await price_locator.text_content()

                    description_locator = await card.query_selector("._1lw0o5c1 ._14bi3x31c .m6hnz60 p")
                    description = await description_locator.text_content()

                    link_locator = await card.query_selector("._1lw0o5c1")
                    link = f"https://www.zoopla.co.uk{await link_locator.get_attribute("href")}"

                    properties.append(Property(
                        address=address,
                        price=price,
                        description=description,
                        link=link
                    ))
                except Exception as e:
                    # print(f"Search Zoopla: {type(e).__name__} - {str(e)}")
                    continue

    except Exception as e:
        # print(f"Search Zoopla: {type(e).__name__} - {str(e)}")
        pass
    finally:
        return properties


async def search_onthemarket(search_params: PropertySearchInput):
    properties = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Constructing the URL
            url = f"https://www.onthemarket.com/for-sale/{search_params.property_type if search_params.property_type else "property"}/{search_params.location.lower()}/?"

            if search_params.min_price:
                url += f"min-price={search_params.min_price}&"
            if search_params.max_price:
                url += f"max-price={search_params.max_price}&"

            # Going to page
            await page.goto(url)

            # Handling Cookie
            cookie = page.locator("button:has-text('Accept all')").nth(1)
            await cookie.click()

            await page.locator("button:has-text('Sort: Recommended')").click()
            await page.locator("span:has-text('Highest price')").click()

            # Handling all the cards
            result_cards = await page.query_selector_all(".otm-PropertyCard")
            for card in result_cards:
                try:
                    address_locator = await card.query_selector("span.address a")
                    address = await address_locator.text_content()

                    price_locator = await card.query_selector("div.otm-Price a")
                    price = await price_locator.text_content()

                    description_locator = await card.query_selector("div.otm-PropertyCardInfo ul")
                    description = await description_locator.text_content()

                    link_locator = await card.query_selector("div.otm-Price a")
                    link = f"https://www.onthemarket.com{await link_locator.get_attribute("href")}"

                    properties.append(Property(
                        address=address,
                        price=price,
                        description=description,
                        link=link
                    ))

                except Exception as e:
                    #print(f"Search Zoopla: {type(e).__name__} - {str(e)}")
                    continue

    except Exception as e:
        # print(f"On the Market: {type(e).__name__} - {str(e)}")
        pass
    finally:
        return properties


async def access_internet(query: str) -> List[str]:
    """
    Return relating google search answers.
    :param query:
    :return: List[Relating Answers]:
    """
    params = {
        "q": query,
        "location": "United Kingdom",
        "api_key": SERP_API_KEY
    }

    # TODO: Abstract the past history of messages to get what the user is talking about
    async with aiohttp.ClientSession() as session:
        async with session.get(SERP_ENDPOINT, params=params) as rsp:
            data = await rsp.json()
            # Snippet is the key for the answer
            related_question_answers = [item.get("snippet", None) for item in data["related_questions"]]

    return related_question_answers


class RightMoveSearchTool(BaseTool):
    name: str = "rightmove_search"
    description: str = "Search properties on Rightmove"
    args_schema: Type[BaseModel] = PropertySearchInput
    return_direct: bool = False

    def _run(self, location: str, min_price: Optional[str] = None, max_price: Optional[str] = None,
             property_type: Optional[str] = None):
        search_params = PropertySearchInput(
            location=location,
            min_price=min_price,
            max_price=max_price,
            property_type=property_type
        )
        results = asyncio.run(search_rightmove(search_params))
        return [result.dict() for result in results]

    async def _arun(self, location: str, min_price: Optional[str] = None, max_price: Optional[str] = None,
             property_type: Optional[str] = None):
        search_params = PropertySearchInput(
            location=location,
            min_price=min_price,
            max_price=max_price,
            property_type=property_type
        )
        results = await search_rightmove(search_params)
        return [result.dict() for result in results]


class ZooplaSearchTool(BaseTool):
    name: str = "zoopla_search"
    description: str = "Search properties on Zoopla"
    args_schema: Type[BaseModel] = PropertySearchInput
    return_direct: bool = False

    def _run(self, location: str, min_price: Optional[str] = None, max_price: Optional[str] = None,
             property_type: Optional[str] = None):
        search_params = PropertySearchInput(
            location=location,
            min_price=min_price,
            max_price=max_price,
            property_type=property_type
        )
        results = asyncio.run(search_zoopla(search_params))
        return [result.dict() for result in results]

    async def _arun(self, location: str, min_price: Optional[str] = None, max_price: Optional[str] = None,
             property_type: Optional[str] = None):
        search_params = PropertySearchInput(
            location=location,
            min_price=min_price,
            max_price=max_price,
            property_type=property_type
        )
        results = await search_zoopla(search_params)
        return [result.dict() for result in results]


if __name__ == "__main__":
    asyncio.run(search_onthemarket(PropertySearchInput(
        location="london",
        min_price="500000",
        property_type="detached"
    )))
