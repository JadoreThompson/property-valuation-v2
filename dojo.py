import os
from dotenv import load_dotenv


def run_dojo():
    while True:
        prompt = input("You: ")
        print("Bot: ")


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

from datetime import datetime, timedelta
d = datetime.today() - timedelta(days=365)

current_year = datetime.today().year
previous_year = (datetime.today() - timedelta(days=365)).year
# print(f"""
#     SELECT (AVG(CASE WHEN year = {current_year} THEN price_paid END) -
#     AVG(CASE WHEN year = {previous_year} THEN price_paid END))
#     AVG(CASE WHEN year = {previous_year} THEN price_paid END)
#     FROM property_data;
# """)

if __name__ == "__main__":
    pass
