import os
from dotenv import load_dotenv
from urllib.parse import quote
from datetime import datetime, timedelta
from pprint import pprint, pformat

# LangChain Modules
from langchain.agents import initialize_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, FewShotPromptTemplate, PromptTemplate, \
    SystemMessagePromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS

# Directory modules
from Valora.agent_tools import *


load_dotenv("../.env")

# Environment Variables
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

LANGCHAIN_TRACING_V2 = True
LANGCHAIN_ENDPOINT = "https://api.smith.langchain.com"
LANGCHAIN_API_KEY = str(os.getenv("LANGCHAIN_API_KEY"))
LANGCHAIN_PROJECT = "pr-roasted-prefix-54"

DB_PASSWORD = quote(os.getenv("DB_PASSWORD"))
DB = SQLDatabase.from_uri(
    f"postgresql+psycopg2://{os.getenv("DB_USER")}:{DB_PASSWORD}@{os.getenv("DB_HOST")}/{os.getenv("DB_NAME")}")

# Defining LLM
LLM = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.0)
conversational_memory = ConversationBufferWindowMemory(
    memory_key='chat_history',
    k=5,
    return_messages=True
)

# Templates
RESPONSE_TEMPLATE = """\
You are an expert analyst in the real estate industry tasked with answering\
a broad range of questions.

Generate an informative, comprehensive, and coherent response\
while maintaining a concise structure. Your response should be based on\
the provided search results (content) and data from within our database.\
Use a helpful tone and combine the search results and the data to form your response.\
For readability, include bullet points where necessary. When mentioning prices,\
use a single pound sign at the start of the number, include commas for every thousand,\
and round to the nearest pound.

Anything between the following 'context' block is retrieved from a knowledge bank\
and is not part of the conversation between you and the user. Use the knowledge bank\
to provide information appropriate to the user's question:

<context>
    {context}
</context>

REMEMBER: Use the chat history to answer the user's question.\
If no relevant context is available and you cannot use the chat history,\
simply reply with "Hmm, that one I'm not sure about." Only do this if both\
the chat history and context data cannot be used to answer the question. Your response\
should be no more than 250 words and remain concise, avoiding unnecessary elaboration.\
Do not speak negatively about the data sources. Merge the search results and database information\
to create a unified answer. In your response, avoid phrases like "Our resources"—\
you are the information bank, so speak with authority. Provide a well-rounded answer,\
resolving any conflicting data by averaging the differences or combining the information logically.\
Ensure the final answer is consistent and conflict-free, with no lists of conflicting values.\
If you have to average out the prices, return the averaged out prices as your answer

Question: {input}

Below is the chat history; use it to inform your answer if needed:
{chat_history}

Use the history to gain insight into the user's intent. If the context is irrelevant to the question\
and the history doesn't help, respond with "Hmm, that one I'm not sure about."

The date is {date}.
"""


FEW_SHOT_PREFIX = """
You are an agent designed to interact with a SQL database.\
Given an input question, create a syntactically correct {dialect} query to run,\
then look at the results of the query and return the answer.

Unless the user specifies a specific number of examples they wish to obtain, always limit your query\
to at most {top_k} results.You can order the results by a relevant column to return the most interesting examples\
 in the database.Never query for all the columns from a specific table, only ask for the relevant columns given the question.\
You have access to tools for interacting with the database.


Only use the given tools. Only use the information returned by the tools to construct your final answer.\
You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query\
and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

If the question does not seem related to the database, just return "I don't know" as the answer.\
If you try to query a particular district and it doesn't work. use the LIKE ability to make it work. for example\
SELECT price_paid FROM property_data WHERE district LIKE '%KENSINGTON%';
For property types, they're all stored with the first letter a capital and the rest lower case. for example\
Detached, Flat, Maisonette

When the output is relating to prices or prices are being spoken about ensure that you use proper formatting.\
That means putting only one pound sign before the number.\
"""


# Few Shot Examples
# TODO: Add more examples with wider range (may improve consistency)
few_shot_examples = [
    {
        "input": "what's the average price of a house in london",
        "query": f"""
                            SELECT AVG(price_paid)
                            FROM property_data
                            WHERE town = 'LONDON';
                        """
    },
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


# Configuring SQL Agent
def configure_sql_agent():
    """
    :return: SQL Agent
    """
    few_shot_example_selector = SemanticSimilarityExampleSelector.from_examples(
        few_shot_examples,
        GoogleGenerativeAIEmbeddings(model="models/embedding-001"),
        FAISS,
        k=5,
        input_keys=["input"]
    )

    few_shot_prompt = FewShotPromptTemplate(
        example_selector=few_shot_example_selector,
        example_prompt=PromptTemplate.from_template(
            "User Input: {input}\nSQL Query:{query}\n\n"    # Using the keys from the few shot examples to create the prompt
        ),
        # input_variables=["input", "dialect", "top_k", "history"],
        input_variables=["input", "dialect", "top_k"],
        prefix=FEW_SHOT_PREFIX,
        suffix="",
    )

    sql_agent_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate(prompt=few_shot_prompt),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
    ])

    SQL_AGENT = create_sql_agent(llm=LLM, db=DB, verbose=True, agent_type="tool-calling", prompt=sql_agent_prompt)
    return SQL_AGENT


