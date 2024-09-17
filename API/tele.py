import datetime
import os

import requests
import aiohttp
from dotenv import load_dotenv
import asyncio

# Directory Modules
from API.models import ContactSalesForm

load_dotenv('.env')

TOKEN = os.getenv('TELE_API_KEY')
CHAT_ID = os.getenv('TELE_CHAT_ID')
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/"


async def notify_tele(session, form: ContactSalesForm = None):
    """
    :param session:
    :param form[ContactSalesForm]:
    :return: Tele Message
    """

    message = "Testing"
    if form:
        message = f"""\
        {form.name} has contacted Sales
        - Email: {form.email}
        - Phone: {form.phone}
        - No. Employees: {form.employees}
        - Message: {form.message}
        """

    url = BASE_URL + f"sendMessage?chat_id={CHAT_ID}&text={message}"
    async with session.get(url) as rsp:
        outcome = await rsp.json()
        if rsp.status == 200:
            if outcome["ok"]:
                print(outcome)
                return True
        print(outcome)
    return False

if __name__ == '__main__':
    pass
