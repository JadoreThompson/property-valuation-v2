import os
from dotenv import load_dotenv
from urllib.parse import quote
from datetime import datetime, timedelta

from operator import itemgetter
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool

from langchain_community.agent_toolkits import create_sql_agent
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
)

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from dojo import ROOT_DIR
from db_connection import get_db_conn


load_dotenv(os.path.join(ROOT_DIR, ".env"))
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

LANGCHAIN_TRACING_V2 = True
LANGCHAIN_ENDPOINT = "https://api.smith.langchain.com"
LANGCHAIN_API_KEY = str(os.getenv("LANGCHAIN_API_KEY"))
LANGCHAIN_PROJECT = "pr-roasted-prefix-54"

few_shot_examples = [
    {
        "input": "what's a trend you can see from the house prices last year and this year for enfield",
        "query": f"""
                        SELECT ((AVG(CASE WHEN year = {datetime.today().year} THEN price_paid END) -
                        AVG(CASE WHEN year = {(datetime.today() - timedelta(days=365)).year} THEN price_paid END)) / 
                        AVG(CASE WHEN year = {(datetime.today() - timedelta(days=365)).year} THEN price_paid END)) * 100 AS percentage_change
                        FROM property_data
                        WHERE district = 'ENFIELD';
                    """
    },
    {
        "input": "what's the average house price in Barnet for this year?",
        "query": f"""
                        SELECT AVG(price_paid) AS average_price
                        FROM property_data
                        WHERE district = 'BARNET'
                        AND year = {datetime.today().year};
                    """
    },
    {
        "input": "how many properties were sold in Greenwich last year?",
        "query": f"""
                        SELECT COUNT(*) AS properties_sold
                        FROM property_data
                        WHERE district = 'GREENWICH'
                        AND year = {(datetime.today() - timedelta(days=365)).year};
                    """
    },
    {
        "input": "what's the highest price paid for a property in Camden this year?",
        "query": f"""
                        SELECT MAX(price_paid) AS highest_price
                        FROM property_data
                        WHERE district = 'CAMDEN'
                        AND year = {datetime.today().year};
                    """
    },
    {
        "input": "what's change in house prices between last year and this year for kensington",
        "query":  f"""
                        SELECT ((AVG(CASE WHEN year = {datetime.today().year} THEN price_paid END) -
                        AVG(CASE WHEN year = {(datetime.today() - timedelta(days=365)).year} THEN price_paid END)) / 
                        AVG(CASE WHEN year = {(datetime.today() - timedelta(days=365)).year} THEN price_paid END)) * 100 AS percentage_change
                        FROM property_data
                        WHERE district LIKE '%KENSINGTON%';
                    """
    },
    {
        "input": "how many houses sold last year in enfield?",
        "query": f"""
                        SELECT COUNT(*)
                        FROM property_data
                        WHERE district = 'ENFIELD' AND year = {datetime.today().year};
                    """
    }
]

from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_google_genai import GoogleGenerativeAIEmbeddings

query_example_selector = SemanticSimilarityExampleSelector.from_examples(
    few_shot_examples,
    GoogleGenerativeAIEmbeddings(model="models/embedding-001"),
    FAISS,
    k=5,
    input_keys=["input"],
)

system_prefix = """You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most {top_k} results.
You can order the results by a relevant column to return the most interesting examples in the database.
Never query for all the columns from a specific table, only ask for the relevant columns given the question.
You have access to tools for interacting with the database.
Only use the given tools. Only use the information returned by the tools to construct your final answer.
You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

If the question does not seem related to the database, just return "I don't know" as the answer. If you try to query a particular
district and it doesn't work. use the LIKE ability to make it work. for example SELECT price_paid FROM property_data WHERE district LIKE '%KENSINGTON%';

Here are some examples of user inputs and their corresponding SQL queries:"""

few_shot_prompt = FewShotPromptTemplate(
    example_selector=query_example_selector,
    example_prompt=PromptTemplate.from_template(
        "User input: {input}\nSQL query: {query}"
    ),
    input_variables=["input", "dialect", "top_k"],
    prefix=system_prefix,
    suffix="",
)

full_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate(prompt=few_shot_prompt),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ]
)

# Connecting to Database
DB_PASSWORD = quote(os.getenv("DB_PASSWORD"), safe='')
db = SQLDatabase.from_uri(
    f"postgresql+psycopg2://{os.getenv("DB_USER")}:{DB_PASSWORD}@{os.getenv("DB_HOST")}/{os.getenv("DB_NAME")}")

# Declaring LLM and Agent
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

sql_agent = create_sql_agent(llm=llm, db=db, agent_type="tool-calling", verbose=True, prompt=full_prompt)

# rsp = sql_agent.invoke({"input": "what's change in house prices between last year and this year for kensington"})
# print(rsp["output"])
