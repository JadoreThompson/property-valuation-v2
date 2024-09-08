# FastAPI Modules
import psycopg2
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Directory Modules
from webapi.models import ChatRequest, ChatResponse, ContactSales, ContactSalesResponse
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
                cur.execute(f"""\
                        INSERT INTO contact_sales({", ".join(columns)})\
                        VALUES ({placeholders})\
                        RETURNING id;\
                """, (insert_values, ))
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
