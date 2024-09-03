import os
from dotenv import load_dotenv
from urllib.parse import quote

from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_google_genai import ChatGoogleGenerativeAI

from dojo import ROOT_DIR
from db_connection import get_db_conn


load_dotenv(os.path.join(ROOT_DIR, ".env"))

LANGCHAIN_TRACING_V2 = True
LANGCHAIN_ENDPOINT = "https://api.smith.langchain.com"
LANGCHAIN_API_KEY = str(os.getenv("LANGCHAIN_API_KEY"))
LANGCHAIN_PROJECT = "pr-roasted-prefix-54"

# Connecting to Database
password = os.getenv("DB_PASSWORD")
DB_PASSWORD = quote(password, safe='')

db = SQLDatabase.from_uri(
    f"postgresql+psycopg2://{os.getenv("DB_USER")}:{DB_PASSWORD}@{os.getenv("DB_HOST")}/{os.getenv("DB_NAME")}")

# Declaring LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    google_api_key=os.getenv("GEMINI_API_KEY")
)
chain = create_sql_query_chain(llm, db)
response = chain.invoke({
    "question": "Houses sold in enflied 2022"
})
response = response.replace("```", "").replace("sql", "")

if __name__ == "__main__":
    print(response)
    print("----------")
    print(db.run(response))

