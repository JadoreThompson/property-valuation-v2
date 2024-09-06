import os
from dotenv import load_dotenv
from urllib.parse import quote
from datetime import datetime, timedelta

from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits import create_sql_agent
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotPromptTemplate,
    FewShotChatMessagePromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
)

from dojo import ROOT_DIR


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
                        SELECT ((AVG(CASE WHEN year = {datetime.today().year} THEN price_paid END)) -
                        (AVG(CASE WHEN year = {(datetime.today() - timedelta(days=365)).year} THEN price_paid END))) / 
                        AVG(CASE WHEN year = {(datetime.today() - timedelta(days=365)).year} THEN price_paid END) * 100 AS percentage_change
                        FROM property_data
                        WHERE district LIKE '%KENSINGTON%';
                    """
    },
    {
        "input": "how many houses sold last year in enfield?",
        "query": f"""
                        SELECT COUNT(*)
                        FROM property_data
                        WHERE district = 'ENFIELD' AND year = {(datetime.today() - timedelta(days=365)).year};
                    """
    }
]

# Prompt template to format each few shot example
example_prompt = ChatPromptTemplate.from_messages([
    ("human", "{input}"),
    ("ai", "{query}"),
])
few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=few_shot_examples,
)

# Above we use the keys from the few shot examples and format into the example prompt for the model to know how to respond
final_prompt = ChatPromptTemplate.from_messages([
    ("system", """You're a information powerhouse and real estate assistant playing the role of an assistant for professionals in the
               industry"""),
    few_shot_prompt,
    ("human", "{input}"),
])

chain = final_prompt | ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.0)
rsp = chain.invoke({"input": "based on this years statistics, which areas have grown the most in average price"})
print(rsp.content)
