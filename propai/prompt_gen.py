import os
from dotenv import load_dotenv
from urllib.parse import quote
from datetime import datetime, timedelta
from pprint import pprint, pformat

# LangChain Modules
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
from propai.agent_tools import access_internet


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

# Templates
RESPONSE_TEMPLATE = """\
You are an expert analyst in the real estate industry tasked with answering\
a broad range of questions.

Generate an informative, comprehensive and coherent response\
all the while maintaining a concise structure. Your response should be based around\
the provided search results (content) and data from within our database.\
You should use a helpful tone. Combine the search results and the data together to form your response.\
You should use bullet points in your answer for readability when necessary. When talking about prices\
remember to put only one pound sign at the beginning of the number and commas for every thousand\
as well as rounding to the nearest pound. 


Below is the chat history, use the chat history to answer the user's question if needed

{history}

Anything between the following 'context' block is retrieved form a knowledge bank\
and is not part of the conversation between the user.

<context>
    {context}
<context/>

You must use the history to gain insight into what the user is trying to ask if he history is there.\
If there is nothing in the context relevant to the question at hand, and the history doesn't help\
to answer the user's question just respond with "Hmm, that one I'm not sure about".

REMEMBER: Use the history to answer  the user's question.\
If there is no relevant context, and you can't use the chat history to answer the user's question\
simply reply with "Hmm, that one I'm not sure about". Only do this if you can't use the chat history\
and the context data can't be used to answer the question. Your response should be no more than\
250 words.  

Question: {input}\
"""


FEW_SHOT_PREFIX = """
You are an agent designed to interact with a SQL database.\
Given an input question, create a syntactically correct {dialect} query to run,\
then look at the results of the query and return the answer.

Unless the user specifies a specific number of examples they wish to obtain, always limit your query\
to at most {top_k} results.You can order the results by a relevant column to return the most interesting examples\
 in the database.Never query for all the columns from a specific table, only ask for the relevant columns given the question.\
You have access to tools for interacting with the database.

Below is the current history of messages. If the history is there, use the history of messages to get context as to what\
the SQL query should look like. Only generate a query if you can get the necessary pieces of information relating  to the\
table structure.

History: 
{history}

Only use the given tools. Only use the information returned by the tools to construct your final answer.\
You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query\
and try again.

DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

If the question does not seem related to the database, just return "I don't know" as the answer.\
If you try to query a particular district and it doesn't work. use the LIKE ability to make it work. for example\
SELECT price_paid FROM property_data WHERE district LIKE '%KENSINGTON%';

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
"""We Use this to retrieve the most relating items in the few shot examples list"""
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
    input_variables=["input", "dialect", "top_k", "history"],
    prefix=FEW_SHOT_PREFIX,
    suffix="",
)

sql_agent_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate(prompt=few_shot_prompt),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
])

SQL_AGENT = create_sql_agent(llm=LLM, db=DB, verbose=True, agent_type="tool-calling", prompt=sql_agent_prompt)

# Defining Chain
llm_prompt = ChatPromptTemplate.from_template(RESPONSE_TEMPLATE)

CHAIN = (
    # {"context": access_internet, "input": RunnablePassthrough()}
    # ^ Invocation
    llm_prompt  # The keys above are fed to the prompt
    | LLM  # Prompt is then fed to LLM
    | StrOutputParser() # LLM Output is the fed through the Parser to a str
)


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in STORE:
        STORE[session_id] = ChatMessageHistory()
    return STORE[session_id]


STORE = {}
with_message_history = RunnableWithMessageHistory(
    CHAIN,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)


async def context_chain(question:str) -> dict:
    """
    :param question:
    :return:
        - dict:
            - internet_results: List[str]
            - sql_result: str
    """

    # Task for getting SQL Agent and Access to input
    access_internet_task = asyncio.create_task(access_internet(question))
    sql_agent_task = asyncio.create_task(SQL_AGENT.ainvoke({"input": question, "history": STORE}))
    # OG: sql_agent_task = asyncio.create_task(SQL_AGENT.ainvoke({"input": question}))

    access_internet_result, sql_agent_result = await asyncio.gather(
        access_internet_task, sql_agent_task
    )

    return {
        "internet_result": access_internet_result,
        "sql_result": sql_agent_result
    }


# Example Usage
async def get_llm_response(): # question):
    """
        :param: question:
        :return: LLM Response
    """
    while True:
        question = input("You: ")

        context = await context_chain(question)

        # OG: response = await CHAIN.ainvoke({"context": context, "input": question})

        response = await with_message_history.ainvoke(
            {"context": context, "input": question, "history": STORE},
            config={"configurable": {"session_id": "abc123"}}
        )
        print("Bot: ", response)

    # OG: return response


import asyncio
if __name__ == "__main__":
    asyncio.run(get_llm_response())
