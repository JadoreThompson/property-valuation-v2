from typing import List, Any

import aiohttp
import asyncio
import os
from dotenv import load_dotenv
import json
from pprint import pprint

from langchain_core.tools import tool

load_dotenv("../.env")

# Environment Variables
SERP_ENDPOINT = "https://serpapi.com/search"
SERP_API_KEY = os.getenv("SERP_API_KEY")


#@tool
async def access_internet(tool_input: str) -> List[str]:
    """
    Return relating google search answers.

    :param tool_input:
    :return: List[Relating Answers]:
    """

    params = {
        "q": tool_input,
        "location": "United Kingdom",
        "api_key": SERP_API_KEY
    }

    # TODO: Abstract the past history of messages to get what the user is talking about
    async with aiohttp.ClientSession() as session:
        async with session.get(SERP_ENDPOINT, params=params) as rsp:
            data = await rsp.json()

            # Snippet is the key for the answer
            related_question_answers = [item["snippet"] for item in data["related_questions"]]

    return related_question_answers


if __name__ == "__main__":
    asyncio.run(access_internet("average price of house with in london"))
