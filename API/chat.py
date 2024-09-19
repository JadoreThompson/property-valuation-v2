import asyncio

import psycopg2

# FastAPI Modules
from fastapi import HTTPException, APIRouter
from fastapi.responses import JSONResponse

# Directory Modules
from API.models import (
    #'ChatResponse,
    ChatRequest,
    ChatMessage,
    EditMessage,
    MessageType,
    LoadChatRequest,
    RoomRequest
)
from API.robot import get_insert_data
from Valora.prompt_gen import get_llm_response
from db_connection import get_db_conn


chat = APIRouter(prefix='/chat', tags=["chat"])


@chat.post("/get-response")
async def get_response(rsp_req: ChatMessage):
    try:
        question = rsp_req.message
        task = asyncio.create_task(add_chat(rsp_req))

        rsp = await get_llm_response(question)
        rsp_model = ChatMessage(message=rsp, room_id=rsp_req.room_id, type=MessageType.BOT.value)
        rsp_task = asyncio.create_task(add_chat(rsp_model))

        await task, rsp_task

        return JSONResponse(
            status_code=200, content={"response": rsp}
        )

    except Exception as e:
        print(f"Get Response: {str(e)}")
        raise HTTPException(status_code=500, detail="Something went wrong, please try again")


@chat.post("/add-chat")
async def add_chat(message: ChatMessage):
    if message.type not in [item.value for item in MessageType]:
        return JSONResponse(
            status_code=400, content={"detail": "Invalid message type"}
        )

    with get_db_conn() as conn:
        with conn.cursor() as cur:
            try:
                cols, placeholders, vals = get_insert_data(message.dict())
                cur.execute(f"""\
                INSERT INTO messages({", ".join(cols)})
                VALUES ({placeholders})
                RETURNING id;
            """, vals)
                conn.commit()
                message_id = cur.fetchone()
                if message_id:
                    return JSONResponse(
                        status_code=200, content={"message_id": message_id[0]}
                    )
                else:
                    raise HTTPException(
                        status_code=500, detail="Failed to save message"
                    )
            except psycopg2.Error as e:
                conn.rollback()
                print(f"Add Chat: {type(e).__name__} - {str(e)}")
                raise HTTPException(
                    status_code=500, detail="Internal Server Error"
                )


@chat.put("/edit-chat")
async def edit_chat(message: EditMessage):
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("""\
                    SELECT 1
                    FROM messages
                    WHERE id = %s;
                """, (message.message_id, ))
                if cur.fetchone() is None:
                    raise HTTPException(
                        status_code=403, detail="Message doesn't exist"
                    )

                cols, _, values = get_insert_data(message.dict())
                cur.execute("""\
                    UPDATE messages\
                    SET message = '%s'\
                    WHERE room_id = %s AND id = %s\
                    RETURNING id;
                """, values)
                conn.commit()

                if cur.fetchone() is None:
                    raise HTTPException(
                        status_code=500,
                        detail="Something went wrong"
                    )

                raise HTTPException(
                    status_code=200, detail="Message Edited"
                )

            except psycopg2.Error as e:
                print(f"Edit Chat: {type(e).__name__} - {str(e)}")


@chat.post("/load-chats")
async def load_chats(load_request: LoadChatRequest):
    """
    :param load_request:
    :return:
    """
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("""\
                    SELECT type, message
                    FROM messages
                    WHERE room_id = %s;
                """, (load_request.room_id, ))
                chats = cur.fetchall()
                if chats is None:
                    raise HTTPException(
                        status_code=404, detail="No messages exist for room"
                    )
                return JSONResponse(
                    status_code=200, content={"chats": chats}
                )
            except psycopg2.Error as e:
                conn.rolback()
                raise HTTPException(
                    status_code=500, detail="Internal server error, please try again"
                )
