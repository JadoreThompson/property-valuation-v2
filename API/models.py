import re

# Pydantic and Fast API related
from pydantic import BaseModel, Field, field_validator, ValidationError, model_validator
from typing import Optional, List, Any


class HTTPResponse(BaseModel):
    status: int


class User(BaseModel):
    email: str
    password: str


class SignUpUser(User):
    fname: str
    sname: str


class AuthResponse(HTTPResponse):
    detail: str


class ChatRequest(BaseModel):
    question: str


class ChatResponse(HTTPResponse):
    response: str


class ContactSalesForm(BaseModel):
    name: str
    email: str
    phone: str
    employees: int = Field(ge=1)
    message: str = Field(max_length=200)


if __name__ == "__main__":
    user = ContactSalesForm(
        name="ja",
        email="email",
        phone="phone",
        employees=0,
        message="hi"
    )
