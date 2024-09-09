import json

import argon2.exceptions
from argon2 import PasswordHasher

# FastAPI Modules
import psycopg2
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

# Directory Modules
from webapi.models import (
    User,
    SignUpUser,
    AuthResponse,
    ChatRequest,
    ChatResponse,
    ContactSales,
    ContactSalesResponse
)
from propai.prompt_gen import get_llm_response
from db_connection import get_db_conn


#Enviroment Variables
ph = PasswordHasher()

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
                cur.execute("""\
                    SELECT 1\
                    FROM users\
                    WHERE email = %s; 
                """, (user.email,))
                existing_user = cur.fetchone()
                if existing_user:
                    raise HTTPException(status_code=409, detail="User already exists")

                user_dict = dict(user)
                user_dict["password"] = ph.hash(user_dict["password"])

                cols = [key for key in user_dict if user_dict[key] != None]
                placeholders = ", ".join(["%s"] * len(cols))
                values = [(user_dict[key], ) for key in cols]

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
                cur.execute("""\
                    SELECT password\
                    FROM users\
                    WHERE email = %s; 
                """, (user.email, ))
                existing_user = cur.fetchone()

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


@app.post("/contact-sales", response_model=ContactSalesResponse)
async def contact_sales(contact_sales_form: ContactSales):
    """
    :param contact_sales_form:
    :return: HTTPException:
        - 200, email supplied and new user added to Contact Sales Table
        - 400, no email supplied
        - 409, user with email already exists
        - 500, internal server error
    """

    try:
        assert contact_sales_form
    except ValidationError as e:
        print(e)
        raise HTTPException(status_code=429, detail=str(e))

    contact_sales_form_dict = dict(contact_sales_form)
    columns = [key for key in contact_sales_form_dict if contact_sales_form_dict[key] != None]
    insert_values = [(contact_sales_form_dict[key], ) for key in contact_sales_form_dict]
    placeholders = ", ".join(["%s"] * len(columns))

    if not contact_sales_form.email:
        raise HTTPException(status_code=400, detail="You must provide an email")

    with get_db_conn() as conn:
        with conn.cursor() as cur:
            try:
                # Checking if user exists
                cur.execute("""\
                    SELECT 1\
                    FROM contact_sales\
                    WHERE email = %s;\
                """, (contact_sales_form.email, ))
                existing_user = cur.fetchone()
                if existing_user:
                    raise HTTPException(status_code=409, detail="User with email already exists")

                # Adding to Contact Sales Table
                cur.execute(f"""
                        INSERT INTO contact_sales({", ".join(columns)})\
                        VALUES ({placeholders})\
                        RETURNING id;\
                """, insert_values)
                conn.commit()

                user_id = cur.fetchone()
                if not user_id:
                    raise Exception
                return ContactSalesResponse(status=200, response="Successfully Added")

            except psycopg2.Error as e:
                conn.rollback()
                print("Psycopg2 Error: ", str(e))
                raise HTTPException(status_code=500, detail="Something went wrong please try again.")


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=80, reload=True)
