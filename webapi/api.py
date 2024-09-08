# FastAPI Modules
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Directory Modules
from webapi.models import ChatRequest, ChatResponse
from propai.prompt_gen import get_llm_response
from db_connection import get_db_conn


#Enviroment Variables
origins = [
    "http://127.0.0.1:5000",
    "http://127.0.0.1:5000/dashboard",
    "https://localhost:5000",
    "https://localhost:5000/dashboard"
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_credentials=True,
)


@app.post("/get-response", response_model=ChatResponse)
async def get_response(chat_request: ChatRequest):
    """
    :param chat_request:
    :return: ChatResponse(JSON):
        - response: str
    """
    try:
        question = chat_request.question
        rsp = await get_llm_response(question)
        return ChatResponse(response=rsp)
    except Exception as e:
        print(f"Get Response: {str(e)}")
        raise HTTPException(status_code=500, detail="Something went wrong, please try again")


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=80, reload=True)
