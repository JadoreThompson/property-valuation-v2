import asyncio
import aiohttp

#from Valora.prompt_gen import get_llm_response


async def test_llm_response():
    questions = [
        "average price of a house in enfield",
        """what's the difference in price between flats houses in enfield\
        from last year to this year""",
    ]

    async with aiohttp.ClientSession() as session:
        for q in questions:
            data = {"question": q}
            async with session.post("http://127.0.0.1:80/get-response", data=data) as rsp:
                print(f"You: {q}")
                print(f"Bot: {await rsp.json()}")


if __name__ == "__main__":
    asyncio.run(test_llm_response())
