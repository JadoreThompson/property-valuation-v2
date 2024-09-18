import json
import psycopg2
from typing import List, Tuple, Any
import aiohttp
import argon2.exceptions
from argon2 import PasswordHasher

# FastAPI Modules
import pydantic
#from pydantic import ValidationError
from pydantic_core import ValidationError

import uvicorn
from fastapi import FastAPI, HTTPException,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Directory Modules
from API.models import *
from Valora.prompt_gen import get_llm_response
from db_connection import get_db_conn
from API.tele import *


def get_existing_user(cur, email, table="users", field='1'):
    cur.execute(f"""\
        SELECT {field}\
        FROM {table}\
        WHERE email = %s;
    """, (email, ))
    return cur.fetchone()


def get_insert_data(data: dict) -> Tuple[List, str, List]:
    cols = [key for key in data if data[key] != None]
    placeholders = ", ".join(["%s"] * len(cols))
    values = [(data[key]) for key in cols]
    return cols, placeholders, values


max_rooms = {
    PricingPlan.BASIC.value: 1,
    PricingPlan.ENTERPRISE.value: 5,
    PricingPlan.PROFESSIONAL.value: 20
}

#Enviroment Variables
ph = PasswordHasher()

origins = [
    "http://127.0.0.1:5000",
    "http://127.0.0.1:5000/dashboard",
    "https://localhost:5000",
    "https://localhost:5000/dashboard",
    "http://127.0.0.1:5000"
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_credentials=True,
)


# Custom ValidationError
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, e: ValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Form fields not submitted correctly", "message": 'fail'}
    )


# Custom normal Exception Handler
@app.exception_handler(Exception)
async def custom_exception_handler(request: Request, e: Exception):
    return JSONResponse(status_code=400, content={"detail": f"{type(e).__name__} - {str(e)}"})


@app.get("/")
async def read_root():
    return {"status_code": 200, "detail": "Success"}


@app.post("/signup")
async def signup(user: SignUpUser):
    """
    :param user: SignUpUser
    :return: Insert into Users Table
    """

    with get_db_conn() as conn:
        with conn.cursor() as cur:
            try:
                # Checking if someone already exists
                if get_existing_user(cur=cur, email=user.email):
                    raise HTTPException(status_code=409, detail="User already exists")

                user_dict = dict(user)
                user_dict["password"] = ph.hash(user_dict["password"])
                cols, placeholders, values = get_insert_data(user_dict)

                # Inserting to Users Table
                cur.execute(f"""\
                    INSERT INTO users ({", ".join(cols)})\
                    VALUES ({placeholders})\
                    RETURNING id;
                """, values)
                user = cur.fetchone()
                conn.commit()

                if user is None:
                    raise HTTPException(status_code=400, detail="Something went wrong")
                return AuthResponse(status=200, detail="Successfully Signed Up")

            except psycopg2.Error as e:
                conn.rollback()
                print("Signup, Psycopg2 Error: ", str(e))
                raise HTTPException(status_code=500, detail="Something went wrong")


@app.post("/login")
async def login(user: User):
    """
    :param user:
    :return: HTTPException:
        - 200, Successfully logged in, both email and password match
        - 409, User with email doesn't exist
        - 401, Passwords don't match
        - 410
    """

    with get_db_conn() as conn:
        with conn.cursor() as cur:
            try:
                # Checking if someone already exists
                existing_user = get_existing_user(cur=cur, email=user.email, field='password')
                if not existing_user:
                    raise HTTPException(status_code=409, detail="User doesn't exist")

                # Passwords don't match
                if not ph.verify(existing_user[0], user.password):
                    raise HTTPException(status_code=401, detail="Invalid credentials")
                return AuthResponse(status=200, detail="Successfully logged in")

            except psycopg2.Error as e:
                conn.rollback()
                print("Login, Psycopg2 Error: ", str(e))
                raise HTTPException(status_code=500, detail="Something went wrong")
            except argon2.exceptions.VerifyMismatchError as e:
                conn.rollback()
                print("Login, Argon2Error: ", str(e))
                raise HTTPException(status_code=410, detail="Invalid credentials")


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
        return ChatResponse(status=200, response=rsp)
    except Exception as e:
        print(f"Get Response: {str(e)}")
        raise HTTPException(status_code=500, detail="Something went wrong, please try again")


