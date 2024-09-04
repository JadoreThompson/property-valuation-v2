import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from propai import prompt_gen


api = FastAPI()

origins = [
    "http://127.0.0.1:5000",
    "http://127.0.0.1:5000/dashboard",
    "https://localhost:5000",
    "https://localhost:5000/dashboard"
]
api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class Message(BaseModel):
    message: str


@api.post("/get-response")
async def get_response(message: Message):
    try:
        rsp = prompt_gen.sql_agent.invoke({"input": message.message})
        result = rsp["output"]
        if result:
            return JSONResponse(status_code=200, content={"response": result})
    except Exception as e:
        print(f"(API) Get Response, {e}")
        raise HTTPException(status_code=404, detail="Sorry I couldn't answer that, try something else")


if __name__ == "__main__":
    uvicorn.run("api:api", port=80)
