import psycopg2
import argon2.exceptions
from argon2 import PasswordHasher

# FastAPI Modules
from fastapi import HTTPException, APIRouter
from fastapi.responses import JSONResponse

# Directory Modules
from API.models import *
from API.robot import get_existing_user, get_insert_data
from db_connection import get_db_conn


# Environment Variables
ph = PasswordHasher()
auth = APIRouter(prefix="/auth", tags=["auth"])


@auth.post("/signup")
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
                return_data = cur.fetchone()
                conn.commit()

                if return_data is None:
                    raise HTTPException(status_code=400, detail="Something went wrong")
                return JSONResponse(status_code=200, content={"user_id": return_data[0]})

            except psycopg2.Error as e:
                conn.rollback()
                print("Signup, Psycopg2 Error: ", str(e))
                raise HTTPException(status_code=500, detail="Something went wrong")


@auth.post("/login")
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
                cur.execute("SELECT id FROM users WHERE email = %s;", (user.email, ))
                existing_user = cur.fetchone()
                if not existing_user:
                    raise HTTPException(status_code=409, detail="User doesn't exist")

                # Passwords don't match
                cur.execute("SELECT password FROM users WHERE email = %s;", (user.email,))
                password = cur.fetchone()
                if not ph.verify(password[0], user.password):
                    raise HTTPException(status_code=401, detail="Invalid credentials")

                return JSONResponse(status_code=200, content={"user_id": existing_user[0]})
            except psycopg2.Error as e:
                conn.rollback()
                print("Login, Psycopg2 Error: ", str(e))
                raise HTTPException(status_code=500, detail="Something went wrong")
            except argon2.exceptions.VerifyMismatchError as e:
                conn.rollback()
                print("Login, Argon2Error: ", str(e))
                raise HTTPException(status_code=410, detail="Invalid credentials")