@app.post("/contact-sales")
async def contact_sales(form: ContactSalesForm):
    """
    :param ContactSalesForm:
    :return:
    """
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            try:
                if get_existing_user(cur=cur, email=form.email, table="contact_sales"):
                    raise HTTPException(status_code=409, detail="User has already contacted sales")

                # Insert
                cols, placeholders, vals = get_insert_data(form.dict())
                cur.execute(f"""\
                    INSERT INTO contact_sales({", ".join(cols)})
                    VALUES ({placeholders})
                    RETURNING id;
                """, vals)
                conn.commit()
                if cur.fetchone():
                    raise HTTPException(status_code=200, detail="We'll Contact You Soon")
            # TODO: Perform Action on the form e.g. Send Email
            except psycopg2.Error as e:
                conn.rollback()
                print(f"Contact Sales: {type(e).__name__} - {str(e)}")
                raise HTTPException(status_code=500, detail="Internal Server Error")


# TODO: Improve Security on endpoint
@app.post("/checkout")
async def checkout(form: CheckoutForm):
    """
    :param form[CheckoutForm]:
    :return:
        - 200, success
        - 404, email doesn't exists
        - 500, DB error
    """
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            try:
                if not get_existing_user(cur=cur, email=form.email):
                    raise HTTPException(
                        status_code=404,
                        detail="Please sign up"
                    )

                # Updating pricing plan
                cur.execute("""\
                    UPDATE users
                    SET pricing_plan = %s
                    WHERE email = %s
                    RETURNING id;
                """, (form.pricing_plan.value.strip(), form.email, ))
                conn.commit()
                if not cur.fetchone():
                    raise psycopg2.Error

                raise HTTPException(
                    status_code=200,
                    detail="Payment Successful"
                )
            except psycopg2.Error as e:
                conn.rollback()
                print(f"Checkout: {type(e).__name__} - {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail="Internal Server Error, please try again"
                )


@app.post("/create-room")
async def create_room(room_request: CreateRoomRequest):
    """
    :param room_request:
    :return:
        - 200, Inserted new Room to DB
    """
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("""\
                    SELECT id, pricing_plan
                    FROM users
                    WHERE email = %s;
                """, (room_request.email, ))
                admin_data = cur.fetchall()
                room_request = room_request.dict()
                room_request["admin_id"] = admin_data[0][0]

                if admin_data is None:
                    raise HTTPException(
                        status_code=401,
                        detail="Must be logged in"
                    )

                # Check current room limit
                room_limit = max_rooms[admin_data[0][1]]
                print(f"{room_request["email"]} limit is {room_limit}")

                cur.execute("""\
                    SELECT COUNT(room_name) AS room_count, 
                       ARRAY_AGG(room_name) AS room_names
                    FROM rooms
                    WHERE admin_id = %s; 
                """, (room_request["admin_id"], ))
                room_data = cur.fetchall()
                print("Room Data: ", room_data)
                print(room_data[0][1])
                if room_data:
                    if room_data[0][0] == room_limit:
                        raise HTTPException(
                            status_code=412,
                            detail="You've reached your limit"
                        )
                    if room_request["room_name"] in room_data[0][1]:
                        raise HTTPException(
                            status_code=405,
                            detail="yo"
                        )

                # Inserting into table
                del room_request["email"]
                cols, placeholders, vals = get_insert_data(room_request)

                cur.execute(f"""\
                    INSERT INTO rooms ({", ".join(cols)})
                    VALUES ({placeholders})
                    RETURNING id;
                """, vals)
                conn.commit()

                room_id = cur.fetchone()
                if room_id is None:
                    raise psycopg2.Error
                raise HTTPException(
                    status_code=200, detail="Successfully created room"
                )
            except psycopg2.Error as e:
                conn.rollback()
                print(f"Create Room: {type(e).__name__} - {str(e)}")
                raise HTTPException(
                    status_code=500, detail="Internal Server Error. Please try again"
                )

if __name__ == "__main__":
    uvicorn.run("api:app", port=80, reload=True)