def configure_topic_agent():
    """
    :return: Get topics agent
    """
    # Create response schemas
    response_schemas = [
        ResponseSchema(name="location", description="The location to search for properties"),
        ResponseSchema(name="min_price", description="Minimum Price"),
        ResponseSchema(name="max_price", description="Maximum Price"),
        ResponseSchema(name="property_type", description="Type of property (e.g., house, flat, detached)"),
    ]

    # Create the parser
    # we
    parser = StructuredOutputParser.from_response_schemas(response_schemas)

    template = """\
    Extract the following information from the user's question about property search:
    1. Location
    2. Minimum Price (if mentioned)
    3. Maximum Price (if mentioned)
    4. Property Type has to be one of: detached, semi-detached, terraced, flat, maisonette, (if mentioned)
    
    If any information is not provided, just leave it blank
    
    User question: {input}
    
    {format_instructions}
    """
    prompt = PromptTemplate(
        input_variables=["input"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
        template=template
    )
    chain = prompt | LLM | parser
    return chain


# All agents finally initialised
llm_prompt = ChatPromptTemplate.from_template(RESPONSE_TEMPLATE)
LLM_CHAIN = (llm_prompt | LLM | StrOutputParser())
SQL_AGENT = configure_sql_agent()
TOPIC_CHAIN = configure_topic_agent()

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in STORE:
        STORE[session_id] = ChatMessageHistory()
    return STORE[session_id]

STORE = {}
with_message_history = RunnableWithMessageHistory(
    LLM_CHAIN,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)


async def create_context(question):
    # Processing all Agents
    sql_agent_task = asyncio.create_task(SQL_AGENT.ainvoke({"input": question}))
    topic_chain_task = asyncio.create_task(TOPIC_CHAIN.ainvoke({"input": question}))
    access_internet_task = asyncio.create_task(access_internet(question))

    sql_agent_result, topic_chain_result, access_internet_result = await asyncio.gather(
        sql_agent_task,
        topic_chain_task,
        access_internet_task,
        return_exceptions=True
    )

    # Removing empty fields
    topic_chain_result = {key: value for key, value in topic_chain_result.items() if topic_chain_result[key].strip()}

    # PropertyPortal Tool Activation
    zoopla_task = asyncio.create_task(search_zoopla(PropertySearchInput(**topic_chain_result)))
    rightmove_task = asyncio.create_task(search_rightmove(PropertySearchInput(**topic_chain_result)))
    onthemarket_task = asyncio.create_task(search_onthemarket(PropertySearchInput(**topic_chain_result)))

    zoopla_result, rightmove_result, onthemarket_result = await asyncio.gather(
        zoopla_task,
        rightmove_task,
        onthemarket_task,
        return_exceptions=True
    )

    portal_results = [result.dict() for result in rightmove_result]
    if zoopla_result != None:
        portal_results.append([result.dict() for result in zoopla_result])
    if onthemarket_result != None:
        portal_results.append([result.dict() for result in onthemarket_result])

    return {
        "sql_agent_result": sql_agent_result,
        "property_portal_result": portal_results,
        "access_internet_result": access_internet_result
    }


import asyncio
async def get_llm_response(question):
    context = await create_context(question)

    # chain = RunnableWithMessageHistory(
    #     RunnablePassthrough.assign(
    #         context=lambda _: context,
    #         input=lambda x: x['input']
    #     ) | LLM_CHAIN,
    #     lambda session_id: conversational_memory,
    #     input_messages_key="input",
    #     history_messages_key="chat_history"
    # )

    # response = await chain.invoke(
    #     {"input": question},
    #     config={"configurable": {"session_id": "my_session"}}
    # )

    response = await with_message_history.ainvoke(
        {"input": question, "context": context, "chat_history": STORE, "date": datetime.now()},
        config={"configurable": {"session_id": "abc123"}}
    )

    return response


if __name__ == "__main__":
    asyncio.run(get_llm_response("average price of a house in enfield"))
    # asyncio.run(create_context("average price of a house in enfield"))
